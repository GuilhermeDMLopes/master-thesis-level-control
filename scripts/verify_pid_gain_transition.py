"""Offline closed-loop experiment, not an IEC 61499 runtime implementation."""
import argparse
import csv
import json
from pathlib import Path
import sys
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from simulation.adaptive.identification import RLS4
from verify_pid_model_tuning import tune

T=0.1
OUTPUT_CHANGE_LIMIT=0.02
GAIN_FRACTION_LIMIT=0.02

def limit_gains(active, target, features):
    delta=target-active
    effect=float(delta@features)
    scale=np.maximum(np.abs(active), np.array([0.01,0.01,0.001]))
    fraction=float(np.max(np.abs(delta)/scale))
    alpha=min(1.0, OUTPUT_CHANGE_LIMIT/max(abs(effect),1e-300),
              GAIN_FRACTION_LIMIT/max(fraction,1e-300))
    return active+alpha*delta, float(alpha)


def run(mode, reference_changes=False, forgetting=0.8):
    active,_=tune([1.2,-.36,.1,.06])
    initial=active.copy()
    target=active.copy()
    estimator=RLS4(forgetting=forgetting)
    y1=y2=u1=u2=integral=old_error=0.0
    flag=True
    histories=[]
    rows=[]
    accepted=rejected=0
    last_model=estimator.theta.copy()
    for k in range(1,401):
        sp=1.0 if not reference_changes else (1.0 if ((k-1)//50)%2==0 else .8)
        phi=np.array([y1,y2,u1,u2])
        b1=.4 if k>=151 else .1
        y=1.2*y1-.36*y2+b1*u1+.06*u2
        prediction,prediction_error=estimator.step(phi,y)
        histories.append(phi.copy())
        # Identifier receives only applied-command history and measured output.
        if mode.startswith('rls') and k>=50 and k%10==0:
            window=np.array(histories[-50:])
            norms=np.linalg.norm(window,axis=0)
            cond=np.linalg.cond(window/np.maximum(norms,1e-15))
            try:
                if cond>1e6 or not flag:
                    raise ValueError('Insufficient excitation or saturation')
                target,_=tune(estimator.theta)
                last_model=estimator.theta.copy()
                accepted+=1
            except (ValueError,np.linalg.LinAlgError):
                rejected+=1
                target=active.copy()  # Cancel any pending transition on rejection.
        elif mode.startswith('prescribed') and k==171:
            target,_=tune([1.2,-.36,.4,.06])
        error=sp-y
        next_integral=integral+T/2*(error+old_error) if flag else integral
        derivative=(error-old_error)/T
        features=np.array([error,next_integral,derivative])
        prior_raw=float(active@features)
        candidate=active.copy()
        if mode.endswith('abrupt'):
            candidate=target.copy()
        elif mode.endswith('limited') and flag and 0<=prior_raw<=10:
            candidate,_=limit_gains(active,target,features)
            # Check this scheduled point on latest accepted model (not actual plant).
            model=last_model if mode.startswith('rls') else np.array([1.2,-.36,.4 if k>=171 else .1,.06])
            kp,ki,kd=candidate
            q=np.array([kp+ki*T/2+kd/T,-kp+ki*T/2-2*kd/T,kd/T])
            a1,a2,bb1,bb2=model
            poly=[1,-1-a1+bb1*q[0],a1-a2+bb1*q[1]+bb2*q[0],a2+bb1*q[2]+bb2*q[1],bb2*q[2]]
            if max(abs(np.roots(poly)))>=1 or not 0<=float(candidate@features)<=10:
                candidate=active.copy()
        active=candidate
        raw=float(active@features)
        gain_effect=raw-prior_raw
        u=float(np.clip(raw,0,10))
        new_flag=0<=raw<=10
        rows.append([k,sp,y,u,error,gain_effect,*active,*estimator.theta,prediction_error,int(new_flag)])
        y2,y1=y1,y
        u2,u1=u1,u
        integral,old_error,flag=next_integral,error,new_flag
    a=np.array(rows)
    summary={'iae_seconds':float(T*np.sum(abs(a[:,4]))),
             'post_change_iae_seconds':float(T*np.sum(abs(a[150:,4]))),
             'final_error':float(a[-1,4]),'peak_output':float(a[:,2].max()),
             'max_gain_induced_raw_change':float(abs(a[:,5]).max()),
             'saturated_samples':int(np.sum(a[:,-1]==0)),
             'accepted_tuning_requests':accepted,'rejected_tuning_requests':rejected,
             'initial_gains':initial.tolist(),'final_gains':active.tolist(),
             'final_estimated_coefficients':estimator.theta.tolist()}
    if mode.endswith('limited'):
        assert summary['max_gain_induced_raw_change']<=OUTPUT_CHANGE_LIMIT+1e-12
    assert np.isfinite(a).all()
    return summary,rows


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--forgetting',type=float,default=0.8)
    parser.add_argument('--output-dir',type=Path,default=Path('results/adaptive/gain-transition'))
    args=parser.parse_args()
    args.output_dir.mkdir(parents=True,exist_ok=True)
    result={'scope':'Offline Python only; RLS runs on closed-loop applied input/output. No sensor noise, no physical test.',
      'design':{'sample_s':T,'samples':400,'rls_forgetting':args.forgetting,'tuning_every_samples':10,
                'warmup_samples':50,'process_change_sample':151,'gain_induced_raw_limit':OUTPUT_CHANGE_LIMIT,
                'gain_fraction_per_sample':GAIN_FRACTION_LIMIT,'excitation_window_samples':50,
                'normalized_regressor_condition_limit':1e6},'cases':{}}
    for changing in (False,True):
        for mode in ('fixed','prescribed_abrupt','prescribed_limited','rls_abrupt','rls_limited'):
            label=('steps_' if changing else 'constant_')+mode
            summary,rows=run(mode,changing,args.forgetting)
            result['cases'][label]=summary
            with (args.output_dir/(label+'.csv')).open('w',newline='') as f:
                w=csv.writer(f)
                w.writerow(['sample','setpoint','output','applied_command','error','gain_induced_raw_change','kp','ki','kd','a1_est','a2_est','b1_est','b2_est','prediction_error','flag'])
                w.writerows(rows)
    # Limiter must not modify gains already at target.
    g=np.array([1.,2.,.1]); out,_=limit_gains(g,g,np.array([1.,3.,2.]))
    assert np.array_equal(g,out)
    (args.output_dir/'summary.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    for name,s in result['cases'].items():
        print(name, 'IAE=',round(s['iae_seconds'],6),'gain_jump=',round(s['max_gain_induced_raw_change'],6),'accepted=',s['accepted_tuning_requests'],'final_error=',round(s['final_error'],8))

if __name__=='__main__':
    main()
