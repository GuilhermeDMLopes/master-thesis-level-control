"""Generate a stateless event gate; quality calculation remains external."""
from generate_pid_transition_prototypes import fb,state,edge,algorithm,write

def generate():
 data=['PROCESS_OUTPUT','OUTPUT_PREVIOUS_1','OUTPUT_PREVIOUS_2','INPUT_PREVIOUS_1','INPUT_PREVIOUS_2']
 ins={n:'LREAL' for n in data};ins['UPDATE_ALLOWED']='BOOL'
 outs={'LATCHED_'+n:'LREAL' for n in data}
 r,e=fb('IDENTIFICATION_UPDATE_GATE',ins,outs,{'REQ':list(ins)},{'UPDATE':list(outs),'HOLD':[]},{'ALLOW_CAPTURED':'BOOL'})
 for n,a,o in [('START',None,None),('CAPTURE','CAPTURE',None),('FORWARD',None,'UPDATE'),('PAUSE',None,'HOLD')]:state(e,n,a,o)
 for x,y,c in [('START','CAPTURE','REQ'),('CAPTURE','FORWARD','ALLOW_CAPTURED'),('CAPTURE','PAUSE','NOT ALLOW_CAPTURED'),('FORWARD','START','1'),('PAUSE','START','1')]:edge(e,x,y,c)
 algorithm(r,'CAPTURE',['ALLOW_CAPTURED := UPDATE_ALLOWED;','IF ALLOW_CAPTURED THEN']+[f'LATCHED_{n} := {n};' for n in data]+['END_IF;'])
 write(r)
if __name__=='__main__':generate()
