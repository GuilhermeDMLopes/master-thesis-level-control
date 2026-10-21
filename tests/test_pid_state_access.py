"""Offline ST/ECC checks, not native WITH/concurrency validation."""
from pathlib import Path
import sys
import unittest
import xml.etree.ElementTree as E
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import verify_pid_whiteboard as runtime
BASE=ROOT/'4diac/application/PID_Whiteboard/Type Library/pid'
EXPERIMENTAL=ROOT/'4diac/prototypes/PID_Adaptation/Type Library/pid'


def block(name,directory):
    old=runtime.TYPES
    try:
        runtime.TYPES=directory
        return runtime.OfflineBlock(name)
    finally:
        runtime.TYPES=old


def initialize(b):
    b.values.update(KP=1.,KI=.5,KD=.1,TS_S=.1,U_MIN=0.,U_MAX=10.)
    assert b.trigger('INIT')==['INITO']


class StateAccessTests(unittest.TestCase):
    def test_initial_state_is_first_declared_state(self):
        b=block('PID_FLAG_STATE_ACCESS',EXPERIMENTAL)
        self.assertEqual(b.xml.find('BasicFB/ECC/ECState').get('Name'),'START')
        self.assertEqual(b.state,'START')
        initialize(b)
        b.values.update(SP=1.,PV=0.)
        self.assertEqual(b.trigger('REQ'),['CNF'])
        self.assertEqual(b.trigger('READ_STATE'),['STATE_CNF'])
        self.assertAlmostEqual(b.values['MV'],2.025)
        self.assertAlmostEqual(b.values['INTEGRAL_MEMORY'],.05)

    def test_original_algorithms_unchanged(self):
        original=E.parse(BASE/'PID_FLAG.fbt').getroot()
        candidate=E.parse(EXPERIMENTAL/'PID_FLAG_STATE_ACCESS.fbt').getroot()
        for a in original.findall('BasicFB/Algorithm'):
            self.assertEqual(a.find('ST').get('Text'),candidate.find("BasicFB/Algorithm[@Name='%s']/ST"%a.get('Name')).get('Text'))

    def test_read_before_init_and_after_error(self):
        b=block('PID_FLAG_STATE_ACCESS',EXPERIMENTAL)
        self.assertEqual(b.trigger('READ_STATE'),['STATE_ERR'])
        self.assertEqual(b.state,'START')
        initialize(b)
        b.values.update(SP=float('nan'),PV=0.)
        self.assertEqual(b.trigger('REQ'),['ERR'])
        self.assertEqual(b.trigger('READ_STATE'),['STATE_ERR'])
        self.assertEqual(b.state,'FAILED_IDLE')
        initialize(b)
        self.assertEqual(b.trigger('READ_STATE'),['STATE_CNF'])

    def test_snapshot_preserves_memory_and_control_trace(self):
        old=block('PID_FLAG',BASE)
        new=block('PID_FLAG_STATE_ACCESS',EXPERIMENTAL)
        initialize(old);initialize(new)
        for k in range(100):
            if k==40:
                for b in (old,new):
                    b.values.update(KP=.7,KI=.3,KD=.05)
                    self.assertEqual(b.trigger('SET_GAINS'),['GAINS_CNF'])
            frozen={key:new.values[key] for key in old.values}
            self.assertEqual(new.trigger('READ_STATE'),['STATE_CNF'])
            self.assertEqual(frozen,{key:new.values[key] for key in old.values})
            self.assertEqual(new.values['INTEGRAL_MEMORY'],new.values['I_MEMORY'])
            self.assertEqual(new.values['PREVIOUS_ERROR'],new.values['E_PREV'])
            self.assertEqual(new.values['ACTIVE_INTEGRAL_GAIN'],new.values['KI_ACTIVE'])
            self.assertEqual(new.values['INTEGRATION_ENABLED'],new.values['FLAG'])
            for b in (old,new):
                b.values.update(SP=20. if k<20 else 1.,PV=.02*k)
                self.assertEqual(b.trigger('REQ'),['CNF'])
            self.assertEqual(old.values,{key:new.values[key] for key in old.values})

    def test_snapshot_event_associations(self):
        r=E.parse(EXPERIMENTAL/'PID_FLAG_STATE_ACCESS.fbt').getroot()
        event=r.find("InterfaceList/EventOutputs/Event[@Name='STATE_CNF']")
        names=[w.get('Var') for w in event.findall('With')]
        self.assertEqual(len(names),9)
        declared={v.get('Name') for v in r.findall('InterfaceList/OutputVars/VarDeclaration')}
        self.assertTrue(set(names)<=declared)

if __name__=='__main__':unittest.main()
