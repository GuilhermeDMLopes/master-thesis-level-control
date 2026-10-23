# Validação nativa: sintonia com disparo único

Registro em 23/10/2026, a partir dos cinco prints enviados pelo usuário nesta data. Evidência visual do 4diac/FORTE; não é ensaio em planta física.

## Procedimento observado
Após novo deployment, a identificação completou 400 amostras com o PID fixo. ModelTuner permaneceu com REQ=0. O PID separado foi inicializado e recebeu um REQ, produzindo MV=2.025. Um único disparo manual em ModelTuner.REQ acionou a cadeia de sintonia, leitura do estado, transição, atualização dos ganhos e novo cálculo do PID.

## Resultado
- Identifier: REQ/CNF=400/400, ERR=0; coeficientes aproximadamente [1.2, -0.36, 0.4, 0.06].
- ModelTuner: REQ/CNF=1/1, ERR=0, VALID=TRUE.
- GainTransitionTest: REQ/CNF=1/1, ERR=0, VALID=TRUE, UPDATE_APPLIED=TRUE.
- PID_FLAG_STATE_ACCESS: REQ/CNF=2/2, SET_GAINS/GAINS_CNF=1/1, READ_STATE/STATE_CNF=1/1, ERR=0 e STATE_ERR=0.
- Ganhos candidatos: KP=0.15516028902911, KI=0.582261347445562, KD=0.0045728679014891.
- Ganhos transferidos: KP=0.98229351144916, KI=0.501724066219671, KD=0.098.
- Saída final: MV=1.05755212138211; P=0.98229351144916, I=0.0752586099329507, D=0.
- FLAG=TRUE, SATURATED=FALSE.
- Efeito previsto da atualização dos ganhos: aproximadamente -0.01744788, dentro do limite 0.02. A comparação correta é com a saída 1.075 do próximo cálculo com ganhos antigos, não com 2.025 do primeiro cálculo, que contém derivada inicial.

Os valores coincidem com a previsão offline do ensaio. As saídas ACTIVE_* e INTEGRAL_MEMORY continuam mostrando o snapshot anterior à atualização (ganhos 1, 0.5, 0.1 e memória 0.05). Não representam uma nova leitura automática do estado após SET_GAINS.

## Escopo e próximo passo
A cadeia de atualização única está funcional no runtime nativo. O PID separado ainda usa SP=1 e PV=0 e não atua no processo; FixedPID continua fechando a malha. Portanto, este resultado não valida controle adaptativo em malha fechada nem desempenho superior.

Preservar a configuração local validada antes de editar. Próximo ensaio: integrar o PID com acesso ao estado à malha simulada, inicialmente com ganhos fixos e sintonia desativada, verificando reprodução da referência. Depois inserir uma atualização controlada entre amostras, com uma única execução do PID por amostra. Não ligar diretamente o evento periódico ao sintonizador nesta etapa.

## Evidências
Prints recebidos: Imagem do ChatGPT 23 de out. de 2026, 14_56_33.png, 14_56_35.png, 14_56_37.png, 14_56_39.png e 14_56_41.png. O último mostra o resultado final; os anteriores mostram a configuração e os estados intermediários. Binários não incorporados neste commit.
