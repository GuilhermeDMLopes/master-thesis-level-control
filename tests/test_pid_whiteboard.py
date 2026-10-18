"""Hand-calculated algorithm and local ECC/connection checks, not FORTE tests."""
import unittest
import xml.etree.ElementTree as ET
from scripts.verify_pid_whiteboard import OfflineBlock, ROOT, TYPES, demo


class WhiteboardPIDTests(unittest.TestCase):
    def make(self, **params):
        b = OfflineBlock('PID_FLAG')
        b.values.update(KP=1., KI=0., KD=0., TS_S=1., U_MIN=-100., U_MAX=100.)
        b.values.update(params)
        self.assertEqual(b.trigger('INIT'), ['INITO'])
        return b

    def sample(self, b, error):
        b.values.update(SP=error, PV=0.)
        self.assertEqual(b.trigger('REQ'), ['CNF'])
        self.assertEqual(b.state, 'READY')
        return b.values

    def test_scientific_literals_use_explicit_exponent_sign(self):
        # 4diac 2.0.1 exporter reported E100 as an extraneous token.
        for path in TYPES.glob('*.fbt'):
            text = path.read_text()
            self.assertNotIn('1.0E100', text)
            self.assertIn('1.0E+100', text)

    def test_proportional(self):
        b = self.make(KP=2.)
        self.assertEqual(self.sample(b, 3.)['MV'], 6.)
        self.assertEqual(self.sample(b, -2.)['MV'], -4.)

    def test_trapezoid_and_zero_history(self):
        b = self.make(KP=0., KI=2., TS_S=.1)
        for error, expected in [(2., .2), (2., .6), (0., .8)]:
            self.assertAlmostEqual(self.sample(b, error)['MV'], expected)

    def test_backward_derivative_first_sample_and_step(self):
        b = self.make(KP=0., KD=.5, TS_S=.1)
        for error, expected in [(2., 10.), (2., 0.), (1., -5.)]:
            self.assertAlmostEqual(self.sample(b, error)['MV'], expected)

    def test_delayed_flag_and_known_freeze_limitation(self):
        b = self.make(KP=1., KI=1., U_MIN=0., U_MAX=1.)
        v = self.sample(b, 10.)
        self.assertEqual((v['I_MEMORY'], v['RAW'], v['MV'], v['FLAG']), (5., 15., 1., False))
        for _ in range(5):
            v = self.sample(b, -1.)
            self.assertEqual((v['I_MEMORY'], v['RAW'], v['MV'], v['FLAG']), (5., 4., 1., False))
        # Saturation ends at equality; integration only resumes on NEXT sample.
        v = self.sample(b, -4.)
        self.assertEqual((v['I_MEMORY'], v['MV'], v['FLAG']), (5., 1., True))
        self.assertEqual(self.sample(b, -4.)['I_MEMORY'], 1.)

    def test_lower_limit_and_strict_equality(self):
        b = self.make(U_MIN=-1., U_MAX=1.)
        for e, mv, flag in [(-2., -1., False), (-1., -1., True), (1., 1., True), (2., 1., False)]:
            v = self.sample(b, e)
            self.assertEqual((v['MV'], v['FLAG']), (mv, flag))
            self.assertEqual(v['SATURATED'], not flag)

    def test_gain_event_latches_triplet_without_calculating_or_resetting(self):
        b = self.make(KI=1.)
        self.sample(b, 2.)
        old = {k:b.values[k] for k in ['I_MEMORY', 'E_PREV', 'FLAG', 'MV']}
        b.values.update(KP=2., KI=3., KD=4.)
        self.assertEqual(b.trigger('SET_GAINS'), ['GAINS_CNF'])
        self.assertEqual(old, {k:b.values[k] for k in old})
        self.assertEqual([b.values[k] for k in ['KP_ACTIVE','KI_ACTIVE','KD_ACTIVE']], [2.,3.,4.])
        b.values.update(KP=99., KI=99., KD=99.)  # data alone does not update gains
        self.assertEqual(self.sample(b, 2.)['MV'], 13.)  # 2*2 + 3*(1+2) + 4*0

    def test_reinit_and_uninitialized_request(self):
        b = OfflineBlock('PID_FLAG')
        self.assertEqual(b.trigger('REQ'), ['ERR'])
        self.assertFalse(b.values['VALID'])
        b = self.make(KI=1.)
        self.sample(b, 3.)
        self.assertEqual(b.trigger('INIT'), ['INITO'])
        self.assertEqual((b.values['I_MEMORY'], b.values['E_PREV'], b.values['FLAG']), (0.,0.,True))

    def test_bad_configuration_and_failed_update_preserve_memory(self):
        for params in [dict(TS_S=0.), dict(TS_S=-1.), dict(U_MIN=100.), dict(KP=float('inf')),dict(KI=float('nan'))]:
            with self.subTest(params=params):
                b = OfflineBlock('PID_FLAG')
                b.values.update(KP=1., KI=0., KD=0., TS_S=1., U_MIN=0., U_MAX=100.)
                b.values.update(params)
                self.assertEqual(b.trigger('INIT'), ['ERR'])
        for bad in [float('nan'), float('inf'), -float('inf'), 1e101]:
            b = self.make(KI=1.)
            self.sample(b, 2.)
            old = {k:b.values[k] for k in ['I_MEMORY', 'E_PREV', 'FLAG', 'MV']}
            b.values['PV'] = bad
            self.assertEqual(b.trigger('REQ'), ['ERR'])
            self.assertEqual(old, {k:b.values[k] for k in old})
            self.assertEqual(b.trigger('REQ'), [])  # latched fault, INIT required

    def test_overflow_and_invalid_gain_update(self):
        b = self.make(KP=1e100)
        b.values.update(SP=1e100, PV=0.)
        self.assertEqual(b.trigger('REQ'), ['ERR'])
        self.assertEqual(b.values['I_MEMORY'], 0.)
        b = self.make()
        b.values.update(KP=2., KI=float('nan'), KD=4.)
        self.assertEqual(b.trigger('SET_GAINS'), ['ERR'])
        self.assertEqual([b.values[k] for k in ['KP_ACTIVE','KI_ACTIVE','KD_ACTIVE']], [1.,0.,0.])

    def test_synthetic_process_latches_input_only_on_apply(self):
        b = OfflineBlock('PID_DEMO_PROCESS')
        self.assertEqual(b.trigger('INIT'), ['INITO'])
        b.values['U'] = 2.
        self.assertEqual(b.trigger('REQ'), ['CNF'])
        self.assertEqual(b.values['Y'], 0.)
        self.assertEqual(b.trigger('APPLY'), ['ACK'])
        self.assertEqual(b.values['Y'], 0.)
        self.assertEqual(b.trigger('REQ'), ['CNF'])
        self.assertAlmostEqual(b.values['Y'], .2)

    def test_closed_loop_hand_calculation(self):
        rows = demo(100)
        # k1: y=0,e=1,I=.05,D=10 -> u=1+.025+1=2.025
        # k2: y=.2025,e=.7975,I=.139875,D=-2.025 -> u=.6649375
        self.assertAlmostEqual(rows[0]['mv'], 2.025)
        self.assertAlmostEqual(rows[1]['pv'], .2025)
        self.assertAlmostEqual(rows[1]['mv'], .6649375)
        for prev, row in zip(rows, rows[1:]):
            self.assertAlmostEqual(row['pv'], .9*prev['pv'] + .1*prev['mv'])
            self.assertEqual(row['previous_applied_u'], prev['mv'])

    def test_ports_with_associations_and_network_edges(self):
        network = ET.parse(ROOT/'4diac/application/PID_Whiteboard/PID_Whiteboard.sys').getroot().find('Application/SubAppNetwork')
        base = TYPES.parent
        blocks = {}
        for fb in network.findall('FB'):
            typ = fb.get('Type')
            folder = 'events' if typ == 'E_CYCLE' else 'pid'
            blocks[fb.get('Name')] = ET.parse(base/folder/(typ+'.fbt')).getroot()
        for block in blocks.values():
            for direction in ['Input','Output']:
                vs = {v.get('Name') for v in block.findall('InterfaceList/'+direction+'Vars/VarDeclaration')}
                for ev in block.findall('InterfaceList/Event'+direction+'s/Event'):
                    self.assertLessEqual({w.get('Var') for w in ev.findall('With')}, vs)
        for kind in ['Event','Data']:
            for edge in network.findall(kind+'Connections/Connection'):
                ports = []
                for side,direction in [('Source','Output'),('Destination','Input')]:
                    instance,port = edge.get(side).split('.')
                    tag = 'Event'+direction+'s/Event' if kind=='Event' else direction+'Vars/VarDeclaration'
                    found = blocks[instance].find(f"InterfaceList/{tag}[@Name='{port}']")
                    self.assertIsNotNone(found, edge.attrib)
                    ports.append(found)
                self.assertEqual(ports[0].get('Type'),ports[1].get('Type'))
        edges = {(e.get('Source'),e.get('Destination')) for e in network.findall('EventConnections/Connection')}
        self.assertIn(('Process.CNF','Controller.REQ'),edges)
        self.assertIn(('Controller.CNF','Process.APPLY'),edges)
        self.assertNotIn(('Cycle.EO','Controller.REQ'),edges)


if __name__ == '__main__':
    unittest.main()
