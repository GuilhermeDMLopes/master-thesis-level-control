# PID adaptativo básico: implementação

Este guia descreve a versão `PID_Basic_Adaptive` com atualização periódica executada no FORTE. O objetivo é implementar e explicar o funcionamento, sem estudo comparativo. As recomendações dos documentos antigos sobre transição de ganhos e leitura de estado pertencem aos protótipos anteriores; esses blocos não fazem parte desta aplicação.

## 1. Estrutura

| Instância | Tipo | Responsabilidade |
|---|---|---|
| Process | OBSERVER_DEMO_PROCESS | Simular o processo e fornecer a medição e os históricos de entrada e saída |
| Identifier | PROCESS_IDENTIFIER | Estimar o modelo por MMQE e calcular novos ganhos quando chegar a amostra configurada |
| Controller | PID_CONTROLLER | Calcular a ação PID, limitar a saída e receber os novos ganhos |
| SamplingClock | E_CYCLE | Solicitar uma amostra a cada 100 ms |

`Identifier` encapsula três funções: `RLS_PARAMETER_ESTIMATOR`, `TUNING_TRIGGER` e `PID_MODEL_TUNER`. O encapsulamento mantém a rede principal simples, sem esconder a separação entre identificação, decisão do instante de atualização e sintonia.

## 2. Processo e identificação

A convenção de sinais do modelo é:

$$y_k=a_1y_{k-1}+a_2y_{k-2}+b_1u_{k-1}+b_2u_{k-2}.$$

O estimador recebe a medição atual e os históricos dos comandos efetivamente aplicados. Não recebe os coeficientes verdadeiros do simulador.

Com $\varphi_k=[y_{k-1},y_{k-2},u_{k-1},u_{k-2}]^T$ e $\theta=[a_1,a_2,b_1,b_2]^T$, o MMQE utiliza:

$$\hat y_k=\varphi_k^T\hat\theta_{k-1},\qquad \varepsilon_k=y_k-\hat y_k,$$
$$L_k=\frac{P_{k-1}\varphi_k}{\lambda+\varphi_k^TP_{k-1}\varphi_k},$$
$$\hat\theta_k=\hat\theta_{k-1}+L_k\varepsilon_k,\qquad P_k=\frac{P_{k-1}-L_k\varphi_k^TP_{k-1}}{\lambda}.$$

O ensaio utiliza $\lambda=0{,}8$, $P_0=10000I$ e estimativas iniciais nulas. A identificação ocorre a cada amostra. As verificações numéricas do bloco não comprovam, por si só, que há informação suficiente para identificar o processo.

O simulador usa $a_1=1{,}2$, $a_2=-0{,}36$, $b_2=0{,}06$ e altera $b_1$ de $0{,}1$ para $0{,}4$ na amostra 151. A referência alterna entre 1 e 0,8 a cada 50 amostras. A execução termina em 400 amostras. Essa mudança é programada no simulador; os ganhos são calculados a partir do modelo estimado em malha fechada.

## 3. Por que existe a sintonia

O MMQE fornece coeficientes do processo, não ganhos de um controlador. `PID_MODEL_TUNER` transforma o modelo estimado em $K_P$, $K_I$ e $K_D$, usando também o período de amostragem e um polo desejado configurado pelo projetista.

A regra implementada procura três polos iguais a $p=0{,}7$ e calcula um quarto polo $r$. Não se deve atribuir essa regra aos artigos ou ao material de aula sem conferir suas equações: ela é a regra de sintonia implementada neste projeto.

Para reproduzir o cálculo escalar do bloco:

$$c_1=-3p,\quad c_2=3p^2,\quad c_3=-p^3,$$
$$h_0=c_1+1+a_1,\quad h_1=c_2-a_1+a_2,\quad h_2=c_3-a_2,$$
$$s_0=h_0/b_1,\quad t_0=-1/b_1,$$
$$s_1=(h_1-b_2s_0)/b_1,\quad t_1=(-c_1-b_2t_0)/b_1,$$
$$s_2=(h_2-b_2s_1)/b_1,\quad t_2=(-c_2-b_2t_1)/b_1,$$
$$r=\frac{-b_2s_2}{b_2t_2+c_3},\qquad q_i=s_i+t_ir\quad(i=0,1,2),$$
$$K_P=(q_0-q_1-3q_2)/2,\quad K_I=(q_0+q_1+q_2)/T_s,\quad K_D=T_sq_2.$$

O bloco verifica divisores, valores numéricos, ganhos não negativos, $|r|<1$ e resíduo polinomial. Uma sintonia inválida emite `ERR`. A solução de polos do modelo linear com ganhos fixos não é uma prova de estabilidade de toda a adaptação com saturação.

## 4. PID e flag de integração

A forma de cálculo do PID original foi preservada, com nomes descritivos na interface:

$$e_k=SP_k-PV_k,$$
$$I_k=\begin{cases}I_{k-1}+\frac{T_s}{2}(e_k+e_{k-1}),&\text{se a flag anterior permitir},\\I_{k-1},&\text{caso contrário},\end{cases}$$
$$v_k=K_Pe_k+K_II_k+K_D\frac{e_k-e_{k-1}}{T_s},\qquad u_k=\operatorname{clip}(v_k,0,10).$$

A flag fica falsa quando a saída não limitada excede os limites e controla a integração da próxima amostra. Na inicialização, a memória integral e o erro anterior são zero e a flag é verdadeira.

`SET_GAINS` armazena os três ganhos ativos e emite `GAINS_CNF`. Não recalcula a saída nem reinicializa a memória integral. Os parâmetros `INITIAL_*` continuam mostrando os valores de inicialização, mesmo depois da atualização.

A troca é direta: mudar $K_I$ altera o produto $K_II_k$, mesmo preservando $I_k$. Portanto esta versão não implementa compensação para garantir transferência sem salto. Não há bloco de transição gradual na aplicação básica.

## 5. Quando cada cálculo ocorre

O PID e a identificação executam a cada 0,1 s. A sintonia usa o mesmo encadeamento de eventos, mas somente nas amostras selecionadas; não precisa de outro relógio.

Configuração executada:

| Parâmetro | Valor |
|---|---:|
| ENABLE_UPDATE | TRUE |
| UPDATE_AT_SAMPLE | 275 |
| UPDATE_INTERVAL_SAMPLES | 25 |
| SAMPLE_TIME_S | 0.1 |
| DESIRED_POLE | 0.7 |

Isso produz atualizações nas amostras 275, 300, 325, 350, 375 e 400. O intervalo nominal é 2,5 s. Intervalo zero mantém uma única atualização; `ENABLE_UPDATE=FALSE` desabilita a sintonia, mantendo a identificação e o controle. A configuração do gatilho é capturada na inicialização.

A sequência de uma amostra é:

1. `SamplingClock.EO` solicita `Process.REQ`.
2. `Process.CNF` entrega medição e históricos a `Identifier.REQ`.
3. O estimador atualiza o modelo e o gatilho decide se há sintonia.
4. Em uma amostra comum, `CONTROL_READY` solicita `Controller.REQ`.
5. Em uma amostra de atualização, o sintonizador calcula os ganhos; `GAINS_READY` solicita `Controller.SET_GAINS`; somente `Controller.GAINS_CNF` solicita `Controller.REQ`.
6. `Controller.CNF` solicita `Process.APPLY`, que armazena o comando calculado.

Há um cálculo PID por amostra, inclusive quando os ganhos mudam. As associações `WITH` transportam os dados correspondentes aos eventos. A inicialização segue processo, identificador, controlador e partida do relógio. `DONE` encerra o ensaio. Os eventos de erro interrompem o relógio; isso não equivale a comandar uma saída segura em equipamento físico.

## 6. O que foi confirmado

Os 11 testes Python passaram no Windows. O monitoramento nativo enviado em 28/10/2026 mostrou:

- 400 amostras e 400 cálculos PID;
- 394 eventos `CONTROL_READY` e 6 eventos `GAINS_READY`;
- 6 eventos `SET_GAINS` e 6 confirmações `GAINS_CNF`;
- contadores de erro zerados e saída final sem saturação;
- referência 0,8, medição final aproximadamente 0,800000203 e comando aproximadamente 0,278260878;
- ganhos finais aproximadamente $K_P=0{,}155160289$, $K_I=0{,}582261347$ e $K_D=0{,}004572868$.

Essa evidência confirma a execução nativa da estrutura simples com atualizações periódicas no processo sintético. Uma captura final não mede o salto máximo durante as trocas, o jitter ou toda a trajetória. A aplicação adaptativa ainda não está validada na planta física.

## 7. Continuidade

Preservar este projeto e seu executável como ponto funcional. Para repetir o ensaio, usar a configuração acima e inicializar uma única vez; quando a ligação de partida já inicializar automaticamente, não injetar outro `INIT`. Registrar os contadores e a saída final.

A próxima mudança funcional, se o destino for a bancada, será adequar a interface de entrada e saída ao equipamento e às suas escalas. Isso depende de conhecer os sinais e limites reais; não exige adicionar novos blocos de adaptação ao ensaio atual.

Referências do próprio projeto:

- [Configuração periódica](20261027-periodic-gain-updates.md)
- [Compilação nativa periódica](20261028-periodic-native-build.md)
- [Resultado nativo periódico](20261028-periodic-native-result.md)
- [Código dos blocos](../../4diac/application/PID_Basic_Adaptive/Type%20Library/adaptive/)
- [Testes da aplicação](../../tests/test_pid_basic_adaptive.py)
