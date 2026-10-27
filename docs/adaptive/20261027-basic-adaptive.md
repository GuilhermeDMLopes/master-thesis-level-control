# PID básico: identificação, sintonia e controle

## Decisão

A pedido do Guilherme, a aplicação principal passa a mostrar **Process, Identifier e Controller**, além do relógio. O projeto `PID_Basic_Adaptive` é a versão simplificada para continuar o desenvolvimento. `PID_Identification_Observer` fica preservado como evidência dos ensaios anteriores; não precisa ser mantido em evolução paralela.

O composto `PROCESS_IDENTIFIER` contém somente MMQE (`RLS_PARAMETER_ESTIMATOR`), sintonia (`PID_MODEL_TUNER`) e seleção de uma amostra (`TUNING_TRIGGER`). A seleção é necessária para distinguir o ensaio fixo do ensaio com uma atualização. Foram retirados da aplicação os blocos de transição de ganhos, leitura de estado e a sequência anterior de confirmações.

O `PID_CONTROLLER` mantém exatamente a equação e a flag de `PID_FLAG`. As portas têm nomes descritivos. Os ganhos iniciais e os ganhos atualizados usam entradas separadas: assim, as saídas inicialmente zeradas do sintonizador não substituem os parâmetros de inicialização. O evento `SET_GAINS` armazena o trio de ganhos, sem executar o PID ou reiniciar sua memória.

## Ordem dos eventos

- Inicialização: `Process.INIT → Identifier.INIT → Controller.INIT → SamplingClock.START` (cada etapa só segue pela confirmação anterior).
- Amostra normal: relógio → processo → MMQE → `CONTROL_READY` → cálculo PID → aplicação do comando.
- Amostra de sintonia: relógio → processo → MMQE → sintonia → `GAINS_READY` → `Controller.SET_GAINS` → `GAINS_CNF` → cálculo PID → aplicação do comando.

O mesmo relógio de 100 ms dirige o ensaio. Não há segundo temporizador. O processo sintético já rejeita uma nova requisição enquanto espera a aplicação do comando anterior. Eventos `ERR` param o relógio; isso não constitui uma função de segurança para uma planta física.

A aplicação usa basic FBs com ECC e ST e um composite FB com conexões de eventos/dados e associações WITH. A verificação realizada é estrutural e por replay do subconjunto ST/ECC, não certificação de conformidade integral IEC 61499 nem validação temporal nativa.

## Dois modos, mesma aplicação

| Parâmetro em Identifier | Ensaio fixo | Uma atualização |
|---|---:|---:|
| ENABLE_UPDATE | FALSE | TRUE |
| UPDATE_AT_SAMPLE | 275 | 275 |
| FORGETTING_FACTOR | 0.8 | 0.8 |
| INITIAL_COVARIANCE | 10000.0 | 10000.0 |
| SAMPLE_TIME_S | 0.1 | 0.1 |
| DESIRED_POLE | 0.7 | 0.7 |

Os parâmetros do modo são lidos em INIT. Execute um novo ensaio desde o início após alterar o modo. O modelo é identificado a cada amostra; os ganhos são recalculados e aplicados somente na amostra 275, uma vez por inicialização. Portanto, esta etapa é uma ressintonia única baseada no modelo estimado, ainda não adaptação contínua.

## Resultado offline

400 amostras em ambos os modos; seis testes aprovados. O modo fixo coincide com o CSV nativo anterior até 12 casas decimais. Não houve execução nativa deste novo projeto.

| Medida | Fixo | Troca direta |
|---|---:|---:|
| IAE (s) | 1.5114068161 | 1.9530440587 |
| Comando na amostra 275 | 0.2782648799 | 0.0989036489 |
| Saída final | 0.8000000008 | 0.8000002026 |
| Atualizações de ganhos | 0 | 1 |

A troca direta aumenta o IAE em aproximadamente 29,2%. Preservar a memória integral não impede salto quando KI muda. Não há compensação, limitação de passo ou alegação de troca sem perturbação. Não foi demonstrada superioridade do controle adaptativo. Um erro de sintonia interrompe o ensaio antes da aplicação dos ganhos; isso é coberto por teste.

Resultados reproduzíveis em `basic-adaptive-summary.json`. Testes: baseline nativo, atualização única e ordem de eventos, erro de sintonia, estrutura/mapeamento, preservação da equação com flag. O executor é serial e não substitui ensaio no FORTE.

## Referências e limites

- Estrutura com identificador e PID e flag: requisitos do orientador registrados na conversa e nos documentos `../pid/20261018-whiteboard-flag-contract.md` e `20261020-pid-state-access.md`.
- MMQE e processo: implementação existente, com rastreabilidade em `README.md` e `4diac-design.md` (materiais de aula, páginas 29, 30 e 37 anteriormente registradas).
- Sintonia: candidato de alocação de polos documentado em `20261019-pid-tuning-candidate.md` e `20261020-pid-model-tuner.md`. Não afirmar que essa fórmula foi extraída dos dois artigos ou do quadro sem conferir os originais.
- Comparação anterior com transição limitada: `20261026-native-comparison-result.md`. Seus resultados não são validação nativa desta simplificação.

## Passos no Windows

1. Salvar tudo no IDE. Atualizar a branch sem descartar alterações locais; se Git interromper, preservar a saída e os arquivos.
2. Executar `scripts/backup_pid_projects.ps1`. O backup verifica hashes dos projetos salvos; não captura memória em execução, C++ exportado ou o executável.
3. Executar `python -m unittest discover -s tests -p test_pid_basic_adaptive.py -v` com o Python do ambiente `pid-adaptativo`.
4. Importar **Existing Projects into Workspace**, pasta `4diac/application/PID_Basic_Adaptive`. Não copiar sobre o projeto antigo. Conferir Problems e os quatro blocos de `Basic_Control`.
5. Exportar os **seis tipos** da pasta `Type Library/adaptive` para uma pasta nova. Incluir o composto `PROCESS_IDENTIFIER`: exportar somente os básicos provoca `UNSUPPORTED_TYPE` no deployment.
6. Compilar com o script existente e a opção `-BasicAdaptive -ExportDirectory <pasta>`. Não usar os antigos switches `Include...`. O build isolado não altera os fontes antigos e não inicia o runtime.
7. Executar somente o novo runtime local. Deploy do projeto; habilitar monitoramento; iniciar por `Process.INIT`, uma vez. Primeiro `ENABLE_UPDATE=FALSE`; depois repetir desde o início com TRUE. Verificar 400 cálculos e aplicações, zero ERR e exatamente um `Controller.SET_GAINS` no modo habilitado.

Exemplo de compilação após exportação:

```powershell
& .\scripts\build_forte_pid_identification_observer.ps1 `
    -BasicAdaptive `
    -ExportDirectory 'C:\Projetos\forte-pid-basic-adaptive\exports'
```

A exportação, compilação C++ e execução no 4diac/FORTE desta versão continuam pendentes. O coletor CSV anterior instrumenta outro tipo de PID; não reutilizar sua instrumentação automaticamente neste projeto.
