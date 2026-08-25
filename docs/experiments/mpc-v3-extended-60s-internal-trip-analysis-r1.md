# MPC V3 — diagnóstico robusto do desligamento interno no ensaio de 60 s

## Resultado

Classificação: **INTERNAL_PV_RAW_TRIP_CONFIRMED_BY_FBT_AND_TRACE**

O diagnóstico foi refeito parseando estruturalmente o XML do FBT, em vez de
assumir que o ST apareceria como texto bruto no formato
`PV_RAW >= LREAL#<valor>`.

Limiares superiores resolvidos para `PV_RAW`:

- 800.0

Limiares superiores resolvidos para `predicted_y`:

- 650.0, 750.0

## Trajetória experimental

- transição observada `Enable=TRUE -> FALSE`: 34.141 s;
- raw imediatamente antes: 726.0;
- raw na primeira amostra com Enable falso: 757.0;
- Median9 antes/depois: 736.0 / 757.0;
- AppliedDAC antes/depois: 11846.0 / 0.0;
- raw máximo do ensaio: 818.0;
- Median9 máxima: 757.0;
- DAC máximo: 11850.0;
- taxa positiva máxima: 67.3 raw/s;
- watchdog saudável em todas as amostras: True;
- watchdog tripped em alguma amostra: False;
- altura física máxima observada: aproximadamente 1.0 cm.

## Interpretação

A queda do caminho de atuação ocorreu com o watchdog saudável. O relatório
`results/mpc-v3-extended-20260822/v3-trip-st-diagnostic.txt` preserva as linhas
exatas do ST relacionadas a `PV_RAW`, `predicted_y` e `trip_code_internal`.

A classificação acima é deliberadamente limitada ao que o FBT e o CSV
efetivamente suportam. Se o parser resolver o limiar medido e houver cruzamento
próximo à transição, o diagnóstico sustenta trip interno por nível. Caso
contrário, não se deve afirmar o código/limiar sem observar os estados internos
do controlador em uma execução futura.

## Faixa física

O ensaio atingiu 818.0 raw com apenas cerca de 1.0 cm
observados fisicamente. Isso sustenta que os limites usados no commissioning
foram conservadores, mas não autoriza automaticamente uma faixa de 1400–1500 raw.

Uma ampliação deve continuar sendo aditiva, manter o V3 atual preservado e usar
um limite físico em centímetros como proteção independente.
