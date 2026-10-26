"""
config.py - CORRIGIDO
Aceita qualquer provedor gratuito, não exige XAI_API_KEY
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Telegram
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
DEFAULT_TICKER = os.getenv("DEFAULT_TICKER", "BTC-USD")
PAPER_TRADING = os.getenv("PAPER_TRADING", "true").lower() == "true"

# LLM - aceita vários nomes pra não quebrar
def get_llm_config():
    api_key = (
        os.getenv("LLM_API_KEY")
        or os.getenv("LLAMA_API_KEY")
        or os.getenv("OPENAI_API_KEY")
        or os.getenv("OPENROUTER_API_KEY")
        or os.getenv("XAI_API_KEY")  # compatibilidade com seu antigo
        or os.getenv("GROQ_API_KEY")
        or "sk-dummy"
    )
    
    base_url = os.getenv("LLM_BASE_URL", "https://openrouter.ai/api/v1")
    model = os.getenv("LLM_MODEL", "meta-llama/llama-4-maverick:free")
    
    return {
        "api_key": api_key,
        "api_key_env": "LLM_API_KEY",
        "base_url": base_url,
        "model": model,
    }

# Para compatibilidade com código antigo que espera XAI
XAI_API_KEY = os.getenv("XAI_API_KEY") or os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY")
