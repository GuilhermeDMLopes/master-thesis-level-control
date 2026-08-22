# MPC V3 ??? diagn??stico robusto do desligamento interno no ensaio de 60 s

## Resultado

Classifica????o: **INTERNAL_PV_RAW_TRIP_CONFIRMED_BY_FBT_AND_TRACE**

O diagn??stico foi refeito parseando estruturalmente o XML do FBT, em vez de
assumir que o ST apareceria como texto bruto no formato
`PV_RAW >= LREAL#<valor>`.

Limiares superiores resolvidos para `PV_RAW`:

- 800.0

Limiares superiores resolvidos para `predicted_y`:

- 650.0, 750.0

## Trajet??ria experimental

- transi????o observada `Enable=TRUE -> FALSE`: 34.141 s;
- raw imediatamente antes: 726.0;
- raw na primeira amostra com Enable falso: 757.0;
- Median9 antes/depois: 736.0 / 757.0;
- AppliedDAC antes/depois: 11846.0 / 0.0;
- raw m??ximo do ensaio: 818.0;
- Median9 m??xima: 757.0;
- DAC m??ximo: 11850.0;
- taxa positiva m??xima: 67.3 raw/s;
- watchdog saud??vel em todas as amostras: True;
- watchdog tripped em alguma amostra: False;
- altura f??sica m??xima observada: aproximadamente 1.0 cm.

## Interpreta????o

A queda do caminho de atua????o ocorreu com o watchdog saud??vel. O relat??rio
`results/mpc-v3-extended-20260822/v3-trip-st-diagnostic.txt` preserva as linhas
exatas do ST relacionadas a `PV_RAW`, `predicted_y` e `trip_code_internal`.

A classifica????o acima ?? deliberadamente limitada ao que o FBT e o CSV
efetivamente suportam. Se o parser resolver o limiar medido e houver cruzamento
pr??ximo ?? transi????o, o diagn??stico sustenta trip interno por n??vel. Caso
contr??rio, n??o se deve afirmar o c??digo/limiar sem observar os estados internos
do controlador em uma execu????o futura.

## Faixa f??sica

O ensaio atingiu 818.0 raw com apenas cerca de 1.0 cm
observados fisicamente. Isso sustenta que os limites usados no commissioning
foram conservadores, mas n??o autoriza automaticamente uma faixa de 1400???1500 raw.

Uma amplia????o deve continuar sendo aditiva, manter o V3 atual preservado e usar
um limite f??sico em cent??metros como prote????o independente.
