from pathlib import Path
import sys,unittest,xml.etree.ElementTree as E
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from verify_pid_identification_observer import ObserverNetwork,run,PROJECT
from verify_pid_observer import run as baseline

def xml_signature(element):
 # Ignore only whitespace between XML elements; preserve all attributes,
 # including ST Text, port names, types, WITH associations and ECC conditions.
 text=element.text if element.text and element.text.strip() else None
 tail=element.tail if element.tail and element.tail.strip() else None
 return (element.tag,tuple(sorted(element.attrib.items())),text,tail,
         tuple(xml_signature(child) for child in element))

class MinimalObserverTests(unittest.TestCase):
 def test_full_network_matches_existing_fixed_pid_observer(self):
  rows,n=run();expected=baseline()
  self.assertEqual(len(rows),400);self.assertFalse(n.running)
  for r,b in zip(rows,expected):
   self.assertAlmostEqual(r['measurement'],b['measurement'],places=12)
   self.assertAlmostEqual(r['applied_command'],b['applied_command'],places=12)
   self.assertEqual(r['reference'],b['setpoint']);self.assertTrue(r['estimation_valid'])
  for key,value in [('estimated_a1',1.2),('estimated_a2',-.36),('estimated_b1',.4),('estimated_b2',.06)]:self.assertAlmostEqual(rows[-1][key],value,places=6)
  self.assertFalse(any('SET_GAINS' in x for x in n.trace))
 def test_first_sample_event_order_and_initialization(self):
  n=ObserverNetwork();n.deliver('SimulatedProcess.INIT');self.assertTrue(n.running)
  self.assertEqual(n.trace,['SimulatedProcess.INIT','SimulatedProcess.INITO','Identifier.INIT','Identifier.INITO','FixedPID.INIT','FixedPID.INITO','SamplingClock.START'])
  n.trace=[];n.tick()
  self.assertEqual(n.trace,['SimulatedProcess.REQ','SimulatedProcess.CNF','Identifier.REQ','Identifier.CNF','FixedPID.REQ','FixedPID.CNF','SimulatedProcess.APPLY','SimulatedProcess.APPLIED'])
 def test_process_rejects_overlap_and_invalid_command(self):
  for fault in ['REQ','INIT','APPLY']:
   n=ObserverNetwork();b=n.blocks['SimulatedProcess'];b.trigger('INIT');b.trigger('REQ');b.values['COMMAND']=float('nan')
   self.assertEqual(b.trigger(fault),['ERR']);self.assertEqual(b.values['U1'],0)
 def test_xml_comparison_ignores_final_newline_but_detects_algorithm_changes(self):
  source=(PROJECT/'Type Library/observer/PID_FLAG.fbt').read_text()
  original=E.fromstring(source.rstrip())
  formatted=E.fromstring(source.rstrip()+'\r\n')
  self.assertEqual(xml_signature(original),xml_signature(formatted))
  st=formatted.find('BasicFB/Algorithm/ST')
  st.set('Text',st.get('Text')+'\nFLAG := FALSE;')
  self.assertNotEqual(xml_signature(original),xml_signature(formatted))
 def test_decimal_parameters_have_leading_digit(self):
  x=E.parse(PROJECT/'PID_Identification_Observer.sys')
  gains=[p for p in x.findall('.//Parameter') if p.get('Name') in ('KP','KD')]
  self.assertEqual(len(gains),4)
  for p in gains:self.assertRegex(p.get('Value'),r'^0\.[0-9]+$')
 def test_original_algorithms_preserved_and_mapping_matches(self):
  pairs=[('PID_FLAG','4diac/application/PID_Whiteboard/Type Library/pid'),('RLS_PARAMETER_ESTIMATOR','4diac/application/Adaptive_Identification/Type Library/adaptive')]
  for name,path in pairs:
   copied=E.parse(PROJECT/'Type Library/observer'/f'{name}.fbt').getroot()
   original=E.parse(ROOT/path/f'{name}.fbt').getroot()
   self.assertEqual(xml_signature(copied),xml_signature(original),name)
  x=E.parse(PROJECT/'PID_Identification_Observer.sys');a=x.find('Application/SubAppNetwork');b=x.find('Device/Resource/FBNetwork')
  self.assertEqual(len(a.findall('FB')),4);self.assertEqual(len(x.findall('Mapping')),4)
  for tag in ['EventConnections','DataConnections']:
   self.assertEqual([(c.get('Source'),c.get('Destination')) for c in a.find(tag)],[(c.get('Source'),c.get('Destination')) for c in b.find(tag)])
  for src,dst in [(c.get('Source'),c.get('Destination')) for c in a.find('EventConnections')]:self.assertNotIn('SET_GAINS',dst)
if __name__=='__main__':unittest.main()
