"""Replay the checked-in application connections; no FORTE scheduling emulation."""
from pathlib import Path
from collections import deque
import xml.etree.ElementTree as E
import argparse,json,csv
import verify_pid_whiteboard as runtime
ROOT=Path(__file__).resolve().parents[1]
PROJECT=ROOT/'4diac/application/PID_Identification_Observer'

class ObserverNetwork:
 def __init__(self):
  self.network=E.parse(PROJECT/'PID_Identification_Observer.sys').find('Application/SubAppNetwork')
  old=runtime.TYPES;runtime.TYPES=PROJECT/'Type Library/observer'
  try:self.blocks={b.get('Name'):runtime.OfflineBlock(b.get('Type')) for b in self.network.findall('FB') if b.get('Type')!='E_CYCLE'}
  finally:runtime.TYPES=old
  for b in self.network.findall('FB'):
   if b.get('Name') in self.blocks:
    for p in b.findall('Parameter'):self.blocks[b.get('Name')].values[p.get('Name')]=float(p.get('Value'))
  self.events=[(c.get('Source'),c.get('Destination')) for c in self.network.findall('EventConnections/Connection')]
  self.data=[(c.get('Source'),c.get('Destination')) for c in self.network.findall('DataConnections/Connection')]
  self.running=False;self.trace=[]
 def deliver(self,destination):
  queue=deque([destination])
  while queue:
   dst=queue.popleft();name,event=dst.split('.')
   self.trace.append(dst)
   if name=='SamplingClock':
    if event=='START':self.running=True
    elif event=='STOP':self.running=False
    continue
   for source,target in self.data:
    dest,port=target.split('.')
    if dest==name:
     src,out=source.split('.');self.blocks[name].values[port]=self.blocks[src].values[out]
   for emitted in self.blocks[name].trigger(event):
    source=name+'.'+emitted;self.trace.append(source)
    queue.extend(dst for src,dst in self.events if src==source)
 def tick(self):
  if not self.running:raise RuntimeError('Clock stopped')
  for src,dst in self.events:
   if src=='SamplingClock.EO':self.deliver(dst)

def run():
 n=ObserverNetwork();n.deliver('SimulatedProcess.INIT');rows=[]
 while n.running and len(rows)<401:
  n.tick();p=n.blocks['SimulatedProcess'].values;c=n.blocks['FixedPID'].values;e=n.blocks['Identifier'].values
  rows.append(dict(sample=p['SAMPLE_COUNT'],reference=p['REFERENCE'],measurement=p['PROCESS_OUTPUT'],applied_command=p['APPLIED_COMMAND'],estimated_a1=e['EST_OUTPUT_COEFFICIENT_1'],estimated_a2=e['EST_OUTPUT_COEFFICIENT_2'],estimated_b1=e['EST_INPUT_COEFFICIENT_1'],estimated_b2=e['EST_INPUT_COEFFICIENT_2'],estimation_valid=e['ESTIMATION_VALID'],active_kp=c['KP_ACTIVE'],active_ki=c['KI_ACTIVE'],active_kd=c['KD_ACTIVE']))
  if any(x.endswith('.ERR') for x in n.trace):raise AssertionError('Block error')
 assert len(rows)==400 and not n.running
 return rows,n

def main():
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
 rows,n=run()
 with (a.output/'observer.csv').open('w',newline='',encoding='utf-8') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 result={'scope':'Application XML connections + actual ST/ECC subset replay; no native FORTE or wall-clock validation','samples':len(rows),'clock_stopped':not n.running,'final':rows[-1]}
 text=json.dumps(result,indent=2);(a.output/'summary.json').write_text(text+'\n');print(text)
if __name__=='__main__':main()
