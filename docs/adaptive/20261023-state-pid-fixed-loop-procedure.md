# PID com acesso ao estado na malha: referência com ganhos fixos

Roteiro preparado em 23/10/2026. Execução nativa deste arranjo pendente. O ensaio anterior validou a atualização única em PID separado.

## Preservação
Salvar o projeto no IDE e copiar a pasta PID_Identification_Observer para backup externo antes de editar. O .sys local contém conexões adicionais às do repositório; não substituí-lo pela versão remota.

## Preparação na aplicação Observer_Test
Usar a instância existente PID_FLAG_STATE_ACCESS, denominada PID abaixo. Manter FixedPID disponível, porém desconectado.
Remover as conexões de eventos e dados de FixedPID (cinco de eventos e três de dados).
Desconectar os eventos ModelTuner.CNF → PID.READ_STATE, PID.STATE_CNF → GainTransitionTest.REQ, GainTransitionTest.CNF → PID.SET_GAINS e PID.GAINS_CNF → PID.REQ. ModelTuner.REQ permanece sem origem de evento. As ligações de dados da sintonia podem permanecer.
A ausência de eventos impede atualização de ganhos durante a referência.

## Parâmetros do PID
KP=0.45882339553937435
KI=1.6381884387801722
KD=0.016705052344105673
TS_S=0.1
U_MIN=0.0
U_MAX=10.0
Remover constantes SP=1/PV=0 do ensaio separado; estes dados virão do processo.
Manter SamplingClock.DT=T#100ms, Identifier.FORGETTING_FACTOR=0.8 e INITIAL_COVARIANCE=10000.0.

## Novas conexões
Eventos:
- Identifier.INITO → PID.INIT
- PID.INITO → SamplingClock.START
- Identifier.CNF → PID.REQ
- PID.CNF → SimulatedProcess.APPLY
- PID.ERR → SamplingClock.STOP

Dados:
- SimulatedProcess.REFERENCE → PID.SP
- SimulatedProcess.PROCESS_OUTPUT → PID.PV
- PID.MV → SimulatedProcess.COMMAND

Preservar as demais conexões de processo, identificador e relógio, incluindo DONE/ERR → STOP. SimulatedProcess.COMMAND terá somente um produtor: PID.MV.
A sequência por amostra é relógio → processo → identificador → PID → aplicação do comando.
Conferir a atualização das conexões mapeadas em LocalObserver.EMB_RES antes do download.

## Execução e aceitação
Salvar, efetuar novo deployment completo com contadores zerados e habilitar monitoramento. Não é necessária recompilação se utilizado o mesmo runtime que executou o teste anterior.
Disparar somente SimulatedProcess.INIT uma vez e aguardar aproximadamente 40 s.
Não disparar manualmente INIT/REQ/READ_STATE do PID ou REQ do sintonizador durante o ensaio.

Esperado:
- SAMPLE_COUNT=400 e DONE=1.
- Identifier e PID: REQ/CNF=400/400, ERR=0.
- PID.SET_GAINS=0 e READ_STATE=0.
- ModelTuner.REQ=0; GainTransitionTest.REQ=0; FixedPID.REQ=0.
- PROCESS_OUTPUT aproximadamente 0.800000000843.
- PID.MV aproximadamente 0.2782608693.
- Coeficientes estimados aproximadamente [1.2,-0.36,0.4,0.06].

Registrar contadores e valores finais em screenshot. Comparação final confirma o ponto de chegada; igualdade de toda a trajetória exige registro amostra a amostra. Não declarar controle adaptativo validado nesta etapa.
