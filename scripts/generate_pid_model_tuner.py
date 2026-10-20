"""Experimental scalar ARX(2,2) PID tuner; generates only one prototype."""
from generate_pid_transition_prototypes import fb,state,edge,algorithm,write,finite

def generate():
 ins={n:'LREAL' for n in ['MODEL_OUTPUT_COEFFICIENT_1','MODEL_OUTPUT_COEFFICIENT_2','MODEL_INPUT_COEFFICIENT_1','MODEL_INPUT_COEFFICIENT_2','SAMPLE_TIME_S','DESIRED_POLE']}
 outs={n:'LREAL' for n in ['TARGET_PROPORTIONAL_GAIN','TARGET_INTEGRAL_GAIN','TARGET_DERIVATIVE_GAIN','REMAINING_POLE','POLYNOMIAL_RESIDUAL']};outs['VALID']='BOOL'
 names='A1 A2 B1 B2 P C1 C2 C3 H0 H1 H2 H3 S0 S1 S2 T0 T1 T2 DEN SCALE Q0 Q1 Q2 R KP KI KD RES MAG V1 V2 V3 V4'.split()
 r,e=fb('PID_MODEL_TUNER',ins,outs,{'REQ':list(ins)},{'CNF':list(outs),'ERR':['VALID']},{n:'LREAL' for n in names})
 for n,a,o in [('START',None,None),('CALCULATE','CALCULATE',None),('DONE',None,'CNF'),('REJECTED',None,'ERR')]:state(e,n,a,o)
 for x,y,c in [('START','CALCULATE','REQ'),('CALCULATE','DONE','VALID'),('CALCULATE','REJECTED','NOT VALID'),('DONE','START','1'),('REJECTED','START','1')]:edge(e,x,y,c)
 L=['VALID := '+finite(ins)+' AND (SAMPLE_TIME_S > 0.0) AND (DESIRED_POLE > 0.0) AND (DESIRED_POLE < 1.0);', 'IF VALID THEN',
 'A1 := MODEL_OUTPUT_COEFFICIENT_1;','A2 := MODEL_OUTPUT_COEFFICIENT_2;','B1 := MODEL_INPUT_COEFFICIENT_1;','B2 := MODEL_INPUT_COEFFICIENT_2;','P := DESIRED_POLE;',
 'SCALE := B1;','IF SCALE < 0.0 THEN','SCALE := -SCALE;','END_IF;','MAG := B2;','IF MAG < 0.0 THEN','MAG := -MAG;','END_IF;','IF MAG > SCALE THEN','SCALE := MAG;','END_IF;',
 'MAG := B1;','IF MAG < 0.0 THEN','MAG := -MAG;','END_IF;','VALID := (SCALE > 1.0E-12) AND (MAG > 1.0E-10 * SCALE);', 'IF VALID THEN',
 'C1 := -3.0 * P;','C2 := 3.0 * P * P;','C3 := -P * P * P;',
 'H0 := C1 + 1.0 + A1;','H1 := C2 - A1 + A2;','H2 := C3 - A2;','H3 := 0.0;',
 'S0 := H0 / B1;','T0 := -1.0 / B1;',
 'S1 := (H1 - B2 * S0) / B1;','T1 := (-C1 - B2 * T0) / B1;',
 'S2 := (H2 - B2 * S1) / B1;','T2 := (-C2 - B2 * T1) / B1;',
 'DEN := B2 * T2 + C3;','SCALE := B2 * T2;','IF SCALE < 0.0 THEN','SCALE := -SCALE;','END_IF;', 'MAG := C3;','IF MAG < 0.0 THEN','MAG := -MAG;','END_IF;','SCALE := SCALE + MAG;','MAG := DEN;','IF MAG < 0.0 THEN','MAG := -MAG;','END_IF;',
 'VALID := '+finite(['S0','S1','S2','T0','T1','T2','DEN','SCALE'])+' AND (MAG > 1.0E-10 * SCALE) AND (MAG > 1.0E-12);',
 'IF VALID THEN','R := (H3 - B2 * S2) / DEN;','Q0 := S0 + T0 * R;','Q1 := S1 + T1 * R;','Q2 := S2 + T2 * R;',
 'KP := (Q0 - Q1 - 3.0 * Q2) / 2.0;','KI := (Q0 + Q1 + Q2) / SAMPLE_TIME_S;','KD := SAMPLE_TIME_S * Q2;',
 'V1 := -1.0 - A1 + B1 * Q0 - (C1 - R);','V2 := A1 - A2 + B1 * Q1 + B2 * Q0 - (C2 - C1 * R);','V3 := A2 + B1 * Q2 + B2 * Q1 - (C3 - C2 * R);','V4 := B2 * Q2 + C3 * R;', 'RES := 0.0;']
 for v in ['V1','V2','V3','V4']:
  L += [f'MAG := {v};','IF MAG < 0.0 THEN','MAG := -MAG;','END_IF;','IF MAG > RES THEN','RES := MAG;','END_IF;']
 L += ['VALID := '+finite(['R','Q0','Q1','Q2','KP','KI','KD','V1','V2','V3','V4','RES'])+' AND (R > -1.0) AND (R < 1.0) AND (KP >= 0.0) AND (KI >= 0.0) AND (KD >= 0.0) AND (RES <= 1.0E-9);',
 'IF VALID THEN','TARGET_PROPORTIONAL_GAIN := KP;','TARGET_INTEGRAL_GAIN := KI;','TARGET_DERIVATIVE_GAIN := KD;','REMAINING_POLE := R;','POLYNOMIAL_RESIDUAL := RES;','END_IF;','END_IF;','END_IF;','END_IF;']
 algorithm(r,'CALCULATE',L);write(r)
if __name__=='__main__':generate()
