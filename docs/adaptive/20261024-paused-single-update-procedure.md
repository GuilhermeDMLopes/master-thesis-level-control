# Ensaio mínimo: uma atualização com relógio pausado

24/10/2026. Procedimento nativo pendente. Preservar backup do projeto validado com ganhos fixos. Não é adaptação autônoma nem ensaio físico.

## Decisão
O PID_SAMPLE_COORDINATOR existente não inclui o caminho de sintonia/rejeição. Para validar uma atualização sem acrescentar blocos ou recompilar, usar pausa manual do relógio. O tempo da simulação só avança por REQ; este procedimento não se transfere diretamente para uma planta física que continua evoluindo durante a pausa.

## Rede
Preservar toda a malha validada com PID_FLAG_STATE_ACCESS.
Adicionar eventos:
ModelTuner.CNF → PID_FLAG_STATE_ACCESS.READ_STATE
PID_FLAG_STATE_ACCESS.STATE_CNF → GainTransitionTest.REQ
GainTransitionTest.CNF → PID_FLAG_STATE_ACCESS.SET_GAINS

Não conectar GAINS_CNF a REQ. O único evento periódico que calcula o PID continua Identifier.CNF → PID.REQ.
ModelTuner.REQ permanece manual e sem conexão automática.
Não conectar ERR do sintonizador a REQ do PID: se a sintonia falhar, manter ganhos e encerrar a tentativa enquanto o relógio está parado.

Dados: substituir constantes SETPOINT=1/PROCESS_VARIABLE=0 em GainTransitionTest por SimulatedProcess.REFERENCE e PROCESS_OUTPUT. Preservar quatro coeficientes do Identifier para tuner e transição, três alvos do tuner, VALID→TUNING_ALLOWED, nove dados STATE_CNF do PID e três NEXT_*→UPDATED_*.
Manter ganhos iniciais e parâmetros da referência, Ts=0.1, polo desejado=0.7, limites de transição=0.02.

## Execução
Novo deployment com contadores zerados. SimulatedProcess.INIT uma vez.
Entre aproximadamente 250 e 300 amostras, disparar SamplingClock.STOP. Esperar que SAMPLE_COUNT estabilize e verificar igualdade entre processo REQ/APPLY, Identifier.REQ/CNF e PID.REQ/CNF. Isso confirma término da amostra em curso antes de trocar os ganhos.
Anotar N, PID.MV e SimulatedProcess.COMMAND.
Disparar ModelTuner.REQ uma única vez.
Se aceito: tuner REQ/CNF=1/1, transição REQ/CNF=1/1 e UPDATE_APPLIED=TRUE, PID.READ_STATE/STATE_CNF=1/1, SET_GAINS/GAINS_CNF=1/1. PID.REQ/CNF continuam N/N, SAMPLE_COUNT e comandos não mudam.
Se ERR ou UPDATE_APPLIED=FALSE, registrar; não insistir nem alterar limites para forçar aceitação.
Retomar SamplingClock.START sem reinicializar processo/PID. Completar 400 amostras, conferir PID.REQ/CNF=400/400 e processo.APPLY=400, nenhum erro do controle. Não disparar READ_STATE para monitoramento, pois agora inicia a cadeia.

## Verificação offline
Executado replay parcial ST/ECC com orquestração Python e pausa em N=275. O PID com acesso ao estado substituiu o tipo do PID da rede de referência; nomes de instância internos ao replay mantidos.
Uma atualização aceita; efeito estimado dos ganhos=-0.004939408167616788. SET_GAINS preservou exatamente I_MEMORY, E_PREV e MV; não avançou processo nem comando.
Ao retomar: 400 cálculos e 400 aplicações, saída final=0.8000000012113837, MV=0.2782608692606103.
Esses números são exemplo em N=275, não critérios exatos para uma pausa manual em outra amostra. Não houve validação de agendamento nativo.
O limite 0.02 refere-se à avaliação da transição com os dados capturados. A próxima amostra pode ter outro SP/PV, portanto não é limite absoluto da variação total de MV nem prova geral de estabilidade.
