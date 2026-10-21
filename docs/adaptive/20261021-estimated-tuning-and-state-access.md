# Modelo estimado conectado e preparação da leitura de estado — 21/10/2026

As capturas image(20261021-190352).png e image(20261021-190422).png foram examinadas na conversa (não incorporadas neste commit).
Antes de REQ, ModelTuner tem entradas amostradas zero e VALID=FALSE.
Depois de REQ=1: CNF=1, ERR=0, VALID=TRUE; recebe aproximadamente [1.2,-0.36,0.4,0.06] do Identifier, calcula KP=0.1551602890, KI=0.5822613474, KD=0.0045728679, resíduo aproximadamente 4.44e-16.
Identificador e processo completaram 400 amostras; PID SET_GAINS=0. Conexão nativa de dados confirmada, disparo manual, sem adaptação.

## Próximo passo restrito
Preparar o tipo existente PID_FLAG_STATE_ACCESS para teste isolado. Não substituir a instância FixedPID nem modificar a rede validada nesta etapa.
O tipo preserva os algoritmos do PID_FLAG e acrescenta READ_STATE/STATE_CNF e saídas para observar integral, erro anterior, flag, ganhos ativos e configuração.
A leitura deve ocorrer quando o PID estiver inicializado, entre cálculos. Ler o estado não executa o PID e não deve alterar suas memórias.

Quatro testes test_pid_state_access.py e dez test_pid_transition_chain.py passaram localmente no replay ST/ECC limitado.
Não constitui validação nativa do novo tipo.

O script de build aceita agora -IncludeStateAccess, opcional e independente de -IncludeTuner. Com ambas opções exige os cinco pares exportados e verifica os cinco objetos.
Depois de exportar PID_FLAG_STATE_ACCESS:
powershell -NoProfile -File scripts/build_forte_pid_identification_observer.ps1 -IncludeTuner -IncludeStateAccess

## Esclarecimento da transição
Preservar a memória integral, sozinho, não preserva o comando quando KI muda.
A proposta já existente mantém a aritmética do quadro e limita o passo conjunto dos ganhos. Não implementa reescala do integrador; não garante salto zero ou estabilidade adaptativa.
Leitura de estado, transição e coordenação de eventos estão descritas em 20261020-transition-event-chain.md. A integração automática permanece pendente, sem mudança de ganhos na aplicação atual.
