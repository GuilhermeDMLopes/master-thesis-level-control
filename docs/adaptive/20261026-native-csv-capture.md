# Coleta CSV nativa por execução do PID

Instrumentação diagnóstica para o processo sintético local. Não é uma alteração do algoritmo IEC 61499 nem uma aquisição da planta física.

## Origem e preservação

Pacote recebido: 20261026-112541-943-antes-coleta-nativa.zip. O preparador exige SHA256 07308a96e4c10ff7493b2d9bae35bd155d85933222d3c42eae09b270ca7194c1 do PID_FLAG_STATE_ACCESS.cpp exportado. Copia a pasta inteira para um destino novo e insere somente include e chamadas em INIT_OK e SAMPLE_OK. Os FBT, algoritmos exportados e a rede permanecem inalterados. Nova exportação exige nova verificação; nunca aplicar silenciosamente a um export diferente.

## Semântica

Uma linha é escrita após cálculo válido, antes do CNF do PID. Contém referência, medição recebida, comando calculado e ganhos internos realmente usados. Não confirma aplicação pelo processo: conferir também 400 APPLY e ausência de ERR na tela final. sample é contador de cálculos válidos, não contador independente da planta. elapsed_wall_s é tempo de relógio monotônico desde INIT_OK; para o modelo discreto usar Ts=0,1 s, não o intervalo de disco.

A gravação é síncrona e flush por linha; acrescenta latência. Usar disco local. O ensaio não prova cumprimento de prazo de tempo real. Falha de gravação é informada no console e desabilita a coleta, sem alterar o controle. Qualquer PID_TRACE ERROR invalida o arquivo como evidência completa.

Somente uma instância e uma inicialização por processo FORTE. Reiniciar o executável antes de cada ensaio, inclusive depois de novo deployment. Arquivo existente é recusado; usar nome novo por ensaio e um único processo. Não executar dois processos gravando o mesmo caminho.

## Preparação Windows

1. Atualizar a branch, executar prepare_pid_native_trace.py com --source apontando aos exports originais e --destination a uma pasta nova.
2. Executar build_forte_pid_identification_observer.ps1 com -ExportDirectory nessa cópia e switches -IncludeTuner -IncludeStateAccess -IncludeTransition -IncludeSingleUpdate.
3. Encerrar o FORTE anterior. No PowerShell que iniciará o novo executável, definir $env:PID_TRACE_FILE como caminho absoluto de arquivo novo numa pasta existente.
4. Iniciar o executável indicado pelo build, fazer deployment completo do projeto atual com ENABLE_UPDATE=FALSE, disparar somente SimulatedProcess.INIT uma vez. Confirmar PID_TRACE ready no console.
5. Ao terminar, verificar 400 linhas no CSV, contadores 400 e ausência de erro. Encerrar FORTE. Repetir com ENABLE_UPDATE=TRUE e outro arquivo, em novo processo FORTE.

Não exportar novamente os tipos para a cópia instrumentada. Não é necessário alterar conexões. As duas condições devem usar o mesmo executável instrumentado.

## Validação realizada e pendências

Preparador aplicado ao export enviado pelo usuário. Gravador compilado com g++ -std=c++11 -Wall -Wextra e exercitado com 400 linhas: cabeçalho e sequência 1–400 conferidos. Conversão CIEC_LREAL para TForteDFloat conferida no fonte oficial da revisão FORTE 7c8b6296227fa292c13d71d2958a404c6db03e53 (src/core/datatypes/forte_lreal.h).

Isso não é compilação integral do FORTE: build Visual Studio e coleta nativa permanecem pendentes no Windows. O arquivo CSV registra somente os cálculos do PID; é necessário combinar a evidência com os contadores do processo e do sequenciador.
