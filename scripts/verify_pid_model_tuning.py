"""Offline candidate only. Requires numpy; does not drive 4diac or a plant."""
import json
import argparse
from pathlib import Path
import numpy as np


def tune(theta, sample_s=0.1, target_pole=0.7):
    a1, a2, b1, b2 = map(float, theta)
    if not np.all(np.isfinite(theta)) or sample_s <= 0 or not 0 < target_pole < 1:
        raise ValueError('Invalid model or design inputs')
    # D(z)=(z-p)^3(z-r); r is solved, not independently assigned.
    c = np.poly([target_pole] * 3)
    base = np.array([-1-a1, a1-a2, a2, 0.0])
    matrix = np.array([[b1, 0, 0, c[0]], [b2, b1, 0, c[1]],
                       [0, b2, b1, c[2]], [0, 0, b2, c[3]]])
    if np.linalg.cond(matrix) > 1e10:
        raise ValueError('Ill-conditioned tuning equations')
    q0, q1, q2, remainder_pole = np.linalg.solve(matrix, np.r_[c[1:], 0]-base)
    gains = np.array([(q0-q1-3*q2)/2, (q0+q1+q2)/sample_s, sample_s*q2])
    characteristic = np.array([1, -1-a1+b1*q0,
        a1-a2+b1*q1+b2*q0, a2+b1*q2+b2*q1, b2*q2])
    residual = float(np.max(np.abs(characteristic-np.poly([target_pole]*3+[remainder_pole]))))
    roots = np.roots(characteristic)
    if not np.all(np.isfinite(gains)) or np.any(gains < 0) or max(abs(roots)) >= 1 or residual > 1e-9:
        raise ValueError('Rejected candidate')
    return gains, {'gains': gains.tolist(), 'remaining_pole': float(remainder_pole),
                   'max_pole_modulus': float(max(abs(roots))), 'polynomial_residual': residual}


def simulate(initial_gains, switch_gains=None, change=False, setpoint=1.0):
    # ARX lecture process, command is used starting with the NEXT sample.
    y1=y2=u1=u2=integral=old_error=0.0
    flag=True
    rows=[]
    for k in range(1, 301):
        b1 = 0.4 if change and k >= 151 else 0.1
        y=1.2*y1-0.36*y2+b1*u1+0.06*u2
        # Deliberately prescribed update at k=171: not online RLS/adaptation.
        kp,ki,kd = switch_gains if switch_gains is not None and k >= 171 else initial_gains
        error=setpoint-y
        if flag:
            integral += 0.1/2*(error+old_error)
        raw=kp*error+ki*integral+kd*(error-old_error)/0.1
        u=min(10.0,max(0.0,raw))
        flag=0.0 <= raw <= 10.0
        rows.append([k,y,u,error,raw,int(flag)])
        y2,y1=y1,y
        u2,u1=u1,u
        old_error=error
    a=np.array(rows)
    return {'final_output':float(a[-1,1]), 'max_output':float(a[:,1].max()),
            'final_error':float(a[-1,3]), 'iae_sample_units':float(abs(a[:,3]).sum()),
            'saturated_samples':int(np.sum(a[:,5]==0)),
            'max_command':float(a[:,2].max())}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    before, b=tune([1.2,-0.36,0.1,0.06])
    after, a=tune([1.2,-0.36,0.4,0.06])
    estimated, e=tune([1.2002268028562117,-0.3601783843013826,0.3999706137647457,0.059894655811461535])
    # Known zero plant must not produce fabricated gains.
    try:
        tune([1.2,-0.36,0,0])
    except (ValueError,np.linalg.LinAlgError):
        pass
    else:
        raise AssertionError('Zero-input model accepted')
    result={'scope':'Offline candidate; fixed-gain pole checks and prescribed gain switch. No online RLS, ST, FORTE or physical validation.',
      'design':{'sample_s':0.1,'target_pole_triplet':[0.7]*3,'limits':[0,10],
                'process_change_sample':151,'prescribed_gain_update_sample':171},
      'nominal_before':b,'nominal_after':a,'estimated_after_lambda08':e,
      'runs':{'fixed_process':simulate(before),
              'changed_process_fixed_gains':simulate(before,change=True),
              'changed_process_prescribed_retuning':simulate(before,after,True),
              'changed_process_estimated_retuning':simulate(before,estimated,True),
              'saturation_stress_sp20':simulate(before,setpoint=20)}}
    assert abs(result['runs']['fixed_process']['final_error']) < 1e-6
    assert abs(result['runs']['changed_process_estimated_retuning']['final_error']) < 1e-6
    text=json.dumps(result,indent=2,allow_nan=False)
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(text+'\n',encoding='utf-8')
    print(text)

if __name__=='__main__':
    main()
