# PID básico: ensaio nativo com ganhos fixos

Evidência enviada em 27/10/2026: image(20261027-211148).png, monitoramento de LocalObserver.EMB_RES em PID_Basic_Adaptive.

- ENABLE_UPDATE=FALSE; UPDATE_AT_SAMPLE=275.
- Process.SAMPLE_COUNT=400; Process.REQ=400; APPLY=400; APPLIED=399; DONE=1. A última aplicação emite DONE, não APPLIED.
- Controller.REQ=400; CNF=400; SET_GAINS=0; GAINS_CNF=0.
- Identifier.CONTROL_READY=400; GAINS_READY=0.
- PROCESS_OUTPUT aproximadamente 0.80000000084298; CONTROL_OUTPUT aproximadamente 0.278260869300854.
- Eventos ERR visíveis: 0; Controller.VALID=TRUE; SATURATED=FALSE; INTEGRATION_ENABLED=TRUE.

O estado final e os contadores correspondem ao caso fixo esperado. O print não comprova a trajetória completa nem permite calcular IAE. As saídas de ganhos do Identifier permanecem zero porque o sintonizador não foi solicitado neste modo; o PID usa os ganhos iniciais.

O layout local difere do gerado e mostra conexões de START/E_RESTART. Preservar o .sys local. Se a inicialização ocorrer automaticamente no deployment, não disparar INIT novamente durante o ensaio.

Próximo passo: repetir desde a inicialização com ENABLE_UPDATE=TRUE e UPDATE_AT_SAMPLE=275; esperar uma única confirmação de ganhos antes do cálculo PID da amostra 275. Não é necessária nova exportação ou compilação por alterar somente esse parâmetro. Registrar como ressintonia única, não adaptação contínua nem melhoria de desempenho.
