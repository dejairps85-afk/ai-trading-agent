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
