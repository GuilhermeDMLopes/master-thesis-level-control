"""Serial ST/ECC observation harness. No native queues/timers or gain writes."""
import argparse,csv,json
from pathlib import Path
import numpy as np
import verify_pid_whiteboard as runtime
ROOT=Path(__file__).resolve().parents[1]
PORTS=['OUTPUT_COEFFICIENT_1','OUTPUT_COEFFICIENT_2','INPUT_COEFFICIENT_1','INPUT_COEFFICIENT_2']
GAINS=(.45882339553937435,1.6381884387801722,.016705052344105673)

def block(name,folder):
 old=runtime.TYPES
 try:
  runtime.TYPES=ROOT/folder
  return runtime.OfflineBlock(name)
 finally:runtime.TYPES=old

def event(b,name,expected):
 observed=b.trigger(name)
 if observed != [expected]:raise AssertionError((name,observed,expected))

def run(reference_changes=True,observe=True,samples=400,guard_updates=False):
 pid=block('PID_FLAG','4diac/application/PID_Whiteboard/Type Library/pid')
 pid.values.update(KP=GAINS[0],KI=GAINS[1],KD=GAINS[2],TS_S=.1,U_MIN=0.,U_MAX=10.)
 event(pid,'INIT','INITO')
 est=tuner=gate=None
 if observe:
  est=block('RLS_PARAMETER_ESTIMATOR','4diac/application/Adaptive_Identification/Type Library/adaptive')
  est.values.update(FORGETTING_FACTOR=.8,INITIAL_COVARIANCE=10000.)
  event(est,'INIT','INITO')
  tuner=block('PID_MODEL_TUNER','4diac/prototypes/PID_Adaptation/Type Library/pid')
  gate=block('IDENTIFICATION_UPDATE_GATE','4diac/prototypes/PID_Adaptation/Type Library/pid') if guard_updates else None
 y1=y2=u1=u2=0.;history=[];rows=[];estimator_failed=False
 for k in range(1,samples+1):
  sp=1. if not reference_changes or ((k-1)//50)%2==0 else .8
  phi=[y1,y2,u1,u2]
  y=1.2*y1-.36*y2+(.4 if k>=151 else .1)*u1+.06*u2
  row=dict(sample=k,time_s=k*.1,setpoint=sp,measurement=y,previous_applied_command=u1,previous_applied_command_2=u2,previous_output=y1,previous_output_2=y2,tuning_status='disabled',regressor_condition=None,candidate_kp=None,candidate_ki=None,candidate_kd=None)
  if observe:
   history.append(phi)
   window=np.asarray(history[-50:]);norms=np.linalg.norm(window,axis=0)
   condition=float(np.linalg.cond(window/np.maximum(norms,1e-15))) if len(history)>=50 else None
   update_allowed=not guard_updates or len(history)<50 or (np.isfinite(condition) and condition<=1e6)
   row['update_allowed']=bool(update_allowed)
   row['window_condition']=condition if condition is not None and np.isfinite(condition) else None
   sample=dict(PROCESS_OUTPUT=y,OUTPUT_PREVIOUS_1=y1,OUTPUT_PREVIOUS_2=y2,INPUT_PREVIOUS_1=u1,INPUT_PREVIOUS_2=u2)
   if gate is not None:
    gate.values.update(sample,UPDATE_ALLOWED=bool(update_allowed and not estimator_failed))
    event(gate,'REQ','UPDATE' if update_allowed and not estimator_failed else 'HOLD')
    if update_allowed and not estimator_failed:
     est.values.update({n:gate.values['LATCHED_'+n] for n in sample})
   else:est.values.update(sample)
   
   if not estimator_failed and update_allowed:
    result=est.trigger('REQ')
    if result==['ERR']:estimator_failed=True
    elif result!=['CNF']:raise AssertionError(result)
   row['estimation_valid']=not estimator_failed
   row['estimator_updated']=bool(not estimator_failed and update_allowed)
   row['estimator_denominator']=float(est.values['DEN']) if update_allowed else None
   matrix=np.array([[est.values[f'P{i}{j}'] for j in range(1,5)] for i in range(1,5)])
   row['covariance_max_abs']=float(np.max(np.abs(matrix)))
   row['covariance_min_eigenvalue']=float(np.linalg.eigvalsh(matrix).min())
   for n in PORTS:row['estimated_'+n.lower()]=float(est.values['EST_'+n])
   row['prediction_error']=float(est.values['PREDICTION_ERROR']) if row['estimator_updated'] else None
   row['tuning_status']='estimator_failed' if estimator_failed else ('update_held' if not update_allowed else 'not_due')
   if not estimator_failed and update_allowed and k>=50 and k%10==0:
    window=np.asarray(history[-50:]);norms=np.linalg.norm(window,axis=0)
    cond=float(np.linalg.cond(window/np.maximum(norms,1e-15)))
    row['regressor_condition']=cond if np.isfinite(cond) else None
    row['tuning_status']='quality_rejected'
    if np.isfinite(cond) and cond<=1e6 and pid.values['FLAG']:
     for n in PORTS:tuner.values['MODEL_'+n]=est.values['EST_'+n]
     tuner.values.update(SAMPLE_TIME_S=.1,DESIRED_POLE=.7)
     result=tuner.trigger('REQ')
     if result==['CNF']:
      row['tuning_status']='candidate_only'
      for short,long in [('kp','PROPORTIONAL'),('ki','INTEGRAL'),('kd','DERIVATIVE')]:row['candidate_'+short]=float(tuner.values['TARGET_'+long+'_GAIN'])
     elif result==['ERR']:row['tuning_status']='tuner_rejected'
     else:raise AssertionError(result)
  # Deliberately no SET_GAINS path: observer cannot change the PID.
  pid.values.update(SP=sp,PV=y);event(pid,'REQ','CNF')
  u=float(pid.values['MV'])
  row.update(applied_command=u,error=sp-y,active_kp=pid.values['KP_ACTIVE'],active_ki=pid.values['KI_ACTIVE'],active_kd=pid.values['KD_ACTIVE'],integration_enabled=bool(pid.values['FLAG']))
  rows.append(row);y2,y1=y1,y;u2,u1=u1,u
 return rows

def summary(rows):
 statuses={n:sum(r['tuning_status']==n for r in rows) for n in ['candidate_only','quality_rejected','tuner_rejected','update_held']}
 return dict(samples=len(rows),iae_seconds=.1*sum(abs(r['error']) for r in rows),final_measurement=rows[-1]['measurement'],last_estimate=[rows[-1].get('estimated_'+n.lower()) for n in PORTS],first_estimator_failure=next((r['sample'] for r in rows if r.get('estimation_valid') is False),None),max_covariance_entry=max((r.get('covariance_max_abs',0) for r in rows)),minimum_covariance_eigenvalue=min((r.get('covariance_min_eigenvalue',0) for r in rows)),**statuses)

def main():
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--guard-updates',action='store_true');a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
 report={'scope':'Actual PID/RLS/tuner FBT ST/ECC subset replay; Python serial orchestration and synthetic plant; no native FORTE validation; fixed PID gains from nominal model','sample_time_s':.1,'forgetting_factor':.8,'guard_updates':a.guard_updates,'runs':{}}
 for name,changing in [('constant_reference',False),('changing_reference',True)]:
  rows=run(changing,guard_updates=a.guard_updates);baseline=run(changing,False)
  assert [(r['measurement'],r['applied_command']) for r in rows]==[(r['measurement'],r['applied_command']) for r in baseline]
  with (a.output/(name+'.csv')).open('w',newline='',encoding='utf-8') as f:
   w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
  report['runs'][name]={**summary(rows),'identical_to_observer_disabled':True}
 text=json.dumps(report,indent=2,allow_nan=False);(a.output/'summary.json').write_text(text+'\n');print(text)
if __name__=='__main__':main()
