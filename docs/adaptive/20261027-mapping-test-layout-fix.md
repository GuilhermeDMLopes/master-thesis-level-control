# Correção do teste de mapeamento

O teste comparava todos os atributos XML dos blocos, incluindo x/y. O usuário reorganizou legitimamente os blocos na aplicação e no recurso, causando uma falha de apresentação sem evidência de alteração do controle.

A comparação passa a usar nomes, tipos e parâmetros, desconsiderando posições, comentários e ordem XML. As conexões continuam verificadas por origem/destino. São permitidas no recurso as ligações locais START.COLD/WARM → Process.INIT e START.STOP → SamplingClock.STOP; demais ligações adicionais são rejeitadas. O tipo START, se explicitamente declarado, deve ser E_RESTART.

Um teste de regressão move e reordena elementos, verifica aceitação e depois altera tipo, parâmetro e remove ligação, verificando rejeição de cada alteração. Onze testes aprovados localmente. Nenhum .sys, FBT ou algoritmo foi modificado nesta correção. A verificação no arquivo local do usuário ainda depende da nova execução dos testes.
