# Fundação WIN/WDO — etapa 1

## Estado seguro

Módulo PAPER_ONLY. Não conecta à corretora, Profit, DLL, roteador de ordens ou credenciais. Nenhuma ordem real pode ser enviada por estas classes.

## Arquitetura

1. futures_lab.schema define eventos de mercado e sinais normalizados.
2. futures_lab.csv_feed reproduz CSV. Agressão e book permanecem ausentes quando não existem no arquivo; OHLCV não vira tape reading artificial.
3. futures_lab.paper simula posições compradas e vendidas, limites por instrumento, trava contra posição duplicada, quantidade máxima, taxas e slippage configuráveis.
4. Próxima etapa: validar os eventos contra exportações reais do Profit Pro/NTSL; depois criar adaptador local/socket. A IA gera sinais, mas nunca controla diretamente risco ou execução.

## CSV mínimo

Cabeçalho obrigatório: timestamp,instrument,event_type,last_price
Instrumento: WIN ou WDO; tipo: BAR, TRADE ou BOOK. Campos opcionais: volume,aggressor_buy_volume,aggressor_sell_volume,best_bid,best_ask,bid_depth,ask_depth,source.

## Risco e valor por ponto

RiskLimits.point_value deve ser informado explicitamente antes de interpretar PnL financeiro. O padrão None usa multiplicador unitário apenas para testes matemáticos e não representa o valor oficial dos contratos WIN/WDO. Taxas e slippage também devem ser configurados conforme a hipótese do teste.

## Testes

Na raiz: python -m unittest discover -s tests -v

## Limitações

CSV de candles permite replay técnico, não reconstrução fiel de agressão, fila ou profundidade do book. Não há modelo preditivo treinado nem promessa de rentabilidade. Execução real permanece desabilitada.


## Controles adicionados na etapa 2

- Entradas, stops, alvos, custos e multiplicadores rejeitam valores não finitos (NaN/infinito).
- O bloqueio de novas entradas é testado após o PnL realizado atingir a perda diária máxima configurada.
- `mark_to_market(prices)` calcula PnL não realizado e equity para as posições abertas, usando os preços fornecidos pelo replay.
- O mark-to-market é uma estimativa bruta: não desconta custos hipotéticos de encerramento e não substitui cálculo de margem.
- A trava diária usa PnL realizado acumulado nesta instância. Ainda não existe reset automático por data/sessão; isso depende de definir o fuso e o calendário operacional corretos.
- Stops/alvos simulados são acionados no primeiro preço recebido que cruza o nível e contabilizados no preço do stop/alvo. Gaps, prioridade intrabar quando stop e alvo cabem no mesmo candle, fila do book e fills parciais ainda não são modelados.


## Etapa 3 — leitura transparente de fluxo

`TapeReader` agrega agressão compradora/vendedora observada, delta, delta relativo, variação de preço e desequilíbrio de profundidade quando bid_depth/ask_depth existem. Exige uma janela mínima e dados reais de agressão; quando ausentes, retorna `INSUFFICIENT_DATA`, sem inferir tape a partir de candles.

As classes `BUY_PRESSURE` e `SELL_PRESSURE` são leituras descritivas. `POSSIBLE_BUY_ABSORPTION` e `POSSIBLE_SELL_ABSORPTION` são apenas candidatos heurísticos: agressão sem deslocamento compatível do preço não prova absorção nem identifica quem absorveu. O resultado explicitamente não é recomendação nem ordem.

A janela deve conter apenas WIN ou apenas WDO. Os eventos são ordenados por timestamp antes dos cálculos. A profundidade é agregada somente entre eventos que realmente carregam os dois lados do book.

Ainda não há parâmetros calibrados para mercado, sessão ou ativo. Os thresholds são defaults de pesquisa e precisam ser avaliados fora da amostra antes de qualquer uso operacional.


## Etapa 4 — motor de decisão determinístico

O `DecisionEngine` transforma as métricas do TapeReader em `BUY`, `SELL` ou `HOLD`, sem enviar ordens. O padrão é fail-closed: dados insuficientes, fluxo neutro, possível absorção, ausência de confirmação do preço, spread não verificável ou book contrário resultam em HOLD quando o filtro correspondente estiver ativo.

A confiança é uma transformação simples do módulo do delta_ratio, não uma probabilidade estatística calibrada. A configuração de book e spread é opcional e deve ser explicitamente habilitada. O motor não usa modelo treinado, não substitui limites de risco e não constitui recomendação de negociação.

A validação dos eventos agora rejeita valores NaN/infinito, volume/profundidade negativos, tipos de evento inválidos e timestamps inválidos. A camada continua isolada em PAPER_ONLY.


## Etapa 5 — replay histórico e métricas

`ReplayEngine` reproduz eventos cronológicos de um único instrumento por execução. Exige `ReplayConfig(point_value=...)` explícito para impedir que o multiplicador unitário seja confundido com o valor financeiro oficial. Inclui custos e slippage configuráveis, limite de perda diária reiniciado na mudança de data do timestamp, stops/alvos opcionais e encerramento opcional ao final do replay.

Relatório: quantidade de eventos/decisões/operações, taxa de acerto, PnL líquido e bruto, fator de lucro, média por operação, drawdown máximo em valor e percentual, curva de equity e lista de operações. Fator de lucro é `null` quando não há operações perdedoras, em vez de inventar infinito.

Limitações: o replay trabalha com eventos observados e não reconstrói fills, fila, latência, gaps ou ambiguidade intrabar. Stops e alvos são avaliados na sequência de preços recebida e contabilizados no nível configurado pelo broker simulado. A taxa de acerto e o PnL não provam capacidade preditiva. Antes de qualquer conclusão, é necessário validar dados reais, custos, point_value e executar separação cronológica treino/validação/teste (walk-forward), sem otimizar nos períodos de teste. Cada chamada processa um único instrumento; não há conexão com Profit, corretora, DLL ou ordens reais.


## Etapa 6 — separação cronológica de dados

`chronological_split` divide eventos em treino, validação e teste por ordem temporal, sem embaralhar. A função exige ao menos três eventos, proporções válidas, apenas WIN ou apenas WDO por chamada e timestamps com a mesma condição de fuso horário. As três partições são não vazias e disjuntas.

A divisão usa contagem de eventos, não dias de pregão. Para estudos de séries temporais, a validação e o teste devem permanecer posteriores ao treino. Não ajustar thresholds com o conjunto de teste. Esta etapa ainda não implementa otimização de parâmetros nem walk-forward com janelas móveis.

Atenção a aquecimento: as primeiras janelas de cada partição podem não ter contexto suficiente para o TapeReader. Em uma próxima camada, o histórico anterior poderá ser usado apenas como contexto de leitura, sem permitir entradas antes do início da partição avaliada. Não misturar candles com dados de agressão/book que não estejam presentes na fonte.


## Etapa 7 — walk-forward de parâmetros congelados

`walk_forward_replay` avalia blocos de teste cronológicos e não sobrepostos, usando janelas anteriores de treino e validação como histórico de contexto. Esse histórico pode aquecer o TapeReader, mas não gera operações nem entra nas métricas do bloco de teste.

**Importante:** esta etapa não ajusta nem treina parâmetros. O mesmo motor determinístico e a mesma configuração congelada são usados em todos os folds. Portanto, é uma avaliação rolling out-of-sample, não treinamento de IA nem otimização automática. A comparação inicial usa baseline flat (nenhuma posição), com PnL zero; isso é uma referência conservadora, não um benchmark sofisticado.

Cada fold reinicia o capital simulado, e o PnL agregado soma os resultados dos blocos de teste. Não interpretar essa soma como curva de capital contínua. Custos, point_value e qualidade dos dados precisam ser confirmados para cada instrumento antes de qualquer interpretação financeira. Sem eventos reais de agressão/book, o motor mantém HOLD por insuficiência de dados.


## Etapa 8 — auditoria conservadora de datasets

`audit_csv(path, expected_instrument=...)` verifica cabeçalho, preços, timestamps, ordem cronológica, duplicidades, separação WIN/WDO, fuso horário, campos de agressão e book e, quando fornecido, o prefixo do código do contrato. O relatório registra nome do arquivo e metadados declarados, mas não afirma autenticar a origem: `provenance_verified` permanece falso até haver uma cadeia verificável de origem e integridade.

A elegibilidade para replay é estrutural e não significa que o arquivo represente fielmente o mercado. Dados BAR/OHLCV podem ser úteis para replay de candles, mas nunca se tornam negócios, agressão ou book. `tape_ready` só é verdadeiro quando todas as linhas são eventos TRADE e contêm agressão compradora e vendedora. Book L1 e L2 são avaliados separadamente.

O importador não presume cabeçalhos proprietários do Profit. O CSV deve ser exportado/normalizado para o esquema documentado, ou um adaptador específico deve ser criado após receber um arquivo real de exemplo. A auditoria não baixa automaticamente dados B3 nem contorna termos de acesso. Arquivos públicos de fechamento e resumos consolidados não substituem histórico intradiário de negócios e profundidade.


### Modelo normalizado de CSV

Modelo vazio: `examples/market_events_template.csv`. Campos obrigatórios: `timestamp,instrument,event_type,last_price`. Tipos aceitos: `BAR` (barra/candle), `TRADE` (negócio individual) e `BOOK` (atualização do livro). Campos opcionais: volume, agressão compradora/vendedora, bid/ask, profundidade, fonte declarada e código do contrato.

Regras de preparação:
- Use um arquivo por instrumento e informe `WIN` ou `WDO` em todas as linhas.
- Use timestamps ISO 8601 e mantenha uma única convenção de fuso em todo o arquivo; prefira informar o offset quando conhecido.
- Não preencha agressão, bid/ask ou profundidade por estimativa.
- Para declarar Tape Reading apto, todas as linhas precisam ser eventos `TRADE` com agressão compradora e vendedora presentes. Isso ainda não autentica a fonte nem valida a metodologia de classificação do agressor.
- `contract_code` é metadado auxiliar da auditoria; confirme vencimento e rolagem do contrato antes de combinar sessões.
- O modelo é um esquema normalizado de entrada, não uma afirmação de que o Profit exporta exatamente esses nomes de colunas.

### Limites das fontes B3

A página oficial da B3 descreve o COTAHIST como série histórica de cotações em arquivo de largura fixa, com registros anuais e layout próprio. Não se deve tratá-lo como fluxo intradiário de negócios ou book. A documentação do Market Data descreve o segmento de Mercado Futuro e Câmbio e níveis L1/L2; condições de acesso, distribuição e consumo devem ser verificadas na política vigente antes de qualquer uso. Dados de fechamento e estatísticas consolidadas não substituem Times & Trades ou profundidade histórica.


## Etapa 9 — adaptador configurável de CSV do Profit Pro

O módulo `futures_lab.profit_csv` importa arquivos exportados pelo usuário por meio de `ProfitCsvMapping`. Os nomes das colunas são configurados explicitamente; **não existe presunção de que o exemplo seja o layout oficial do Profit Pro**. O perfil em `examples/profit_csv_mapping.example.json` é apenas um modelo editável.

O mapeamento suporta delimitador, separador decimal, codificação, formato de data/hora e fuso IANA explícitos. Se um fuso for informado, timestamps sem fuso recebem esse fuso; timestamps que já contêm offset são preservados. Não se faz conversão silenciosa de horário. O ativo pode vir de coluna WIN/WDO ou ser identificado pelo prefixo do código de contrato; vencimento e rolagem não são inferidos.

O importador separa BAR, TRADE e BOOK, preserva campos ausentes como `None`, não fabrica agressão nem book e aceita negócios distintos com o mesmo timestamp. Se qualquer linha falhar, a importação é invalidada e nenhum evento é liberado para replay. O relatório não autentica a origem do arquivo (`provenance_verified=false`).

Para configurar corretamente o adaptador, ainda é necessário um CSV real exportado pelo Profit Pro, preferencialmente com cabeçalho e algumas linhas anonimizadas. Até lá, os testes usam fixtures sintéticas explicitamente destinadas a testar o parser, não dados reais de mercado.
