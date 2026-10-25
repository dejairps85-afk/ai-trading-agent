"""
Configurações centrais do AI Trading Agent
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data_store"
DATA_DIR.mkdir(exist_ok=True)

# Capital e risco
INITIAL_CAPITAL = float(os.getenv("INITIAL_CAPITAL", "10000"))
RISK_PER_TRADE = float(os.getenv("RISK_PER_TRADE", "0.02"))  # 2% do capital por trade
MAX_POSITIONS = int(os.getenv("MAX_POSITIONS", "3"))
PAPER_TRADING = os.getenv("PAPER_TRADING", "true").lower() == "true"

# Ticker padrão
DEFAULT_TICKER = os.getenv("DEFAULT_TICKER", "BTC-USD")

# LLM
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "xai").lower()
LLM_MODEL = os.getenv("LLM_MODEL", "grok-4")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "")

# Mapeamento de providers para base_url e chave
PROVIDER_CONFIG = {
    "xai": {
        "base_url": "https://api.x.ai/v1",
        "api_key_env": "XAI_API_KEY",
    },
    "openai": {
        "base_url": "https://api.openai.com/v1",
        "api_key_env": "OPENAI_API_KEY",
    },
    "deepseek": {
        "base_url": "https://api.deepseek.com/v1",
        "api_key_env": "DEEPSEEK_API_KEY",
    },
    "google": {
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "api_key_env": "GOOGLE_API_KEY",
    },
    "anthropic": {
        "base_url": "https://api.anthropic.com/v1/",
        "api_key_env": "ANTHROPIC_API_KEY",
    },
    "openai_compatible": {
        "base_url": LLM_BASE_URL or "http://localhost:11434/v1",
        "api_key_env": "OPENAI_COMPATIBLE_API_KEY",
    },
}

def get_llm_config():
    cfg = PROVIDER_CONFIG.get(LLM_PROVIDER, PROVIDER_CONFIG["xai"])
    api_key = os.getenv(cfg["api_key_env"], "")
    if not api_key and LLM_PROVIDER != "openai_compatible":
        raise ValueError(
            f"Chave de API não encontrada. Defina {cfg['api_key_env']} no arquivo .env"
        )
    return {
        "base_url": cfg["base_url"],
        "api_key": api_key or "ollama",
        "model": LLM_MODEL,
        "provider": LLM_PROVIDER,
    }

# Telegram (opcional)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
