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
            expected=a.find('ST').get('Text')
            actual=candidate.find("BasicFB/Algorithm[@Name='%s']/ST"%a.get('Name')).get('Text')
            for short,long in [('KP','PROPORTIONAL'),('KI','INTEGRAL'),('KD','DERIVATIVE')]:
                actual=actual.replace('UPDATED_'+long+'_GAIN',short)
            self.assertEqual(expected,actual)

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
                    if b is new:
                        b.values.update(UPDATED_PROPORTIONAL_GAIN=.7,UPDATED_INTEGRAL_GAIN=.3,UPDATED_DERIVATIVE_GAIN=.05)
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

    def test_separate_update_ports_and_complete_sequence(self):
        from test_pid_transition_chain import setup
        pid=block('PID_FLAG_STATE_ACCESS',EXPERIMENTAL)
        initialize(pid)  # Update ports remain zero, as before transition's first CNF.
        pid.values.update(SP=1.,PV=0.)
        self.assertEqual(pid.trigger('REQ'),['CNF'])
        self.assertAlmostEqual(pid.values['MV'],2.025)
        self.assertEqual(pid.trigger('READ_STATE'),['STATE_CNF'])
        transition=setup()
        transition.values.update(SETPOINT=1.,PROCESS_VARIABLE=0.,
            TARGET_PROPORTIONAL_GAIN=.9,TARGET_INTEGRAL_GAIN=.45,
            TARGET_DERIVATIVE_GAIN=.09,MODEL_INPUT_COEFFICIENT_1=.1)
        names=[w.get('Var') for w in pid.xml.findall("InterfaceList/EventOutputs/Event[@Name='STATE_CNF']/With")]
        for name in names: transition.values[name]=pid.values[name]
        self.assertEqual(transition.trigger('REQ'),['CNF'])
        for name in ('PROPORTIONAL','INTEGRAL','DERIVATIVE'):
            pid.values['UPDATED_'+name+'_GAIN']=transition.values['NEXT_'+name+'_GAIN']
        self.assertEqual(pid.trigger('SET_GAINS'),['GAINS_CNF'])
        self.assertAlmostEqual(pid.values['I_MEMORY'],.05)
        self.assertAlmostEqual(pid.values['MV'],2.025)
        self.assertEqual(pid.trigger('REQ'),['CNF'])
        self.assertAlmostEqual(pid.values['MV'],1.055)
        self.assertAlmostEqual(pid.values['I_MEMORY'],.15)
        # Reinitialization takes the original gains even with nonzero update inputs.
        self.assertEqual(pid.trigger('INIT'),['INITO'])
        self.assertEqual(pid.values['KP_ACTIVE'],1.)
        self.assertEqual(pid.values['KI_ACTIVE'],.5)
        self.assertEqual(pid.values['KD_ACTIVE'],.1)
        self.assertEqual(pid.values['I_MEMORY'],0.)
        events=pid.xml.find('InterfaceList/EventInputs')
        init={w.get('Var') for w in events.find("Event[@Name='INIT']").findall('With')}
        update={w.get('Var') for w in events.find("Event[@Name='SET_GAINS']").findall('With')}
        self.assertTrue({'KP','KI','KD'} <= init)
        self.assertEqual(update,{'UPDATED_PROPORTIONAL_GAIN','UPDATED_INTEGRAL_GAIN','UPDATED_DERIVATIVE_GAIN'})
        self.assertTrue(init.isdisjoint(update))

    def test_snapshot_event_associations(self):
        r=E.parse(EXPERIMENTAL/'PID_FLAG_STATE_ACCESS.fbt').getroot()
        event=r.find("InterfaceList/EventOutputs/Event[@Name='STATE_CNF']")
        names=[w.get('Var') for w in event.findall('With')]
        self.assertEqual(len(names),9)
        declared={v.get('Name') for v in r.findall('InterfaceList/OutputVars/VarDeclaration')}
        self.assertTrue(set(names)<=declared)

if __name__=='__main__':unittest.main()
