# Leitura de estado nativa confirmada; preparação da transição — 21/10/2026

## Evidência
Capturas image(20261021-192522).png, 192544, 192602, 192624 e 192640 examinadas na conversa, não incorporadas neste commit.
Build runs/20261021-162112-247; SHA256 do executável 484E3CDF98E2126380F209B2089B7B73986542EB2AAA7B1EDA657CC441B9D7A0.
Após correção 7331214: INIT/INITO=1; REQ/CNF=1; duas leituras READ_STATE/STATE_CNF=2; ERR=STATE_ERR=0.
MV=2.025, integral armazenada=0.05, erro anterior=1; ganhos ativos [1,0.5,0.1], Ts=0.1, limites [0,10], integração habilitada. Valores preservados entre as leituras.
Conclusão limitada: inicialização, cálculo e leitura repetida funcionaram neste teste nativo isolado. Nenhuma transição de ganhos foi aplicada.

## Preparação do próximo teste
Reutilizar PID_GAIN_TRANSITION existente, sem alterar suas equações ou acrescentar coordenação automática nesta etapa.
O build aceita -IncludeTransition. Com -IncludeTuner -IncludeStateAccess -IncludeTransition, exige seis pares C++ e confere os seis objetos.
A opção não inicia runtime nem modifica a rede do projeto.

Dez testes test_pid_transition_chain.py passaram no replay offline com estado inicial definido pelo primeiro ECState, após a correção do interpretador. O bloco de transição não foi validado nativamente.

Propósito do teste seguinte: fornecer estado coerente, modelo e ganhos-alvo, disparar REQ, observar NEXT_* e GAIN_OUTPUT_CHANGE antes de ligar saídas ao PID.
O limite refere-se à diferença no comando bruto provocada exclusivamente pela troca de ganhos, para o mesmo estado/amostra. Não limita toda variação entre ciclos e não garante salto zero ou estabilidade adaptativa.
UPDATE_APPLIED indica que o bloco calculou um passo aceito; não comprova que o PID recebeu esse passo. O recebimento precisa ser confirmado por GAINS_CNF e leitura posterior.

Preservar FixedPID e PIDStateTest na rede até a montagem do ensaio. Detalhes matemáticos: 20261020-transition-event-chain.md.
