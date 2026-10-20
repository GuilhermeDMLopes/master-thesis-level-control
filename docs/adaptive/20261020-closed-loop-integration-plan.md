# Próxima integração: MMQE, sintonia e PID
Data: 2026-10-20. Plano de implementação; não é resultado de teste.
Base inspecionada: 095e07bad2a646457aa842d16fd4e324b406eed6.

## Objetivo
Montar uma aplicação exclusivamente simulada, preservando o PID do quadro e separando identificação, sintonia, autorização e execução. A aplicação completa ainda não existe. Os protótipos estão em 4diac/prototypes/PID_Adaptation.

## Ordem de uma amostra
1. Capturar y(k), referência e histórico dos comandos efetivamente aplicados.
2. Executar MMQE com [y(k-1), y(k-2), u(k-1), u(k-2)] e saída y(k). Não usar u(k), que ainda será calculado.
3. Após a confirmação do estimador, atualizar os históricos para a próxima amostra.
4. Se a sintonia não estiver vencida, seguir com o alvo anterior ainda autorizado. Se estiver vencida, calcular um novo alvo e avaliar sua admissibilidade antes de continuar.
5. Entregar a mesma referência e medição capturadas ao PID_SAMPLE_COORDINATOR.
6. Coordenador solicita estado do PID, cálculo da transição, confirmação de ganhos, cálculo do PID e aplicação da saída, nesta ordem.
7. Somente a confirmação da aplicação encerra a amostra. Registrar o comando aplicado para o próximo regressor.

O fluxo deve ter um único caminho de continuação após a decisão de sintonia; não disparar o PID por dois caminhos concorrentes. O estimador utiliza os dados capturados, nunca variáveis sendo atualizadas durante o cálculo.

## Frequências propostas para reprodução
PID e identificação: uma execução por amostra de 100 ms.
Sintonia: a cada 10 amostras concluídas, após aquecimento de 50 amostras.
São escolhas da simulação anterior, não parâmetros determinados para a planta.
A sintonia tem frequência menor, mas permanece encadeada por confirmações. Não é necessário criar um segundo relógio independente.
Se uma execução ultrapassar o período, parar o ensaio e registrar a falha; não enfileirar amostras antigas para simular pontualidade.

## Responsabilidades e situação
| Função | Situação |
|---|---|
| PID do quadro com leitura de estado | PID_FLAG_STATE_ACCESS: protótipo com teste offline |
| Limitação da alteração de ganhos | PID_GAIN_TRANSITION: protótipo com teste offline |
| Sequência de eventos do PID | PID_SAMPLE_COORDINATOR: protótipo com teste offline |
| MMQE | RLS_PARAMETER_ESTIMATOR existente; integração em malha fechada nativa pendente |
| Cálculo de KP/KI/KD a partir do modelo | Implementado na simulação Python; bloco nativo pendente |
| Autorização, contador e retenção coerente do alvo/modelo | Integração nativa pendente |
| Processo controlável, histórico do comando aplicado e aplicação completa | Integração nativa pendente |

O PROCESS_IDENTIFICATION existente é um experimento de identificação com reprodução de entrada. Não tratá-lo como controlador adaptativo completo.

## Contrato da autorização
Manter adaptação desabilitada inicialmente. Um alvo só pode ser usado junto ao modelo que o originou.
Rejeição da qualidade ou do cálculo invalida a autorização do alvo anterior, conforme a simulação documentada.
Ganhos ativos permanecem no PID; rejeitar adaptação não deve zerar o controlador.
Não confundir VALID do bloco de transição com qualidade da identificação.
A qualidade deve considerar excitação/condicionamento dos regressores; erro de predição pequeno isoladamente não comprova identificação.
A regra exata do gate e seus limites precisam ser portados da simulação, sem criar limiares novos silenciosamente.

## Ensaios em ordem
1. Adaptação desabilitada: comparar a trajetória ao PID fixo com mesmas condições iniciais e entradas.
2. Alvo conhecido: confirmar READ_STATE -> transição -> SET_GAINS -> GAINS_CNF -> REQ; integral atualizada uma única vez.
3. MMQE em malha fechada, ainda sem aplicar ganhos: observar estimativas e condicionamento.
4. Sintonia em observação: registrar candidatos, aceitação e motivo da rejeição.
5. Habilitar atualização limitada e comparar ao PID fixo.
6. Injetar falha/atraso: verificar interrupção do ensaio e ausência de aplicação após erro.

Registrar por amostra: índice, referência, medição, comando anterior aplicado, comando novo aplicado, quatro coeficientes, ganhos ativos/alvo, autorização, fração de transição, efeito calculado na saída, flag e eventos de erro.
Registrar versão do código, parâmetros e cenário junto ao CSV.
O limite de efeito da troca de ganhos compara comandos calculados para o MESMO estado/amostra. Não é um limite para toda variação entre dois comandos consecutivos.

## Evidências e limites
Os testes anteriores são replay limitado de ST/ECC, não prova de comportamento de filas/eventos no FORTE.
Nesta sessão não foram executados novos testes: ambiente local indisponível.
A simulação anterior em malha fechada não demonstrou desempenho superior ao PID fixo.
A verificação de polos com ganhos congelados não demonstra estabilidade do sistema adaptativo.
Referências: 20261020-transition-event-chain.md; 20261020-gain-transition-and-closed-loop.md; 20261019-pid-tuning-candidate.md.
