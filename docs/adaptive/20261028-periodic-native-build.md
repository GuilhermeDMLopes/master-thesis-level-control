# Build da atualização periódica

Log recebido em 28/10/2026: Texto colado(20261028-134451).txt. O diretório de build indica criação em 27/10/2026, 18:43:41.

Comando: build_forte_pid_identification_observer.ps1 -BasicAdaptive -ExportDirectory C:\Projetos\forte-pid-basic-adaptive\exports-periodic.

Os seis tipos foram compilados, incluindo PROCESS_IDENTIFIER e TUNING_TRIGGER. Resultado: BUILD COMPLETED.

Executável:
```
C:\Projetos\forte-pid-identification-observer\runs\20261027-184341-928\build\src\Debug\forte.exe
```
SHA256 reportado:
```
7297CF77C19C11245441D8CB5AF9EB45690022AFE43AF9F930BD1B588667E877
```

O script não iniciou o runtime nem fez deployment. A compilação bem-sucedida não confirma por si só que os exports contêm a nova porta; confirmar UPDATE_INTERVAL_SAMPLES=25 no Identifier mapeado e os seis eventos de atualização no ensaio nativo. Usar ENABLE_UPDATE=TRUE, UPDATE_AT_SAMPLE=275; iniciar uma vez. Esperar 400 cálculos/aplicações, 394 CONTROL_READY, seis GAINS_READY/SET_GAINS/GAINS_CNF e zero ERR. Ensaio periódico nativo ainda pendente.
