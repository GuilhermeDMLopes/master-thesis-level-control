# Reprodução do observador no Windows — 20/10/2026

Evidência fornecida por Guilherme: saída do PowerShell e dois JSONs anexados. Não é teste FORTE/PLC.
O pull apresentado terminou em b20f58b. O commit.txt, python-version.txt, dependencias.txt e CSVs foram gerados no computador do usuário, mas não enviados; não foram auditados. Existem alterações locais nos projetos 4diac, preservadas pelo pull.
NumPy 2.5.4 instalado conforme terminal. O wheel cp314 indica Python 3.14; a versão exata não foi confirmada pelo arquivo de versão.
Quatro testes de test_identification_update_gate.py passaram em 0.633 s. Não atribuir os 27 testes do ambiente de desenvolvimento à execução Windows.

## Evidências preservadas
- evidence/20261020-windows-observer/original-summary.json: upload summary(1).json, SHA256 1e0562b2e3a7e6c284741c0e2433b72f76a8da9cd8d2cec78332afded7a0e43b.
- evidence/20261020-windows-observer/guarded-summary.json: upload summary(2).json, SHA256 38acd9e4d61188fe57349f411dedb17577d1f7a5cbdfd29309bfc28b5e5e716f.

## Resultados confirmados
| Cenário | Original | Protegido |
|---|---|---|
| Referência constante | primeira falha em k=150 | sem falha, 276 atualizações suspensas |
| Referência variável | sem falha, 32 candidatos, 4 rejeições de sintonia | mesmos resultados |
| Interferência no PID fixo | nenhuma, conforme comparação interna do script | nenhuma, conforme comparação interna do script |

O modelo variável recupera aproximadamente [1.2,-0.36,0.4,0.06]. O protegido constante termina em [1.84456,-0.84530,0.99141,-0.98927], portanto não identifica corretamente o processo.
A saída final 1.0 nesse cenário é desempenho do PID fixo; não valida o modelo estimado.
IAEs iguais entre original e protegido: 1.014203522205899 (constante), 1.511406816099983 (variável). Nenhum ganho candidato foi aplicado.

Os resultados principais coincidem com os anteriores. Há pequenas diferenças nos autovalores mínimos calculados: por exemplo 0.04367619918557676 no Windows contra 0.04367619922538747 no registro anterior. Elas não alteram as conclusões destes ensaios; não alegar igualdade bit a bit de todos os diagnósticos.

## Decisão
Reprodução offline no Windows confirmada pelos resumos e terminal. Não é qualificação nativa nem demonstração de estabilidade adaptativa.
Não repetir esses ensaios sem motivo novo. Próximo trabalho: cálculo de qualidade executável no fluxo de blocos e aplicação integrada de observação, com ganhos fixos e validação nativa posterior.
A proteção permanece experimental: janela/limiar não garantem identificação, e as 49 primeiras amostras não têm o gate de condicionamento.
