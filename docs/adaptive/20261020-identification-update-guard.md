# Proteção da atualização do MMQE: diagnóstico e ensaio

20/10/2026. Proteção supervisória experimental, não substituição da fórmula do MMQE. Apenas replay offline ST/ECC, sem validação FORTE.

## Diagnóstico reproduzido
No cenário de referência constante do ensaio anterior, a janela normalizada de regressores tinha condicionamento ~2.37e6 em k=60 e ~2.64e16 em k=149. A maior entrada absoluta da matriz P chegou a 1.1198e16; um autovalor calculado tornou-se negativo antes de DEN=-0.575 em k=150. O ERR original permanece reproduzível sem proteção.
Esses dados são consistentes com crescimento da covariância sob baixa excitação e perda de propriedades numéricas. Não constituem uma prova geral sobre todas as fontes de erro ou implementações.

Referência de contexto: A Modified Recursive Least Squares Algorithm with Forgetting and Bounded Covariance, texto dos autores disponível em https://dsbaero.engin.umich.edu/wp-content/uploads/sites/441/2019/07/MRLSAdamACC19.pdf . O resumo descreve a divergência da covariância quando os dados não são suficientemente persistentes. NÃO implementamos o algoritmo desse artigo, nem atribuímos a ele a proteção abaixo.

## Proteção ensaiada
Reutilizamos o critério de qualidade que já bloqueava a sintonia, agora ANTES de atualizar o estimador:
- após formar 50 regressores, calcular o condicionamento da janela normalizada por coluna;
- permitir REQ do MMQE somente se o condicionamento for finito e <=1e6;
- caso contrário, não enviar REQ: preservar tanto os coeficientes quanto toda a matriz P;
- continuar a coleta dos históricos reais em cada amostra, inclusive durante a pausa;
- não publicar candidatos de sintonia na amostra suspensa;
- retomar as atualizações quando o critério voltar a ser satisfeito, sem resetar a memória.

As primeiras 49 amostras continuam autorizadas, como aquecimento experimental. Isso não protege partidas arbitrárias com baixa excitação. O limiar e a janela são escolhas do ensaio anterior, não garantias de convergência, nem parâmetros validados na planta. Um modelo pode passar o gate e continuar incorreto; a referência constante demonstrou isso.

## Bloco simples acrescentado
`IDENTIFICATION_UPDATE_GATE`, em `4diac/prototypes/PID_Adaptation/Type Library/pid/`.
REQ amostra UPDATE_ALLOWED e os cinco dados: PROCESS_OUTPUT, OUTPUT_PREVIOUS_1/2, INPUT_PREVIOUS_1/2.
Se autorizado, copia esses valores para LATCHED_* e emite UPDATE; se não, emite HOLD sem alterar as saídas de dados. Não calcula condicionamento, não modifica o MMQE e não possui estado temporal de identificação.

Ligação proposta: Gate.UPDATE -> Estimator.REQ; LATCHED_* -> entradas correspondentes. Estimator.CNF e Gate.HOLD seguem caminhos mutuamente exclusivos de continuação da amostra. HOLD deve invalidar a autorização de adaptação e nunca reutilizar alvo antigo. Estimator.ERR continua sendo falha explícita; não o transformar em CNF.
O cálculo de qualidade ainda está em Python/NumPy. O bloco não é uma solução autônoma pronta para deployment. Tampouco valida dados não finitos: essa responsabilidade permanece no estimador e na fonte da autorização.

## Resultados com 400 amostras
| Cenário | Sem proteção | Com proteção |
|---|---|---|
| Referência constante | ERR em k=150 | Sem ERR; 276 atualizações suspensas |
| Referência variável | Sem ERR; modelo recuperado | Mesmas estimativas e mesmos candidatos, sem suspensões |

Constante protegido: max abs(P)=6.67e7; menor autovalor observado ~0.0437. Modelo final [1.84456,-0.84530,0.99141,-0.98927], distante do modelo real [1.2,-0.36,0.4,0.06]. Portanto a proteção evitou a falha numérica neste ensaio, mas NÃO solucionou a falta de informação para identificação.
Variável protegido: modelo final aproximadamente [1.2,-0.36,0.4,0.06], 32 candidatos e quatro rejeições pelo tuner.
Em ambos, comando e medição permaneceram exatamente iguais ao PID fixo sem observador. Nenhum ganho foi aplicado.

## Reproduzir e interpretar os logs
```powershell
py -m unittest discover -s tests -p test_identification_update_gate.py -v
py scripts/verify_pid_observer.py --output "$env:TEMP\pid-observer-original"
py scripts/verify_pid_observer.py --guard-updates --output "$env:TEMP\pid-observer-guarded"
```
CSV registra estimator_updated, update_allowed, window_condition, covariance_max_abs e covariance_min_eigenvalue. Na pausa, prediction_error e estimator_denominator são vazios para não representar valores antigos como cálculo atual. estimation_valid indica ausência de falha do estimador; NÃO certifica qualidade do modelo nem atualização na amostra.
A condição e os autovalores são diagnósticos offline, não implementações nativas de tempo real.

Passaram 27 testes dos conjuntos atuais, quatro novos para encaminhamento/pausa, retenção dos coeficientes, isolamento do PID e comparação com cenário excitado. Os testes anteriores continuam reproduzindo a falha sem proteção. PID e MMQE originais não foram modificados.

## Limite e próximo passo
Ainda precisamos definir e implementar o cálculo de qualidade em blocos e validar seu comportamento no FORTE. Antes de habilitar adaptação, avaliar excitação e resposta a mudanças: ausência de ERR não deve autorizar ganhos por si só. Não usar esta proteção como alegação de estabilidade adaptativa ou identificação garantida.
