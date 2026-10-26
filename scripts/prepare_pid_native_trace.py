"""Instrument a COPY of the verified 4diac exports; never modifies original exports."""
import argparse
import hashlib
from pathlib import Path
import shutil
EXPECTED='07308a96e4c10ff7493b2d9bae35bd155d85933222d3c42eae09b270ca7194c1'

def prepare(source, destination):
    source=Path(source); destination=Path(destination)
    matches=list(source.rglob('PID_FLAG_STATE_ACCESS.cpp'))
    if len(matches)!=1: raise ValueError('Expected exactly one PID_FLAG_STATE_ACCESS.cpp')
    original=matches[0].read_bytes()
    if hashlib.sha256(original).hexdigest()!=EXPECTED:
        raise ValueError('Export differs from validated upload; send the current export before patching')
    if destination.exists(): raise ValueError('Destination already exists; use a new directory')
    text=original.decode('utf-8').replace('\r\n','\n')
    text=text.replace('#include "PID_FLAG_STATE_ACCESS.h"','#include "PID_FLAG_STATE_ACCESS.h"\n#include "pid_csv_trace.h"',1)
    for state,event,hook in [
        ('INIT_OK','INITO','pid_trace::writer().init(this);'),
        ('SAMPLE_OK','CNF','pid_trace::writer().row(this, static_cast<TForteDFloat>(st_SP()), static_cast<TForteDFloat>(st_PV()), static_cast<TForteDFloat>(st_MV()), static_cast<TForteDFloat>(st_KP_ACTIVE()), static_cast<TForteDFloat>(st_KI_ACTIVE()), static_cast<TForteDFloat>(st_KD_ACTIVE()));')]:
        old=f'  m_nECCState = scm_nState{state};\n  sendOutputEvent(scm_nEvent{event}ID);'
        if text.count(old)!=1: raise ValueError('Unexpected generated state')
        text=text.replace(old,f'  m_nECCState = scm_nState{state};\n  {hook}\n  sendOutputEvent(scm_nEvent{event}ID);')
    shutil.copytree(source,destination)
    output=destination/matches[0].relative_to(source)
    output.write_text(text,encoding='utf-8')
    shutil.copyfile(Path(__file__).parent/'native/pid_csv_trace.h',output.parent/'pid_csv_trace.h')
    print('Instrumented export copy:',destination)
    print('Build with -ExportDirectory pointing to this copy. Original exports preserved.')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',required=True,type=Path)
    p.add_argument('--destination',required=True,type=Path)
    a=p.parse_args();prepare(a.source,a.destination)
