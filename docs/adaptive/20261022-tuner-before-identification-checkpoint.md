# Sintonia solicitada antes da identificação

Capturas image(20261022-130859).png, 131020, 131035, 131119 e 131145 (mesmo prefixo/data), consultadas na conversa, imagens não incorporadas.

Na última captura: SimulatedProcess.INIT=0, SAMPLE_COUNT=0; Identifier.INIT=0/REQ=0, coeficientes estimados zerados e ESTIMATION_VALID=FALSE. O PID de teste recebeu INIT e REQ, produzindo MV=2.025. ModelTuner recebeu REQ=1 e respondeu ERR=1/CNF=0/VALID=FALSE, com quatro coeficientes de entrada zero. Transição REQ=0 e PID.SET_GAINS=0.

Diagnóstico: a identificação de 400 amostras não foi executada nesta sessão de deployment antes da solicitação de sintonia. O tuner rejeitou o modelo nulo e a cadeia não aplicou ganhos. Não há evidência nesta tentativa de falha aritmética com modelo válido.

Recuperação: disparar SimulatedProcess.INIT uma vez para iniciar a cadeia existente de inicialização do observador (processo → identificador → FixedPID → relógio). Aguardar cerca de40s, SAMPLE_COUNT400, parada do relógio e coeficientes próximos de1.2/-0.36/0.4/0.06. Se a contagem não avançar, conferir eventos de inicialização antes de qualquer disparo manual do relógio. Não fazer novo deployment entre identificação e sintonia.

Depois, preparar o PID separado com INIT e REQ uma vez cada, conferir MV2.025 e disparar ModelTuner.REQ uma vez. Sem novo deployment, o ERR anterior do tuner permanece acumulado em1; sucesso desta nova tentativa deve aumentar CNF para1 sem aumentar ERR. Esperado REQ total do tuner2 e MV final do PID≈1.05755212.
