# Projeto mapeado recebido após os ensaios de identificação

Recebido em 19/10/2026: Adaptive_Identification-validado-20261019-201401.zip.

[ZIP original](archives/Adaptive_Identification-validado-20261019-201401.zip)

SHA256: 651709bf11e34b5398a2a0895091886d399796b0e86a6dc4e34df6c7a8e1768b

## Conferência

Os 12 arquivos XML do pacote foram lidos com sucesso: .project, sistema .sys, cinco tipos adaptativos e cinco tipos de suporte. Isso é uma verificação de integridade/sintaxe XML, não certificação da norma.

O sistema contém a aplicação Identification_Offline e os mapeamentos:
- SamplingClock -> LocalIdentification.EMB_RES.SamplingClock;
- IdentificationTest -> LocalIdentification.EMB_RES.IdentificationTest.

Gerência: localhost:61499. Relógio: T#100ms.
As quatro ligações de eventos estão presentes tanto na aplicação quanto no recurso: INITO->START; EO->REQ; DONE->STOP; ERR->STOP.
A partida do experimento continua manual por INIT.

## Configuração persistida

Na aplicação e no recurso: ENABLE_PROCESS_CHANGE=FALSE; FORGETTING_FACTOR=1.0; INITIAL_COVARIANCE=10000.0.
Portanto, o arquivo salvo corresponde ao primeiro ensaio. As alterações online para TRUE/0.8/0.6 estão documentadas nas capturas, mas não foram persistidas neste .sys. Isso não invalida os resultados registrados.

O comentário raiz ainda diz "native export and runtime validation pending"; é um comentário histórico desatualizado, mantido no arquivo original para preservar a evidência. Os quatro estados finais nativos já estão [documentados](20261019-native-identification-summary.md).

O ZIP não contém os C++/headers exportados, o executável FORTE ou os logs do build. Sua preservação cobre o projeto IDE mapeado; não representa sozinho um pacote completo de reprodução binária.

O arquivo .sys também está disponível para leitura em [snapshot](snapshots/20261019-201401/Adaptive_Identification.sys). O projeto de trabalho canônico não foi sobrescrito nesta etapa.
