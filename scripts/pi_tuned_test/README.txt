ETAPA 6.9F - TESTE DO PI RESSINTONIZADO

Destino:
  C:\Projetos\master-thesis-level-control\scripts\pi_tuned_test

Parametros exigidos no projeto salvo:
  RawPI.SETPOINT = 450
  RawPI.PROPORTIONAL_GAIN = 8
  RawPI.INTEGRAL_GAIN = 0.05
  RawPI.SAMPLING_TIME_S = 0.1
  RawPI.MANUAL = TRUE
  RawPI.MANUAL_OUTPUT = -9000
  RawPVFilter.ALPHA = 0.98
  DAC fisico = 0..12000
  MAX_DELTA_DAC = 150

Ordem:
  1. Feche gateway e FORTE. Mantenha a parada fisica ativa.
  2. Salve o projeto no 4diac.
  3. Execute 01_PREFLIGHT.cmd.
  4. Execute 02_START_STACK.cmd.
  5. No 4diac, deploy somente PI_REAL_RAW_SAFE.
  6. Entre em monitoring e dispare RawInitMerge.EI1 uma vez.
  7. Confirme saida zero.
  8. Execute 03_RUN_TUNED_PI_TEST.cmd.
  9. Siga exatamente os prompts exibidos.
 10. Ao final, execute 04_STOP_AND_VALIDATE.cmd.

Sequencia no 4diac durante o monitor:
  - MANUAL=TRUE, MANUAL_OUTPUT=3000.
  - Libere a parada fisica.
  - Quando PV filtrada estiver entre 380 e 400:
      MANUAL_OUTPUT=1500.
  - Quando PV filtrada estiver entre 420 e 450:
      MANUAL=FALSE.
  - Apos a observacao automatica:
      MANUAL_OUTPUT=-9000.
      depois MANUAL=TRUE.
  - Reative a parada fisica quando o fluxo parar.

Em qualquer anomalia:
  - Acione a parada fisica.
  - Pressione Ctrl+C no monitor.
  - O gerenciador encerra gateway/FORTE e tenta confirmar o trip seguro.
