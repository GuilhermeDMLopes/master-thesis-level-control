# Comparação nativa concluída — 26/10/2026

Processo sintético no FORTE/Windows, Ts nominal 0,1 s. Não é ensaio da planta física.
Executável: runs/20261026-113527-390/build/src/Debug/forte.exe.
SHA256: 96B7E0C5ED983DE22046A866708A6A533D55BB50BC902044CA56F70CB49C5281.
Instrumentação: commit a79789f; coleta após cálculo válido do PID, antes do CNF.

## Evidências

CSVs originais recebidos estão em [evidence/20261026-native-comparison](evidence/20261026-native-comparison/). As telas finais enviadas (144439 e 144832) mostram 400 ciclos, zero e uma atualização respectivamente, e contadores de erro visíveis zerados. CSV mede comando calculado; a confirmação de aplicação vem dos contadores do processo na tela.

Ambos os arquivos têm 400 registros finitos, sequenciais de 1 a 400. Referência, saída, comando e três ganhos coincidem numericamente, após leitura como float, com os respectivos CSVs offline em todas as linhas. Tempos de relógio não são comparados com o tempo nominal offline.

Os modos são idênticos até a amostra 274. Uma única troca de ganhos ocorre na amostra 275: KP=0,4504609945115689; KI=1,6091098779067279; KD=0,01637095129722356.

| Métrica | Fixo | Atualização única |
|---|---:|---:|
| IAE nominal, 1–400 | 1,511406816099983 | 1,5156241529442906 |
| IAE nominal, 275–400 | 0,1053521792769796 | 0,10956951612128739 |
| Saída final | 0,8000000008429803 | 0,8000000012113838 |
| Intervalo mínimo entre registros, ms | 94,0424 | 86,5470 |
| Intervalo médio entre registros, ms | 99,9829 | 99,9806 |
| Intervalo máximo entre registros, ms | 115,9961 | 113,9749 |

IAE usa soma abs(SP-PV)*0,1, para comparação do modelo discreto. Não usa intervalos de disco como período do modelo. A instrumentação síncrona acrescenta latência e não estabelece garantia de tempo real.

## Conclusão e limite

A execução nativa reproduz a trajetória offline deste cenário. A atualização é funcional, mas aumenta o IAE total em cerca de 0,28% (4,00% no trecho 275–400). A troca ocorre perto do equilíbrio e reduz o comando de aproximadamente 0,278265 para 0,273326, produzindo pequena perturbação. A limitação de passo não é uma transferência sem salto.

Etapa encerrada: identificação em malha fechada, sintonia e uma atualização automática encadeada por eventos, com captura nativa. Não demonstra superioridade do controlador, adaptação contínua, estabilidade geral ou validação física. Não é necessário repetir estes dois ensaios.

Próximo trabalho proposto: avaliar offline compensação da memória integral na troca de ganhos, antes de qualquer alteração nativa ou atualização repetida. Deve preservar a flag, limites e coerência dos estados, e distinguir salto devido aos ganhos da evolução normal de cada amostra. Nenhuma nova lei foi aplicada nesta etapa.
