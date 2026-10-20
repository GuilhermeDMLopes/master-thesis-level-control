# PID_MODEL_TUNER: cálculo dos ganhos a partir do modelo

Protótipo experimental, 20/10/2026. Testado por replay limitado do ST/ECC real do FBT; não exportado nem executado no FORTE nesta etapa.

## Função
Receber o modelo ARX estimado e calcular um triplo candidato de ganhos. Não executa MMQE, não mede qualidade da identificação, não modifica o PID e não atua no processo.

Arquivo: `4diac/prototypes/PID_Adaptation/Type Library/pid/PID_MODEL_TUNER.fbt`.
Gerador: `scripts/generate_pid_model_tuner.py` (utiliza funções XML do gerador de transição).
Teste: `tests/test_pid_model_tuner.py`.

| Entrada associada a REQ | Significado |
|---|---|
| MODEL_OUTPUT_COEFFICIENT_1/2 | a1/a2, com os sinais da equação abaixo |
| MODEL_INPUT_COEFFICIENT_1/2 | b1/b2, relativos aos comandos anteriores aplicados |
| SAMPLE_TIME_S | período de amostragem do modelo e do PID, em segundos |
| DESIRED_POLE | polo discreto desejado, entre zero e um |

Modelo: y(k)=a1*y(k-1)+a2*y(k-2)+b1*u(k-1)+b2*u(k-2).
CNF publica TARGET_PROPORTIONAL_GAIN, TARGET_INTEGRAL_GAIN, TARGET_DERIVATIVE_GAIN, REMAINING_POLE, POLYNOMIAL_RESIDUAL e VALID=TRUE.
ERR publica apenas VALID=FALSE. As saídas numéricas podem conservar resultados anteriores: nunca consumi-las após ERR. Uma nova REQ permite tentar outro modelo, sem INIT.

## Equações e simplificação
A regra é a candidata derivada em `20261019-pid-tuning-candidate.md`, não uma fórmula atribuída às aulas ou aos artigos. Preserva a integral trapezoidal e a derivada regressiva do PID do quadro.

Escolhemos três polos iguais a p; o quarto, r, é determinado pelas equações. Não existem quatro polos livremente ajustáveis com apenas três ganhos.

c1=-3p; c2=3p²; c3=-p³.
h0=c1+1+a1; h1=c2-a1+a2; h2=c3-a2; h3=0.

Para evitar uma rotina matricial genérica no bloco:
- s0=h0/b1; t0=-1/b1;
- s1=(h1-b2*s0)/b1; t1=(-c1-b2*t0)/b1;
- s2=(h2-b2*s1)/b1; t2=(-c2-b2*t1)/b1;
- r=(h3-b2*s2)/(b2*t2+c3);
- q0=s0+t0*r; q1=s1+t1*r; q2=s2+t2*r;
- KP=(q0-q1-3q2)/2; KI=(q0+q1+q2)/Ts; KD=Ts*q2.

O bloco verifica domínio numérico, ganhos não negativos, |r|<1 e resíduo dos quatro coeficientes <=1e-9. p já é restrito a (0,1). Isso verifica a solução nominal de polos, não estabilidade robusta ou adaptativa.

## Limitação numérica explícita
A solução escalar exige b1 utilizável: max(|b1|,|b2|)>1e-12 e |b1|>1e-10*max(|b1|,|b2|). Exige ainda |b2*t2+c3|>1e-12 e >1e-10*(|b2*t2|+|c3|). Intermediários são limitados ao domínio finito [-1e100,1e100].
Esses são guardas de implementação propostos, não limites da planta ou prescrições dos materiais. O bloco pode rejeitar modelos que uma solução matricial com pivotamento conseguiria resolver, especialmente b1=0. NÃO implementa o critério NumPy cond(M)<=1e10 e não é numericamente equivalente a ele. Não ampliar seu domínio sem testes próprios.

## Validação desta etapa
Cinco testes passaram: modelos nominal/alterado/estimado; entradas inválidas; rejeição após sucesso e recuperação; 250 modelos determinísticos comparados ao solver NumPy e raízes independentes; associações WITH de REQ e ERR.

Resultados nominais, Ts=0.1 e p=0.7:
- [1.2,-0.36,0.1,0.06]: KP=0.4588233955; KI=1.6381884388; KD=0.01670505234.
- [1.2,-0.36,0.4,0.06]: KP=0.1551602890; KI=0.5822613474; KD=0.00457286790.

Reprodução: `py -m unittest discover -s tests -p test_pid_model_tuner.py -v` (NumPy necessário).

## Próxima ligação
Estimador confirmado -> captura coerente do modelo -> decisão de período/qualidade -> Tuner.REQ.
Tuner.CNF -> autorização e retenção conjunta do modelo/alvo -> transição -> PID.
Tuner.ERR -> invalidar autorização do alvo e continuar com os ganhos ativos conforme política da aplicação.
Não conectar ERR a uma escrita de ganhos zero. Não ligar diretamente CNF ao PID contornando a transição.
A aplicação integrada, o gate de qualidade, o contador e os testes nativos continuam pendentes. Primeiro executar identificação e sintonia em observação, sem permitir alteração dos ganhos.
