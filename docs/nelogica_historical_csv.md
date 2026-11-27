# Nelogica historical CSV ingestion

Official references:
- https://ajuda.nelogica.com.br/hc/pt-br/articles/11169423343515
- https://ajuda.nelogica.com.br/hc/pt-br/articles/11169188636443
- https://ajuda.nelogica.com.br/hc/pt-br/articles/360044287672
- https://ajuda.nelogica.com.br/hc/pt-br/articles/11973319153563

Separate quantity (contracts) from monetary turnover and trade count. Preserve original ticker, date/time, adjustment and series metadata. Continuous adjusted series are not executable contracts. Daily and intraday candles cannot establish aggression or book depth. Tick data must preserve trade number and distinguish unknown aggression from zero; DLL trade types 2 and 3 represent buy and sell aggression only, not all trades. Do not assume CSV aggression uses the DLL enum without a verified sample. Require explicit delimiter, decimal convention, timestamp format and timezone. Do not publish licensed raw datasets in GitHub. Historical CSV samples have not yet been acquired; exact header spelling and encoding remain unverified. PAPER_ONLY.
