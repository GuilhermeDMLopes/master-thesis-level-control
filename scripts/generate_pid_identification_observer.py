"""Generate minimal mapped synthetic observer application; no gain adaptation."""
from pathlib import Path
import shutil,copy,xml.etree.ElementTree as E
import generate_pid_transition_prototypes as xml
ROOT=Path(__file__).resolve().parents[1]
PROJECT=ROOT/'4diac/application/PID_Identification_Observer'

def generate():
 out=PROJECT/'Type Library/observer';out.mkdir(parents=True,exist_ok=True)
 inputs={'COMMAND':'LREAL'}
 outputs={n:'LREAL' for n in ['PROCESS_OUTPUT','REFERENCE','OUTPUT_PREVIOUS_1','OUTPUT_PREVIOUS_2','INPUT_PREVIOUS_1','INPUT_PREVIOUS_2','APPLIED_COMMAND','TRUE_INPUT_COEFFICIENT']}
 outputs['SAMPLE_COUNT']='UINT';outputs['VALID']='BOOL'
 internals={n:'LREAL' for n in ['Y1','Y2','U1','U2']};internals.update(REFERENCE_COUNT='UINT',REFERENCE_HIGH='BOOL')
 r,e=xml.fb('OBSERVER_DEMO_PROCESS',inputs,outputs,{'INIT':[],'REQ':[],'APPLY':['COMMAND']},{'INITO':list(outputs),'CNF':list(outputs),'APPLIED':['APPLIED_COMMAND','SAMPLE_COUNT'],'DONE':['APPLIED_COMMAND','SAMPLE_COUNT'],'ERR':['VALID']},internals)
 for n,a,o in [('START',None,None),('INITIALIZE','INITIALIZE','INITO'),('READY',None,None),('CALCULATE','CALCULATE',None),('PUBLISH',None,'CNF'),('WAIT_COMMAND',None,None),('APPLY_COMMAND','APPLY_COMMAND',None),('ACK',None,'APPLIED'),('FINISH',None,'DONE'),('STOPPED',None,None),('FAIL','INVALIDATE','ERR'),('FAILED',None,None)]:xml.state(e,n,a,o)
 for x,y,c in [('START','INITIALIZE','INIT'),('START','FAIL','REQ'),('START','FAIL','APPLY'),('INITIALIZE','READY','1'),('READY','CALCULATE','REQ'),('READY','INITIALIZE','INIT'),('READY','FAIL','APPLY'),('CALCULATE','PUBLISH','VALID'),('CALCULATE','FAIL','NOT VALID'),('PUBLISH','WAIT_COMMAND','1'),('WAIT_COMMAND','APPLY_COMMAND','APPLY'),('WAIT_COMMAND','FAIL','REQ'),('WAIT_COMMAND','FAIL','INIT'),('APPLY_COMMAND','FAIL','NOT VALID'),('APPLY_COMMAND','ACK','VALID AND (SAMPLE_COUNT < 400)'),('APPLY_COMMAND','FINISH','VALID AND (SAMPLE_COUNT >= 400)'),('ACK','READY','1'),('FINISH','STOPPED','1'),('STOPPED','INITIALIZE','INIT'),('FAIL','FAILED','1'),('FAILED','INITIALIZE','INIT')]:xml.edge(e,x,y,c)
 init=[f'{n} := 0.0;' for n in ['Y1','Y2','U1','U2','PROCESS_OUTPUT','OUTPUT_PREVIOUS_1','OUTPUT_PREVIOUS_2','INPUT_PREVIOUS_1','INPUT_PREVIOUS_2','APPLIED_COMMAND']]+['SAMPLE_COUNT := 0;','REFERENCE_COUNT := 0;','REFERENCE_HIGH := TRUE;','REFERENCE := 1.0;','TRUE_INPUT_COEFFICIENT := 0.1;','VALID := TRUE;']
 xml.algorithm(r,'INITIALIZE',init)
 xml.algorithm(r,'CALCULATE',['SAMPLE_COUNT := SAMPLE_COUNT + 1;','IF REFERENCE_COUNT >= 50 THEN','REFERENCE_HIGH := NOT REFERENCE_HIGH;','REFERENCE_COUNT := 0;','END_IF;','REFERENCE_COUNT := REFERENCE_COUNT + 1;','REFERENCE := 0.8;','IF REFERENCE_HIGH THEN','REFERENCE := 1.0;','END_IF;','TRUE_INPUT_COEFFICIENT := 0.1;','IF SAMPLE_COUNT >= 151 THEN','TRUE_INPUT_COEFFICIENT := 0.4;','END_IF;','OUTPUT_PREVIOUS_1 := Y1;','OUTPUT_PREVIOUS_2 := Y2;','INPUT_PREVIOUS_1 := U1;','INPUT_PREVIOUS_2 := U2;','PROCESS_OUTPUT := 1.2 * Y1 - 0.36 * Y2 + TRUE_INPUT_COEFFICIENT * U1 + 0.06 * U2;','VALID := (PROCESS_OUTPUT >= -1.0E+100) AND (PROCESS_OUTPUT <= 1.0E+100);'])
 xml.algorithm(r,'APPLY_COMMAND',['VALID := (COMMAND >= 0.0) AND (COMMAND <= 10.0);','IF VALID THEN','Y2 := Y1;','Y1 := PROCESS_OUTPUT;','U2 := U1;','U1 := COMMAND;','APPLIED_COMMAND := COMMAND;','END_IF;'])
 xml.algorithm(r,'INVALIDATE',['VALID := FALSE;'])
 E.indent(r,space='  ');E.ElementTree(r).write(out/'OBSERVER_DEMO_PROCESS.fbt',encoding='utf-8',xml_declaration=True)
 sources={'PID_FLAG.fbt':ROOT/'4diac/application/PID_Whiteboard/Type Library/pid/PID_FLAG.fbt','RLS_PARAMETER_ESTIMATOR.fbt':ROOT/'4diac/application/Adaptive_Identification/Type Library/adaptive/RLS_PARAMETER_ESTIMATOR.fbt'}
 for name,p in sources.items():shutil.copyfile(p,out/name)
 for rel in ['devices/FORTE_PC.dev','resources/EMB_RES.res','events/E_RESTART.fbt','events/E_CYCLE.fbt','events/E_DELAY.fbt']:
  target=PROJECT/'Type Library'/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/'4diac/application/PID_Whiteboard/Type Library'/rel,target)
 project=E.parse(ROOT/'4diac/application/PID_Whiteboard/.project');project.find('name').text='PID_Identification_Observer';project.write(PROJECT/'.project',encoding='utf-8',xml_declaration=True)
 system=E.Element('System',Name='PID_Identification_Observer',Comment='Synthetic observation only; native export and execution pending')
 app=E.SubElement(system,'Application',Name='Observer_Test',Comment='Fixed PID; no gain-update connections')
 net=E.SubElement(app,'SubAppNetwork')
 params={'SamplingClock':{'DT':'T#100ms'},'SimulatedProcess':{},'Identifier':{'FORGETTING_FACTOR':'0.8','INITIAL_COVARIANCE':'10000.0'},'FixedPID':{'KP':'0.45882339553937435','KI':'1.6381884387801722','KD':'0.016705052344105673','TS_S':'0.1','U_MIN':'0.0','U_MAX':'10.0'}}
 types={'SamplingClock':'E_CYCLE','SimulatedProcess':'OBSERVER_DEMO_PROCESS','Identifier':'RLS_PARAMETER_ESTIMATOR','FixedPID':'PID_FLAG'}
 for i,(name,typ) in enumerate(types.items()):
  b=E.SubElement(net,'FB',Name=name,Type=typ,x=str(400+i*2600),y='600',Comment='')
  for p,v in params[name].items():E.SubElement(b,'Parameter',Name=p,Value=v)
 events=[('SimulatedProcess.INITO','Identifier.INIT'),('Identifier.INITO','FixedPID.INIT'),('FixedPID.INITO','SamplingClock.START'),('SamplingClock.EO','SimulatedProcess.REQ'),('SimulatedProcess.CNF','Identifier.REQ'),('Identifier.CNF','FixedPID.REQ'),('FixedPID.CNF','SimulatedProcess.APPLY'),('SimulatedProcess.DONE','SamplingClock.STOP')]+[(n+'.ERR','SamplingClock.STOP') for n in ['SimulatedProcess','Identifier','FixedPID']]
 data=[('SimulatedProcess.'+n,'Identifier.'+n) for n in ['PROCESS_OUTPUT','OUTPUT_PREVIOUS_1','OUTPUT_PREVIOUS_2','INPUT_PREVIOUS_1','INPUT_PREVIOUS_2']]+[('SimulatedProcess.PROCESS_OUTPUT','FixedPID.PV'),('SimulatedProcess.REFERENCE','FixedPID.SP'),('FixedPID.MV','SimulatedProcess.COMMAND')]
 for tag,edges in [('EventConnections',events),('DataConnections',data)]:
  c=E.SubElement(net,tag)
  for src,dst in edges:E.SubElement(c,'Connection',Source=src,Destination=dst)
 device=E.SubElement(system,'Device',Name='LocalObserver',Type='FORTE_PC',x='2000',y='3000',Comment='Local synthetic test only')
 E.SubElement(device,'Parameter',Name='MGR_ID',Value='"localhost:61499"')
 E.SubElement(device,'Attribute',Name='Profile',Type='STRING',Value='HOLOBLOC')
 resource=E.SubElement(device,'Resource',Name='EMB_RES',Type='EMB_RES',x='0',y='0')
 mapped=copy.deepcopy(net);mapped.tag='FBNetwork';resource.append(mapped)
 for name in types:E.SubElement(system,'Mapping',From='Observer_Test.'+name,To='LocalObserver.EMB_RES.'+name)
 E.indent(system,space='  ');E.ElementTree(system).write(PROJECT/'PID_Identification_Observer.sys',encoding='utf-8',xml_declaration=True)
if __name__=='__main__':generate()
