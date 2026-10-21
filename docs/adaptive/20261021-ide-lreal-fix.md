# Correção de literais no IDE 2.0.1

21/10/2026. Usuário confirmou cinco testes Python aprovados no Windows (0.354 s). Captura image(20261021-153025).png mostra quatro erros Invalid LREAL literal: FixedPID.KP e FixedPID.KD na aplicação Observer_Test e recurso EMB_RES.

Causa: gerador usava .45882339553937435 e .016705052344105673 sem zero antes do separador decimal. Corrigidos para 0.45882339553937435 e 0.016705052344105673 nos dois locais do .sys e no gerador. Valores matemáticos e algoritmos permanecem iguais.

Acrescentado teste que verifica as quatro declarações. Seis testes offline passaram após correção. Falha detectada pelo IDE evidencia que replay Python não substitui validação do formato no 4diac. Reabrir/atualizar o projeto e confirmar Problems sem erros antes de exportar. Exportação, compilação e execução nativa ainda pendentes.
