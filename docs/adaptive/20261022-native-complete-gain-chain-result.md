# Cadeia de atualização de ganhos: validação nativa

Evidência: quatro capturas image(20261022-125443).png, image(20261022-125601).png, image(20261022-125623).png e image(20261022-125640).png, consultadas na conversa (imagens não incorporadas ao commit).

Rede: PID.STATE_CNF → Transition.REQ → Transition.CNF → PID.SET_GAINS → PID.GAINS_CNF → PID.REQ. Nove dados de estado vão do PID à transição; NEXT_* retornam às três entradas UPDATED_* do PID. INIT usa KP/KI/KD separados.

Sequência observada:
1. Rede conectada, Problems sem itens.
2. INIT=1/INITO=1 com UPDATED_* zerados, sem executar a transição.
3. Primeiro REQ/CNF=1, MV=2.025, SET_GAINS=0.
4. READ_STATE=1/STATE_CNF=1; transição REQ=1/CNF=1; PID SET_GAINS=1/GAINS_CNF=1 e REQ=2/CNF=2.

Resultado final: MV=RAW=1.055; P_TERM=0.981395348837209; I_TERM≈0.0736046511627907; D_TERM=0. Ganhos recebidos 0.981395348837209/0.490697674418605/0.0981395348837209. PID VALID/FLAG verdadeiros, SATURATED falso; ERR e STATE_ERR zero. Transição VALID/UPDATE_APPLIED verdadeiros, ERR zero, efeito≈-0.02 e fração≈0.186046511627907.

O ensaio confirma uma passagem completa pelo encadeamento nativo, com inicialização independente das saídas zeradas da transição e aplicação dos novos ganhos no segundo cálculo. Não há evidência de repetição extra nessa passagem.

As saídas ACTIVE_* ainda mostram 1/0.5/0.1 e INTEGRAL_MEMORY mostra0.05: são o retrato publicado em READ_STATE antes da atualização. O cálculo final usa os novos ganhos; a memória interna esperada é0.15, consistente com I_TERM/KI. Não disparar READ_STATE como consulta isolada nessa rede, pois ele inicia outra operação.

Limites: modelo e ganhos alvo fixos, SP1/PV0 constantes, dois blocos no FORTE local; não é ainda validação do MMQE comandando adaptação automática em malha fechada nem ensaio físico. Referência de compilação: 20261022-separated-gains-native-build.md. Próxima etapa: integrar a sintonia ao caminho validado, com dados coerentes e autorização de atualização definida.
