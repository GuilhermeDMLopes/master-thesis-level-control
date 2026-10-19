"""Generate reviewable IEC 61499 XML/ST types for the offline lecture harness.
No native export, compilation or deployment is performed by this script.
"""
from pathlib import Path
import csv
import re
import xml.etree.ElementTree as E
ROOT=Path(__file__).resolve().parents[1]
DEST=ROOT/'4diac/application/Adaptive_Identification'
TYPES=DEST/'Type Library/adaptive'

def sub(p,t,**a):return E.SubElement(p,t,{k:str(v) for k,v in a.items()})
def var(p,name,typ='LREAL',initial=None):
    v=sub(p,'VarDeclaration',Name=name,Type=typ)
    if initial is not None:v.set('InitialValue',str(initial))

def root(name,ins,outs,ei,eo):
    r=E.Element('FBType',Name=name,Comment='Offline identification prototype; see docs/adaptive/4diac-design.md')
    sub(r,'Identification',Standard='61499-2')
    sub(r,'VersionInfo',Version='0.1',Author='Guilherme',Date='2026-09-26')
    interface=sub(r,'InterfaceList')
    for tag,events in [('EventInputs',ei),('EventOutputs',eo)]:
        parent=sub(interface,tag)
        for name,variables in events.items():
            ev=sub(parent,'Event',Name=name,Type='Event')
            for v in variables:sub(ev,'With',Var=v)
    for tag,vs in [('InputVars',ins),('OutputVars',outs)]:
        parent=sub(interface,tag)
        for v in vs:var(parent,*v)
    return r


# Mathematical symbols stay compact inside the generator; exported interfaces are descriptive.
PORT_NAMES = {'CHANGE': 'ENABLE_PROCESS_CHANGE', 'LAMBDA': 'FORGETTING_FACTOR', 'P0': 'INITIAL_COVARIANCE', 'K': 'SAMPLE_INDEX', 'Y': 'PROCESS_OUTPUT', 'Y_CURRENT': 'CURRENT_OUTPUT', 'Y1': 'OUTPUT_PREVIOUS_1', 'Y2': 'OUTPUT_PREVIOUS_2', 'U1': 'INPUT_PREVIOUS_1', 'U2': 'INPUT_PREVIOUS_2', 'B1': 'TRUE_INPUT_COEFFICIENT', 'F1': 'OUTPUT_PREVIOUS_1', 'F2': 'OUTPUT_PREVIOUS_2', 'F3': 'INPUT_PREVIOUS_1', 'F4': 'INPUT_PREVIOUS_2', 'T1': 'EST_OUTPUT_COEFFICIENT_1', 'T2': 'EST_OUTPUT_COEFFICIENT_2', 'T3': 'EST_INPUT_COEFFICIENT_1', 'T4': 'EST_INPUT_COEFFICIENT_2', 'Y_HAT': 'PREDICTED_OUTPUT', 'ERROR': 'PREDICTION_ERROR', 'VALID': 'ESTIMATION_VALID'}

def descriptive_ports(element):
    pattern = re.compile(r"\b(" + "|".join(PORT_NAMES) + r")\b")
    for node in element.iter():
        for key, value in list(node.attrib.items()):
            node.set(key, pattern.sub(lambda match: PORT_NAMES[match.group()], value))

def save(r):
    descriptive_ports(r)
    E.indent(r,space='  ')
    (TYPES/(r.get('Name')+'.fbt')).write_bytes(E.tostring(r,encoding='utf-8',xml_declaration=True))

def basic(name,ins,outs,ei,eo,internal,algorithms,states,transitions):
    r=root(name,ins,outs,ei,eo);b=sub(r,'BasicFB');v=sub(b,'InternalVars')
    for x in internal:var(v,*x)
    ecc=sub(b,'ECC')
    for i,(state,actions) in enumerate(states.items()):
        s=sub(ecc,'ECState',Name=state,x=150+(i%3)*450,y=150+(i//3)*300)
        for algo,event in actions:
            a=sub(s,'ECAction')
            if algo:a.set('Algorithm',algo)
            if event:a.set('Output',event)
    for source,dest,condition in transitions:sub(ecc,'ECTransition',Source=source,Destination=dest,Condition=condition)
    for name,body in algorithms.items():sub(sub(b,'Algorithm',Name=name),'ST',Text=body)
    save(r)

def simple(name,ins,outs,init,calc,internal=()):
    names=[x[0] for x in outs]
    basic(name,ins,outs,{'INIT':[],'REQ':[x[0] for x in ins]}, {'INITO':names,'CNF':names},internal,
          {'INITIALIZE':init,'CALCULATE':calc},
          {'START':[],'INITIALIZE':[('INITIALIZE','INITO')],'READY':[],'EXECUTE':[('CALCULATE','CNF')]},
          [('START','INITIALIZE','INIT'),('INITIALIZE','READY','1'),('READY','INITIALIZE','INIT'),('READY','EXECUTE','REQ'),('EXECUTE','READY','1')])

def main():
    TYPES.mkdir(parents=True,exist_ok=True)
    with (ROOT/'data/sample/adaptive/20260926/fixo_lambda1.csv').open(encoding='utf-8-sig') as f:
        inputs=[0.]+[float(row['u_k']) for row in csv.DictReader(f)]
    seq=['K := K + 1;','U2 := U1;','U1 := NEXT_U;']
    for k in range(1,101):seq += [f'IF K = {k} THEN',f'NEXT_U := {inputs[k]:.17g};','END_IF;']
    seq+=['B1 := 0.1;','IF CHANGE AND (K >= 51) THEN','B1 := 0.4;','END_IF;']
    basic('INPUT_SEQUENCE_REPLAY',[('CHANGE','BOOL','FALSE')],[('K','UINT'),('U1',),('U2',),('B1',)],
          {'INIT':['CHANGE'],'REQ':[]},{'INITO':['K','U1','U2','B1'],'CNF':['K','U1','U2','B1'],'DONE':[]},
          [('NEXT_U',),('CHANGE_ACTIVE','BOOL')],
          {'INITIALIZE':'K := 0;\nU1 := 0.0;\nU2 := 0.0;\nNEXT_U := 0.0;\nB1 := 0.1;\nCHANGE_ACTIVE := CHANGE;',
           'NEXT':'\n'.join(seq).replace('IF CHANGE AND','IF CHANGE_ACTIVE AND')},
          {'START':[],'INITIALIZE':[('INITIALIZE','INITO')],'READY':[],'EXECUTE':[('NEXT','CNF')],'FINISH':[('', 'DONE')]},
          [('START','INITIALIZE','INIT'),('INITIALIZE','READY','1'),('READY','INITIALIZE','INIT'),
           ('READY','EXECUTE','REQ [K < 100]'),('READY','FINISH','REQ [K >= 100]'),('EXECUTE','READY','1'),('FINISH','READY','1')])
    basic('OUTPUT_HISTORY',[('Y_CURRENT',)],[('Y1',),('Y2',)],
          {'INIT':[],'REQ':[],'COMMIT':['Y_CURRENT']},{'INITO':['Y1','Y2'],'CNF':['Y1','Y2'],'ACK':[]},[('H1',),('H2',)],
          {'INITIALIZE':'H1 := 0.0;\nH2 := 0.0;\nY1 := 0.0;\nY2 := 0.0;',
           'SNAPSHOT':'Y1 := H1;\nY2 := H2;', 'COMMIT_SAMPLE':'H2 := H1;\nH1 := Y_CURRENT;'},
          {'START':[],'INITIALIZE':[('INITIALIZE','INITO')],'READY':[],'SNAPSHOT':[('SNAPSHOT','CNF')],'WAIT':[],'STORE':[('COMMIT_SAMPLE','ACK')]},
          [('START','INITIALIZE','INIT'),('INITIALIZE','READY','1'),('READY','INITIALIZE','INIT'),('READY','SNAPSHOT','REQ'),('SNAPSHOT','WAIT','1'),('WAIT','INITIALIZE','INIT'),('WAIT','STORE','COMMIT'),('STORE','READY','1')])
    simple('SECOND_ORDER_PROCESS',[(s,) for s in ['Y1','Y2','U1','U2','B1']], [('Y',)],'Y := 0.0;',
           'Y := 1.2 * Y1 - 0.36 * Y2 + B1 * U1 + 0.06 * U2;')
    init=['VALID := FALSE;','Y_HAT := 0.0;','ERROR := 0.0;','LAMBDA_ACTIVE := LAMBDA;']
    init+= [f'T{i} := 0.0;' for i in range(1,5)]
    init+= [f'P{i}{j} := 0.0;' for i in range(1,5) for j in range(1,5)]
    init+=['IF (LAMBDA > 0.0) AND (LAMBDA <= 1.0) AND (P0 > 0.0) AND (P0 <= 1.0E+100) THEN']
    init += [f'P{i}{i} := P0;' for i in range(1,5)]+['VALID := TRUE;','END_IF;']
    st=['VALID := FALSE;']
    finite=' AND '.join(f'({s} >= -1.0E+100) AND ({s} <= 1.0E+100)' for s in ['Y','F1','F2','F3','F4'])
    st += ['IF '+finite+' THEN']
    st+= ['Y_HAT := '+' + '.join(f'F{i} * T{i}' for i in range(1,5))+';','ERROR := Y - Y_HAT;']
    st+= [f'V{i} := '+' + '.join(f'P{i}{j} * F{j}' for j in range(1,5))+';' for i in range(1,5)]
    st+= [f'R{j} := '+' + '.join(f'F{i} * P{i}{j}' for i in range(1,5))+';' for j in range(1,5)]
    st+= ['DEN := LAMBDA_ACTIVE + '+' + '.join(f'F{i} * V{i}' for i in range(1,5))+';',
          'IF (DEN > 1.0E-100) AND (DEN <= 1.0E+100) THEN']
    st+= [f'G{i} := V{i} / DEN;' for i in range(1,5)]
    st+= [f'N{i} := T{i} + G{i} * ERROR;' for i in range(1,5)]
    st+= [f'C{i}{j} := (P{i}{j} - G{i} * R{j}) / LAMBDA_ACTIVE;' for i in range(1,5) for j in range(1,5)]
    for i in range(1,5):
        for j in range(i+1,5):st += [f'C{i}{j} := (C{i}{j} + C{j}{i}) / 2.0;',f'C{j}{i} := C{i}{j};']
    candidates=[f'N{i}' for i in range(1,5)]+[f'C{i}{j}' for i in range(1,5) for j in range(1,5)]
    finite=' AND '.join(f'({s} >= -1.0E+100) AND ({s} <= 1.0E+100)' for s in candidates)
    st+=['IF '+finite+' THEN']+[f'T{i} := N{i};' for i in range(1,5)]+[f'P{i}{j} := C{i}{j};' for i in range(1,5) for j in range(1,5)]+['VALID := TRUE;','END_IF;','END_IF;','END_IF;']
    outs=[('T1',),('T2',),('T3',),('T4',),('Y_HAT',),('ERROR',),('VALID','BOOL')]
    intern=[(s,) for s in ['LAMBDA_ACTIVE','DEN']+[f'{p}{i}' for p in ['V','R','G','N'] for i in range(1,5)]+[f'{p}{i}{j}' for p in ['P','C'] for i in range(1,5) for j in range(1,5)]]
    basic('RLS_PARAMETER_ESTIMATOR',[('LAMBDA','LREAL','1.0'),('P0','LREAL','10000.0')]+[(s,) for s in ['Y','F1','F2','F3','F4']],outs,
          {'INIT':['LAMBDA','P0'],'REQ':['Y','F1','F2','F3','F4']},
          {'INITO':[s[0] for s in outs],'CNF':[s[0] for s in outs],'ERR':['VALID']},intern,
          {'INITIALIZE':'\n'.join(init),'UPDATE':'\n'.join(st)},
          {'START':[],'INITIALIZE':[('INITIALIZE','')],'READY':[],'EXECUTE':[('UPDATE','')],'INIT_OK':[('','INITO')],'UPDATE_OK':[('','CNF')],'FAILED':[('','ERR')]},
          [('START','INITIALIZE','INIT'),('INITIALIZE','INIT_OK','VALID'),('INITIALIZE','FAILED','NOT VALID'),('INIT_OK','READY','1'),
           ('READY','INITIALIZE','INIT'),('READY','EXECUTE','REQ'),('EXECUTE','UPDATE_OK','VALID'),('EXECUTE','FAILED','NOT VALID'),('UPDATE_OK','READY','1'),('FAILED','INITIALIZE','INIT')])
    # Composite uses a serial event chain; the history commits only after successful RLS.
    outputs=[('K','UINT'),('Y',),('U1',),('U2',),('B1',)]+outs
    r=root('PROCESS_IDENTIFICATION', [('CHANGE','BOOL','FALSE'),('LAMBDA','LREAL','1.0'),('P0','LREAL','10000.0')],outputs,
           {'INIT':['CHANGE','LAMBDA','P0'],'REQ':[]}, {'INITO':['VALID'],'CNF':[v[0] for v in outputs],'DONE':[],'ERR':['VALID']})
    net=sub(r,'FBNetwork')
    for name,typ,x,y in [('InputSequence','INPUT_SEQUENCE_REPLAY',400,200),('OutputHistory','OUTPUT_HISTORY',2100,200),('SimulatedProcess','SECOND_ORDER_PROCESS',2100,1600),('ParameterEstimator','RLS_PARAMETER_ESTIMATOR',400,1600)]:sub(net,'FB',Name=name,Type=typ,x=x,y=y)
    events=[('INIT','InputSequence.INIT'),('InputSequence.INITO','OutputHistory.INIT'),('OutputHistory.INITO','SimulatedProcess.INIT'),('SimulatedProcess.INITO','ParameterEstimator.INIT'),('ParameterEstimator.INITO','INITO'),('REQ','InputSequence.REQ'),('InputSequence.CNF','OutputHistory.REQ'),('OutputHistory.CNF','SimulatedProcess.REQ'),('SimulatedProcess.CNF','ParameterEstimator.REQ'),('ParameterEstimator.CNF','OutputHistory.COMMIT'),('OutputHistory.ACK','CNF'),('InputSequence.DONE','DONE'),('ParameterEstimator.ERR','ERR')]
    ec=sub(net,'EventConnections')
    for a,b in events:sub(ec,'Connection',Source=a,Destination=b)
    data=[('CHANGE','InputSequence.CHANGE'),('LAMBDA','ParameterEstimator.LAMBDA'),('P0','ParameterEstimator.P0'),('SimulatedProcess.Y','ParameterEstimator.Y'),('SimulatedProcess.Y','OutputHistory.Y_CURRENT'),('SimulatedProcess.Y','Y')]
    for s in ['U1','U2','B1']:data += [('InputSequence.'+s,'SimulatedProcess.'+s),('InputSequence.'+s,s)]
    data += [('InputSequence.K','K')]
    for s,phi in [('Y1','F1'),('Y2','F2')]:data += [('OutputHistory.'+s,'SimulatedProcess.'+s),('OutputHistory.'+s,'ParameterEstimator.'+phi)]
    for s,phi in [('U1','F3'),('U2','F4')]:data += [('InputSequence.'+s,'ParameterEstimator.'+phi)]
    for s in [v[0] for v in outs]:data += [('ParameterEstimator.'+s,s)]
    dc=sub(net,'DataConnections')
    for a,b in data:sub(dc,'Connection',Source=a,Destination=b)
    save(r)
    # Unmapped engineering application: operator maps a dedicated offline resource.
    sys=E.Element('System',Name='Adaptive_Identification',Comment='Offline only; native export and runtime validation pending')
    app=sub(sys,'Application',Name='Identification_Offline');network=sub(app,'SubAppNetwork')
    timer=sub(network,'FB',Name='SamplingClock',Type='E_CYCLE',x=300,y=300);sub(timer,'Parameter',Name='DT',Value='T#100ms')
    exp=sub(network,'FB',Name='IdentificationTest',Type='PROCESS_IDENTIFICATION',x=2200,y=300)
    for n,v in [('LAMBDA','0.8'),('CHANGE','TRUE'),('P0','10000.0')]:sub(exp,'Parameter',Name=n,Value=v)
    ev=sub(network,'EventConnections')
    for a,b in [('IdentificationTest.INITO','SamplingClock.START'),('SamplingClock.EO','IdentificationTest.REQ'),('IdentificationTest.DONE','SamplingClock.STOP'),('IdentificationTest.ERR','SamplingClock.STOP')]:sub(ev,'Connection',Source=a,Destination=b)
    descriptive_ports(sys)
    E.indent(sys,space='  ');(DEST/'Adaptive_Identification.sys').write_bytes(E.tostring(sys,encoding='utf-8',xml_declaration=True))
    project=E.Element('projectDescription');sub(project,'name').text='Adaptive_Identification';sub(project,'comment').text='Offline lecture identification';sub(project,'projects');sub(project,'buildSpec');sub(sub(project,'natures'),'nature').text='org.eclipse.fordiac.ide.systemmanagement.FordiacNature'
    E.indent(project,space='  ');(DEST/'.project').write_bytes(E.tostring(project,encoding='utf-8',xml_declaration=True))
    print('Generated four basic types, one composite and an unmapped offline application.')

if __name__=='__main__':main()
