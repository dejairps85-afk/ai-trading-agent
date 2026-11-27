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
