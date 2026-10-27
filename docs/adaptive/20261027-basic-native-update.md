# PID básico: ressintonia única no FORTE — 27/10/2026

Evidência: screenshot image(20261027-211831).png enviado pelo usuário, recurso LocalObserver.EMB_RES de PID_Basic_Adaptive.

ENABLE_UPDATE=TRUE e UPDATE_AT_SAMPLE=275. Process.SAMPLE_COUNT=400; REQ=400; APPLY=400; APPLIED=399; DONE=1. Identifier.CONTROL_READY=399 e GAINS_READY=1. Controller.REQ=400, CNF=400, SET_GAINS=1 e GAINS_CNF=1. Eventos ERR dos três blocos visíveis em zero. Controller.VALID=TRUE; SATURATED=FALSE; INTEGRATION_ENABLED=TRUE.

Ganhos enviados pelo Identifier e presentes nas entradas UPDATED do Controller:
- KP aproximadamente 0.155160307084448.
- KI aproximadamente 0.582261370310948.
- KD aproximadamente 0.00457287219454029.

Saída final do processo aproximadamente 0.800000202640364; referência 0.8; comando aproximadamente 0.278260878233689. Estes valores finais correspondem ao replay offline da troca direta. Os parâmetros INITIAL_* continuam exibindo os ganhos originais: são configuração de inicialização, não indicação dos ganhos ativos após SET_GAINS.

Conclusão limitada: evidência nativa da operação da estrutura básica com uma transferência de ganhos confirmada e 400 cálculos/aplicações. O print final não comprova sozinho o instante exato da transferência, a trajetória completa, o salto na amostra 275 ou o IAE nativo. O instante é configurado para 275 e verificado no replay offline. Não confundir esta ressintonia única com adaptação contínua, estabilidade geral ou melhoria de desempenho. O replay anterior mostrou aumento do IAE com a troca direta.

Próximo marco: preservar o projeto local salvo e os exports/executável utilizados; comparação temporal fixa versus ressintonia antes de qualquer afirmação de desempenho ou integração física. Não adicionar novos blocos à rede para este marco.
