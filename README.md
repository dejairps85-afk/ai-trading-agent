# AI Trading Agent — Celular (iPhone + Android)

Agente multi-IA de trading **pronto para o celular**.

Duas formas de usar no celular:

1. **Telegram** (recomendado) → funciona perfeitamente no iPhone e Android  
2. **Web mobile** → abre no Safari do iPhone / Chrome do Android

---

## O que tem de novo

- ✅ Comando `/close TICKER` e `/close all`
- ✅ Suporte a **Mini Índice (WIN)** e **Mini Dólar (WDO)** da B3 (via proxies)
- ✅ Ações brasileiras (`PETR4.SA`, `VALE3.SA`...)
- ✅ Versão web mobile-friendly para iPhone
- ✅ Paper trading completo

---

## 1. Versão Telegram (melhor para iPhone e Android)

### Criar o bot
1. Telegram → **@BotFather** → `/newbot`
2. Copie o token

### Configurar
```bash
unzip ai-trading-agent.zip
cd ai-trading-agent
python -m venv .venv
source .venv/bin/activate          # ou .venv\Scripts\activate no Windows
pip install -r requirements.txt
cp .env.example .env
```

Edite o `.env`:
```env
XAI_API_KEY=sua_chave
LLM_PROVIDER=xai
LLM_MODEL=grok-4

TELEGRAM_BOT_TOKEN=token_do_BotFather
TELEGRAM_CHAT_ID=seu_chat_id        # opcional (recomendado)
```

### Rodar
```bash
python bot.py
```

### Comandos no celular

| Comando | Função |
|---------|--------|
| `/analyze BTC-USD` | Crypto |
| `/analyze PETR4.SA` | Ação brasileira |
| `/analyze WIN` | Mini Índice (proxy BOVA11) |
| `/analyze WDO` | Mini Dólar (proxy USD/BRL) |
| `/status` | Portfólio paper |
| `/trade WIN` | Paper buy se aprovado |
| `/close WIN` | Fecha a posição |
| `/close all` | Fecha todas as posições |

---

## 2. Versão Web (Safari do iPhone)

Ideal se você não quiser usar Telegram.

```bash
python web.py
```

No iPhone (mesmo Wi-Fi do computador):
1. Descubra o IP do PC (`ipconfig` ou `ifconfig`)
2. Abra o Safari: `http://IP_DO_PC:5000`
3. Adicione à Tela de Início (compartilhar → Adicionar à Tela de Início) para parecer um app

---

## Tickers brasileiros suportados

| Você digita | O que é usado | Observação |
|-------------|---------------|------------|
| `WIN` ou `MINI_INDICE` | BOVA11.SA | Proxy do Mini Índice |
| `WDO` ou `MINI_DOLAR` | USDBRL=X | Proxy do Mini Dólar |
| `PETR4` ou `PETR4.SA` | PETR4.SA | Ação real |
| `VALE3` | VALE3.SA | Ação real |
| `IBOV` | ^BVSP | Índice Ibovespa |

> **Importante:** WIN e WDO reais são contratos futuros da B3. O Yahoo Finance não oferece a série contínua oficial de graça. Por isso usamos os melhores *proxies* públicos disponíveis. Serve para estudo e paper trading, não para execução real de futuros.

---

## Onde deixar o bot rodando 24h

| Local | Custo | Observação |
|-------|-------|------------|
| Seu PC | Grátis | Mais fácil |
| Railway / Render | Grátis | 24h online |
| Termux (Android) | Grátis | Tudo no celular |
| VPS | ~R$15/mês | Mais estável |

**iPhone:** o bot Telegram já funciona nativamente. A versão web também abre no Safari.

---

## Estrutura

```
ai-trading-agent/
├── bot.py          ← Telegram (iPhone/Android)
├── web.py          ← Versão web mobile (Safari iPhone)
├── main.py         ← Terminal
├── agents/         ← Técnico, Sentimento, Risco, Trader
├── data/fetcher.py ← Yahoo + aliases BR (WIN/WDO)
├── portfolio/      ← Paper trading + /close
└── ...
```

---

## Avisos

- Paper trading por padrão (nenhum dinheiro real)
- WIN e WDO são **proxies** (não os contratos oficiais da B3)
- LLM pode errar — use por conta e risco
- Não é consultoria financeira

Boa sorte e trade com responsabilidade.
