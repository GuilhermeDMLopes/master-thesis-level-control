"""Reproduce the archived lecture experiments with the recorded input sequence."""
import csv
import json
import sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from simulation.adaptive.identification import run_experiment

def main():
    data=ROOT/'data/sample/adaptive/20260926'
    inputs=[0.0]
    with (data/'fixo_lambda1.csv').open(encoding='utf-8-sig') as f:
        inputs.extend(float(row['u_k']) for row in csv.DictReader(f))
    summary={}
    for name,forgetting,change in [('fixo_lambda1',1.,False),('mudanca_lambda1',1.,True),('mudanca_lambda08',.8,True),('mudanca_lambda06',.6,True)]:
        rows,est=run_experiment(inputs,forgetting,change)
        expected=np.loadtxt(data/f'{name}.csv',delimiter=',',skiprows=1)
        np.testing.assert_allclose(rows,expected,atol=1e-9,rtol=1e-9)
        summary[name]={'parameters':est.theta.tolist(),'rmse_last20':float(np.sqrt(np.mean(rows[-20:,6]**2)))}
    print(json.dumps(summary,indent=2))
    print('All four archived experiments reproduced. No FORTE or PLC execution.')

if __name__=='__main__':main()
