# Compilação nativa com entradas de atualização separadas

Evidências recebidas: image(20261022-124435).png e Texto colado(20261022-124810).txt. Consultadas na conversa, anexos não incorporados neste commit.

A captura mostra as três entradas UPDATED_* no PID_FLAG_STATE_ACCESS e zero itens em Problems. A instância aparece com nome PID_FLAG_STATE_ACCESS, em vez de PIDStateTest. A ligação STATE_CNF → GainTransitionTest.REQ e os dados de estado estão presentes. As três ligações de retorno de ganhos, CNF → SET_GAINS e GAINS_CNF → REQ ainda não aparecem conectadas.

O log confirma compilação dos seis tipos (OBSERVER_DEMO_PROCESS, PID_FLAG, PID_FLAG_STATE_ACCESS, PID_GAIN_TRANSITION, PID_MODEL_TUNER, RLS_PARAMETER_ESTIMATOR) e BUILD COMPLETED.

Executável: C:\Projetos\forte-pid-identification-observer\runs\20261022-094537-948\build\src\Debug\forte.exe

SHA256: 699EC705A45B627E7F1BFD080258D7687466FC61449192028576150AE0F85684

O script informa explicitamente que o runtime não foi iniciado e nenhuma aplicação foi implantada. Compilação confirmada; teste funcional da cadeia completa permanece pendente. Ao usar instância substituída, conferir mapeamento para LocalObserver.EMB_RES antes do deployment.
