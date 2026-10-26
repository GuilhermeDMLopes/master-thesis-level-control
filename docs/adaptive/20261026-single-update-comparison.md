# Comparação: PID fixo e atualização única

## Evidência nativa enviada em 26/10/2026

As telas image(20261026-140902).png e image(20261026-141510).png mostram os modos habilitado e desabilitado, respectivamente. Ambas terminam em 400 amostras, com 400 execuções do PID e contadores de erro visíveis zerados. O primeiro modo registra uma sintonia e um SET_GAINS; o segundo registra zero. A saída final é aproximadamente 0,8 nos dois casos. Essas observações são transcrições das telas; não representam aquisição de trajetória nativa.

ACTIVE_* são saídas de fotografia do READ_STATE. Podem permanecer antigas ou zeradas sem indicar que o controlador esteja usando ganhos zero.

## Reprodução offline comparável

Executar da raiz do repositório:

```powershell
& "$env:USERPROFILE\venvs\pid-adaptativo\Scripts\python.exe" scripts/compare_pid_single_update.py --output "$env:USERPROFILE\Documents\Ensaios-PID\comparacao-single-update"
```

A pasta de saída deve ser nova. O script reutiliza o executor de rede dos testes e os FBT do arquivo validado, aplicando o sequenciador atual. Não modifica o projeto 4diac, não acessa PLC/FORTE e não coleta dados nativos. Exporta fixed.csv, single_update.csv e summary.json. Requer os arquivos de tests e scripts do repositório.

Cada CSV contém 400 linhas: amostra, tempo nominal, referência, saída, erro, comando, variação do comando e os três ganhos efetivamente usados. O tempo é k*0,1 s, não tempo medido de execução.

| Métrica offline | PID fixo | Atualização única |
|---|---:|---:|
| Integral do erro absoluto, 400 amostras | 1,5114068161 | 1,5156241529 |
| Integral do erro absoluto, amostras 275–400 | 0,1053521793 | 0,1095695161 |
| Variação total do comando (inclui partida de zero) | 3,2301883889 | 3,2296612968 |
| Variação do comando na amostra 275 | -0,0000003763 | -0,0049397008 |

IAE = soma de abs(referência - saída)*0,1. A atualização aumenta o IAE total em aproximadamente 0,28% e o IAE a partir da amostra 275 em aproximadamente 4,00%. Portanto este ensaio demonstra funcionamento da sequência e limitação do passo de ganhos, mas não superioridade de desempenho. Não ajustar parâmetros apenas para obter um resultado favorável.

A atualização ocorre antes do cálculo do PID na amostra 275; o ensaio manual anterior pausava após esse cálculo. A mudança total do comando inclui a evolução normal do PID e não é igual à previsão isolada do efeito dos ganhos.

## Validação e próximo passo

Os sete testes de test_pid_single_update.py passaram em 26/10/2026. Os dois replays concluíram 400 amostras, com zero e uma atualização, respectivamente. CSVs foram gerados e os valores finais coincidem, à precisão exibida, com as telas nativas. Essa coincidência não substitui captura das trajetórias no FORTE.

Manter os blocos e ganhos atuais. Antes de habilitar adaptação repetida, decidir e implementar aquisição sincronizada de cada amostra no FORTE; leitura periódica não sincronizada da monitoração pode perder amostras. A coleta nativa ainda não foi implementada nesta etapa. Não é necessário repetir os ensaios por captura de tela.
