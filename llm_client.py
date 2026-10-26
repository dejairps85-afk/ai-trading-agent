"""
llm_client.py - Cliente centralizado para Llama API gratuita
Suporta: Meta Llama API oficial, OpenRouter (free), Groq
"""
import os
import time
from functools import lru_cache
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("LLM_BASE_URL", "https://openrouter.ai/api/v1")
API_KEY = os.getenv("LLM_API_KEY") or os.getenv("LLAMA_API_KEY")
MODEL = os.getenv("LLM_MODEL", "meta-llama/llama-4-maverick:free")

if not API_KEY:
    print("⚠️ LLM_API_KEY não configurado - usando fallback")

_client = None

def get_client():
    global _client
    if _client is None:
        _client = OpenAI(
            base_url=BASE_URL,
            api_key=API_KEY or "dummy",
        )
    return _client

# Cache simples em memória com TTL
_cache = {}

def cached_call(key: str, ttl_seconds: int = 300):
    """Decorator para cache com TTL"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            now = time.time()
            # Limpa expirados
            expired = [k for k, (v, t) in _cache.items() if now - t > ttl_seconds]
            for k in expired:
                del _cache[k]
            
            cache_key = f"{key}:{args}:{kwargs}"
            if cache_key in _cache:
                value, ts = _cache[cache_key]
                if now - ts < ttl_seconds:
                    return value
            
            result = func(*args, **kwargs)
            _cache[cache_key] = (result, now)
            return result
        return wrapper
    return decorator

def chat(system: str, user: str, temperature: float = 0.3, max_tokens: int = 800) -> str:
    """Chamada única ao LLM"""
    try:
        client = get_client()
        resp = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        print(f"LLM Error: {e}")
        # Fallback para não quebrar o bot
        return f"ERRO_LLM: {str(e)[:100]}"
