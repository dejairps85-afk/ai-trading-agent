"""
llm_client.py - FINAL CORRIGIDO
Compativel com llm.py antigo e novo
"""
import os
import time
import hashlib
import re

_cache = {}

def _get_config():
    api_key = (
        os.getenv("LLM_API_KEY")
        or os.getenv("LLAMA_API_KEY")
        or os.getenv("OPENAI_API_KEY")
        or os.getenv("OPENROUTER_API_KEY")
        or os.getenv("XAI_API_KEY")
        or os.getenv("GROQ_API_KEY")
        or "sk-dummy"
    )
    base_url = os.getenv("LLM_BASE_URL", "https://openrouter.ai/api/v1")
    model = os.getenv("LLM_MODEL", "meta-llama/llama-4-maverick:free")
    # Limpa base_url se vier com espacos
    base_url = str(base_url).strip().replace("=", "")
    return api_key.strip(), base_url, model.strip()

def call_llama(prompt: str, system: str = "Voce e um assistente.", temperature: float = 0.3, use_cache: bool = True, max_tokens: int = 500):
    """Funcao principal - usada pelo llm.py"""
    try:
        from openai import OpenAI
    except ImportError:
        return '{"sentiment": "NEUTRAL", "confidence": 0.5, "summary": "openai lib nao instalada"}'

    api_key, base_url, model = _get_config()

    key_raw = f"{system}|{prompt}|{model}"
    cache_key = hashlib.md5(key_raw.encode()).hexdigest()
    now = time.time()

    if use_cache and cache_key in _cache:
        ts, resp = _cache[cache_key]
        if now - ts < 300:
            return resp

    try:
        client = OpenAI(base_url=base_url, api_key=api_key)
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt}
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        text = completion.choices[0].message.content.strip()
    except Exception as e:
        print(f"[LLM ERROR] {e} | base_url={base_url} model={model}")
        text = '{"sentiment": "NEUTRAL", "confidence": 0.5, "summary": "LLM offline fallback", "action": "HOLD", "confidence": 0.5, "time_horizon": "DAY_TRADE", "reasoning": "LLM offline, mantendo posicao"}'

    if use_cache:
        _cache[cache_key] = (now, text)
        if len(_cache) > 200:
            _cache.clear()

    return text

# Alias compatibilidade - alguns arquivos chamam chat()
def chat(system: str, user: str, temperature: float = 0.3, max_tokens: int = 500):
    return call_llama(prompt=user, system=system, temperature=temperature, max_tokens=max_tokens)
