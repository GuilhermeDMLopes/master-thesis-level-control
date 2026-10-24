# Resultado nativo: PID com acesso ao estado na malha, ganhos fixos

Evidência recebida em 24/10/2026: image(20261024-153610).png (rede) e image(20261024-153747).png (monitoramento final). Imagens não incorporadas neste commit.

## Resultado observado
- PID_FLAG_STATE_ACCESS: INIT/INITO=1/1, REQ/CNF=400/400, ERR=0.
- SET_GAINS=0, READ_STATE=0, STATE_ERR=0.
- PID: MV aproximadamente 0.278260869300854, SP=0.8, PV aproximadamente 0.80000000084298; erro aproximadamente -8.43e-10.
- PID: VALID=TRUE, FLAG=TRUE, SATURATED=FALSE.
- Processo: SAMPLE_COUNT=400, DONE=1, ERR=0, APPLY=400.
- Identificador: REQ/CNF=400/400, ERR=0; coeficientes aproximadamente [1.2,-0.36,0.4,0.06].
- ModelTuner e GainTransitionTest: REQ=0.
- FixedPID aparece desconectado na rede. Seus contadores não estão destacados no monitoramento final; não atribuir a eles uma leitura numérica observada.

O novo PID assume a malha e reproduz os valores finais da referência anterior com os mesmos ganhos. Os prints não demonstram igualdade de toda a trajetória amostra a amostra. A sintonia permanece desativada, portanto este ensaio ainda não valida adaptação em malha fechada.

## Saídas de leitura do estado
ACTIVE_* e INTEGRAL_MEMORY são atualizadas por READ_STATE. Como READ_STATE=0, suas saídas zeradas e INTEGRATION_ENABLED=FALSE não descrevem os ganhos/memória efetivamente usados no cálculo corrente. FLAG=TRUE é a saída de controle pertinente neste ensaio.

## Próxima integração
Preservar o .sys local validado e o runtime. Antes de habilitar adaptação, revisar a sequência entre amostras para manter um cálculo e uma aplicação do comando por amostra, incluindo caminho de continuação quando a sintonia rejeita o modelo. Substituir as constantes de ensaio SETPOINT=1/PROCESS_VARIABLE=0 na transição pelos sinais coerentes do processo. Não basta religar o sintonizador ao evento periódico nem manter simultaneamente dois caminhos de disparo do PID. Próximo ensaio deve introduzir uma atualização controlada no processo simulado; pendente de preparação e execução.
