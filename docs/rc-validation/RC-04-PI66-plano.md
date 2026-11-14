# RC-04 — PI fixo 6/6 no FORTE
Status: PREPARADO, não executado no PLC nesta revisão.
Kp=6, Ki=6, Kd=0, solicitados pelo operador a pedido dos orientadores.
Este teste substitui a proposta preliminar de P puro. Não habilita Identifier/Tuning.

## Evidência recebida RC-03
ZIP original enviado pelo operador e analisado. Apenas rc03_degrau.py foi incorporado em results/rc-validation/20261114-120332. A publicação dos arquivos brutos amostras.csv e resumo.json foi bloqueada pela revisão automática de autorização de compartilhamento externo; os arquivos continuam disponíveis no computador do operador e no anexo do chat.
SHA256 dos bytes originais antes da normalização textual pela API Git:
- rc03_degrau.py: 957da4adeb32475f7c03f6572d917ba9ba52de774a5b33b9de72c7e876b59c69
- amostras.csv: c6a2c3267e053fabac252088e456039adb124dad5a4183829446f02a91a376d8
- resumo.json: 4d7d0c22f873f2e9e082725f5a8c808065fb9132b026e880060490688992549a
CSV: 213 linhas, 71 por fase. Resumo confirma retorno. Escritas solicitadas em t=0.002773700, 8.017082900 e 16.022425600 s, valores 1,2,1.
Ajuste exploratório por mínimos quadrados: y(t)=y_inf+(y0-y_inf)*exp(-max(t-L,0)/tau), tempos relativos à solicitação de escrita no PC; y0 é primeira leitura da fase.
Limites: y_inf alvo +/-0.1; tau 0.1..5 s; L 0..0.5 s.
Subida: y_inf=1.99979061, tau=1.23409131 s, L=0.11028144 s, RMSE=0.00722710.
Descida: y_inf=1.00764270, tau=1.23018003 s, L=0.10823492 s, RMSE=0.00771477.
Valores aparentes incluem ciclo PLC, comunicação e aquisição no PC; não equivalem a uma medida independente de R*C nem provam identificação exata de G(s)=1/(s+1).

## Implementação RC-04
Script scripts/rc-validation/rc04_pi66.py reutiliza observar.py e forte_local.py do pacote RC-02 já executado no computador do operador.
A sintaxe foi conferida; a execução nativa e o desempenho temporal RC-04 estão pendentes.
Instância própria FORTE em 127.0.0.1:61525; recurso RC_OBS, FB Controller PID_TANK_CONTROLLER. Não altera o projeto visual existente no IDE.
Hash de runtime exigido: 65fc443f19963b845192fe72c6dd148dfbdc89efbe5f957f2ac05c10894b48fc (consultar script para valor autoritativo completo).
PI com saída direta 0..2, sem bias do tanque. Manual=1 inicialmente para estabelecer a condição de transferência antes de entrar em automático.
Período nominal 0.2 s. Aborta se dt entre leituras ficar fora de 0.15..0.25 s ou cálculo/transporte FORTE exceder 0.2 s. Isso não certifica tempo real.
Preparo a 1 por 8 s; 120 ciclos PI: 20 ciclos SP1, 50 ciclos SP1.25, 50 ciclos SP1; retorno final em malha aberta a1 e observação por8s.
Escrita OPC UA pelo Python; cálculo P/I no FORTE. UaExpert somente leitura de ACAO_CONTROLE e ADC_R, evitando outro escritor.
Restaurar a1 é tentativa em finally, não watchdog físico: falha de rede/processo pode exigir intervenção local.
CSV inclui referência, PV, comando lido/solicitado, P,I,erro e saturação. Resumo inclui resultado e confirmação do retorno. COLETA_CONCLUIDA não aprova automaticamente desempenho.
A referência não é uma variável publicada no PLC RC atual; aparece no CSV/terminal. O controle integrado não foi ainda aprovado.
