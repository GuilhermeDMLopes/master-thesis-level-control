# Atualização periódica dos ganhos

## Escopo acordado

O artigo terá foco na implementação e na explicação da estrutura. Não será desenvolvido um estudo comparativo de desempenho. Os ensaios e testes verificam funcionamento, equações e encadeamento de eventos. As evidências anteriores permanecem como histórico.

## Alteração mínima

A aplicação continua com Process, Identifier e Controller, mais SamplingClock. Nenhum bloco foi adicionado. Foram alterados apenas os tipos PROCESS_IDENTIFIER e TUNING_TRIGGER, seu gerador e os testes. O arquivo .sys não foi substituído, para preservar o layout e as ligações de inicialização feitos pelo usuário.

Identifier recebe uma entrada adicional: **UPDATE_INTERVAL_SAMPLES**, do tipo UINT, associada a INIT. Ela é repassada ao Trigger interno, que armazena o intervalo na inicialização.

| Configuração | Efeito |
|---|---|
| ENABLE_UPDATE=FALSE | Identificação ativa; ganhos do PID permanecem fixos |
| ENABLE_UPDATE=TRUE, intervalo=0 | Uma atualização em UPDATE_AT_SAMPLE (compatibilidade com o ensaio anterior) |
| ENABLE_UPDATE=TRUE, intervalo maior que zero | Primeira atualização em UPDATE_AT_SAMPLE; seguintes ao completar o intervalo |

UPDATE_AT_SAMPLE continua sendo a primeira amostra de sintonia. Não é um parâmetro da planta identificado pelo MMQE: é uma escolha de agendamento do ensaio. Não há temporizador separado.

## Configuração para o próximo ensaio sintético

- ENABLE_UPDATE = TRUE.
- UPDATE_AT_SAMPLE = 275.
- UPDATE_INTERVAL_SAMPLES = 25.
- Relógio = T#100ms; SAMPLE_TIME_S = 0.1.
- Demais parâmetros permanecem como no ensaio já executado.

O processo e o PID são calculados a cada 100 ms. O MMQE atualiza o modelo a cada amostra. A sintonia ocorre nas amostras **275, 300, 325, 350, 375 e 400**, ou seja, a cada 2,5 s após o início escolhido.

Na amostra de atualização: processo → MMQE → sintonia → GAINS_READY → Controller.SET_GAINS → GAINS_CNF → Controller.REQ → aplicação do comando. Nas demais, CONTROL_READY segue diretamente para Controller.REQ. Os três ganhos são armazenados juntos antes do cálculo do PID. A memória integral e o erro anterior são preservados, assim como a flag original. A troca é direta: não há compensação de salto nem mecanismo novo de transição.

Um erro dos blocos continua interrompendo o relógio. Esta é uma aplicação sintética finita de 400 amostras. O contador UINT e seu reinício não foram transformados em um mecanismo de operação contínua de planta; inicializar novamente os blocos para reiniciar o ensaio.

## Verificação realizada

Dez testes offline aprovados. Incluem ordem de eventos em cada atualização, exatamente 400 cálculos e aplicações, seis atualizações nas amostras especificadas, modo desabilitado, compatibilidade com intervalo zero, configuração armazenada em INIT, reinicialização, limites do contador e integridade das interfaces/mapeamentos. O cálculo PID e sua flag permanecem inalterados.

Resultado esperado do replay periódico: saída final aproximadamente 0.800000202640857 e comando final aproximadamente 0.278260878233759. Valores finitos, zero ERR. Essa verificação usa o subconjunto ST/ECC e a rede de eventos em execução serial Python; não é execução nativa desta alteração.

## Atualização no Windows

1. Salvar e fechar o projeto no IDE; executar backup_pid_projects.ps1 antes do git pull.
2. Atualizar a branch e executar test_pid_basic_adaptive.py. O .sys local é preservado por este commit. Não executar o gerador sobre o projeto editado no IDE.
3. Abrir o IDE e atualizar PID_Basic_Adaptive com F5. Aceitar a atualização de tipos, caso solicitada. A nova entrada deve aparecer em Identifier. Conferir também a instância mapeada em EMB_RES.
4. Informar os três parâmetros acima na aplicação; salvar e conferir Problems.
5. Exportar novamente os seis tipos da pasta adaptive para uma pasta nova, incluindo PROCESS_IDENTIFIER e TUNING_TRIGGER.
6. Compilar com build_forte_pid_identification_observer.ps1 -BasicAdaptive -ExportDirectory <nova pasta>. O executável anterior não possui esta interface e lógica periódica.
7. Após o build, encerrar o runtime anterior, iniciar o novo e fazer deployment. Inicializar uma vez, considerando as ligações locais de START. Não injetar INIT de novo se o ensaio já começou.

Contadores esperados ao terminar: Process.SAMPLE_COUNT=400; Controller.REQ/CNF=400; SET_GAINS/GAINS_CNF=6; Identifier.CONTROL_READY=394; GAINS_READY=6; zero ERR visíveis. A confirmação nativa permanece pendente até o ensaio do usuário.
