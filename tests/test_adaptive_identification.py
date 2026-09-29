"""Mathematical and XML/ST regression tests; NOT a native FORTE qualification."""
import ast
import csv
from pathlib import Path
import re
import xml.etree.ElementTree as ET
import numpy as np
import pytest
from simulation.adaptive.identification import RLS4, run_experiment
ROOT=Path(__file__).resolve().parents[1]
TYPES=ROOT/'4diac/application/Adaptive_Identification/Type Library/adaptive'
DATA=ROOT/'data/sample/adaptive/20260926'
CASES=[('fixo_lambda1',1.,False),('mudanca_lambda1',1.,True),('mudanca_lambda08',.8,True),('mudanca_lambda06',.6,True)]

def expression(s):
    s=re.sub(r'\bTRUE\b','True',s);s=re.sub(r'\bFALSE\b','False',s)
    for a,b in [('AND','and'),('OR','or'),('NOT','not')]:s=re.sub(r'\b'+a+r'\b',b,s)
    s=s.replace('<>','!=');s=re.sub(r'(?<![<>=!:])=(?!=)','==',s)
    return s

class STBlock:
    """Execute only this prototype's assignment/IF ST subset and local ECC.

    This deliberately does not model runtime scheduling, transport, WITH sampling,
    native types/overflow or the general IEC 61131/61499 language semantics.
    """
    def __init__(self,name):
        self.xml=ET.parse(TYPES/(name+'.fbt')).getroot();self.values={};self.state='START'
        for v in self.xml.findall('.//VarDeclaration'):
            initial=v.get('InitialValue','FALSE' if v.get('Type')=='BOOL' else '0')
            self.values[v.get('Name')]=eval(expression(initial),{'__builtins__':{}},{})
        self.algorithms={}
        for a in self.xml.findall('BasicFB/Algorithm'):
            text=a.find('ST').get('Text');indent=0;lines=[]
            for line in text.splitlines():
                line=line.strip()
                if not line:continue
                if line=='END_IF;':indent-=1;continue
                if line.startswith('IF '):
                    lines.append('    '*indent+'if '+expression(line[3:-5].strip())+':');indent+=1
                else:
                    target,rhs=line.rstrip(';').split(':=')
                    lines.append('    '*indent+target.strip()+' = '+expression(rhs.strip()))
            code='\n'.join(lines);ast.parse(code)
            self.algorithms[a.get('Name')]=compile(code,'<ST subset>','exec')
    def trigger(self,event):
        outputs=[]
        for _ in range(32):
            found=None
            for t in self.xml.findall('BasicFB/ECC/ECTransition'):
                if t.get('Source')!=self.state:continue
                c=t.get('Condition');m=re.fullmatch(r'(\w+)\s*\[(.*)\]',c)
                if m:ok=event==m[1] and eval(expression(m[2]),{'__builtins__':{}},self.values)
                elif c in ('INIT','REQ','COMMIT'):ok=event==c
                else:ok=bool(eval(expression(c),{'__builtins__':{}},self.values))
                if ok:found=t;break
            if found is None:return outputs
            event=None;self.state=found.get('Destination')
            s=self.xml.find(f"BasicFB/ECC/ECState[@Name='{self.state}']")
            for a in s.findall('ECAction'):
                if a.get('Algorithm'):exec(self.algorithms[a.get('Algorithm')],{'__builtins__':{}},self.values)
                if a.get('Output'):outputs.append(a.get('Output'))
        raise AssertionError('Non-terminating local ECC')

def inputs():
    with (DATA/'fixo_lambda1.csv').open(encoding='utf-8-sig') as f:
        return [0.]+[float(r['u_k']) for r in csv.DictReader(f)]

@pytest.mark.parametrize('name,lam,change',CASES)
def test_archived_math_and_batch_solution(name,lam,change):
    rows,est=run_experiment(inputs(),lam,change)
    expected=np.loadtxt(DATA/(name+'.csv'),delimiter=',',skiprows=1)
    np.testing.assert_allclose(rows,expected,atol=1e-9,rtol=1e-9)
    y=rows[:,4];X=np.column_stack([np.r_[0,y[:-1]],np.r_[0,0,y[:-2]],rows[:,2],rows[:,3]])
    weights=lam**np.arange(99,-1,-1)
    batch=np.linalg.solve(X.T@(weights[:,None]*X)+(lam**100/10000)*np.eye(4),X.T@(weights*y))
    np.testing.assert_allclose(est.theta,batch,atol=1e-6,rtol=1e-6)

@pytest.mark.parametrize('name,lam,change',CASES)
def test_actual_st_algorithms_match_archived_samples(name,lam,change):
    replay,history,plant,rls=[STBlock(n) for n in ['ADP_REPLAY100','ADP_HISTORY2','ADP_ARX22_PROCESS','ADP_RLS4']]
    replay.values['CHANGE']=change;rls.values.update(LAMBDA=lam,P0=10000.)
    for b in (replay,history,plant,rls):assert b.trigger('INIT')==['INITO']
    expected=np.loadtxt(DATA/(name+'.csv'),delimiter=',',skiprows=1)
    for row in expected:
        assert replay.trigger('REQ')==['CNF'];assert history.trigger('REQ')==['CNF']
        plant.values.update({k:history.values[k] for k in ['Y1','Y2']})
        plant.values.update({k:replay.values[k] for k in ['U1','U2','B1']})
        assert plant.trigger('REQ')==['CNF']
        rls.values.update(Y=plant.values['Y'],F1=history.values['Y1'],F2=history.values['Y2'],F3=replay.values['U1'],F4=replay.values['U2'])
        assert rls.trigger('REQ')==['CNF']
        actual=[replay.values['K'],replay.values['U1'],replay.values['U2'],plant.values['Y'],rls.values['Y_HAT'],rls.values['ERROR']]+[rls.values[f'T{i}'] for i in range(1,5)]
        np.testing.assert_allclose(actual,row[[0,2,3,4,5,6,7,8,9,10]],atol=1e-8,rtol=1e-8)
        history.values['Y_CURRENT']=plant.values['Y'];assert history.trigger('COMMIT')==['ACK']
    assert replay.trigger('REQ')==['DONE'];assert replay.values['K']==100
    for b in (replay,history,plant,rls):assert b.trigger('INIT')==['INITO']
    assert history.values['Y1']==0 and replay.values['K']==0 and rls.values['T1']==0

@pytest.mark.parametrize('bad',[0.,-1.,1.1,float('nan'),float('inf')])
def test_invalid_forgetting_rejected(bad):
    with pytest.raises(ValueError):RLS4(bad)
    b=STBlock('ADP_RLS4');b.values.update(LAMBDA=bad,P0=10000.)
    assert b.trigger('INIT')==['ERR'];assert b.trigger('REQ')==[]


def test_rls_failed_input_preserves_state_and_requires_init():
    b=STBlock('ADP_RLS4');b.values.update(LAMBDA=.8,P0=10000.)
    assert b.trigger('INIT')==['INITO']
    old={k:v for k,v in b.values.items() if re.fullmatch(r'T[1-4]|P[1-4][1-4]',k)}
    b.values['Y']=float('nan');assert b.trigger('REQ')==['ERR']
    assert old=={k:b.values[k] for k in old};assert b.trigger('REQ')==[]


def test_composite_connections_and_with_contracts():
    r=ET.parse(TYPES/'ADP_IDENTIFICATION.fbt').getroot()
    fbs={b.get('Name'):ET.parse(TYPES/(b.get('Type')+'.fbt')).getroot() for b in r.findall('FBNetwork/FB')}
    def resolve(endpoint,kind,source):
        if '.' in endpoint:
            inst,port=endpoint.split('.');node=fbs[inst];direction='Output' if source else 'Input'
        else:node=r;port=endpoint;direction='Input' if source else 'Output'
        tag=('Event'+direction+'s/Event') if kind=='Event' else (direction+'Vars/VarDeclaration')
        v=node.find(f"InterfaceList/{tag}[@Name='{port}']");assert v is not None,endpoint
        return v
    for kind in ['Event','Data']:
        for c in r.findall('FBNetwork/'+kind+'Connections/Connection'):
            a=resolve(c.get('Source'),kind,True);b=resolve(c.get('Destination'),kind,False)
            assert a.get('Type')==b.get('Type')
    for node in [r,*fbs.values()]:
        for direction in ['Input','Output']:
            vs={v.get('Name') for v in node.findall('InterfaceList/'+direction+'Vars/VarDeclaration')}
            for ev in node.findall('InterfaceList/Event'+direction+'s/Event'):
                assert {w.get('Var') for w in ev.findall('With')}<=vs
    edges={(c.get('Source'),c.get('Destination')) for c in r.findall('FBNetwork/EventConnections/Connection')}
    assert ('Estimator.CNF','History.COMMIT') in edges
    assert ('History.ACK','CNF') in edges
    assert ('Process.CNF','Estimator.REQ') in edges
