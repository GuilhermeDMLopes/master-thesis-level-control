# Validação da bancada RC e dos blocos FORTE

Registro consolidado em 14/11/2026. Ensaios relatados em 13/11/2026.
Base: feature/adaptive-pid-iec61499.

## Proveniência e limites
Este registro transcreve resultados e caminhos enviados pelo operador no terminal.
Os CSV, JSON, logs e executáveis originais das pastas locais abaixo ainda NÃO foram anexados a este registro Git. Não se trata de uma nova execução independente dos testes.
PASS significa aprovação nos casos exercitados; não certifica todos os comportamentos, controle físico em malha fechada nem atendimento temporal universal.

## Bancada
PLC B&R X20CP0483; projeto informado: C:\projects\circuito_RC.apj\Config1.
Modelo nominal informado pelos orientadores e demonstrado no Octave: G(s)=1/(1+s).
Notebook Ethernet 10.0.0.1/24; PLC RC 10.0.0.2; OPC UA opc.tcp://10.0.0.2:4840.
O PLC do tanque usa 10.0.0.3 e não é alvo destes testes.
Namespace confirmado urn:B&R/pv/, índice observado 6:
- ACAO_CONTROLE: ns=6;s=::Program:ACAO_CONTROLE, REAL/Float.
- ADC_R: ns=6;s=::Program:ADC_R, REAL/Float.

A leitura de ACAO_CONTROLE confirma a variável publicada, não mede diretamente a tensão na saída.
A leitura sequencial OPC UA não garante captura atômica/sincronizada com o ciclo PLC.
No projeto analisado, ADC_R = ADC_I*10/32767; DAC_R = ACAO_CONTROLE*3276.7; DAC_I = REAL_TO_INT(DAC_R). O programa realiza escalas de E/S; não se deve confundi-lo com um simulador Python do tanque.

## Registro dos testes

| ID | Escopo | Resultado relatado |
|---|---|---|
| RC-01 | Conectividade e 100 leituras OPC UA reais | Concluído, comando 1 e resposta aproximadamente 1,0019–1,0044 |
| ID-01 | RLS_PARAMETER_ESTIMATOR no FORTE | PASS, 243 atualizações e 110 pontos de validação |
| TU-01 | PID_TUNING no FORTE | 10/10 PASS |
| CT-02 | PID_TANK_CONTROLLER no FORTE | 12/12 PASS |
| IF-01 | TANK_SAMPLE_INTERFACE no FORTE | 12/12 PASS, JSON conferido após falha de formatação do relatório |
| RC-02 | Leitura física + comando hipotético local FORTE | PASS, 60 leituras; nenhuma atuação enviada ao PLC |
| RC-03 | Degrau físico 1 → 2 por 8 s → 1 por 8 s | Preparado; execução e análise PENDENTES |
| RC fechado | Controle físico com ganhos fixos | PENDENTE |
| RC adaptativo | Identificação/sintonia aplicadas fisicamente | PENDENTE |

### RC-01
Arquivo local: Documents/ensaios-RC/rc-leitura-20261113-171227-583.csv.
100 leituras em aproximadamente 11,161 s. Não declarar período exato de 100 ms: o script aguardava 100 ms além do custo de leitura.
Valor ACAO_CONTROLE=1; ADC_R coerente com leitura relatada no Automation Studio (~1,0023).
Sem escrita.

### ID-01 — identificação
243 atualizações; validação de 110 pontos.
Coeficientes finais relatados:
[0.920972144809703, 0.00156187850392946, -0.000188957181858543, 0.0776483769627278].
Maior divergência dos coeficientes frente à referência: 4.996003610813204e-16.
RMSE relatado: 0.005042197832440788.
A reprodução numérica não demonstra sozinha identificação ótima ou equivalência exata ao modelo nominal.
Primeira tentativa: START retornou INVALID_OBJECT. Corrigido o endereçamento do START ao recurso, com Request sem elemento FB.
Evidência: identifier-20261113-172324-330/resultado-20261113-172429-024925.

### TU-01 — sintonia
Casos: init, before, first, duplicate, between, periodic, init_rc, reject_rc, init_off, disabled.
Todos PASS. Verificações incluem agendamento da atualização, duplicação, periodicidade, desabilitação e rejeição do caso RC.
Importante: reject_rc PASS significa que a rejeição esperada funcionou; NÃO significa aprovação dos ganhos adaptativos para a bancada RC.
Evidência: tuning-20261113-172842-017/resultado-20261113-172842-328406.

### CT-02 — controlador
Casos: init, primeira_amostra, erro_constante, novos_ganhos, transferencia, retoma_integral, manual, retorno_auto, limite_superior, limite_inferior_integral_congelada, reset, periodo_invalido.
Todos PASS. Cobertura: cálculo PID, troca de ganhos, transferência, modos manual/automático, saturação, integral congelada, reset e rejeição de período inválido.
Evidência: controller-20261113-173053-235/resultado-20261113-173053-405287.

### IF-01 — interface
Casos: inicio, solicita_controle, rampa_inicial, ack1, segunda_amostra, duplicada, segunda_rampa, ack2, historico_para_rls, parada_zero, falha_escrita, salto_sequencia.
Todos PASS.
O script original falhou ao concatenar uma lista na geração do Markdown, APÓS gravar resumo.json. O operador conferiu o nome do bloco, resultado global e os 12 nomes/resultados no JSON e gerou registro_IF-01_conferido.md com hashes.
Não ocultar essa falha nem considerar que houve uma nova execução.
Evidência: interface-20261113-173304-102/resultado-20261113-173304-335529.

### RC-02 — observação sem atuação
60 leituras físicas. ACAO_CONTROLE permaneceu 1.
Referência local: 1 (1–20), 1,25 (21–40), 1 (41–60).
Exemplos:
- leitura 1: u=1; PV=1,00192; SP=1; comando hipotético=0,99904.
- leitura 21: u=1; PV=1,00192; SP=1,25; comando hipotético=1,12404.
- leitura 60: u=1; PV=1,00436; SP=1; comando hipotético=0,99782.
O comando calculado localmente não foi escrito no PLC. Este é um teste de leitura e cálculo, não de malha fechada.
Evidência aprovada: observacao-20261113-174038-736/resultado-20261113-174038-991965.
Tentativa anterior observacao-20261113-173811-925/resultado-20261113-173812-252344: INCOMPLETO por timeout de conexão. Ethernet estava Disconnected.
Após reconexão, Ethernet Up 100 Mbps, origem 10.0.0.1 e TCP 4840 confirmado.
Um guard PowerShell rejeitou indevidamente a conexão ao comparar SourceAddress convertido em texto; a execução seguinte do coletor original concluiu PASS.

## Rastreabilidade
Todos os caminhos de evidência acima são relativos a C:\Users\guilh\Documents\ensaios-RC.
Runtime dos testes isolados:
C:\Projetos\forte-pid-adaptive-tank\runs\20261029-162842-127\build\src\Debug\forte.exe
SHA256 relatado no ID-01: 65fc443f19963b845192fe72c6dd148dfbdc89efbe5f957f2ac05c10894b48fc.
Não inferir identidade de todos os executáveis sem conferir os respectivos resumos.
Pacotes utilizados: RC_Identifier_FORTE.zip, RC_Tuning_Registro.zip, RC_Controller_Registro.zip, RC_PlantInterface_Registro.zip e RC_02_Observacao_FORTE.zip.
Os pacotes originais não são anexados por este commit.

## RC-03 e próximos passos
O operador autorizou explicitamente o comando 2,0 e informou acesso ao Automation Studio.
Sequência: conferir estado inicial 1,0; registrar baseline; escrever 2,0; aguardar aproximadamente 8 segundos adquirindo ADC_R; escrever 1,0 e observar mais 8 segundos.
A restauração via software depende de comunicação e processo disponíveis. Se falhar, restaurar localmente.
Registrar CSV e resumo, inclusive falhas; não marcar PASS de modelo automaticamente.
Após analisar degrau e retorno: decidir ganhos fixos e fechar a malha RC. Sintonia adaptativa requer aprovação específica do modelo e dos ganhos.
Não transportar bias 9000, escala raw de nível ou limites DAC do tanque para o RC.

## Contexto anterior (separado do RC)
O tanque simulado concluiu ensaio de 2000 amostras e 70 atualizações de ganhos; isso não constitui validação física do RC.
Houve outras execuções interrompidas por tempo de aquisição/resposta. Monitoramento desligado coincidiu com ensaio concluído, sem demonstrar causalidade exclusiva.
A bancada RC é a etapa intermediária solicitada pelos orientadores antes do tanque.

## Evidências ainda a incorporar
Copiar seletivamente CSV, resumo.json, registro Markdown conferido e logs das pastas citadas, conferindo conteúdo e hashes. Não inventar medições ausentes nem publicar binários automaticamente.
O histórico documental está consolidado; os arquivos brutos permanecem no computador do operador.
