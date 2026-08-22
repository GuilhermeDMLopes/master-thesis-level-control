# Compara????o experimental PI ?? MPC V3 na planta real

## Escopo da compara????o

Esta se????o compara dois experimentos reais preservados no projeto:

- baseline PI: `data/sample/real-raw-pi-v1-monitor.csv`;
- MPC V3: `data/sample/mpc-v3-clean-evidence-20260822/clean-active-monitor.csv`.

Ambos usam refer??ncia de **450 contagens raw**. A baseline PI foi validada como
baseline funcional segura, sem alega????o de sintonia ??tima. O experimento MPC V3
foi encerrado automaticamente pela prote????o de mediana em 550 raw e, portanto,
n??o valida regula????o em regime permanente.

A compara????o ?? **descritiva**. Ela n??o ?? um ensaio A/B estatisticamente controlado:
as condi????es iniciais e o hist??rico de comissionamento dos dois experimentos s??o
diferentes.

## M??tricas principais

| M??trica | PI | MPC V3 |
|---|---:|---:|
| Classifica????o | VALIDATED_FUNCTIONAL_BASELINE | BOUNDED_SAFETY_ABORT |
| Dura????o analisada (s) | 29.89 | 27.30 |
| Mediana inicial (raw) | 625.00 | 298.00 |
| Erro inicial absoluto (raw) | 175.00 | 152.00 |
| Mediana m??xima (raw) | 736.00 | 553.00 |
| Overshoot m??ximo (raw) | 286.00 | 103.00 |
| Overshoot m??ximo (% SP) | 63.56 | 22.89 |
| MAE (raw) | 92.83 | 139.85 |
| RMSE (raw) | 123.28 | 155.57 |
| IAE (raw??s) | 2757.10 | 3812.96 |
| Primeiro 440???460 raw (s) | 12.62 | 24.39 |
| Acomoda????o permanente 440???460 (s) | n??o observado | n??o observado |
| AppliedDAC m??nimo | 11082.00 | 0.00 |
| AppliedDAC m??ximo | 11730.00 | 11850.00 |
| Varia????o total de AppliedDAC | 1252.00 | 11862.00 |
| Watchdog saud??vel em todas as amostras | sim | sim |

## Interpreta????o

A baseline PI atingiu uma faixa de mediana m??vel mais ampla e apresentou um
transiente inicial importante; ela permanece classificada apenas como baseline
funcional segura, n??o como controlador otimamente sintonizado.

O MPC V3 demonstrou integra????o funcional completa com PLC, gateway e FORTE e
levou a vari??vel de processo ?? regi??o do setpoint. Entretanto, a resposta tardia
da planta produziu overshoot suficiente para atingir o limite de seguran??a da
mediana. Assim, o experimento MPC V3 deve ser reportado como **comissionamento
limitado por seguran??a**, e n??o como valida????o de regime permanente.

A camada de seguran??a foi eficaz nos dois fluxos experimentais: os comandos
permaneceram limitados e o MPC V3 foi encerrado antes de uma excurs??o maior.

## Conclus??o para a disserta????o

Os resultados permitem concluir que:

1. a arquitetura PLC B&R ??? gateway Python ??? FORTE foi validada com PI e MPC;
2. o PI forneceu uma refer??ncia real, segura e reproduz??vel;
3. o MPC V3 incorporou explicitamente atraso de transporte e foi executado na planta real;
4. o MPC V3 alcan??ou a regi??o do setpoint, mas apresentou resposta tardia n??o prevista com precis??o suficiente;
5. a prote????o supervis??ria detectou e interrompeu a excurs??o;
6. n??o h?? evid??ncia experimental suficiente para afirmar superioridade global do MPC V3 sobre o PI em regula????o de n??vel;
7. a principal contribui????o experimental do MPC ?? demonstrar implementa????o, integra????o, tratamento expl??cito do atraso e identifica????o das limita????es do modelo na planta real.

## Figuras

- `docs/figures/pi-vs-mpc-v3/pi-vs-mpc-v3-level-response.png`
- `docs/figures/pi-vs-mpc-v3/pi-vs-mpc-v3-applied-dac.png`
- `docs/figures/pi-vs-mpc-v3/pi-vs-mpc-v3-absolute-error.png`

Os dados completos da compara????o est??o em:

- `results/pi-vs-mpc-v3-20260822/metrics.csv`
- `results/pi-vs-mpc-v3-20260822/comparison.json`
