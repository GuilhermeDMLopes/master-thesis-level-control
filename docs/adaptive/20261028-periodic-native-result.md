# Confirmação funcional nativa da atualização periódica

Em 28/10/2026 o usuário enviou image(20261028-135342).png, monitorando PID_Basic_Adaptive em LocalObserver.EMB_RES.

## Evidência observada

- Identifier: ENABLE_UPDATE=TRUE, UPDATE_AT_SAMPLE=275, UPDATE_INTERVAL_SAMPLES=25, SAMPLE_TIME_S=0.1.
- SamplingClock: DT=T#100ms, EO=400, START=1, STOP=1.
- Process: INIT=1, REQ=400, APPLY=400, APPLIED=399, DONE=1, SAMPLE_COUNT=400, VALID=TRUE.
- Identifier: REQ=400, CONTROL_READY=394, GAINS_READY=6.
- Controller: INIT=1, REQ=400, CNF=400, SET_GAINS=6, GAINS_CNF=6, VALID=TRUE, SATURATED=FALSE, INTEGRATION_ENABLED=TRUE.
- Eventos ERR visíveis dos três blocos: zero. Problems: zero itens.
- Referência final=0.8; saída do processo aproximadamente 0.800000202640857; comando aproximadamente 0.278260878233759.
- Ganhos enviados e presentes nas entradas UPDATED do PID: KP aproximadamente 0.155160289029149; KI aproximadamente 0.58226134744561; KD aproximadamente 0.00457286790150321.

## Conclusão e escopo

A rede básica executou 400 cálculos/aplicações e seis transferências confirmadas de ganhos no FORTE. Os contadores e valores finais são consistentes com o replay offline da configuração periódica. A última aplicação do processo emite DONE; por isso APPLIED=399 é esperado.

O início é configurado para a amostra 275 e o intervalo para 25 amostras (2.5 s nominais). Os instantes 275,300,325,350,375,400 foram verificados no teste offline; o print final confirma a contagem nativa, mas não mede individualmente esses instantes nem o jitter.

Isto encerra a verificação funcional desta configuração sintética finita. Não representa ensaio no PLC/planta física, certificação IEC 61499, estabilidade geral ou avaliação comparativa de desempenho. O escopo do artigo, conforme solicitado, é implementar e explicar a estrutura.

Preservar o projeto local salvo com layout e conexões de START, os exports usados e o executável registrado em 20261028-periodic-native-build.md. Próximo trabalho: consolidar a explicação dos três blocos, equações e sequência de eventos, mantendo a arquitetura existente.
