# Sintonia ligada à cadeia: ensaio com identificação concluída

Preparação offline em 22/10/2026; execução nativa pendente. Sem novos tipos nem recompilação. Preservar a malha do FixedPID/Identifier; PID_FLAG_STATE_ACCESS permanece isolado do comando do processo.

Conectar ModelTuner.CNF → PID_FLAG_STATE_ACCESS.READ_STATE. Conectar os três ModelTuner.TARGET_*_GAIN às entradas homônimas da GainTransitionTest; remover os três parâmetros constantes substituídos. Ligar ModelTuner.VALID → GainTransitionTest.TUNING_ALLOWED, removendo TRUE constante.

Manter os quatro dados Identifier → ModelTuner e acrescentar Identifier → GainTransitionTest: EST_OUTPUT_COEFFICIENT_1/2 → MODEL_OUTPUT_COEFFICIENT_1/2; EST_INPUT_COEFFICIENT_1/2 → MODEL_INPUT_COEFFICIENT_1/2. Remover os quatro parâmetros constantes da transição. Assim ambas leem o mesmo modelo, que deve estar congelado durante este ensaio.

Não conectar Identifier.CNF ao ModelTuner.REQ nesta etapa. ModelTuner.ERR não deve disparar aplicação nem cálculo do PID. Preservar todas as ligações da cadeia anteriormente validada. Não ligar PID.CNF a READ_STATE.

Após salvar e fazer deployment, repetir o ensaio do observador com 400 amostras e mudança programada do processo. Aguardar SAMPLE_COUNT=400 e relógio parado. Confirmar estimativas próximas de 1.2,-0.36,0.4,0.06 e ausência de erros. Não reiniciar a identificação durante a sequência seguinte.

ModelTuner: SAMPLE_TIME_S=0.1, DESIRED_POLE=0.7. PID de teste: KP1/KI0.5/KD0.1, Ts0.1, limites0/10, SP1/PV0. Transição: SETPOINT1/PROCESS_VARIABLE0, limites de atualização0.02 e escalas0.01/0.01/0.001. Inicializar PID de teste uma vez, executar REQ uma vez (MV2.025). Depois disparar apenas ModelTuner.REQ uma vez.

Sequência: ModelTuner.CNF → PID.READ_STATE → PID.STATE_CNF → Transition.REQ → Transition.CNF → PID.SET_GAINS → PID.GAINS_CNF → PID.REQ.

Referência offline usando os quatro coeficientes exatos acima e os algoritmos FBT atuais:
- Ganhos alvo: 0.1551602890291068,0.582261347445557,0.004572867901485869.
- Ganhos aplicados: 0.9822935114491606,0.5017240662196708,0.098.
- Fração:0.020958399943690035; efeito:-0.017447878617888657.
- Segundo ciclo PID: P0.9822935114491606, I0.07525860993295064, D0; MV1.0575521213821113.

Os valores podem diferir nas últimas casas devido aos coeficientes estimados. Esperado ModelTuner.REQ/CNF1, transiçãoREQ/CNF1, PIDREAD_STATE/STATE_CNF1, PIDSET_GAINS/GAINS_CNF1, PIDREQ/CNF2. ACTIVE_* e INTEGRAL_MEMORY ainda mostram o estado anterior à atualização, publicado pelo único READ_STATE.

Limite: identificação foi realizada em malha fechada com PID fixo; esta sequência aplica sua sintonia a um PID separado, com SP/PV constantes e modelo congelado. Ainda não é controle adaptativo automático da planta simulada. O polo desejado é escolha de projeto; não é parâmetro identificado pelo MMQE. Aprovação do cálculo pelo tuner não substitui avaliação da qualidade da identificação.
