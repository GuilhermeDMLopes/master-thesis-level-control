# Transição limitada: resultado nativo e aplicação manual ao PID

## Evidência recebida
Captura image(20261021-200057).png, teste isolado GainTransitionTest no 4diac/FORTE local. Imagem consultada na conversa; não incorporada neste commit.
REQ=1, CNF=1, ERR=0, VALID=TRUE, UPDATE_APPLIED=TRUE.
Ganhos calculados: KP=0.981395348837209; KI=0.490697674418605; KD=0.0981395348837209.
STEP_FRACTION=0.186046511627907; GAIN_OUTPUT_CHANGE=-0.0199999999999998.
Confirma o cálculo do passo limitado. Ainda não confirma aplicação ao PID nem adaptação automática em malha fechada.

## Próximo ensaio: aplicação manual (pendente de execução nativa)
Usar PIDStateTest isolado, sem conexões automáticas de eventos e sem conectar as saídas de ganhos à sua inicialização.
1. Escrever KP=1.0, KI=0.5, KD=0.1, TS_S=0.1, U_MIN=0.0, U_MAX=10.0, SP=1.0, PV=0.0.
2. Disparar INIT uma vez e REQ uma vez. Esperado MV=2.025.
3. Disparar READ_STATE. Esperado INTEGRAL_MEMORY=0.05, PREVIOUS_ERROR=1.0.
4. Escrever em KP/KI/KD os três ganhos calculados acima, utilizando escrita online sem novo deployment.
5. Disparar SET_GAINS uma vez. Esperado GAINS_CNF; saída MV continua 2.025. Não disparar INIT.
6. Disparar READ_STATE. Ganhos ativos devem ser os novos; memória integral permanece 0.05 e erro anterior 1.0.
7. Manter SP=1.0, PV=0.0 e disparar REQ exatamente uma vez.
8. Esperado P_TERM=0.981395348837209, I_TERM=0.0736046511627908, D_TERM=0, RAW=MV=1.055, FLAG=TRUE, SATURATED=FALSE, VALID=TRUE.
9. Disparar READ_STATE: INTEGRAL_MEMORY=0.15 e PREVIOUS_ERROR=1.0.

As saídas de estado só são publicadas em READ_STATE; os termos P/I/D só são recalculados em REQ.
A escrita de KP/KI/KD por si só não altera os ganhos internos: SET_GAINS confirma a captura conjunta.
Registrar capturas após passo 6 e passos 8–9. Em caso de divergência, interromper a sequência para preservar a evidência.

## Interpretação
No próximo ciclo, com os ganhos antigos, a saída seria 1 + 0.5*0.15 = 1.075.
Com os novos ganhos, será 1.055: diferença de -0.02 atribuível à troca de ganhos.
A comparação não é com MV=2.025 do primeiro ciclo, que incluía contribuição derivativa de 1.0.
A memória da integral é preservada; sua contribuição muda quando KI muda.
Este ensaio ainda usa ganhos transferidos manualmente. O encadeamento automático e o MMQE comandando a atualização permanecem etapas posteriores.
