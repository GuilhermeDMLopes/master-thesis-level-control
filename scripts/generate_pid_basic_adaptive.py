"""Generate the minimal synthetic project; never alter the validated observer."""
from pathlib import Path
import copy
import re
import shutil
import xml.etree.ElementTree as E
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'4diac/application/PID_Identification_Observer'
PROJECT=ROOT/'4diac/application/PID_Basic_Adaptive'
TYPES=PROJECT/'Type Library/adaptive'
PROTO=ROOT/'4diac/prototypes/PID_Adaptation/Type Library/pid'
def save(root,path):
    path.parent.mkdir(parents=True,exist_ok=True);E.indent(root);E.ElementTree(root).write(path,encoding='utf-8',xml_declaration=True)
def connections(net,tag,pairs):
    parent=E.SubElement(net,tag)
    for source,destination in pairs:E.SubElement(parent,'Connection',Source=source,Destination=destination)
def fb(net,name,kind,x,y,params=None):
    node=E.SubElement(net,'FB',Name=name,Type=kind,x=str(x),y=str(y))
    for k,v in (params or {}).items():E.SubElement(node,'Parameter',Name=k,Value=str(v))
    return node
def generate():
    TYPES.mkdir(parents=True,exist_ok=True)
    for folder in ['devices','events','resources']:
        shutil.copytree(SOURCE/'Type Library'/folder,PROJECT/'Type Library'/folder,dirs_exist_ok=True)
    for name in ['OBSERVER_DEMO_PROCESS','RLS_PARAMETER_ESTIMATOR']:
        shutil.copyfile(SOURCE/'Type Library/observer'/f'{name}.fbt',TYPES/f'{name}.fbt')
    shutil.copyfile(PROTO/'PID_MODEL_TUNER.fbt',TYPES/'PID_MODEL_TUNER.fbt')
    # Keep the exact PID recurrence and flag. Separate initial gains from updates.
    pid=E.parse(SOURCE/'Type Library/observer/PID_FLAG.fbt').getroot()
    pid.set('Name','PID_CONTROLLER');pid.set('Comment','Whiteboard flag PID; direct atomic gain update; synthetic validation')
    names={'KP':'INITIAL_PROPORTIONAL_GAIN','KI':'INITIAL_INTEGRAL_GAIN','KD':'INITIAL_DERIVATIVE_GAIN','TS_S':'SAMPLE_TIME_S','U_MIN':'OUTPUT_MIN','U_MAX':'OUTPUT_MAX','SP':'SETPOINT','PV':'PROCESS_VARIABLE','MV':'CONTROL_OUTPUT','RAW':'UNLIMITED_OUTPUT','FLAG':'INTEGRATION_ENABLED'}
    # Replace whole identifiers, including ST and WITH, without changing expressions.
    text=E.tostring(pid,encoding='unicode')
    for old,new in names.items():text=re.sub(r'\b'+old+r'\b',new,text)
    pid=E.fromstring(text)
    gains=['PROPORTIONAL_GAIN','INTEGRAL_GAIN','DERIVATIVE_GAIN']
    for gain in gains:
        E.SubElement(pid.find('InterfaceList/InputVars'),'VarDeclaration',Name='UPDATED_'+gain,Type='LREAL')
        for w in pid.findall("InterfaceList/EventInputs/Event[@Name='SET_GAINS']/With"):
            if w.get('Var')=='INITIAL_'+gain:w.set('Var','UPDATED_'+gain)
        st=pid.find("BasicFB/Algorithm[@Name='UPDATE_GAINS']/ST")
        st.set('Text',st.get('Text').replace('INITIAL_'+gain,'UPDATED_'+gain))
    save(pid,TYPES/'PID_CONTROLLER.fbt')
    # A small event selector: one tuning attempt per initialization, no transition/state read.
    gate=E.Element('FBType',Name='TUNING_TRIGGER',Comment='Select normal control or one model tuning at a specified sample')
    E.SubElement(gate,'Identification',Standard='61499-2');interface=E.SubElement(gate,'InterfaceList')
    for tag,events in [('EventInputs',{'INIT':['ENABLE_UPDATE','UPDATE_AT_SAMPLE'],'REQ':['SAMPLE_NUMBER']}),('EventOutputs',{'INITO':[],'CONTROL_READY':[],'TUNE':['UPDATE_ATTEMPTED'],'ERR':[]})]:
        parent=E.SubElement(interface,tag)
        for name,variables in events.items():
            event=E.SubElement(parent,'Event',Name=name,Type='Event')
            for var in variables:E.SubElement(event,'With',Var=var)
    for tag,variables in [('InputVars',{'ENABLE_UPDATE':'BOOL','UPDATE_AT_SAMPLE':'UINT','SAMPLE_NUMBER':'UINT'}),('OutputVars',{'UPDATE_ATTEMPTED':'BOOL'})]:
        parent=E.SubElement(interface,tag)
        for name,kind in variables.items():E.SubElement(parent,'VarDeclaration',Name=name,Type=kind)
    basic=E.SubElement(gate,'BasicFB');iv=E.SubElement(basic,'InternalVars')
    for name,kind in {'ENABLED':'BOOL','TARGET_SAMPLE':'UINT','DUE':'BOOL','VALID':'BOOL'}.items():E.SubElement(iv,'VarDeclaration',Name=name,Type=kind)
    ecc=E.SubElement(basic,'ECC')
    states={'START':(None,None),'INITIALIZE':('INITIALIZE',None),'INITIALIZED':(None,'INITO'),'READY':(None,None),'SELECT':('SELECT',None),'TUNE':('MARK','TUNE'),'PASS':(None,'CONTROL_READY'),'FAILED':(None,'ERR')}
    for i,(name,(alg,out)) in enumerate(states.items()):
        state=E.SubElement(ecc,'ECState',Name=name,x=str(300+(i%4)*2000),y=str(300+(i//4)*2000))
        if alg or out:E.SubElement(state,'ECAction',**({'Algorithm':alg} if alg else {}),**({'Output':out} if out else {}))
    edges=[('START','INITIALIZE','INIT'),('READY','INITIALIZE','INIT'),('FAILED','INITIALIZE','INIT'),('START','FAILED','REQ'),('INITIALIZE','INITIALIZED','VALID'),('INITIALIZE','FAILED','NOT VALID'),('INITIALIZED','READY','1'),('READY','SELECT','REQ'),('SELECT','TUNE','DUE'),('SELECT','PASS','NOT DUE'),('TUNE','READY','1'),('PASS','READY','1')]
    for s,d,c in edges:E.SubElement(ecc,'ECTransition',Source=s,Destination=d,Condition=c,x='500',y='500')
    for name,code in {'INITIALIZE':'ENABLED := ENABLE_UPDATE;\nTARGET_SAMPLE := UPDATE_AT_SAMPLE;\nUPDATE_ATTEMPTED := FALSE;\nVALID := (NOT ENABLED) OR (TARGET_SAMPLE > 0);','SELECT':'DUE := ENABLED AND (NOT UPDATE_ATTEMPTED) AND (SAMPLE_NUMBER = TARGET_SAMPLE);','MARK':'UPDATE_ATTEMPTED := TRUE;'}.items():E.SubElement(E.SubElement(basic,'Algorithm',Name=name),'ST',Text=code)
    save(gate,TYPES/'TUNING_TRIGGER.fbt')
    # Composite boundary has only measurement/configuration and gain/control events.
    composite=E.Element('FBType',Name='PROCESS_IDENTIFIER',Comment='RLS identification and one model-based PID tuning')
    E.SubElement(composite,'Identification',Standard='61499-2');interface=E.SubElement(composite,'InterfaceList')
    measurements=['PROCESS_OUTPUT','OUTPUT_PREVIOUS_1','OUTPUT_PREVIOUS_2','INPUT_PREVIOUS_1','INPUT_PREVIOUS_2']
    config=['FORGETTING_FACTOR','INITIAL_COVARIANCE','SAMPLE_TIME_S','DESIRED_POLE','ENABLE_UPDATE','UPDATE_AT_SAMPLE']
    for tag,events in [('EventInputs',{'INIT':config,'REQ':measurements+['SAMPLE_NUMBER']}),('EventOutputs',{'INITO':[],'CONTROL_READY':[],'GAINS_READY':gains,'ERR':[]})]:
        parent=E.SubElement(interface,tag)
        for name,variables in events.items():
            event=E.SubElement(parent,'Event',Name=name,Type='Event')
            for var in variables:E.SubElement(event,'With',Var=var)
    for tag,variables in [('InputVars',config+measurements+['SAMPLE_NUMBER']),('OutputVars',gains)]:
        parent=E.SubElement(interface,tag)
        for name in variables:E.SubElement(parent,'VarDeclaration',Name=name,Type='BOOL' if name=='ENABLE_UPDATE' else 'UINT' if name in ['SAMPLE_NUMBER','UPDATE_AT_SAMPLE'] else 'LREAL')
    net=E.SubElement(composite,'FBNetwork')
    fb(net,'Estimator','RLS_PARAMETER_ESTIMATOR',400,400);fb(net,'Trigger','TUNING_TRIGGER',4000,400);fb(net,'Tuner','PID_MODEL_TUNER',7500,400)
    connections(net,'EventConnections',[('INIT','Estimator.INIT'),('Estimator.INITO','Trigger.INIT'),('Trigger.INITO','INITO'),('REQ','Estimator.REQ'),('Estimator.CNF','Trigger.REQ'),('Trigger.CONTROL_READY','CONTROL_READY'),('Trigger.TUNE','Tuner.REQ'),('Tuner.CNF','GAINS_READY'),('Estimator.ERR','ERR'),('Trigger.ERR','ERR'),('Tuner.ERR','ERR')])
    data=[(v,'Estimator.'+v) for v in measurements+config[:2]]+[(v,'Trigger.'+v) for v in ['ENABLE_UPDATE','UPDATE_AT_SAMPLE','SAMPLE_NUMBER']]+[(v,'Tuner.'+v) for v in ['SAMPLE_TIME_S','DESIRED_POLE']]
    for side in ['OUTPUT','INPUT']:
        for i in [1,2]:data.append((f'Estimator.EST_{side}_COEFFICIENT_{i}',f'Tuner.MODEL_{side}_COEFFICIENT_{i}'))
    data += [('Tuner.TARGET_'+v,v) for v in gains]
    connections(net,'DataConnections',data);save(composite,TYPES/'PROCESS_IDENTIFIER.fbt')
    system=E.parse(SOURCE/'PID_Identification_Observer.sys').getroot();system.set('Name','PID_Basic_Adaptive');system.set('Comment','Minimal synthetic PID with one direct gain update; native validation pending')
    app=system.find('Application');app.set('Name','Basic_Control');app.set('Comment','Process, identifier/tuner and flag PID')
    net=E.Element('SubAppNetwork')
    fb(net,'SamplingClock','E_CYCLE',400,400,{'DT':'T#100ms'})
    fb(net,'Process','OBSERVER_DEMO_PROCESS',2400,400)
    fb(net,'Identifier','PROCESS_IDENTIFIER',6200,400,dict(zip(config,['0.8','10000.0','0.1','0.7','FALSE','275'])))
    fb(net,'Controller','PID_CONTROLLER',10200,400,{'INITIAL_PROPORTIONAL_GAIN':'.45882339553937435','INITIAL_INTEGRAL_GAIN':'1.6381884387801722','INITIAL_DERIVATIVE_GAIN':'0.016705052344105673','SAMPLE_TIME_S':'0.1','OUTPUT_MIN':'0.0','OUTPUT_MAX':'10.0'})
    net.find("FB[@Name='Controller']/Parameter[@Name='INITIAL_PROPORTIONAL_GAIN']").set('Value','0.45882339553937435')
    events=[('Process.INITO','Identifier.INIT'),('Identifier.INITO','Controller.INIT'),('Controller.INITO','SamplingClock.START'),('SamplingClock.EO','Process.REQ'),('Process.CNF','Identifier.REQ'),('Identifier.CONTROL_READY','Controller.REQ'),('Identifier.GAINS_READY','Controller.SET_GAINS'),('Controller.GAINS_CNF','Controller.REQ'),('Controller.CNF','Process.APPLY'),('Process.DONE','SamplingClock.STOP')]+[(n+'.ERR','SamplingClock.STOP') for n in ['Process','Identifier','Controller']]
    connections(net,'EventConnections',events)
    data=[('Process.'+v,'Identifier.'+v) for v in measurements]+[('Process.SAMPLE_COUNT','Identifier.SAMPLE_NUMBER'),('Process.REFERENCE','Controller.SETPOINT'),('Process.PROCESS_OUTPUT','Controller.PROCESS_VARIABLE'),('Controller.CONTROL_OUTPUT','Process.COMMAND')]+[('Identifier.'+v,'Controller.UPDATED_'+v) for v in gains]
    connections(net,'DataConnections',data)
    app.remove(app.find('SubAppNetwork'));app.append(net)
    device=system.find('Device')
    if device.find("Attribute[@Name='Color']") is None:
        device.insert(list(device).index(device.find('Resource')), E.Element('Attribute',Name='Color',Type='STRING',Value='217,173,117',Comment='color'))
    resource=system.find('Device/Resource');resource.remove(resource.find('FBNetwork'));mapped=copy.deepcopy(net);mapped.tag='FBNetwork';resource.append(mapped)
    for mapping in list(system.findall('Mapping')):system.remove(mapping)
    for node in net.findall('FB'):E.SubElement(system,'Mapping',From='Basic_Control.'+node.get('Name'),To='LocalObserver.EMB_RES.'+node.get('Name'))
    save(system,PROJECT/'PID_Basic_Adaptive.sys')
    desc=E.parse(SOURCE/'.project').getroot();desc.find('name').text='PID_Basic_Adaptive';save(desc,PROJECT/'.project')
if __name__=='__main__':generate()
