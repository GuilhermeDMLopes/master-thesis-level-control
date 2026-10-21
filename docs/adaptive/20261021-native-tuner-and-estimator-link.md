# Sintonia nativa e conexão ao identificador — 21/10/2026

## Teste isolado confirmado
Evidências examinadas na conversa: Texto colado(20261021-185005).txt e image(20261021-185524).png. Anexos não incorporados neste commit.
Build: runs/20261021-154257-811, script com -IncludeTuner.
SHA256 do executável: 4BF5A4CE3BEE5127BAC31B15EC2D96EFE7639BD80701B680A43634EC85B27F89.
A captura mostra ModelTuner com REQ=1, CNF=1, ERR=0, VALID=TRUE.
Entradas manuais: a1=1.2, a2=-0.36, b1=0.4, b2=0.06, Ts=0.1, polo desejado=0.7.
Saídas aproximadas: KP=0.1551602890, KI=0.5822613474, KD=0.0045728679, quarto polo=0.0079991858; resíduo=5.55e-17.
Conclusão: cálculo nativo confirmado para um modelo fornecido manualmente. Não houve atualização de ganhos nem validação de estabilidade adaptativa.

## Próximo ensaio mínimo: dados estimados, disparo manual ao final
Editar Observer_Test com monitoramento desativado. Preservar a rede de eventos validada.
Remover os parâmetros constantes nas quatro entradas de modelo de ModelTuner e conectar:

| Identifier | ModelTuner |
|---|---|
| EST_OUTPUT_COEFFICIENT_1 | MODEL_OUTPUT_COEFFICIENT_1 |
| EST_OUTPUT_COEFFICIENT_2 | MODEL_OUTPUT_COEFFICIENT_2 |
| EST_INPUT_COEFFICIENT_1 | MODEL_INPUT_COEFFICIENT_1 |
| EST_INPUT_COEFFICIENT_2 | MODEL_INPUT_COEFFICIENT_2 |

Manter SAMPLE_TIME_S=0.1 e DESIRED_POLE=0.7 como parâmetros.
Manter ModelTuner mapeado para LocalObserver.EMB_RES.
Não conectar saídas do tuner a FixedPID nem alterar SET_GAINS.

Salvar, reiniciar o runtime validado e realizar deployment completo, para iniciar uma execução limpa.
Monitorar a rede do recurso. Disparar SimulatedProcess.INIT uma vez, aguardar SAMPLE_COUNT=400 e DONE=1.
Confirmar Identifier.ESTIMATION_VALID=TRUE, ERR=0, coeficientes finais próximos de [1.2,-0.36,0.4,0.06].
Só então disparar ModelTuner.REQ uma vez. REQ possui associação WITH com as quatro entradas do modelo, Ts e polo desejado; o bloco executa ao receber esse evento. O processo já terminou, evitando competição com novas estimativas neste ensaio.

Esperado: CNF=1, ERR=0, VALID=TRUE e ganhos próximos dos valores acima; FixedPID.SET_GAINS permanece zero.
Não interpretar valores de entrada exibidos antes de REQ como confirmação da amostragem do bloco. Conferir entradas e saídas após REQ.
Não disparar REQ se o identificador tiver falhado ou o ensaio não tiver concluído.

Este teste verifica a ligação de dados entre identificador e sintonia. O disparo permanece manual e não constitui adaptação automática. Não exige exportação ou recompilação: mudam apenas conexões/parâmetros da aplicação. O .sys local do usuário não foi sobrescrito por este commit.
