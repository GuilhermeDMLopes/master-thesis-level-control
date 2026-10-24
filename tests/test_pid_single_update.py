"""Actual uploaded FBT ST/ECC subset + transformed XML network; no native scheduler."""
from pathlib import Path
from collections import deque
import copy
import sys
import tempfile
import unittest
import zipfile
import xml.etree.ElementTree as E
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import verify_pid_whiteboard as runtime
import prepare_pid_single_update as installer
ARCHIVE=ROOT/'docs/adaptive/archives/20261024-paused-update-validated.zip'
PID='PID_FLAG_STATE_ACCESS'
SEQ='SingleUpdateSequence'

def unpack(folder):
    with zipfile.ZipFile(ARCHIVE) as archive:
        for item in archive.infolist():
            name=item.filename.replace('\\','/')
            if '..' in Path(name).parts:raise ValueError('Unsafe archive entry')
            target=folder/name
            if name.endswith('/'):target.mkdir(parents=True,exist_ok=True)
            else:target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(archive.read(item))
    return folder/'PID_Identification_Observer'

class Network:
    def __init__(self,project,enabled=True,rejection=None):
        self.root=installer.transform(E.parse(project/'PID_Identification_Observer.sys').getroot())
        self.net=self.root.find('Application/SubAppNetwork');self.blocks={};self.trace=[];self.rows=[];self.running=False;self.rejection=rejection
        previous=runtime.TYPES
        try:
            for fb in self.net.findall('FB'):
                kind=fb.get('Type')
                if kind=='E_CYCLE':continue
                runtime.TYPES=installer.TYPE_FILE.parent if kind=='PID_SINGLE_UPDATE_SEQUENCE' else project/'Type Library/observer'
                b=runtime.OfflineBlock(kind);self.blocks[fb.get('Name')]=b
                for p in fb.findall('Parameter'):
                    val=p.get('Value');b.values[p.get('Name')]=val=='TRUE' if val in ['TRUE','FALSE'] else float(val)
        finally:runtime.TYPES=previous
        self.blocks[SEQ].values['ENABLE_UPDATE']=enabled
        self.events=installer.pairs(self.net,'EventConnections');self.data=installer.pairs(self.net,'DataConnections')
    def deliver(self,destination):
        queue=deque([destination]);steps=0
        while queue:
            steps+=1
            if steps>200:raise AssertionError('Event loop')
            dst=queue.popleft();self.trace.append(dst);name,event=dst.split('.')
            if name=='SamplingClock':
                self.running=event=='START';continue
            b=self.blocks[name]
            # Sample only the incoming data declared WITH this event.
            variables={w.get('Var') for w in b.xml.findall(f"InterfaceList/EventInputs/Event[@Name='{event}']/With")}
            for source,target in self.data:
                d,port=target.split('.')
                if d==name and port in variables:
                    src,out=source.split('.');b.values[port]=self.blocks[src].values[out]
            if dst=='ModelTuner.REQ' and self.rejection=='tuner':b.values['DESIRED_POLE']=1.5
            if dst=='GainTransitionTest.REQ' and self.rejection=='transition':b.values['MAX_GAIN_OUTPUT_CHANGE']=-1.
            if dst=='GainTransitionTest.REQ' and self.rejection=='hold':b.values['TUNING_ALLOWED']=False
            if dst==PID+'.REQ' and self.rejection=='pid' and len(self.rows)==20:b.values['PV']=float('nan')
            if dst==PID+'.SET_GAINS':before={k:b.values[k] for k in ['I_MEMORY','E_PREV','MV']}
            outputs=b.trigger(event)
            if dst==PID+'.SET_GAINS':assert before=={k:b.values[k] for k in before}
            for out in outputs:
                source=name+'.'+out;self.trace.append(source)
                queue.extend(d for s,d in self.events if s==source)
    def run(self):
        self.deliver('SimulatedProcess.INIT')
        while self.running and len(self.rows)<401:
            self.deliver('SimulatedProcess.REQ')
            p=self.blocks['SimulatedProcess'].values;c=self.blocks[PID].values
            self.rows.append((p['SAMPLE_COUNT'],p['PROCESS_OUTPUT'],c['MV'],c['KP_ACTIVE'],c['KI_ACTIVE'],c['KD_ACTIVE']))
        return self

class SingleUpdateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory();cls.project=unpack(Path(cls.temp.name))
    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()
    def test_one_update_before_calculation_275_and_400_commands(self):
        n=Network(self.project).run();v=n.blocks[SEQ].values
        self.assertEqual(v['COMPLETED_SAMPLES'],400);self.assertTrue(v['UPDATE_ATTEMPTED']);self.assertFalse(v['UPDATE_REJECTED_BY_ERROR'])
        for event in ['ModelTuner.REQ','GainTransitionTest.REQ',PID+'.SET_GAINS',PID+'.READ_STATE']:self.assertEqual(n.trace.count(event),1)
        for event in [PID+'.REQ','SimulatedProcess.APPLY']:self.assertEqual(n.trace.count(event),400)
        index=n.trace.index('ModelTuner.REQ');self.assertEqual(n.trace[:index].count(PID+'.REQ'),274)
        self.assertEqual(n.trace.count('SamplingClock.START'),1);self.assertEqual(n.trace.count('SamplingClock.STOP'),1)
        self.assertFalse(any(e.endswith('.ERR') or e.endswith('.STATE_ERR') for e in n.trace))
        self.assertTrue(n.blocks['GainTransitionTest'].values['UPDATE_APPLIED'])
        self.assertAlmostEqual(n.rows[-1][1],.8,places=7)
    def test_disabled_matches_uploaded_fixed_pid_reference(self):
        n=Network(self.project,enabled=False).run()
        self.assertEqual(n.trace.count('ModelTuner.REQ'),0)
        self.assertEqual(n.blocks[SEQ].values['COMPLETED_SAMPLES'],400)
        # Independent recurrence of the validated fixed-gain controller and process.
        y1=y2=u1=u2=memory=previous_error=0.;flag=True
        kp,ki,kd=.45882339553937435,1.6381884387801722,.016705052344105673
        for k,y,mv,*_ in n.rows:
            expected_y=1.2*y1-.36*y2+(.1 if k<151 else .4)*u1+.06*u2
            sp=1. if ((int(k)-1)//50)%2==0 else .8
            error=sp-expected_y
            if flag:memory+=.05*(error+previous_error)
            raw=kp*error+ki*memory+kd*(error-previous_error)/.1
            expected_u=min(10.,max(0.,raw));flag=0.<=raw<=10.
            self.assertAlmostEqual(y,expected_y,places=12);self.assertAlmostEqual(mv,expected_u,places=12)
            y2,y1,u2,u1=y1,expected_y,u1,expected_u;previous_error=error
    def test_tuner_and_transition_error_continue_old_gains(self):
        baseline=Network(self.project,enabled=False).run().rows
        for failure in ['tuner','transition','hold']:
            with self.subTest(failure=failure):
                n=Network(self.project,rejection=failure).run()
                self.assertEqual(n.rows,baseline)
                self.assertEqual(n.trace.count(PID+'.REQ'),400);self.assertEqual(n.trace.count('SimulatedProcess.APPLY'),400)
                self.assertEqual(n.trace.count('ModelTuner.REQ'),1)
                self.assertEqual(n.blocks[SEQ].values['UPDATE_REJECTED_BY_ERROR'],failure!='hold')
                self.assertEqual(n.trace.count(PID+'.SET_GAINS'),1 if failure=='hold' else 0)
    def test_control_fault_stops_clock(self):
        n=Network(self.project,rejection='pid').run()
        self.assertIn(PID+'.ERR',n.trace);self.assertEqual(n.blocks[SEQ].state,'FAILED')
        self.assertFalse(n.running);self.assertLess(len(n.rows),400)
    def test_duplicate_sample_and_out_of_order_ack_cannot_duplicate_control(self):
        n=Network(self.project);s=n.blocks[SEQ];s.trigger('INIT');s.values['SAMPLE_NUMBER']=1
        self.assertEqual(s.trigger('SAMPLE'),['EXECUTE_PID']);self.assertEqual(s.trigger('GAINS_READY'),[])
        self.assertEqual(s.trigger('SAMPLE'),['ERR']);self.assertEqual(s.trigger('OUTPUT_APPLIED'),[])
        self.assertEqual(s.trigger('INIT'),['INITO']);s.values['SAMPLE_NUMBER']=2
        self.assertEqual(s.trigger('SAMPLE'),['ERR'])
    def test_mapping_ports_and_event_with_associations(self):
        n=Network(self.project)
        app=n.net;resource=n.root.find('Device/Resource/FBNetwork')
        for tag in ['EventConnections','DataConnections']:self.assertEqual(set(installer.pairs(app,tag)),set(installer.pairs(resource,tag)))
        self.assertIsNotNone(n.root.find(f"Mapping[@From='Observer_Test.{SEQ}']"))
        for source,dest in n.data:
            s,sp=source.split('.');d,dp=dest.split('.')
            self.assertIsNotNone(n.blocks[s].xml.find(f"InterfaceList/OutputVars/VarDeclaration[@Name='{sp}']"))
            self.assertIsNotNone(n.blocks[d].xml.find(f"InterfaceList/InputVars/VarDeclaration[@Name='{dp}']"))
        self.assertEqual([s for s,d in n.events if d==PID+'.REQ'],[SEQ+'.EXECUTE_PID'])
    def test_installer_backup_preserves_original_and_refuses_second_run(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder);project=unpack(path/'source');original=(project/'PID_Identification_Observer.sys').read_bytes()
            installer.prepare(project,path/'backups')
            saved=list((path/'backups').rglob('PID_Identification_Observer.sys'))
            self.assertEqual(len(saved),1);self.assertEqual(saved[0].read_bytes(),original)
            with self.assertRaises(ValueError):installer.prepare(project,path/'backups')

if __name__=='__main__':unittest.main()
