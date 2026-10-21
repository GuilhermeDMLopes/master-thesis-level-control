# Compilação com sintonia em observação — 21/10/2026

O usuário confirmou a exportação de PID_MODEL_TUNER pelo exportador FORTE 1.x NG.
O script build_forte_pid_identification_observer.ps1 agora aceita -IncludeTuner.

Sem a opção, preserva o build dos três tipos do observador.
Com a opção:
- exige oito arquivos exportados, únicos e não vazios;
- copia os quatro pares .cpp/.h para um novo build isolado;
- registra os tipos e hashes no transcript;
- verifica a presença dos quatro objetos compilados, incluindo PID_MODEL_TUNER.obj.

Comando no PowerShell, a partir da raiz do repositório:

~~~powershell
powershell -NoProfile -File .\scripts\build_forte_pid_identification_observer.ps1 -IncludeTuner
~~~

A alteração reutiliza o procedimento que compilou o observador no Windows.
Revisão estática da seleção de tipos concluída; a nova compilação Windows ainda depende da execução pelo usuário. O script não inicia o runtime nem faz deployment.
Nenhuma conexão aos ganhos do PID foi adicionada. A próxima verificação é nativa, em observação, conforme [plano](20261021-native-observer-result.md).
