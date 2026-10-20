"""Actual generated ST/ECC subset replay, not native FORTE validation."""
from pathlib import Path
import sys, unittest
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import verify_pid_whiteboard as runtime
from verify_pid_model_tuning import tune

class TunerTests(unittest.TestCase):
 def block(self,theta=(1.2,-.36,.1,.06),period=.1,pole=.7):
  old=runtime.TYPES
  try:
   runtime.TYPES=ROOT/'4diac/prototypes/PID_Adaptation/Type Library/pid'
   b=runtime.OfflineBlock('PID_MODEL_TUNER')
  finally:runtime.TYPES=old
  for n,v in zip(['MODEL_OUTPUT_COEFFICIENT_1','MODEL_OUTPUT_COEFFICIENT_2','MODEL_INPUT_COEFFICIENT_1','MODEL_INPUT_COEFFICIENT_2'],theta):b.values[n]=v
  b.values.update(SAMPLE_TIME_S=period,DESIRED_POLE=pole)
  return b
 def gains(self,b):return [b.values['TARGET_'+n+'_GAIN'] for n in ['PROPORTIONAL','INTEGRAL','DERIVATIVE']]
 def test_lecture_models_and_estimated_model(self):
  for theta in [(1.2,-.36,.1,.06),(1.2,-.36,.4,.06),(1.200226802856,-.360178384301,.399970613765,.059894655811)]:
   b=self.block(theta);self.assertEqual(b.trigger('REQ'),['CNF'])
   expected,details=tune(theta);np.testing.assert_allclose(self.gains(b),expected,rtol=1e-10,atol=1e-12)
   self.assertAlmostEqual(b.values['REMAINING_POLE'],details['remaining_pole'])
 def test_reject_bad_inputs(self):
  for theta,ts,p in [((1.2,-.36,0,0),.1,.7),((1.2,-.36,0,.06),.1,.7),((float('nan'),0,.1,.06),.1,.7),((1.2,-.36,.1,.06),0,.7),((1.2,-.36,.1,.06),.1,1),((1.2,-.36,.1,.06),float('inf'),.7),((1.2,-.36,.1,.06),.1,float('nan'))]:
   b=self.block(theta,ts,p);self.assertEqual(b.trigger('REQ'),['ERR']);self.assertFalse(b.values['VALID'])
 def test_rejection_does_not_publish_stale_gains_and_recovers(self):
  b=self.block();b.trigger('REQ');previous=self.gains(b)
  b.values['MODEL_INPUT_COEFFICIENT_1']=0
  self.assertEqual(b.trigger('REQ'),['ERR']);self.assertEqual(self.gains(b),previous)
  b.values['MODEL_INPUT_COEFFICIENT_1']=.4
  self.assertEqual(b.trigger('REQ'),['CNF']);self.assertNotEqual(self.gains(b),previous)
 def test_independent_random_matrix_and_roots(self):
  rng=np.random.default_rng(61499);accepted=0;rejected=0
  for _ in range(250):
   theta=[rng.uniform(.8,1.5),rng.uniform(-.5,-.2),rng.uniform(.05,.5),rng.uniform(0,.1)]
   b=self.block(theta);events=b.trigger('REQ')
   try:expected,_=tune(theta)
   except ValueError:
    rejected+=1;self.assertEqual(events,['ERR']);continue
   self.assertEqual(events,['CNF']);accepted+=1
   np.testing.assert_allclose(self.gains(b),expected,rtol=1e-9,atol=1e-10)
   kp,ki,kd=self.gains(b);q0=kp+ki*.05+kd/.1;q1=-kp+ki*.05-2*kd/.1;q2=kd/.1
   a1,a2,b1,b2=theta
   self.assertLess(max(abs(np.roots([1,-1-a1+b1*q0,a1-a2+b1*q1+b2*q0,a2+b1*q2+b2*q1,b2*q2]))),1)
  self.assertGreater(accepted,10);self.assertGreater(rejected,10)
 def test_event_data_associations(self):
  b=self.block();x=b.xml
  inputs={v.get('Name') for v in x.findall('InterfaceList/InputVars/VarDeclaration')}
  withs={v.get('Var') for v in x.findall("InterfaceList/EventInputs/Event[@Name='REQ']/With")}
  self.assertEqual(inputs,withs)
  self.assertEqual([v.get('Var') for v in x.findall("InterfaceList/EventOutputs/Event[@Name='ERR']/With")],['VALID'])
if __name__=='__main__':unittest.main()
