# Diagnóstico: sintonia repetida durante identificação

Captura image(20261022-131816).png consultada na conversa. Não incorporada como imagem neste commit.

Processo e identificador chegaram a400 amostras, ERR0, coeficientes≈1.2/-0.36/0.4/0.06; relógioSTOP1. Porém ModelTuner.REQ401, CNF350 e ERR51; transiçãoREQ/CNF350; PID separadoREQ/CNF351 e SET_GAINS350. Isso não corresponde ao ensaio de uma solicitação manual após modelo congelado. Contagens indicam disparos repetidos durante a identificação; origem exata deve ser conferida na ligação de entrada ModelTuner.REQ.

PID separado continua SP1/PV0, erro1 constante. Após centenas de execuções, integral acumulada≈8.75, RAW≈10.0518, MV10, SATURATED=TRUE e FLAG=FALSE. TransiçãoVALID=TRUE, UPDATE_APPLIED=FALSE, fração0: mantém ganhos ao receber integração desabilitada. Não interpretar saturação desse PID separado como falha da malha FixedPID, que finalizou PV≈0.8.

Correção do ensaio: na aplicação, remover todas as conexões de eventos que chegam a ModelTuner.REQ, mantendo dados do Identifier e ModelTuner.CNF→PID.READ_STATE. Salvar e fazer novo deployment para contadores limpos. Repetir identificação até400 e conferir ModelTuner.REQ=0 antes de continuar. Inicializar PID separado, REQ uma vez (MV2.025), disparar ModelTuner.REQ manualmente uma vez. Esperado tunerREQ/CNF1, ERR0; transiçãoREQ/CNF1; PIDSET_GAINS1 e REQ/CNF2; MV≈1.05755212.

As51 rejeições não devem ser atribuídas individualmente sem histórico de amostras. Modelos intermediários não admissíveis são uma hipótese compatível com execução da sintonia antes da identificação concluir. Este resultado não valida a integração pretendida nem controle adaptativo em malha fechada.
