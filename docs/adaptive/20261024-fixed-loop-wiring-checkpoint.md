# Conferência da transferência do PID para a malha

Prints recebidos em 24/10/2026: image(20261024-152611).png e image(20261024-152840).png. Evidência visual; imagens não incorporadas neste commit.

O monitoramento mostra 400 amostras no processo e identificador, FixedPID.INIT=1 e REQ/CNF=400/400. PID_FLAG_STATE_ACCESS.INIT=0, REQ/CNF=0/0, MV=0 e VALID=FALSE. ModelTuner e GainTransitionTest permanecem sem execução. Os ganhos iniciais do novo PID foram preenchidos, mas a transferência da malha ainda não foi executada no recurso observado. VALID=FALSE no novo PID é compatível com ausência de inicialização; não há evidência de erro do algoritmo.

Correção: na aplicação Observer_Test, substituir as cinco conexões de eventos e três de dados de FixedPID pelas correspondentes em PID_FLAG_STATE_ACCESS, conforme roteiro 20261023-state-pid-fixed-loop-procedure.md. Conferir as mesmas conexões no recurso mapeado LocalObserver.EMB_RES antes de novo deployment completo. Não iniciar manualmente o novo PID para compensar conexões ausentes.

Critério pendente: após disparar apenas SimulatedProcess.INIT, o novo PID deve receber INIT=1 e REQ/CNF=400/400; FixedPID.REQ=0; sintonia sem execução. A saída final do processo neste print é a referência antiga, não uma validação da substituição do controlador.
