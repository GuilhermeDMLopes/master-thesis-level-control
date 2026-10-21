"""Limited offline ST/ECC replay, NOT a compiler or a native FORTE emulator.

Executes the actual local FBT assignments/IF statements to check their arithmetic.
Does not model WITH snapshots, queues, timers, native numeric types or concurrency.
Only use trusted repository FBTs: expressions are evaluated as Python.
"""
from pathlib import Path
import argparse
import ast
import csv
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
TYPES = ROOT / '4diac/application/PID_Whiteboard/Type Library/pid'


def expression(text):
    for old, new in [('TRUE', 'True'), ('FALSE', 'False'), ('AND', 'and'),
                     ('OR', 'or'), ('NOT', 'not')]:
        text = re.sub(r'\b' + old + r'\b', new, text)
    text = text.replace('<>', '!=')
    return re.sub(r'(?<![<>=!:])=(?!=)', '==', text)


class OfflineBlock:
    """Only the assignment/IF subset and ECC used by these two local types."""
    def __init__(self, name):
        self.xml = ET.parse(TYPES / (name + '.fbt')).getroot()
        self.values = {v.get('Name'): (False if v.get('Type') == 'BOOL' else 0.0)
                       for v in self.xml.findall('.//VarDeclaration')}
        self.events = {e.get('Name') for e in self.xml.findall('InterfaceList/EventInputs/Event')}
        self.state = self.xml.find('BasicFB/ECC/ECState').get('Name')
        self.algorithms = {}
        for alg in self.xml.findall('BasicFB/Algorithm'):
            lines, indent = [], 0
            for line in alg.find('ST').get('Text').splitlines():
                line = line.strip()
                if not line:
                    continue
                if line == 'END_IF;':
                    indent -= 1
                    continue
                if line.startswith('IF '):
                    assert line.endswith(' THEN'), line
                    lines.append('    ' * indent + 'if ' + expression(line[3:-5]) + ':')
                    indent += 1
                else:
                    lhs, rhs = line.rstrip(';').split(':=')
                    lines.append('    ' * indent + lhs.strip() + ' = ' + expression(rhs.strip()))
            assert indent == 0
            source = '\n'.join(lines)
            ast.parse(source)
            self.algorithms[alg.get('Name')] = compile(source, '<local ST subset>', 'exec')

    def trigger(self, event):
        assert event in self.events, event
        outputs = []
        for _ in range(32):
            match = None
            for edge in self.xml.findall('BasicFB/ECC/ECTransition'):
                if edge.get('Source') != self.state:
                    continue
                condition = edge.get('Condition')
                take = (condition == event if condition in self.events else
                        bool(eval(expression(condition), {'__builtins__': {}}, self.values)))
                if take:
                    match = edge
                    break
            if match is None:
                return outputs
            event = None
            self.state = match.get('Destination')
            state = self.xml.find(f"BasicFB/ECC/ECState[@Name='{self.state}']")
            for action in state.findall('ECAction'):
                if action.get('Algorithm'):
                    exec(self.algorithms[action.get('Algorithm')], {'__builtins__': {}}, self.values)
                if action.get('Output'):
                    outputs.append(action.get('Output'))
        raise AssertionError('ECC did not settle')


def demo(samples=100):
    """Follow the checked-in application's data and event connections serially.

    E_CYCLE is replaced by a Python loop: no wall-clock timing claim.
    Each row is y[k], computed u[k]; y[k] used the previously latched u[k-1].
    """
    app = ET.parse(ROOT / '4diac/application/PID_Whiteboard/PID_Whiteboard.sys').getroot()
    network = app.find('Application/SubAppNetwork')
    blocks = {fb.get('Name'): OfflineBlock(fb.get('Type'))
              for fb in network.findall('FB') if fb.get('Type') != 'E_CYCLE'}
    for fb in network.findall('FB'):
        if fb.get('Name') in blocks:
            for p in fb.findall('Parameter'):
                blocks[fb.get('Name')].values[p.get('Name')] = float(p.get('Value'))
    edges = [(e.get('Source'), e.get('Destination')) for e in network.findall('EventConnections/Connection')]
    data = [(e.get('Source').split('.'), e.get('Destination').split('.'))
            for e in network.findall('DataConnections/Connection')]
    running = False

    def dispatch(target):
        nonlocal running
        queue = [target]
        count = 0
        while queue:
            count += 1
            assert count < 100, 'Unexpected event cycle'
            name, event = queue.pop(0).split('.')
            if name == 'Cycle':
                running = event == 'START'
                continue
            for (src, port), (dst, inp) in data:
                if dst == name:
                    blocks[dst].values[inp] = blocks[src].values[port]
            for out in blocks[name].trigger(event):
                queue.extend(dst for src, dst in edges if src == name + '.' + out)
    dispatch('Process.INIT')
    assert running
    rows = []
    for k in range(1, samples + 1):
        assert running, 'Stopped on an error'
        applied_before = blocks['Process'].values['APPLIED_U']
        for src, dst in edges:
            if src == 'Cycle.EO':
                dispatch(dst)
        v = blocks['Controller'].values
        rows.append(dict(k=k, time_s=k * v['TS_ACTIVE'], pv=blocks['Process'].values['Y'],
                         sp=v['SP'], previous_applied_u=applied_before, mv=v['MV'],
                         error=v['ERROR'], p=v['P_TERM'], i=v['I_TERM'], d=v['D_TERM'],
                         raw=v['RAW'], flag=int(v['FLAG'])))
    return rows


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--csv', type=Path, help='Optional synthetic trace output')
    args = parser.parse_args()
    rows = demo()
    for row in rows[:3]:
        print(row)
    print('Final:', rows[-1])
    print('Offline ST/ECC subset replay only. No native FORTE or PLC test.')
    if args.csv:
        args.csv.parent.mkdir(parents=True, exist_ok=True)
        with args.csv.open('w', newline='', encoding='utf-8') as stream:
            writer = csv.DictWriter(stream, fieldnames=rows[0])
            writer.writeheader()
            writer.writerows(rows)
        print('Synthetic CSV:', args.csv)
