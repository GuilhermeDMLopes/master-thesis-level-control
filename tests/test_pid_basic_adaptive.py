"""Actual FBT ST/ECC plus composite/event wiring replay; not native FORTE."""
from pathlib import Path
from collections import deque
import sys, unittest, math, csv
import xml.etree.ElementTree as E
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import verify_pid_whiteboard as runtime
from generate_pid_basic_adaptive import PROJECT,TYPES

def pairs(net,tag):return [(c.get('Source'),c.get('Destination')) for c in net.findall(tag+'/Connection')]
def logical_blocks(net):
    # Coordinates, comments and XML order are editor presentation only.
    return {f.get('Name'):(f.get('Type'),
            {p.get('Name'):p.get('Value') for p in f.findall('Parameter')})
            for f in net.findall('FB')}

def check_mapping(app,resource):
    expected=logical_blocks(app);actual=logical_blocks(resource)
    assert {k:v for k,v in actual.items() if k in expected}==expected, 'Mapped types or parameters differ'
    assert set(actual)-set(expected) <= {'START'}, 'Unexpected resource block'
    if 'START' in actual:assert actual['START'][0]=='E_RESTART'
    for tag in ['EventConnections','DataConnections']:
        wanted=set(pairs(app,tag));found=set(pairs(resource,tag))
        assert wanted <= found, 'Mapped connection missing'
        allowed={('START.COLD','Process.INIT'),('START.WARM','Process.INIT'),
                 ('START.STOP','SamplingClock.STOP')} if tag=='EventConnections' else set()
        assert found-wanted <= allowed, 'Unexpected mapped connection'

class Network:
    def __init__(self,enabled=False,bad_tuner=False,interval=0,first_update=275):
        self.root=E.parse(PROJECT/'PID_Basic_Adaptive.sys').getroot();self.net=self.root.find('Application/SubAppNetwork')
        self.composite=E.parse(TYPES/'PROCESS_IDENTIFIER.fbt').getroot();self.blocks={};self.trace=[];self.rows=[];self.running=False
        self.events=pairs(self.net,'EventConnections');self.data=pairs(self.net,'DataConnections');self.params={}
        old=runtime.TYPES;runtime.TYPES=TYPES
        try:
            for node in self.net.findall('FB'):
                name=node.get('Name');kind=node.get('Type')
                if kind=='E_CYCLE':continue
                if kind!='PROCESS_IDENTIFIER':self.blocks[name]=runtime.OfflineBlock(kind)
                for p in node.findall('Parameter'):
                    v=p.get('Value');v=v=='TRUE' if v in ['TRUE','FALSE'] else float(v)
                    self.params[name+'.'+p.get('Name')]=v
                    if name in self.blocks:self.blocks[name].values[p.get('Name')]=v
            internal=self.composite.find('FBNetwork')
            for node in internal.findall('FB'):self.blocks['Identifier.'+node.get('Name')]=runtime.OfflineBlock(node.get('Type'))
        finally:runtime.TYPES=old
        self.events += [('Identifier.'+s,'Identifier.'+d) for s,d in pairs(internal,'EventConnections')]
        self.data += [('Identifier.'+s,'Identifier.'+d) for s,d in pairs(internal,'DataConnections')]
        self.params['Identifier.ENABLE_UPDATE']=enabled
        self.params['Identifier.UPDATE_INTERVAL_SAMPLES']=interval
        self.params['Identifier.UPDATE_AT_SAMPLE']=first_update
        if bad_tuner:self.params['Identifier.DESIRED_POLE']=1.5
    def value(self,endpoint,seen=None):
        seen=set() if seen is None else seen
        if endpoint in seen:raise AssertionError('Data cycle')
        seen.add(endpoint)
        sources=[s for s,d in self.data if d==endpoint]
        if sources:return self.value(sources[0],seen)
        name,port=endpoint.rsplit('.',1)
        if name in self.blocks:return self.blocks[name].values[port]
        return self.params[endpoint]
    def deliver(self,event):
        queue=deque([event]);steps=0
        while queue:
            steps+=1
            if steps>100:raise AssertionError('Event loop')
            dst=queue.popleft();self.trace.append(dst);name,port=dst.rsplit('.',1)
            if name=='SamplingClock':self.running=port=='START';continue
            if name=='Identifier':
                queue.extend(d for s,d in self.events if s==dst);continue
            block=self.blocks[name]
            variables=[w.get('Var') for w in block.xml.findall(f"InterfaceList/EventInputs/Event[@Name='{port}']/With")]
            for v in variables:
                if any(d==name+'.'+v for _,d in self.data):block.values[v]=self.value(name+'.'+v)
            before={k:block.values[k] for k in ['I_MEMORY','E_PREV','CONTROL_OUTPUT']} if dst=='Controller.SET_GAINS' else None
            outputs=block.trigger(port)
            if before:assert before=={k:block.values[k] for k in before}
            for out in outputs:
                src=name+'.'+out;self.trace.append(src);queue.extend(d for s,d in self.events if s==src)
    def run(self):
        self.deliver('Process.INIT')
        while self.running and len(self.rows)<401:
            self.deliver('Process.REQ');p=self.blocks['Process'].values;c=self.blocks['Controller'].values
            self.rows.append((p['SAMPLE_COUNT'],p['REFERENCE'],p['PROCESS_OUTPUT'],c['CONTROL_OUTPUT'],c['KP_ACTIVE'],c['KI_ACTIVE'],c['KD_ACTIVE']))
        return self
class MinimalTests(unittest.TestCase):
    def test_fixed_matches_native_baseline(self):
        n=Network().run();self.assertEqual(len(n.rows),400)
        path=ROOT/'docs/adaptive/evidence/20261026-native-comparison/fixed-native.csv'
        with path.open() as f:reference=list(csv.DictReader(f))
        for row,ref in zip(n.rows,reference):
            for value,col in zip(row[1:],['setpoint','process_output','command','proportional_gain','integral_gain','derivative_gain']):self.assertAlmostEqual(value,float(ref[col]),places=12)
        self.assertNotIn('Controller.SET_GAINS',n.trace)
    def test_direct_update_once_before_sample275_no_state_or_transition(self):
        n=Network(True).run();self.assertEqual(len(n.rows),400)
        self.assertEqual(n.trace.count('Controller.SET_GAINS'),1);self.assertEqual(n.trace.count('Controller.REQ'),400);self.assertEqual(n.trace.count('Process.APPLY'),400)
        idx=n.trace.index('Controller.SET_GAINS');self.assertEqual(n.trace[:idx].count('Controller.REQ'),274)
        self.assertEqual(n.trace[idx:idx+3],['Controller.SET_GAINS','Controller.GAINS_CNF','Controller.REQ'])
        self.assertTrue(all(math.isfinite(v) for row in n.rows for v in row));self.assertAlmostEqual(n.rows[-1][2],.8,places=5)
        for i,gain in enumerate(['PROPORTIONAL_GAIN','INTEGRAL_GAIN','DERIVATIVE_GAIN']):self.assertEqual(n.rows[274][4+i],n.blocks['Identifier.Tuner'].values['TARGET_'+gain])
        self.assertFalse(any(e.endswith('.ERR') for e in n.trace))
    def test_periodic_updates_before_control_without_extra_calculations(self):
        n=Network(True,interval=25).run()
        self.assertEqual(len(n.rows),400)
        samples=[];calculations=0
        for i,event in enumerate(n.trace):
            if event=='Controller.REQ':calculations+=1
            if event=='Controller.SET_GAINS':
                samples.append(calculations+1)
                self.assertEqual(n.trace[i:i+3],['Controller.SET_GAINS','Controller.GAINS_CNF','Controller.REQ'])
        self.assertEqual(samples,[275,300,325,350,375,400])
        self.assertEqual(calculations,400)
        self.assertEqual(n.trace.count('Process.APPLY'),400)
        self.assertFalse(any(e.endswith('.ERR') for e in n.trace))
        self.assertTrue(all(math.isfinite(v) for row in n.rows for v in row))
    def test_disabled_periodic_does_not_update(self):
        n=Network(False,interval=25).run()
        self.assertEqual(len(n.rows),400)
        self.assertNotIn('Controller.SET_GAINS',n.trace)
    def test_trigger_interval_latched_reset_and_uint_limit(self):
        n=Network(True,interval=25);b=n.blocks['Identifier.Trigger']
        b.values.update(ENABLE_UPDATE=True,UPDATE_AT_SAMPLE=275,UPDATE_INTERVAL_SAMPLES=25)
        self.assertEqual(b.trigger('INIT'),['INITO'])
        b.values['UPDATE_INTERVAL_SAMPLES']=1
        for sample,expected in [(274,'CONTROL_READY'),(275,'TUNE'),(275,'CONTROL_READY'),(299,'CONTROL_READY'),(300,'TUNE')]:
            b.values['SAMPLE_NUMBER']=sample;self.assertEqual(b.trigger('REQ'),[expected])
        b.values.update(UPDATE_AT_SAMPLE=65530,UPDATE_INTERVAL_SAMPLES=5)
        b.trigger('INIT')
        for sample,expected in [(65530,'TUNE'),(65534,'CONTROL_READY'),(65535,'TUNE'),(0,'CONTROL_READY')]:
            b.values['SAMPLE_NUMBER']=sample;self.assertEqual(b.trigger('REQ'),[expected])
        b.values.update(UPDATE_AT_SAMPLE=0,UPDATE_INTERVAL_SAMPLES=25)
        self.assertEqual(b.trigger('INIT'),['ERR'])
    def test_invalid_tuning_stops_before_applying_gains(self):
        n=Network(True,True).run();self.assertFalse(n.running);self.assertIn('Identifier.Tuner.ERR',n.trace);self.assertNotIn('Controller.SET_GAINS',n.trace);self.assertEqual(n.trace.count('Controller.REQ'),274)
    def test_mapping_and_three_blocks_plus_clock(self):
        n=Network();mapped=n.root.find('Device/Resource/FBNetwork')
        check_mapping(n.net,mapped)
        self.assertEqual(len(n.net.findall('FB')),4)
        for s,d in n.data:
            name,port=d.rsplit('.',1)
            xml=n.composite if name=='Identifier' else n.blocks[name].xml
            direction='OutputVars' if name=='Identifier' and any(v.get('Name')==port for v in n.composite.findall('InterfaceList/OutputVars/VarDeclaration')) else 'InputVars'
            self.assertIsNotNone(xml.find(f"InterfaceList/{direction}/VarDeclaration[@Name='{port}']"),d)
    def test_mapping_ignores_layout_but_detects_functional_changes(self):
        import copy
        n=Network();mapped=copy.deepcopy(n.root.find('Device/Resource/FBNetwork'))
        for f in mapped.findall('FB'):
            f.set('x','-1066.6666666666667');f.set('y','800');f.set('Comment','Moved in IDE')
        for group in [mapped,mapped.find('EventConnections'),mapped.find('DataConnections')]:
            group[:]=list(reversed(list(group)))
        E.SubElement(mapped.find('EventConnections'),'Connection',Source='START.COLD',Destination='Process.INIT')
        check_mapping(n.net,mapped)
        for change in ['type','parameter','connection']:
            modified=copy.deepcopy(mapped)
            if change=='type':modified.find("FB[@Name='Controller']").set('Type','WrongType')
            if change=='parameter':modified.find("FB[@Name='Controller']/Parameter").set('Value','999')
            if change=='connection':
                group=modified.find('DataConnections');group.remove(group.find('Connection'))
            with self.assertRaises(AssertionError):check_mapping(n.net,modified)
    def test_mapped_device_has_ide_color(self):
        root=E.parse(PROJECT/'PID_Basic_Adaptive.sys').getroot()
        for mapping in root.findall('Mapping'):
            name=mapping.get('To').split('.')[0]
            color=root.find(f"Device[@Name='{name}']/Attribute[@Name='Color']")
            self.assertIsNotNone(color)
            self.assertEqual(color.get('Type'),'STRING')
            rgb=[int(component) for component in color.get('Value').split(',')]
            self.assertEqual(len(rgb),3)
            self.assertTrue(all(0 <= component <= 255 for component in rgb))
    def test_event_endpoints_and_data_types(self):
        n=Network()
        clock=E.parse(PROJECT/'Type Library/events/E_CYCLE.fbt').getroot()
        def declaration(endpoint,section):
            name,port=endpoint.rsplit('.',1)
            xml=n.composite if name=='Identifier' else clock if name=='SamplingClock' else n.blocks[name].xml
            element='Event' if section.startswith('Event') else 'VarDeclaration'
            return xml.find(f"InterfaceList/{section}/{element}[@Name='{port}']")
        for net,prefix in [(n.net,''),(n.composite.find('FBNetwork'),'Identifier.')]:
            for s,d in pairs(net,'EventConnections'):
                ssection='EventInputs' if prefix and '.' not in s else 'EventOutputs'
                dsection='EventOutputs' if prefix and '.' not in d else 'EventInputs'
                self.assertIsNotNone(declaration(prefix+s,ssection),s)
                self.assertIsNotNone(declaration(prefix+d,dsection),d)
            for s,d in pairs(net,'DataConnections'):
                ssection='InputVars' if prefix and '.' not in s else 'OutputVars'
                dsection='OutputVars' if prefix and '.' not in d else 'InputVars'
                source=declaration(prefix+s,ssection);dest=declaration(prefix+d,dsection)
                self.assertIsNotNone(source,s);self.assertIsNotNone(dest,d)
                self.assertEqual(source.get('Type'),dest.get('Type'))
    def test_pid_flag_calculation_unchanged_except_descriptive_names(self):
        import re
        original=E.parse(ROOT/'4diac/application/PID_Identification_Observer/Type Library/observer/PID_FLAG.fbt').getroot().find("BasicFB/Algorithm[@Name='CALCULATE']/ST").get('Text')
        actual=E.parse(TYPES/'PID_CONTROLLER.fbt').getroot().find("BasicFB/Algorithm[@Name='CALCULATE']/ST").get('Text')
        for old,new in {'SP':'SETPOINT','PV':'PROCESS_VARIABLE','MV':'CONTROL_OUTPUT','RAW':'UNLIMITED_OUTPUT','FLAG':'INTEGRATION_ENABLED'}.items():original=re.sub(r'\b'+old+r'\b',new,original)
        self.assertEqual(original,actual)
if __name__=='__main__':unittest.main()
