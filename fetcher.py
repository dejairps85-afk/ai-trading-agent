"""
Busca de dados de mercado via Yahoo Finance (gratuito)
Suporta ações, crypto, ETFs e proxies para Mini Índice / Mini Dólar (B3).
"""
import yfinance as yf
import pandas as pd
from typing import Dict, Any
import ta

# Mapeamento de aliases brasileiros → ticker Yahoo Finance
# Mini Índice e Mini Dólar não têm série contínua perfeita no Yahoo.
# Usamos os melhores proxies disponíveis gratuitamente.
TICKER_ALIASES = {
    # Mini Índice (WIN) → proxy Ibovespa / ETF
    "WIN": "BOVA11.SA",
    "MINI_INDICE": "BOVA11.SA",
    "MINIINDICE": "BOVA11.SA",
    "WIN$": "BOVA11.SA",
    "INDICE": "BOVA11.SA",
    "IBOV": "^BVSP",
    "IBOVESPA": "^BVSP",
    # Mini Dólar (WDO) → proxy dólar
    "WDO": "USDBRL=X",
    "MINI_DOLAR": "USDBRL=X",
    "MINIDOLAR": "USDBRL=X",
    "DOLAR": "USDBRL=X",
    "USD": "USDBRL=X",
    "DOL": "USDBRL=X",
    # Ações BR comuns (já funcionam, mas aliases ajudam)
    "PETR4": "PETR4.SA",
    "VALE3": "VALE3.SA",
    "ITUB4": "ITUB4.SA",
    "BBDC4": "BBDC4.SA",
    "BBAS3": "BBAS3.SA",
    "ABEV3": "ABEV3.SA",
    "WEGE3": "WEGE3.SA",
    "RENT3": "RENT3.SA",
    "B3SA3": "B3SA3.SA",
    "SUZB3": "SUZB3.SA",
}


def normalize_ticker(ticker: str) -> str:
    """Converte aliases amigáveis para o ticker real do Yahoo."""
    t = ticker.upper().strip()
    return TICKER_ALIASES.get(t, t)


def fetch_ohlcv(
    ticker: str,
    period: str = "6mo",
    interval: str = "1d",
) -> pd.DataFrame:
    """Baixa OHLCV e calcula indicadores técnicos básicos."""
    real_ticker = normalize_ticker(ticker)
    try:
        data = yf.download(
            real_ticker,
            period=period,
            interval=interval,
            progress=False,
            auto_adjust=True,
        )
        if data.empty:
            raise ValueError(f"Nenhum dado encontrado para {ticker} ({real_ticker})")

        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)

        data = data.dropna()
        return data
    except Exception as e:
        raise RuntimeError(f"Erro ao baixar dados de {ticker}: {e}")


def add_technical_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Adiciona indicadores técnicos comuns."""
    df = df.copy()

    df["SMA_20"] = ta.trend.sma_indicator(df["Close"], window=20)
    df["SMA_50"] = ta.trend.sma_indicator(df["Close"], window=50)
    df["EMA_12"] = ta.trend.ema_indicator(df["Close"], window=12)
    df["EMA_26"] = ta.trend.ema_indicator(df["Close"], window=26)

    macd = ta.trend.MACD(df["Close"])
    df["MACD"] = macd.macd()
    df["MACD_signal"] = macd.macd_signal()
    df["MACD_hist"] = macd.macd_diff()

    df["RSI"] = ta.momentum.rsi(df["Close"], window=14)

    bb = ta.volatility.BollingerBands(df["Close"], window=20, window_dev=2)
    df["BB_upper"] = bb.bollinger_hband()
    df["BB_middle"] = bb.bollinger_mavg()
    df["BB_lower"] = bb.bollinger_lband()

    df["ATR"] = ta.volatility.average_true_range(
        df["High"], df["Low"], df["Close"], window=14
    )

    df["Volume_SMA"] = df["Volume"].rolling(20).mean()

    return df.dropna()


def get_market_snapshot(ticker: str) -> Dict[str, Any]:
    """Retorna um snapshot completo e legível do ativo."""
    real_ticker = normalize_ticker(ticker)
    df = fetch_ohlcv(ticker, period="6mo")
    df = add_technical_indicators(df)

    last = df.iloc[-1]
    prev = df.iloc[-2]

    trend = "NEUTRA"
    if last["Close"] > last["SMA_50"] and last["SMA_20"] > last["SMA_50"]:
        trend = "ALTA"
    elif last["Close"] < last["SMA_50"] and last["SMA_20"] < last["SMA_50"]:
        trend = "BAIXA"

    rsi = float(last["RSI"])
    rsi_status = "NEUTRO"
    if rsi > 70:
        rsi_status = "SOBRECOMPRADO"
    elif rsi < 30:
        rsi_status = "SOBREVENDIDO"

    # Nota especial para proxies de futuros BR
    note = ""
    if real_ticker != ticker.upper():
        if real_ticker in ("BOVA11.SA", "^BVSP"):
            note = " (proxy Mini Índice via ETF/Ibovespa – não é o contrato WIN real)"
        elif real_ticker == "USDBRL=X":
            note = " (proxy Mini Dólar via USD/BRL – não é o contrato WDO real)"

    snapshot = {
        "ticker": ticker.upper(),
        "real_ticker": real_ticker,
        "note": note,
        "price": float(last["Close"]),
        "change_1d_pct": float((last["Close"] / prev["Close"] - 1) * 100),
        "volume": float(last["Volume"]),
        "volume_avg_20": float(last["Volume_SMA"]) if pd.notna(last["Volume_SMA"]) else 0.0,
        "sma_20": float(last["SMA_20"]),
        "sma_50": float(last["SMA_50"]),
        "rsi": rsi,
        "rsi_status": rsi_status,
        "macd": float(last["MACD"]),
        "macd_signal": float(last["MACD_signal"]),
        "macd_hist": float(last["MACD_hist"]),
        "bb_upper": float(last["BB_upper"]),
        "bb_lower": float(last["BB_lower"]),
        "atr": float(last["ATR"]),
        "trend": trend,
        "last_date": str(df.index[-1].date()),
        "history_summary": {
            "high_6m": float(df["High"].max()),
            "low_6m": float(df["Low"].min()),
            "return_6m_pct": float((last["Close"] / df["Close"].iloc[0] - 1) * 100),
        },
    }
    return snapshot


def get_info(ticker: str) -> Dict[str, Any]:
    """Informações básicas do ativo."""
    real_ticker = normalize_ticker(ticker)
    try:
        t = yf.Ticker(real_ticker)
        info = t.info
        name = info.get("shortName") or info.get("longName") or ticker
        # Nomes amigáveis para proxies
        if ticker.upper() in ("WIN", "MINI_INDICE", "MINIINDICE"):
            name = "Mini Índice (proxy BOVA11 / Ibovespa)"
        elif ticker.upper() in ("WDO", "MINI_DOLAR", "MINIDOLAR", "DOLAR"):
            name = "Mini Dólar (proxy USD/BRL)"
        return {
            "name": name,
            "sector": info.get("sector"),
            "industry": info.get("industry"),
            "market_cap": info.get("marketCap"),
            "currency": info.get("currency"),
            "exchange": info.get("exchange"),
            "summary": (info.get("longBusinessSummary") or "")[:400],
        }
    except Exception:
        return {"name": ticker, "summary": ""}
