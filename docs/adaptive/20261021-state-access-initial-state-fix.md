# Correção do estado inicial do PID com leitura — 21/10/2026

As quatro capturas 191558, 191648, 191705 e 191721 mostram INIT=1 sem INITO, REQ=1 sem CNF e READ_STATE=1 com STATE_ERR=1; VALID permanece FALSE. O teste nativo falhou, não foi validado.

O FBT declarava FAILED_READ_REJECTED antes de START. Corrigida a ordem para START ser o primeiro ECState. O replay offline fixava o estado inicial pelo nome START, mascarando a diferença; agora usa o primeiro ECState declarado. Acrescentada regressão para ordem, INIT, REQ e READ_STATE. Cinco testes locais passaram; confirmação nativa depende de nova exportação/build/deployment.

Nenhuma equação PID foi alterada. Substituir a cópia local PID_FLAG_STATE_ACCESS.fbt pelo protótipo corrigido, atualizar no IDE, reexportar o par C++, recompilar com -IncludeTuner -IncludeStateAccess, reiniciar com o novo executável e repetir o teste isolado. Não repetir apenas o deployment usando o executável antigo.
