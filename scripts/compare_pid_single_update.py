"""Compare deterministic FBT subset replays; does not collect native FORTE data."""
import argparse
import csv
import json
from pathlib import Path
import sys
import tempfile
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tests'))
from test_pid_single_update import Network, unpack


def compare(output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    result = {'scope': 'Offline FBT ST/ECC subset replay; synthetic process; NOT native FORTE measurements', 'sample_time_s': 0.1, 'update_sample': 275, 'runs': {}}
    with tempfile.TemporaryDirectory() as temporary:
        project = unpack(Path(temporary))
        for label, enabled in [('fixed', False), ('single_update', True)]:
            network = Network(project, enabled=enabled).run()
            rows = []
            previous = 0.0
            for k, pv, mv, kp, ki, kd in network.rows:
                sp = 1.0 if ((int(k)-1)//50) % 2 == 0 else 0.8
                rows.append(dict(sample=int(k), time_s=k*0.1, setpoint=sp, process_output=pv, error=sp-pv, command=mv, command_change=mv-previous, proportional_gain=kp, integral_gain=ki, derivative_gain=kd))
                previous = mv
            if len(rows) != 400:
                raise RuntimeError('Expected 400 completed samples')
            with (output / (label+'.csv')).open('w', newline='', encoding='utf-8') as stream:
                writer=csv.DictWriter(stream, fieldnames=list(rows[0]))
                writer.writeheader(); writer.writerows(rows)
            result['runs'][label] = {
                'samples': len(rows),
                'iae_all_s': sum(abs(r['error'])*0.1 for r in rows),
                'iae_from_275_s': sum(abs(r['error'])*0.1 for r in rows if r['sample'] >= 275),
                'total_command_variation': sum(abs(r['command_change']) for r in rows),
                'command_change_at_275': rows[274]['command_change'],
                'final_process_output': rows[-1]['process_output'],
                'gain_updates': network.trace.count('PID_FLAG_STATE_ACCESS.SET_GAINS')}
    (output/'summary.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(result, indent=2))
    return result

if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path, help='New output directory (must not exist)')
    compare(parser.parse_args().output)
