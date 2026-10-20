from pathlib import Path
import sys,unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from verify_pid_observer import block,run,PORTS

class UpdateGateTests(unittest.TestCase):
 def test_gate_holds_and_forwards_coherent_sample(self):
  gate=block('IDENTIFICATION_UPDATE_GATE','4diac/prototypes/PID_Adaptation/Type Library/pid')
  names=['PROCESS_OUTPUT','OUTPUT_PREVIOUS_1','OUTPUT_PREVIOUS_2','INPUT_PREVIOUS_1','INPUT_PREVIOUS_2']
  gate.values.update(dict(zip(names,[5.,4.,3.,2.,1.])),UPDATE_ALLOWED=False)
  self.assertEqual(gate.trigger('REQ'),['HOLD'])
  self.assertTrue(all(gate.values['LATCHED_'+n]==0 for n in names))
  gate.values['UPDATE_ALLOWED']=True;self.assertEqual(gate.trigger('REQ'),['UPDATE'])
  self.assertEqual([gate.values['LATCHED_'+n] for n in names],[5.,4.,3.,2.,1.])
  gate.values.update(PROCESS_OUTPUT=999.,UPDATE_ALLOWED=False)
  self.assertEqual(gate.trigger('REQ'),['HOLD']);self.assertEqual(gate.values['LATCHED_PROCESS_OUTPUT'],5.)
 def test_constant_case_avoids_failure_and_preserves_held_estimate(self):
  rows=run(False,guard_updates=True);baseline=run(False,False)
  self.assertTrue(all(r['estimation_valid'] for r in rows))
  self.assertGreater(sum(not r['estimator_updated'] for r in rows),100)
  for i,r in enumerate(rows):
   self.assertEqual(r['applied_command'],baseline[i]['applied_command'])
   if not r['estimator_updated']:
    for n in PORTS:self.assertEqual(r['estimated_'+n.lower()],rows[i-1]['estimated_'+n.lower()])
    self.assertEqual(r['covariance_max_abs'],rows[i-1]['covariance_max_abs'])
    self.assertIsNone(r['prediction_error']);self.assertIsNone(r['candidate_kp'])
  self.assertGreater(min(r['covariance_min_eigenvalue'] for r in rows),0)
 def test_excited_case_is_unchanged(self):
  guarded=run(True,guard_updates=True);original=run(True)
  for a,b in zip(guarded,original):
   self.assertTrue(a['estimator_updated'])
   for n in PORTS:self.assertEqual(a['estimated_'+n.lower()],b['estimated_'+n.lower()])
   self.assertEqual(a['candidate_kp'],b['candidate_kp'])
 def test_guard_does_not_claim_identification_at_constant_reference(self):
  last=run(False,guard_updates=True)[-1]
  self.assertGreater(abs(last['estimated_input_coefficient_1']-.4),.1)
if __name__=='__main__':unittest.main()
