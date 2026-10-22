# Leitura do estado encadeada à transição

Roteiro de integração incremental, ainda pendente de validação nativa. Usa os dois blocos já exportados, sem novos tipos ou recompilação.

Na aplicação Observer_Test, conectar PIDStateTest.STATE_CNF a GainTransitionTest.REQ. Conectar as nove saídas de PIDStateTest às entradas de mesmo nome em GainTransitionTest:

- ACTIVE_PROPORTIONAL_GAIN
- ACTIVE_INTEGRAL_GAIN
- ACTIVE_DERIVATIVE_GAIN
- ACTIVE_SAMPLE_TIME_S
- ACTIVE_OUTPUT_MIN
- ACTIVE_OUTPUT_MAX
- INTEGRAL_MEMORY
- PREVIOUS_ERROR
- INTEGRATION_ENABLED

Remover parâmetros constantes dessas nove entradas conectadas. Manter SP/PV do PID em 1.0/0.0 e SETPOINT/PROCESS_VARIABLE da transição em 1.0/0.0. Para este ensaio são constantes iguais; na integração com processo deverão vir da mesma amostra.

Demais parâmetros da transição: ganhos alvo 0.9/0.45/0.09; MAX_GAIN_OUTPUT_CHANGE=0.02; MAX_RELATIVE_GAIN_STEP=0.02; escalas mínimas proporcional/integral/derivativa 0.01/0.01/0.001; modelo 1.2,-0.36,0.1,0.06; TUNING_ALLOWED=TRUE.

Salvar o projeto local, fazer deployment da rede atualizada no FORTE local e reinicializar o ensaio. PID: KP=1, KI=0.5, KD=0.1, TS_S=0.1, limites0/10, SP=1, PV=0. Disparar INIT, REQ e READ_STATE uma vez cada. READ_STATE deve produzir STATE_CNF e automaticamente REQ/CNF da transição. Não disparar REQ da transição manualmente.

Esperado: PID MV=2.025 e memória0.05; transição ganhos 0.981395348837209,0.490697674418605,0.0981395348837209; fração0.186046511627907; efeito-0.02; VALID/UPDATE_APPLIED verdadeiros; nenhum erro. PID SET_GAINS permanece0. Não ligar CNF do PID a READ_STATE: isso criaria realimentação de eventos quando a cadeia completa for conectada.

A aplicação de ganhos automática permanece pendente. INIT e SET_GAINS compartilham KP/KI/KD; conectar imediatamente saídas inicialmente zeradas da transição a essas entradas pode inicializar o PID com ganhos incorretos. A próxima integração deve definir explicitamente a origem dos ganhos iniciais, preservando a aritmética já validada.

Este roteiro não altera o .sys versionado, preservando a montagem local do usuário.
