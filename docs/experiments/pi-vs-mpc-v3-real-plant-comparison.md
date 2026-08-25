# Comparação experimental PI × MPC V3 na planta real

## Escopo da comparação

Esta seção compara dois experimentos reais preservados no projeto:

- baseline PI: `data/sample/real-raw-pi-v1-monitor.csv`;
- MPC V3: `data/sample/mpc-v3-clean-evidence-20260822/clean-active-monitor.csv`.

Ambos usam referência de **450 contagens raw**. A baseline PI foi validada como
baseline funcional segura, sem alegação de sintonia ótima. O experimento MPC V3
foi encerrado automaticamente pela proteção de mediana em 550 raw e, portanto,
não valida regulação em regime permanente.

A comparação é **descritiva**. Ela não é um ensaio A/B estatisticamente controlado:
as condições iniciais e o histórico de comissionamento dos dois experimentos são
diferentes.

## Métricas principais

| Métrica | PI | MPC V3 |
|---|---:|---:|
| Classificação | VALIDATED_FUNCTIONAL_BASELINE | BOUNDED_SAFETY_ABORT |
| Duração analisada (s) | 29.89 | 27.30 |
| Mediana inicial (raw) | 625.00 | 298.00 |
| Erro inicial absoluto (raw) | 175.00 | 152.00 |
| Mediana máxima (raw) | 736.00 | 553.00 |
| Overshoot máximo (raw) | 286.00 | 103.00 |
| Overshoot máximo (% SP) | 63.56 | 22.89 |
| MAE (raw) | 92.83 | 139.85 |
| RMSE (raw) | 123.28 | 155.57 |
| IAE (raw·s) | 2757.10 | 3812.96 |
| Primeiro 440–460 raw (s) | 12.62 | 24.39 |
| Acomodação permanente 440–460 (s) | não observado | não observado |
| AppliedDAC mínimo | 11082.00 | 0.00 |
| AppliedDAC máximo | 11730.00 | 11850.00 |
| Variação total de AppliedDAC | 1252.00 | 11862.00 |
| Watchdog saudável em todas as amostras | sim | sim |

## Interpretação

A baseline PI atingiu uma faixa de mediana móvel mais ampla e apresentou um
transiente inicial importante; ela permanece classificada apenas como baseline
funcional segura, não como controlador otimamente sintonizado.

O MPC V3 demonstrou integração funcional completa com PLC, gateway e FORTE e
levou a variável de processo à região do setpoint. Entretanto, a resposta tardia
da planta produziu overshoot suficiente para atingir o limite de segurança da
mediana. Assim, o experimento MPC V3 deve ser reportado como **comissionamento
limitado por segurança**, e não como validação de regime permanente.

A camada de segurança foi eficaz nos dois fluxos experimentais: os comandos
permaneceram limitados e o MPC V3 foi encerrado antes de uma excursão maior.

## Conclusão para a dissertação

Os resultados permitem concluir que:

1. a arquitetura PLC B&R ↔ gateway Python ↔ FORTE foi validada com PI e MPC;
2. o PI forneceu uma referência real, segura e reproduzível;
3. o MPC V3 incorporou explicitamente atraso de transporte e foi executado na planta real;
4. o MPC V3 alcançou a região do setpoint, mas apresentou resposta tardia não prevista com precisão suficiente;
5. a proteção supervisória detectou e interrompeu a excursão;
6. não há evidência experimental suficiente para afirmar superioridade global do MPC V3 sobre o PI em regulação de nível;
7. a principal contribuição experimental do MPC é demonstrar implementação, integração, tratamento explícito do atraso e identificação das limitações do modelo na planta real.

## Figuras

- `docs/figures/pi-vs-mpc-v3/pi-vs-mpc-v3-level-response.png`
- `docs/figures/pi-vs-mpc-v3/pi-vs-mpc-v3-applied-dac.png`
- `docs/figures/pi-vs-mpc-v3/pi-vs-mpc-v3-absolute-error.png`

Os dados completos da comparação estão em:

- `results/pi-vs-mpc-v3-20260822/metrics.csv`
- `results/pi-vs-mpc-v3-20260822/comparison.json`
