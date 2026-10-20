"""Offline execution of prototype ST/ECC; no native concurrency claim."""
from pathlib import Path
import sys
import unittest
import random
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import verify_pid_whiteboard as runtime
TYPES=ROOT/'4diac/prototypes/PID_Adaptation/Type Library/pid'

def block(name):
 old=runtime.TYPES
 try:
  runtime.TYPES=TYPES
  return runtime.OfflineBlock(name)
 finally:runtime.TYPES=old

def setup():
 b=block('PID_GAIN_TRANSITION')
 b.values.update(SETPOINT=1.,PROCESS_VARIABLE=1.,INTEGRAL_MEMORY=2.,PREVIOUS_ERROR=0.,ACTIVE_SAMPLE_TIME_S=.1,ACTIVE_OUTPUT_MIN=0.,ACTIVE_OUTPUT_MAX=10.,ACTIVE_PROPORTIONAL_GAIN=.45882339553937435,ACTIVE_INTEGRAL_GAIN=1.6381884387801722,ACTIVE_DERIVATIVE_GAIN=.016705052344105673,TARGET_PROPORTIONAL_GAIN=.15516028902910722,TARGET_INTEGRAL_GAIN=.5822613474455592,TARGET_DERIVATIVE_GAIN=.004572867901485872,MAX_GAIN_OUTPUT_CHANGE=.02,MAX_RELATIVE_GAIN_STEP=.02,PROPORTIONAL_SCALE_FLOOR=.01,INTEGRAL_SCALE_FLOOR=.01,DERIVATIVE_SCALE_FLOOR=.001,MODEL_OUTPUT_COEFFICIENT_1=1.2,MODEL_OUTPUT_COEFFICIENT_2=-.36,MODEL_INPUT_COEFFICIENT_1=.4,MODEL_INPUT_COEFFICIENT_2=.06,INTEGRATION_ENABLED=True,TUNING_ALLOWED=True)
 return b

class TransitionTests(unittest.TestCase):
 def test_gain_effect_bound_and_shared_fraction(self):
  b=setup();self.assertEqual(b.trigger('REQ'),['CNF']);self.assertTrue(b.values['UPDATE_APPLIED'])
  self.assertLessEqual(abs(b.values['GAIN_OUTPUT_CHANGE']),.02+1e-12)
  for n in ['PROPORTIONAL','INTEGRAL','DERIVATIVE']:
   v=b.values;self.assertAlmostEqual(v['NEXT_'+n+'_GAIN'],v['ACTIVE_'+n+'_GAIN']+v['STEP_FRACTION']*(v['TARGET_'+n+'_GAIN']-v['ACTIVE_'+n+'_GAIN']))
 def test_freeze_disallowed_and_invalid_target(self):
  for key,value in [('INTEGRATION_ENABLED',False),('TUNING_ALLOWED',False),('TARGET_INTEGRAL_GAIN',float('nan')),('MODEL_INPUT_COEFFICIENT_1',float('nan'))]:
   b=setup();b.values[key]=value;self.assertEqual(b.trigger('REQ'),['CNF']);self.assertFalse(b.values['UPDATE_APPLIED']);self.assertEqual(b.values['NEXT_INTEGRAL_GAIN'],b.values['ACTIVE_INTEGRAL_GAIN'])
 def test_bad_state_errors_without_authorizing_gains(self):
  for key,value in [('ACTIVE_SAMPLE_TIME_S',0.),('PROCESS_VARIABLE',float('nan')),('MAX_RELATIVE_GAIN_STEP',2.)]:
   b=setup();b.values[key]=value;self.assertEqual(b.trigger('REQ'),['ERR']);self.assertFalse(b.values['VALID'])
 def test_unstable_model_rejects_update(self):
  b=setup();b.values.update(MODEL_OUTPUT_COEFFICIENT_1=3.,MODEL_OUTPUT_COEFFICIENT_2=1.)
  self.assertEqual(b.trigger('REQ'),['CNF']);self.assertFalse(b.values['UPDATE_APPLIED'])
 def test_multiple_states_bound(self):
  rng=random.Random(20261020);accepted=0
  for _ in range(100):
   b=setup();b.values.update(PROCESS_VARIABLE=rng.uniform(.9,1.1),PREVIOUS_ERROR=rng.uniform(-.1,.1),INTEGRAL_MEMORY=rng.uniform(.1,3.))
   self.assertEqual(b.trigger('REQ'),['CNF'])
   if b.values['UPDATE_APPLIED']:
    accepted+=1;self.assertLessEqual(abs(b.values['GAIN_OUTPUT_CHANGE']),.02+1e-12)
  self.assertGreater(accepted,20)

 def test_polynomial_gate_against_independent_roots(self):
  import numpy as np
  rng=random.Random(61499)
  for _ in range(100):
   b=setup();a1=rng.uniform(-2,2);a2=rng.uniform(-1,1);bb1=rng.uniform(.01,1);bb2=rng.uniform(-.2,.2)
   kp,ki,kd=[rng.uniform(.01,1) for _ in range(3)]
   b.values.update(SETPOINT=0.,PROCESS_VARIABLE=0.,INTEGRAL_MEMORY=0.,PREVIOUS_ERROR=0.,ACTIVE_PROPORTIONAL_GAIN=kp,ACTIVE_INTEGRAL_GAIN=ki,ACTIVE_DERIVATIVE_GAIN=kd,TARGET_PROPORTIONAL_GAIN=kp,TARGET_INTEGRAL_GAIN=ki,TARGET_DERIVATIVE_GAIN=kd,MODEL_OUTPUT_COEFFICIENT_1=a1,MODEL_OUTPUT_COEFFICIENT_2=a2,MODEL_INPUT_COEFFICIENT_1=bb1,MODEL_INPUT_COEFFICIENT_2=bb2)
   q0=kp+ki*.05+kd/.1;q1=-kp+ki*.05-2*kd/.1;q2=kd/.1
   roots=np.roots([1,-1-a1+bb1*q0,a1-a2+bb1*q1+bb2*q0,a2+bb1*q2+bb2*q1,bb2*q2])
   self.assertEqual(b.trigger('REQ'),['CNF'])
   self.assertEqual(b.values['CANDIDATE_VALID'],bool(max(abs(roots))<1))

class CoordinatorTests(unittest.TestCase):
 def test_serial_chain_and_latched_measurement(self):
  c=block('PID_SAMPLE_COORDINATOR');self.assertEqual(c.trigger('INIT'),['INITO'])
  c.values.update(SETPOINT=1.,PROCESS_VARIABLE=.2);self.assertEqual(c.trigger('SAMPLE'),['READ_PID_STATE'])
  c.values.update(SETPOINT=99.,PROCESS_VARIABLE=77.)
  for event,expected in [('STATE_READY','CALCULATE_TRANSITION'),('TRANSITION_READY','APPLY_GAINS'),('GAINS_READY','EXECUTE_PID'),('CONTROL_READY','APPLY_OUTPUT'),('OUTPUT_APPLIED','CNF')]:
   self.assertEqual(c.trigger(event),[expected]);self.assertEqual(c.values['LATCHED_SETPOINT'],1.);self.assertEqual(c.values['LATCHED_PROCESS_VARIABLE'],.2)
  self.assertEqual(c.state,'READY')
 def test_overrun_and_fault_stop_chain(self):
  for event in ['SAMPLE','INIT','FAULT']:
   c=block('PID_SAMPLE_COORDINATOR');c.trigger('INIT');c.trigger('SAMPLE');self.assertEqual(c.trigger(event),['ERR']);self.assertEqual(c.trigger('STATE_READY'),[])
 def test_out_of_order_confirmation_cannot_compute(self):
  c=block('PID_SAMPLE_COORDINATOR');c.trigger('INIT');c.trigger('SAMPLE')
  self.assertEqual(c.trigger('GAINS_READY'),[]);self.assertEqual(c.state,'WAIT_STATE')
 def test_integrated_one_sample(self):
  c=block('PID_SAMPLE_COORDINATOR');pid=block('PID_FLAG_STATE_ACCESS');t=setup()
  pid.values.update(KP=.45882339553937435,KI=1.6381884387801722,KD=.016705052344105673,TS_S=.1,U_MIN=0.,U_MAX=10.)
  pid.trigger('INIT');c.trigger('INIT');c.values.update(SETPOINT=1.,PROCESS_VARIABLE=0.);c.trigger('SAMPLE')
  self.assertEqual(pid.trigger('READ_STATE'),['STATE_CNF'])
  for n in ['ACTIVE_PROPORTIONAL_GAIN','ACTIVE_INTEGRAL_GAIN','ACTIVE_DERIVATIVE_GAIN','ACTIVE_SAMPLE_TIME_S','ACTIVE_OUTPUT_MIN','ACTIVE_OUTPUT_MAX','INTEGRAL_MEMORY','PREVIOUS_ERROR','INTEGRATION_ENABLED']:t.values[n]=pid.values[n]
  t.values.update(SETPOINT=c.values['LATCHED_SETPOINT'],PROCESS_VARIABLE=c.values['LATCHED_PROCESS_VARIABLE'])
  c.trigger('STATE_READY');self.assertEqual(t.trigger('REQ'),['CNF']);c.trigger('TRANSITION_READY')
  pid.values.update(KP=t.values['NEXT_PROPORTIONAL_GAIN'],KI=t.values['NEXT_INTEGRAL_GAIN'],KD=t.values['NEXT_DERIVATIVE_GAIN'])
  memory=pid.values['I_MEMORY'];self.assertEqual(pid.trigger('SET_GAINS'),['GAINS_CNF']);self.assertEqual(pid.values['I_MEMORY'],memory)
  self.assertEqual(c.trigger('GAINS_READY'),['EXECUTE_PID'])
  pid.values.update(SP=c.values['LATCHED_SETPOINT'],PV=c.values['LATCHED_PROCESS_VARIABLE'])
  self.assertEqual(pid.trigger('REQ'),['CNF']);self.assertAlmostEqual(pid.values['I_MEMORY'],.05)
  self.assertEqual(c.trigger('CONTROL_READY'),['APPLY_OUTPUT']);self.assertEqual(c.trigger('OUTPUT_APPLIED'),['CNF'])

if __name__=='__main__':unittest.main()
