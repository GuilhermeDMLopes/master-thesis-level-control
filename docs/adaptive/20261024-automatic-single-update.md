# Uma tentativa automática de sintonia na amostra 275

## Objetivo e base

Partir do projeto realmente validado pelo usuário e retirar a pausa manual. A tentativa ocorre depois da identificação da amostra 275 e antes do cálculo do PID dessa amostra. O modelo é estimado pelo MMQE; o instante da tentativa é programado. Ainda não é adaptação periódica nem demonstração de desempenho superior.

Arquivo original preservado: [ZIP validado](archives/20261024-paused-update-validated.zip).
SHA-256: `b41b7a29188ef25ea5215e2674b60098480fde155bbf5e6936511d30448d3908`.

## Mudança mínima

Um bloco novo, `PID_SINGLE_UPDATE_SEQUENCE`, instância `SingleUpdateSequence`. Sua única função é ordenar eventos. Não identifica o processo, não calcula ganhos e não calcula o comando. Os seis tipos existentes no ZIP são usados sem alteração. O protótipo antigo PID_SAMPLE_COORDINATOR é preservado e não é usado neste ensaio.

Parâmetros capturados em INIT: ENABLE_UPDATE=TRUE, UPDATE_AT_SAMPLE=275. SAMPLE recebe SAMPLE_NUMBER (UINT) do processo. UPDATE_ATTEMPTED informa que a tentativa já começou; não significa aceitação. UPDATE_REJECTED_BY_ERROR registra ERR de sintonia/transição. A aceitação matemática continua sendo indicada por GainTransitionTest.UPDATE_APPLIED. COMPLETED_SAMPLES só avança após APPLIED ou DONE do processo.

Em amostras comuns: Identifier.CNF → sequência → PID.REQ → processo.APPLY.
Na amostra escolhida: Identifier.CNF → sequência → ModelTuner.REQ → leitura do PID → transição → SET_GAINS → PID.REQ → processo.APPLY. Cada confirmação volta à sequência antes da próxima solicitação.

A ligação direta Identifier.CNF → PID.REQ é removida. O único produtor de PID.REQ passa a ser SingleUpdateSequence.EXECUTE_PID. GAINS_CNF não é ligado diretamente a REQ.

Inicialização: processo.INITO → identificador.INIT → PID.INIT → sequência.INIT → relógio.START. O sequenciador só fica pronto para a próxima amostra após o processo confirmar a aplicação do comando. DONE também confirma a última amostra e mantém sua ligação de parada do relógio.

## Rejeições e falhas

| Situação | Comportamento |
|---|---|
| ModelTuner.ERR | Não transfere ganhos; executa PID com ganhos anteriores; não repete a tentativa |
| GainTransitionTest.ERR | Não transfere ganhos; executa PID com ganhos anteriores; não repete a tentativa |
| Transição CNF com UPDATE_APPLIED=FALSE | Recebe os ganhos preservados pela transição e continua |
| PID.ERR ou STATE_ERR, Identifier.ERR, processo.ERR | Sequência falha e relógio para |
| Nova SAMPLE enquanto ocupada ou número não consecutivo | ERR, relógio para |
| Confirmação fora da fase esperada | Não dispara o próximo passo |

Não há timeout adicional: uma confirmação ausente mantém a sequência aguardando. O próximo evento periódico provoca o caminho de falha do processo/seqüenciador, em vez de produzir um segundo cálculo. O ensaio é local em um recurso, sem comunicação distribuída. A latência real depende de verificação no FORTE; os testes Python não simulam o agendador nativo.

## Instalação preservando o projeto local

1. Salvar e fechar os editores do projeto no IDE, para evitar gravação de uma versão antiga sobre o arquivo alterado.
2. Atualizar a branch feature/adaptive-pid-iec61499 com git pull --ff-only. Nenhum .sys existente é substituído pelo commit.
3. Executar os testes: python -m unittest discover -s tests -p test_pid_single_update.py -v.
4. Executar scripts/prepare_pid_single_update.py --project com o caminho da pasta PID_Identification_Observer. O instalador confere a rede esperada, faz backup integral em Documents/4diac-backups, acrescenta o tipo e transforma aplicação e recurso mapeado. Recusa instalação repetida ou produtores de eventos inesperados. Os algoritmos existentes são preservados.
5. Reabrir/atualizar o projeto no IDE, conferir Problems e a instância SingleUpdateSequence. Exportar somente o novo tipo PID_SINGLE_UPDATE_SEQUENCE para o mesmo diretório externo utilizado pelos seis tipos anteriores, usando FORTE 1.x NG. Não sobrescrever CMakeLists.txt pelo exportador.
6. Recompilar com scripts/build_forte_pid_identification_observer.ps1 -IncludeTuner -IncludeStateAccess -IncludeTransition -IncludeSingleUpdate. O build ocorre em diretório novo e não inicia FORTE.
7. Parar o runtime antigo e iniciar o executável indicado pelo build. Fazer deployment completo no novo runtime. Se o tipo não foi compilado, o runtime antigo retornará UNSUPPORTED_TYPE.
8. Habilitar monitoramento e disparar somente SimulatedProcess.INIT uma vez. Não pausar o relógio, nem disparar manualmente tuner, leitura de estado ou atualização de ganhos.

## Aceitação nativa pendente

Após cerca de 40 s: processo SAMPLE_COUNT=400, REQ/APPLY=400/400; PID REQ/CNF=400/400, SET_GAINS/GAINS_CNF=1/1; tuner e transição REQ/CNF=1/1; sequência COMPLETED_SAMPLES=400, UPDATE_ATTEMPTED=TRUE, UPDATE_REJECTED_BY_ERROR=FALSE; transição UPDATE_APPLIED=TRUE. Nenhum ERR. Relógio START=1 e STOP=1. Não há pausa manual.

Previsão offline: saída final ≈0.8000000012113838; MV≈0.2782608692606103; ganhos ≈[0.4504609945115689,1.6091098779067279,0.01637095129722356]. Valores precisos em [resumo offline](single-update-offline-summary.json).

Comparado ao ensaio pausado após a amostra 275, os novos ganhos agora são usados no próprio cálculo 275. Nessa amostra, o replay produz MV≈0.2733255553481108. Não se exige a igualdade da trajetória com a troca feita após esse cálculo.

## Verificações realizadas

Sete testes passaram usando ST/ECC dos FBTs do ZIP e a rede XML transformada, com cópia de dados limitada às associações WITH das entradas. Incluem 400 amostras com uma atualização antes do cálculo 275, referência desativada comparada a recorrência independente, rejeição do sintonizador, erro/retenção da transição, parada por falha de controle, duplicação de amostra/confirmação fora de ordem, igualdade de aplicação/recurso e preservação do backup. SET_GAINS preserva memória integral, erro anterior e MV antes do próximo REQ.

Não foi executada compilação Windows, exportação pelo IDE ou validação FORTE deste novo tipo neste ambiente. Não é certificação de conformidade IEC 61499, prova de estabilidade adaptativa geral ou ensaio físico. O controle de atualização usa a regra candidata já documentada; nenhuma nova atribuição a material de aula foi introduzida.
