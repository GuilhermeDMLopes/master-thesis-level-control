# Aplicação manual dos ganhos: resultado nativo

Ensaio no FORTE local, observado em quatro capturas enviadas pelo usuário em 22/10/2026. Capturas consultadas na conversa; arquivos de imagem não incorporados neste commit.

| Captura | Evidência |
|---|---|
| image(20261022-120841).png | Configuração inicial do PIDStateTest isolado; sem valores monitorados. |
| image(20261022-120954).png | INIT=1, REQ=1, READ_STATE=1; MV=2.025; memória integral=0.05; erro anterior=1; ganhos ativos 1, 0.5, 0.1. |
| image(20261022-121121).png | SET_GAINS=1, GAINS_CNF=1, READ_STATE=2; ganhos ativos 0.981395348837209, 0.490697674418605, 0.0981395348837209; memória=0.05 e MV=2.025 preservados; REQ continua 1. |
| image(20261022-121203).png | REQ=2, CNF=2, READ_STATE=3; MV=RAW=1.055; P_TERM≈0.98139535; I_TERM≈0.07360465; D_TERM=0; memória=0.15; erro anterior=1. |

ERR=0 e STATE_ERR=0 nas capturas monitoradas. VALID e FLAG verdadeiros, SATURATED falso.

Conclusão: neste ensaio isolado, SET_GAINS captura os três ganhos sem zerar a memória nem recalcular a saída. O próximo REQ utiliza os novos ganhos. READ_STATE publica o estado preservado e posteriormente atualizado.

Referência matemática: o segundo ciclo com os ganhos antigos produziria 1.075; com os novos produziu 1.055. A diferença atribuível aos ganhos é -0.02. A queda desde 2.025 inclui o desaparecimento natural do termo derivativo inicial e não deve ser interpretada como salto causado apenas pela sintonia.

Limite da evidência: ganhos escritos manualmente no PID; blocos isolados. Ainda não valida a cadeia automática de eventos, atualização comandada pelo MMQE, desempenho adaptativo ou planta física. Próximo passo: encadear leitura de estado, cálculo da transição, SET_GAINS e REQ, tratando explicitamente os ganhos iniciais.
