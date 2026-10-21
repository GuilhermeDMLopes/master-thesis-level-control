# Aplicação mínima: PID fixo e MMQE em observação

21/10/2026. Escopo reduzido a pedido do usuário. Projeto: `4diac/application/PID_Identification_Observer`.
Status: XML gerado, rede e algoritmos exercitados por replay offline. Importação/exportação no IDE 2.0.1, compilação Windows e execução FORTE ainda pendentes. Não é certificação de conformidade IEC 61499.

## Quatro blocos visíveis
| Instância | Tipo | Função |
|---|---|---|
| SamplingClock | E_CYCLE | Dispara a amostra a cada T#100ms |
| SimulatedProcess | OBSERVER_DEMO_PROCESS | Processo ARX simulado, históricos e condições do ensaio |
| Identifier | RLS_PARAMETER_ESTIMATOR | MMQE: estima os quatro coeficientes |
| FixedPID | PID_FLAG | Controla com ganhos fixos e a flag original |

PID_FLAG e RLS_PARAMETER_ESTIMATOR são cópias com estrutura XML e algoritmos equivalentes aos tipos existentes. Os nomes legados SP/PV/MV significam referência, medição e comando; KP/KI/KD são os ganhos. Não foram renomeados para preservar o tipo validado.
Não há sintonia, gate, transição de ganhos ou ligação SET_GAINS nesta aplicação. Os protótipos anteriores permanecem fora dela.

## Execução
Inicialização manual: SimulatedProcess.INIT -> INITO -> Identifier.INIT -> INITO -> FixedPID.INIT -> INITO -> SamplingClock.START.
Amostra: SamplingClock.EO -> SimulatedProcess.REQ -> CNF -> Identifier.REQ -> CNF -> FixedPID.REQ -> CNF -> SimulatedProcess.APPLY.
O processo só atualiza os históricos ao receber APPLY. Assim, o MMQE usa y(k), y(k-1), y(k-2), u(k-1), u(k-2), antes do novo comando u(k).
APPLIED confirma a aplicação nas amostras 1–399; DONE na 400 para o relógio. ERR de qualquer bloco também para o relógio. Uma REQ recebida pelo processo enquanto aguarda APPLY gera ERR.
A confirmação final não dispara nova amostra: a próxima vem do relógio. Não há teste de prazo máximo ou garantia de execução a cada 100 ms; isso deve ser observado no runtime.

## Cenário único e explícito
ARX: y(k)=1.2*y(k-1)-0.36*y(k-2)+b1*u(k-1)+0.06*u(k-2).
b1=0.1 até k=150 e 0.4 desde k=151. Referência alterna 1.0/0.8 a cada 50 amostras, começando em 1.0. Esses contadores são condições do simulador, não identificação/adaptação.
MMQE: lambda=0.8, P0=10000, estimativa inicial zero. PID: KP=0.45882339553937435, KI=1.6381884387801722, KD=0.016705052344105673, Ts=0.1, limites [0,10]. Ganhos calculados previamente do modelo nominal conhecido, conforme documento da regra candidata. Não alegar partida com planta desconhecida.
Não usar esse ensaio para alegar confiabilidade com referência constante: a falha conhecida do MMQE nessa condição permanece documentada.

## Evidências offline
Quatro testes: inicialização/ordem de eventos, 400 amostras equivalentes ao ensaio anterior, rejeição de sobreposição/comando inválido, igualdade dos tipos originais e mapeamento.
Saída final: 0.8000000008429803; comando final: 0.27826086930085353; estimativa final aproximadamente [1.2,-0.36,0.4,0.06]; relógio parado na amostra 400.
O executor lê as conexões do .sys e os algoritmos dos .fbt. Não modela filas nativas, associação WITH em transporte, temporização real ou concorrência. Não substitui os testes FORTE.

## Importar no 4diac
1. Atualizar a branch feature/adaptive-pid-iec61499 preservando alterações locais.
2. File > Import > General > Existing Projects into Workspace. Selecionar a pasta do novo projeto; manter sem cópia para trabalhar no checkout. Caso o IDE apresente outro assistente de importação, enviar a tela antes de alterar os projetos existentes.
3. Abrir PID_Identification_Observer.sys, aplicação Observer_Test. Confirmar os quatro blocos e aba Problems sem erros.
4. O mapeamento já está em LocalObserver/EMB_RES, localhost:61499. A inicialização é manual; E_RESTART não está conectado à aplicação.

## Exportar e compilar — etapa seguinte
Exportar somente OBSERVER_DEMO_PROCESS, PID_FLAG e RLS_PARAMETER_ESTIMATOR para C:\Projetos\forte-pid-identification-observer\external-modules\PID_IDENTIFICATION_OBSERVER. Esperados três .cpp e três .h.
E_CYCLE/E_DELAY e os tipos de recurso pertencem ao runtime; não exportá-los como tipos novos.
Depois de conferir exportação, executar:

```powershell
powershell -NoProfile -File scripts/build_forte_pid_identification_observer.ps1
```
O script deriva do build anterior, cria um worktree isolado na revisão FORTE 7c8b6296227fa292c13d71d2958a404c6db03e53, inclui somente os três tipos, mantém OPC-UA desabilitado e não inicia o runtime. Não foi executado no Windows nesta etapa.
Usar o executável recém-compilado, não os runtimes antigos que não possuem OBSERVER_DEMO_PROCESS. Não iniciar dois FORTE na mesma porta.

## Primeiro teste nativo
Após exportação/build/deployment sem erros, habilitar monitoramento e disparar SimulatedProcess.INIT uma vez. Não disparar REQ ou APPLY manualmente durante execução. Ao final, registrar SAMPLE_COUNT=400, PROCESS_OUTPUT, APPLIED_COMMAND e as quatro saídas EST_* do Identifier. O ensaio deve durar aproximadamente 40 segundos, mas a temporização não foi medida.
Para interromper: SamplingClock.STOP. Para repetir após erro ou interrupção em meio a uma transação, reiniciar/reimplantar a aplicação antes de INIT. Não tratar reinicialização durante execução como procedimento normal.

Reprodução offline opcional antes de importar:
```powershell
& "$env:USERPROFILE\venvs\pid-adaptativo\Scripts\python.exe" -m unittest discover -s tests -p test_pid_identification_observer.py -v
& "$env:USERPROFILE\venvs\pid-adaptativo\Scripts\python.exe" scripts/verify_pid_identification_observer.py --output "$env:TEMP\pid-minimal-observer"
```
Gerador: scripts/generate_pid_identification_observer.py. Regerá-lo substitui os arquivos desse projeto: não executar sobre alterações locais feitas no IDE.

## Correção do teste de comparação — 21/10/2026
No Windows, três testes passaram e a comparação byte a byte falhou: a saída enviada mostra uma quebra de linha final presente em uma cópia e ausente na outra. A comparação agora analisa a estrutura XML, ignorando apenas espaços entre elementos e formatação externa. Todos os atributos, incluindo Text dos algoritmos ST, portas, WITH e transições ECC continuam comparados. Não houve alteração nos blocos ou nas equações. Um teste adicional confirma que a quebra de linha final é tolerada e uma mudança real no algoritmo é detectada. Cinco testes passaram no ambiente de desenvolvimento após a correção; nova execução Windows pendente.
