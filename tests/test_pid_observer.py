from pathlib import Path
import sys,unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from verify_pid_observer import run,GAINS

class ObserverTests(unittest.TestCase):
 def test_observer_never_changes_control(self):
  for changing in [False,True]:
   observed=run(changing);baseline=run(changing,False)
   self.assertEqual([(r['measurement'],r['applied_command']) for r in observed],[(r['measurement'],r['applied_command']) for r in baseline])
   for r in observed:self.assertEqual(tuple(r['active_'+n] for n in ['kp','ki','kd']),GAINS)
 def test_applied_history_and_request_schedule(self):
  rows=run()
  for i,r in enumerate(rows):
   self.assertEqual(r['previous_applied_command'],rows[i-1]['applied_command'] if i else 0.)
   self.assertEqual(r['previous_applied_command_2'],rows[i-2]['applied_command'] if i>=2 else 0.)
   if r['tuning_status'] in ['candidate_only','quality_rejected','tuner_rejected']:
    self.assertGreaterEqual(r['sample'],50);self.assertEqual(r['sample']%10,0)
   if r['tuning_status']!='candidate_only':self.assertIsNone(r['candidate_kp'])
 def test_constant_reference_failure_is_latched(self):
  rows=run(False);failures=[r for r in rows if not r['estimation_valid']]
  self.assertTrue(failures)
  for r in failures:
   self.assertEqual(r['tuning_status'],'estimator_failed');self.assertIsNone(r['candidate_ki'])
 def test_excited_case_recovers_changed_model(self):
  rows=run(True);last=rows[-1]
  self.assertTrue(all(r['estimation_valid'] for r in rows))
  for key,value in [('output_coefficient_1',1.2),('output_coefficient_2',-.36),('input_coefficient_1',.4),('input_coefficient_2',.06)]:self.assertAlmostEqual(last['estimated_'+key],value,places=6)
if __name__=='__main__':unittest.main()
