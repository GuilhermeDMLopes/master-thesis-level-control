# MMQE e sintonia em observação

20/10/2026. Integração offline dos algoritmos ST/ECC reais de PID_FLAG, RLS_PARAMETER_ESTIMATOR e PID_MODEL_TUNER. Orquestração sequencial e processo sintético em Python; ainda não é uma aplicação .sys nem validação nativa de eventos/filas/tempos.

## O que executamos
A cada amostra: processo usa comandos anteriores -> MMQE recebe saída e históricos -> avaliação de qualidade e eventual REQ de sintonia -> PID fixo calcula -> comando aplicado fica disponível para a próxima amostra.
Não existe chamada SET_GAINS no ensaio. Os candidatos são apenas registrados.

400 amostras, Ts=0.1 s, lambda=0.8, P0=10000, estimativa inicial zero. Sintonia a cada dez amostras a partir de k=50. Janela de 50 regressores normalizados por norma de coluna, cond<=1e6 e flag anterior verdadeira para solicitar sintonia. O gate usa NumPy, não um bloco nativo.
Processo ARX [1.2,-0.36,0.1,0.06], b1 muda para 0.4 em k=151. Referência constante 1 ou alternada 1/0.8 a cada 50 amostras. Sem ruído. Ganhos fixos calculados do modelo nominal conhecido: não é demonstração de partida com processo desconhecido.

## Resultados
| Cenário | Resultado do identificador | Candidatos | Rejeição qualidade | Rejeição sintonia |
|---|---|---:|---:|---:|
| Referência constante | ERR em k=150, DEN=-0.575 | 1 | 9 | 0 |
| Referência variável | 400 amostras sem ERR; modelo final aproximadamente [1.2,-0.36,0.4,0.06] | 32 | 0 | 4 |

Após ERR, o ensaio desabilita permanentemente identificação/sintonia até reiniciar a execução. O PID fixo continua somente porque este é um observador em simulação, sem ligação de atualização de ganhos. Estimativas mantidas no CSV após falha são antigas: estimation_valid=False. Nenhum ganho candidato é preenchido após rejeição/falha.

A falha de denominador no ST sob referência constante evidencia uma limitação numérica da implementação atual neste cenário; não foi corrigida ou ocultada. Falta de excitação e crescimento/perda de propriedades da covariância são hipóteses a investigar, não causa comprovada nesta etapa. Não extrapolar os resultados da implementação NumPy para o ST: operações arredondadas em ordens diferentes podem divergir em problemas mal condicionados.

Nos dois cenários a trajetória (medição e comando) foi exatamente igual à obtida sem executar o observador. IAE: constante 1.0142035222; variável 1.5114068161. Isso confirma ausência de interferência do observador; não demonstra benefício de adaptação.

## Reproduzir
Na raiz do repositório, com Python e NumPy disponíveis:

```powershell
py -m unittest discover -s tests -p test_pid_observer.py -v
py scripts/verify_pid_observer.py --output "$env:TEMP\pid-observer"
```

São criados constant_reference.csv, changing_reference.csv e summary.json. Os CSVs incluem histórico aplicado, saída, estimativa, erro de predição, validade, denominador, candidatos, status e ganhos ativos. O condicionamento só é calculado quando a sintonia está vencida. None no condicionamento significa não calculado ou não finito; o status distingue a decisão.

Quatro testes novos verificam isolamento do controle, alinhamento dos comandos anteriores/calendário, bloqueio após falha e recuperação no cenário excitado. Total de 23 testes passou nos conjuntos de estado/transição/sintonia/observação. Não houve alteração dos FBTs nesta etapa.

## Próximo passo necessário
Investigar e tratar a robustez do MMQE em baixa excitação, com preservação de estados válidos e bloqueio explícito da adaptação. Depois portar o gate/calendário e montar a aplicação .sys. Ainda não habilitar ganhos adaptativos nem conectar à planta.

Fontes matemáticas e limites de proveniência permanecem nos documentos de sintonia e referências existentes; este ensaio não introduz uma nova regra de controle.
