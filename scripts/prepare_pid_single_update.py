"""Add the single-update sequence to the user's saved project, with a full backup."""
from pathlib import Path
from datetime import datetime
import argparse
import copy
import shutil
import xml.etree.ElementTree as E
ROOT=Path(__file__).resolve().parents[1]
TYPE_FILE=ROOT/'4diac/prototypes/PID_Adaptation/Type Library/pid/PID_SINGLE_UPDATE_SEQUENCE.fbt'
PID='PID_FLAG_STATE_ACCESS'
NAME='SingleUpdateSequence'
REMOVE=[(f'{PID}.INITO','SamplingClock.START'),('Identifier.CNF',f'{PID}.REQ'),('ModelTuner.CNF',f'{PID}.READ_STATE'),(f'{PID}.STATE_CNF','GainTransitionTest.REQ'),('GainTransitionTest.CNF',f'{PID}.SET_GAINS')]
ADD=[(f'{PID}.INITO',f'{NAME}.INIT'),(f'{NAME}.INITO','SamplingClock.START'),('Identifier.CNF',f'{NAME}.SAMPLE'),(f'{NAME}.REQUEST_TUNING','ModelTuner.REQ'),('ModelTuner.CNF',f'{NAME}.TUNING_READY'),('ModelTuner.ERR',f'{NAME}.UPDATE_REJECTED'),(f'{NAME}.READ_PID_STATE',f'{PID}.READ_STATE'),(f'{PID}.STATE_CNF',f'{NAME}.STATE_READY'),(f'{NAME}.CALCULATE_TRANSITION','GainTransitionTest.REQ'),('GainTransitionTest.CNF',f'{NAME}.TRANSITION_READY'),('GainTransitionTest.ERR',f'{NAME}.UPDATE_REJECTED'),(f'{NAME}.APPLY_GAINS',f'{PID}.SET_GAINS'),(f'{PID}.GAINS_CNF',f'{NAME}.GAINS_READY'),(f'{NAME}.EXECUTE_PID',f'{PID}.REQ'),('SimulatedProcess.APPLIED',f'{NAME}.OUTPUT_APPLIED'),('SimulatedProcess.DONE',f'{NAME}.OUTPUT_APPLIED'),(f'{NAME}.ERR','SamplingClock.STOP'),(f'{PID}.STATE_ERR',f'{NAME}.FAULT'),(f'{PID}.ERR',f'{NAME}.FAULT'),('Identifier.ERR',f'{NAME}.FAULT'),('SimulatedProcess.ERR',f'{NAME}.FAULT')]

def pairs(net,tag):
    return [(c.get('Source'),c.get('Destination')) for c in net.findall(tag+'/Connection')]

def transform(root):
    root=copy.deepcopy(root)
    nets=[root.find("Application[@Name='Observer_Test']/SubAppNetwork"),root.find("Device[@Name='LocalObserver']/Resource[@Name='EMB_RES']/FBNetwork")]
    if any(n is None for n in nets):raise ValueError('Expected application/resource not found')
    for net in nets:
        if net.find(f"FB[@Name='{NAME}']") is not None:raise ValueError('Sequence already exists; no changes made')
        for name,kind in [('SimulatedProcess','OBSERVER_DEMO_PROCESS'),('Identifier','RLS_PARAMETER_ESTIMATOR'),(PID,PID),('ModelTuner','PID_MODEL_TUNER'),('GainTransitionTest','PID_GAIN_TRANSITION')]:
            fb=net.find(f"FB[@Name='{name}']")
            if fb is None or fb.get('Type').split('::')[-1]!=kind:raise ValueError('Unexpected block: '+name)
        events=pairs(net,'EventConnections');data=pairs(net,'DataConnections')
        for connection in REMOVE+[(f'{PID}.CNF','SimulatedProcess.APPLY')]:
            if events.count(connection)!=1:raise ValueError('Missing or duplicate expected event: '+str(connection))
        # Exactly the manually validated update/control paths; reject extra triggering sources.
        for dest,source in [('ModelTuner.REQ',None),(f'{PID}.REQ','Identifier.CNF'),(f'{PID}.READ_STATE','ModelTuner.CNF'),(f'{PID}.SET_GAINS','GainTransitionTest.CNF'),('GainTransitionTest.REQ',f'{PID}.STATE_CNF')]:
            actual=[s for s,d in events if d==dest]
            if actual!=([source] if source else []):raise ValueError('Unexpected event producers for '+dest)
        required=[('SimulatedProcess.REFERENCE',f'{PID}.SP'),('SimulatedProcess.PROCESS_OUTPUT',f'{PID}.PV'),('SimulatedProcess.REFERENCE','GainTransitionTest.SETPOINT'),('SimulatedProcess.PROCESS_OUTPUT','GainTransitionTest.PROCESS_VARIABLE'),(f'{PID}.MV','SimulatedProcess.COMMAND')]
        for s,d in required:
            if [a for a,b in data if b==d]!=[s]:raise ValueError('Unexpected data source for '+d)
        fb=E.Element('FB',Name=NAME,Type='PID_SINGLE_UPDATE_SEQUENCE',x='400',y='1900',Comment='One automatic attempt before PID calculation at sample 275')
        E.SubElement(fb,'Parameter',Name='ENABLE_UPDATE',Value='TRUE');E.SubElement(fb,'Parameter',Name='UPDATE_AT_SAMPLE',Value='275')
        ec=net.find('EventConnections');net.insert(list(net).index(ec),fb)
        for c in list(ec):
            if (c.get('Source'),c.get('Destination')) in REMOVE:ec.remove(c)
        for s,d in ADD:E.SubElement(ec,'Connection',Source=s,Destination=d)
        E.SubElement(net.find('DataConnections'),'Connection',Source='SimulatedProcess.SAMPLE_COUNT',Destination=f'{NAME}.SAMPLE_NUMBER')
    for tag in ['EventConnections','DataConnections']:
        if set(pairs(nets[0],tag))!=set(pairs(nets[1],tag)):raise ValueError('Application/resource wiring differs; reconcile in IDE first')
    E.SubElement(root,'Mapping',From=f'Observer_Test.{NAME}',To=f'LocalObserver.EMB_RES.{NAME}')
    return root

def prepare(project,backup_root):
    system=project/'PID_Identification_Observer.sys'
    original=system.read_bytes();root=transform(E.fromstring(original))
    target=project/'Type Library/observer'/TYPE_FILE.name
    if target.exists():raise ValueError('Sequence type already exists; preserved')
    backup=backup_root/(datetime.now().strftime('%Y%m%d-%H%M%S-%f')+'-before-single-update')
    shutil.copytree(project,backup/project.name)
    E.indent(root,space='  ')
    payload=E.tostring(root,encoding='utf-8',xml_declaration=True)
    temporary=system.with_suffix('.sys.single-update.tmp')
    try:
        if system.read_bytes()!=original:raise RuntimeError('Project changed while preparing; close IDE editors and retry')
        target.write_bytes(TYPE_FILE.read_bytes());temporary.write_bytes(payload)
        E.parse(temporary);temporary.replace(system)
    except Exception:
        target.unlink(missing_ok=True)
        raise
    finally:temporary.unlink(missing_ok=True)
    print('Backup:',backup)
    print('Prepared:',system)
    print('Export PID_SINGLE_UPDATE_SEQUENCE and rebuild FORTE before deployment.')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--project',type=Path,required=True)
    p.add_argument('--backup-root',type=Path,default=Path.home()/'Documents/4diac-backups')
    a=p.parse_args();prepare(a.project,a.backup_root)
