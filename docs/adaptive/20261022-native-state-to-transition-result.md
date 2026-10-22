# Estado do PID para transição: resultado nativo

Capturas recebidas em 22/10/2026, FORTE local. Imagens consultadas na conversa, não incorporadas neste commit.

- image(20261022-122636).png: ligação STATE_CNF → REQ e nove ligações de dados entre PIDStateTest e GainTransitionTest.
- image(20261022-122731).png: após INIT, INITO=1; READ_STATE=0 e transição REQ=0. Saídas de estado ainda não publicadas, portanto zeradas.
- image(20261022-122748).png: primeiro REQ do PID, MV=2.025; transição ainda REQ=0.
- image(20261022-122807).png: READ_STATE=1, STATE_CNF=1; transição REQ=1, CNF=1, ERR=0. Recebe ganhos ativos 1/0.5/0.1, Ts=0.1, limites0/10, memória0.05, erro anterior1 e integração habilitada.

Transição calculada: KP=0.981395348837209, KI=0.490697674418605, KD=0.0981395348837209; fração=0.186046511627907; efeito≈-0.02; VALID e UPDATE_APPLIED verdadeiros.

Resultado compatível com o encadeamento automático proposto: a publicação do estado dispara o cálculo da transição. PID continua MV=2.025, SET_GAINS=0, GAINS_CNF=0: ganhos ainda não retornam automaticamente ao controlador.

Escopo: teste de dois blocos com referência, medição, modelo e ganhos alvo fixos. Não constitui validação da adaptação automática pelo MMQE. Próxima etapa: resolver a separação entre ganhos de inicialização e ganhos recebidos antes de conectar o retorno ao PID.
