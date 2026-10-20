"""Generate experimental transition and serial event coordinator types."""
from pathlib import Path
import xml.etree.ElementTree as E
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'4diac/prototypes/PID_Adaptation/Type Library/pid'

def fb(name,inputs,outputs,events_in,events_out,internal):
 r=E.Element('FBType',Name=name,Comment='Experimental; offline checks only; native export/runtime pending')
 E.SubElement(r,'Identification',Standard='61499-2')
 E.SubElement(r,'VersionInfo',Version='0.1',Author='Guilherme',Date='2026-10-20')
 it=E.SubElement(r,'InterfaceList')
 for kind,items in [('EventInputs',events_in),('EventOutputs',events_out)]:
  container=E.SubElement(it,kind)
  for name,ports in items.items():
   event=E.SubElement(container,'Event',Name=name,Type='Event')
   for port in ports:E.SubElement(event,'With',Var=port)
 for kind,items in [('InputVars',inputs),('OutputVars',outputs)]:
  container=E.SubElement(it,kind)
  for name,typ in items.items():E.SubElement(container,'VarDeclaration',Name=name,Type=typ)
 basic=E.SubElement(r,'BasicFB');iv=E.SubElement(basic,'InternalVars')
 for name,typ in internal.items():E.SubElement(iv,'VarDeclaration',Name=name,Type=typ)
 return r,E.SubElement(basic,'ECC')

def state(ecc,name,algorithm=None,event=None):
 s=E.SubElement(ecc,'ECState',Name=name,x=str(300+len(ecc)%5*1900),y=str(300+len(ecc)//5*1800))
 if algorithm or event:E.SubElement(s,'ECAction',**({'Algorithm':algorithm} if algorithm else {}),**({'Output':event} if event else {}))
def edge(ecc,src,dst,condition):E.SubElement(ecc,'ECTransition',Source=src,Destination=dst,Condition=condition,x='500',y='500')
def algorithm(r,name,lines):E.SubElement(E.SubElement(r.find('BasicFB'),'Algorithm',Name=name),'ST',Text='\n'.join(lines))
def finite(names):return ' AND '.join(f'({n} >= -1.0E+100) AND ({n} <= 1.0E+100)' for n in names)
def write(r):
 OUT.mkdir(parents=True,exist_ok=True);E.indent(r,space='  ');E.ElementTree(r).write(OUT/(r.get('Name')+'.fbt'),encoding='utf-8',xml_declaration=True)

def transition():
 names=['SETPOINT','PROCESS_VARIABLE','INTEGRAL_MEMORY','PREVIOUS_ERROR','ACTIVE_SAMPLE_TIME_S','ACTIVE_OUTPUT_MIN','ACTIVE_OUTPUT_MAX',
 'ACTIVE_PROPORTIONAL_GAIN','ACTIVE_INTEGRAL_GAIN','ACTIVE_DERIVATIVE_GAIN','TARGET_PROPORTIONAL_GAIN','TARGET_INTEGRAL_GAIN','TARGET_DERIVATIVE_GAIN',
 'MAX_GAIN_OUTPUT_CHANGE','MAX_RELATIVE_GAIN_STEP','PROPORTIONAL_SCALE_FLOOR','INTEGRAL_SCALE_FLOOR','DERIVATIVE_SCALE_FLOOR',
 'MODEL_OUTPUT_COEFFICIENT_1','MODEL_OUTPUT_COEFFICIENT_2','MODEL_INPUT_COEFFICIENT_1','MODEL_INPUT_COEFFICIENT_2']
 ins={n:'LREAL' for n in names};ins.update(INTEGRATION_ENABLED='BOOL',TUNING_ALLOWED='BOOL')
 outs={n:'LREAL' for n in ['NEXT_PROPORTIONAL_GAIN','NEXT_INTEGRAL_GAIN','NEXT_DERIVATIVE_GAIN','GAIN_OUTPUT_CHANGE','STEP_FRACTION']};outs.update(UPDATE_APPLIED='BOOL',VALID='BOOL')
 internals=['CURRENT_ERROR','NEXT_INTEGRAL','CURRENT_DERIVATIVE','OLD_RAW','NEW_RAW','DELTA_P','DELTA_I','DELTA_D','FULL_EFFECT','MAGNITUDE','SCALE','RELATIVE_STEP','FRACTION_LIMIT','CANDIDATE_P','CANDIDATE_I','CANDIDATE_D','Q0','Q1','Q2','A1','A2','A3','A4','DENOMINATOR','B1','B2','B3','C1','C2','D1']
 r,e=fb('PID_GAIN_TRANSITION',ins,outs,{'REQ':list(ins)},{'CNF':list(outs),'ERR':['VALID']},{**{n:'LREAL' for n in internals},'CANDIDATE_VALID':'BOOL'})
 for n,a,o in [('START',None,None),('CALCULATE','CALCULATE',None),('DONE',None,'CNF'),('FAILED',None,'ERR')]:state(e,n,a,o)
 edge(e,'START','CALCULATE','REQ');edge(e,'CALCULATE','DONE','VALID');edge(e,'CALCULATE','FAILED','NOT VALID');edge(e,'DONE','START','1');edge(e,'FAILED','START','1')
 # Stateless per request: outputs are candidate gains, never direct actuator writes.
 L=['VALID := '+finite(names[:10]+names[13:18])+' AND (ACTIVE_SAMPLE_TIME_S > 0.0) AND (ACTIVE_OUTPUT_MIN < ACTIVE_OUTPUT_MAX) AND (MAX_GAIN_OUTPUT_CHANGE > 0.0) AND (MAX_RELATIVE_GAIN_STEP > 0.0) AND (MAX_RELATIVE_GAIN_STEP <= 1.0) AND (PROPORTIONAL_SCALE_FLOOR > 0.0) AND (INTEGRAL_SCALE_FLOOR > 0.0) AND (DERIVATIVE_SCALE_FLOOR > 0.0);',
 'UPDATE_APPLIED := FALSE;','GAIN_OUTPUT_CHANGE := 0.0;','STEP_FRACTION := 0.0;','IF VALID THEN',
 'NEXT_PROPORTIONAL_GAIN := ACTIVE_PROPORTIONAL_GAIN;','NEXT_INTEGRAL_GAIN := ACTIVE_INTEGRAL_GAIN;','NEXT_DERIVATIVE_GAIN := ACTIVE_DERIVATIVE_GAIN;',
 'IF TUNING_ALLOWED AND INTEGRATION_ENABLED THEN',
 'CANDIDATE_VALID := '+finite(names[10:13]+names[18:])+' AND (TARGET_PROPORTIONAL_GAIN >= 0.0) AND (TARGET_INTEGRAL_GAIN >= 0.0) AND (TARGET_DERIVATIVE_GAIN >= 0.0);',
 'IF CANDIDATE_VALID THEN',
 'CURRENT_ERROR := SETPOINT - PROCESS_VARIABLE;','NEXT_INTEGRAL := INTEGRAL_MEMORY + ACTIVE_SAMPLE_TIME_S / 2.0 * (CURRENT_ERROR + PREVIOUS_ERROR);',
 'CURRENT_DERIVATIVE := (CURRENT_ERROR - PREVIOUS_ERROR) / ACTIVE_SAMPLE_TIME_S;',
 'OLD_RAW := ACTIVE_PROPORTIONAL_GAIN * CURRENT_ERROR + ACTIVE_INTEGRAL_GAIN * NEXT_INTEGRAL + ACTIVE_DERIVATIVE_GAIN * CURRENT_DERIVATIVE;',
 'DELTA_P := TARGET_PROPORTIONAL_GAIN - ACTIVE_PROPORTIONAL_GAIN;','DELTA_I := TARGET_INTEGRAL_GAIN - ACTIVE_INTEGRAL_GAIN;','DELTA_D := TARGET_DERIVATIVE_GAIN - ACTIVE_DERIVATIVE_GAIN;',
 'FULL_EFFECT := DELTA_P * CURRENT_ERROR + DELTA_I * NEXT_INTEGRAL + DELTA_D * CURRENT_DERIVATIVE;',
 'CANDIDATE_VALID := '+finite(['CURRENT_ERROR','NEXT_INTEGRAL','CURRENT_DERIVATIVE','OLD_RAW','FULL_EFFECT'])+' AND (OLD_RAW >= ACTIVE_OUTPUT_MIN) AND (OLD_RAW <= ACTIVE_OUTPUT_MAX);',
 'IF CANDIDATE_VALID THEN','STEP_FRACTION := 1.0;','MAGNITUDE := FULL_EFFECT;','IF MAGNITUDE < 0.0 THEN','MAGNITUDE := -MAGNITUDE;','END_IF;',
 'IF MAGNITUDE > MAX_GAIN_OUTPUT_CHANGE THEN','STEP_FRACTION := MAX_GAIN_OUTPUT_CHANGE / MAGNITUDE;','END_IF;']
 for short,long in [('P','PROPORTIONAL'),('I','INTEGRAL'),('D','DERIVATIVE')]:
  L += [f'SCALE := ACTIVE_{long}_GAIN;','IF SCALE < 0.0 THEN','SCALE := -SCALE;','END_IF;',f'IF SCALE < {long}_SCALE_FLOOR THEN',f'SCALE := {long}_SCALE_FLOOR;','END_IF;',f'MAGNITUDE := DELTA_{short};','IF MAGNITUDE < 0.0 THEN','MAGNITUDE := -MAGNITUDE;','END_IF;',
        'RELATIVE_STEP := MAGNITUDE / SCALE;','IF RELATIVE_STEP > MAX_RELATIVE_GAIN_STEP THEN','FRACTION_LIMIT := MAX_RELATIVE_GAIN_STEP / RELATIVE_STEP;','IF FRACTION_LIMIT < STEP_FRACTION THEN','STEP_FRACTION := FRACTION_LIMIT;','END_IF;','END_IF;',f'CANDIDATE_{short} := ACTIVE_{long}_GAIN + STEP_FRACTION * DELTA_{short};']
 L += ['CANDIDATE_P := ACTIVE_PROPORTIONAL_GAIN + STEP_FRACTION * DELTA_P;', 'CANDIDATE_I := ACTIVE_INTEGRAL_GAIN + STEP_FRACTION * DELTA_I;', 'CANDIDATE_D := ACTIVE_DERIVATIVE_GAIN + STEP_FRACTION * DELTA_D;', 'NEW_RAW := CANDIDATE_P * CURRENT_ERROR + CANDIDATE_I * NEXT_INTEGRAL + CANDIDATE_D * CURRENT_DERIVATIVE;',
 'Q0 := CANDIDATE_P + CANDIDATE_I * ACTIVE_SAMPLE_TIME_S / 2.0 + CANDIDATE_D / ACTIVE_SAMPLE_TIME_S;',
 'Q1 := -CANDIDATE_P + CANDIDATE_I * ACTIVE_SAMPLE_TIME_S / 2.0 - 2.0 * CANDIDATE_D / ACTIVE_SAMPLE_TIME_S;',
 'Q2 := CANDIDATE_D / ACTIVE_SAMPLE_TIME_S;',
 'A1 := -1.0 - MODEL_OUTPUT_COEFFICIENT_1 + MODEL_INPUT_COEFFICIENT_1 * Q0;',
 'A2 := MODEL_OUTPUT_COEFFICIENT_1 - MODEL_OUTPUT_COEFFICIENT_2 + MODEL_INPUT_COEFFICIENT_1 * Q1 + MODEL_INPUT_COEFFICIENT_2 * Q0;',
 'A3 := MODEL_OUTPUT_COEFFICIENT_2 + MODEL_INPUT_COEFFICIENT_1 * Q2 + MODEL_INPUT_COEFFICIENT_2 * Q1;',
 'A4 := MODEL_INPUT_COEFFICIENT_2 * Q2;',
 'CANDIDATE_VALID := '+finite(['CANDIDATE_P','CANDIDATE_I','CANDIDATE_D','NEW_RAW','A1','A2','A3','A4'])+' AND (NEW_RAW >= ACTIVE_OUTPUT_MIN) AND (NEW_RAW <= ACTIVE_OUTPUT_MAX);']
 # Schur recursion on monic characteristic polynomial; avoid divisions when rejected.
 for src,dst,n in [('A','B',4),('B','C',3),('C','D',2)]:
  L += ['IF CANDIDATE_VALID THEN',f'CANDIDATE_VALID := ({src}{n} > -1.0) AND ({src}{n} < 1.0);','IF CANDIDATE_VALID THEN',f'DENOMINATOR := 1.0 - {src}{n} * {src}{n};','CANDIDATE_VALID := DENOMINATOR > 1.0E-12;','IF CANDIDATE_VALID THEN']
  for j in range(1,n):L += [f'{dst}{j} := ({src}{j} - {src}{n} * {src}{n-j}) / DENOMINATOR;']
  L += ['CANDIDATE_VALID := '+finite([f'{dst}{j}' for j in range(1,n)])+';','END_IF;','END_IF;','END_IF;']
 L += ['IF CANDIDATE_VALID THEN','CANDIDATE_VALID := (D1 > -1.0) AND (D1 < 1.0);','END_IF;',
 'IF CANDIDATE_VALID THEN','NEXT_PROPORTIONAL_GAIN := CANDIDATE_P;','NEXT_INTEGRAL_GAIN := CANDIDATE_I;','NEXT_DERIVATIVE_GAIN := CANDIDATE_D;','GAIN_OUTPUT_CHANGE := NEW_RAW - OLD_RAW;','UPDATE_APPLIED := (DELTA_P <> 0.0) OR (DELTA_I <> 0.0) OR (DELTA_D <> 0.0);','END_IF;',
 'IF NOT CANDIDATE_VALID THEN','STEP_FRACTION := 0.0;','END_IF;','END_IF;','END_IF;','END_IF;','END_IF;']
 algorithm(r,'CALCULATE',L);write(r)

def coordinator():
 ins={'SETPOINT':'LREAL','PROCESS_VARIABLE':'LREAL'};outs={'LATCHED_SETPOINT':'LREAL','LATCHED_PROCESS_VARIABLE':'LREAL'}
 ei={k:[] for k in ['INIT','SAMPLE','STATE_READY','TRANSITION_READY','GAINS_READY','CONTROL_READY','OUTPUT_APPLIED','FAULT']};ei['SAMPLE']=list(ins)
 eo={k:[] for k in ['INITO','READ_PID_STATE','CALCULATE_TRANSITION','APPLY_GAINS','EXECUTE_PID','APPLY_OUTPUT','CNF','ERR']}
 eo['READ_PID_STATE']=list(outs);eo['CALCULATE_TRANSITION']=list(outs);eo['EXECUTE_PID']=list(outs)
 r,e=fb('PID_SAMPLE_COORDINATOR',ins,outs,ei,eo,{})
 for n,a,o in [('START',None,None),('INITIALIZED',None,'INITO'),('READY',None,None),('CAPTURE','CAPTURE','READ_PID_STATE'),('WAIT_STATE',None,None),('REQUEST_TRANSITION',None,'CALCULATE_TRANSITION'),('WAIT_TRANSITION',None,None),('REQUEST_GAINS',None,'APPLY_GAINS'),('WAIT_GAINS',None,None),('REQUEST_CONTROL',None,'EXECUTE_PID'),('WAIT_CONTROL',None,None),('REQUEST_OUTPUT',None,'APPLY_OUTPUT'),('WAIT_OUTPUT',None,None),('COMPLETE',None,'CNF'),('FAILED',None,'ERR')]:state(e,n,a,o)
 edge(e,'START','INITIALIZED','INIT');edge(e,'INITIALIZED','READY','1');edge(e,'FAILED','INITIALIZED','INIT');edge(e,'READY','INITIALIZED','INIT');edge(e,'START','FAILED','SAMPLE');edge(e,'READY','CAPTURE','SAMPLE');edge(e,'CAPTURE','WAIT_STATE','1')
 for wait,trigger,action,nxt in [('WAIT_STATE','STATE_READY','REQUEST_TRANSITION','WAIT_TRANSITION'),('WAIT_TRANSITION','TRANSITION_READY','REQUEST_GAINS','WAIT_GAINS'),('WAIT_GAINS','GAINS_READY','REQUEST_CONTROL','WAIT_CONTROL'),('WAIT_CONTROL','CONTROL_READY','REQUEST_OUTPUT','WAIT_OUTPUT'),('WAIT_OUTPUT','OUTPUT_APPLIED','COMPLETE','READY')]:
  edge(e,wait,action,trigger);edge(e,action,nxt,'1')
  edge(e,wait,'FAILED','SAMPLE');edge(e,wait,'FAILED','INIT');edge(e,wait,'FAILED','FAULT')
 edge(e,'READY','FAILED','FAULT')
 algorithm(r,'CAPTURE',['LATCHED_SETPOINT := SETPOINT;','LATCHED_PROCESS_VARIABLE := PROCESS_VARIABLE;']);write(r)

if __name__=='__main__':transition();coordinator()
