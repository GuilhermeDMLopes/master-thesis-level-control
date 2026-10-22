# Ganhos iniciais e atualização separados

Mudança em PID_FLAG_STATE_ACCESS: KP/KI/KD continuam associados a INIT. SET_GAINS passa a capturar UPDATED_PROPORTIONAL_GAIN, UPDATED_INTEGRAL_GAIN e UPDATED_DERIVATIVE_GAIN. A aritmética do PID, memória e confirmação GAINS_CNF são preservadas. O algoritmo de captura só muda os nomes das entradas utilizadas.

Motivo: as saídas da transição iniciam em zero. Uma ligação direta às entradas usadas por INIT poderia substituir os ganhos iniciais. As novas entradas permitem a conexão permanente sem acrescentar blocos ou alterar PID_FLAG.

Migração: copiar o FBT do protótipo para a biblioteca observer local após backup. Atualizar o tipo no IDE, exportar novamente PID_FLAG_STATE_ACCESS (FORTE 1.x NG) e recompilar usando build_forte_pid_identification_observer.ps1 -IncludeTuner -IncludeStateAccess -IncludeTransition. Parar runtime anterior e executar o novo antes de deployment. Não usar runtime compilado com a interface antiga.

## Ligações adicionais na aplicação
Preservar STATE_CNF → GainTransitionTest.REQ e as nove ligações de estado já validadas.

| Origem em GainTransitionTest | Destino em PIDStateTest |
|---|---|
| NEXT_PROPORTIONAL_GAIN | UPDATED_PROPORTIONAL_GAIN |
| NEXT_INTEGRAL_GAIN | UPDATED_INTEGRAL_GAIN |
| NEXT_DERIVATIVE_GAIN | UPDATED_DERIVATIVE_GAIN |
| CNF | SET_GAINS |

Conectar PIDStateTest.GAINS_CNF → PIDStateTest.REQ.
Não conectar PID.CNF a READ_STATE: a cadeia deve terminar após um cálculo. READ_STATE passa a iniciar uma operação de controle neste arranjo de teste; não utilizá-lo como simples consulta após fechar as ligações.

## Ensaio nativo pendente
Manter os parâmetros do ensaio anterior: ganhos iniciais 1/0.5/0.1, Ts0.1, limites0/10, SP1/PV0, alvos0.9/0.45/0.09, limites de atualização0.02, modelo1.2/-0.36/0.1/0.06.
Após novo deployment: INIT uma vez, REQ uma vez (MV2.025), READ_STATE uma vez. A cadeia deve executar transição → SET_GAINS → REQ automaticamente.
Esperado PID REQ2/CNF2, SET_GAINS1/GAINS_CNF1, READ_STATE1/STATE_CNF1; transição REQ1/CNF1, nenhum erro. MV=1.055, P≈0.98139535, I≈0.07360465, D=0.
A saída INTEGRAL_MEMORY permanece0.05: é o retrato publicado antes do segundo cálculo; a memória interna já é0.15. Não disparar outro READ_STATE para tentar atualizar apenas a visualização, pois iniciará outra passagem pela cadeia. Mesma observação para as saídas ACTIVE_*.

## Validação offline
6 testes de estado e 10 testes de transição/coordenador passaram. Novo teste verifica associação WITH separada, inicialização com entradas de atualização zeradas, transferência dos nove dados de estado, captura dos ganhos preservando memória e saída1.055 no próximo REQ, além de reinicialização com os ganhos originais. Execução ST/ECC parcial em Python; encadeamento nativo desta nova interface ainda não validado.

Este estágio usa ganhos alvo e modelo fixos. MMQE não comanda a adaptação automaticamente. O .sys local não é substituído.
