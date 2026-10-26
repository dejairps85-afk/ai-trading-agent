 """
llm_client.py - Corrigido para Render
Não cria cliente no import, só quando chamar
"""
import os
import time
import hashlib

_cache = {}

def _get_config():
    # Aceita qualquer nome de variável pra não dar erro
    api_key = (
        os.getenv("LLM_API_KEY")
        or os.getenv("LLAMA_API_KEY")
        or os.getenv("OPENAI_API_KEY")
        or os.getenv("OPENROUTER_API_KEY")
        or "sk-dummy-key-for-init"  # dummy pra não crashar no init
    )
    base_url = os.getenv("LLM_BASE_URL", "https://openrouter.ai/api/v1")
    model = os.getenv("LLM_MODEL", "meta-llama/llama-4-maverick:free")
    return api_key, base_url, model

def call_llama(prompt: str, system: str = "Você é um analista.", temperature: float = 0.3, use_cache: bool = True):
    # Importa SÓ AQUI, lazy
    from openai import OpenAI

    api_key, base_url, model = _get_config()

    # Cache simples
    key_raw = f"{system}|{prompt}|{model}"
    cache_key = hashlib.md5(key_raw.encode()).hexdigest()
    now = time.time()

    if use_cache and cache_key in _cache:
        ts, resp = _cache[cache_key]
        if now - ts < 300:
            return resp

    client = OpenAI(base_url=base_url, api_key=api_key)

    try:
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt}
            ],
            temperature=temperature,
            max_tokens=500,
        )
        text = completion.choices[0].message.content.strip()
    except Exception as e:
        print(f"[LLM ERROR] {e}")
        # Fallback pra não derrubar o bot
        return '{"sentiment": "NEUTRAL", "confidence": 0.5, "summary": "fallback", "action": "HOLD", "reasoning": "LLM offline"}'

    if use_cache:
        _cache[cache_key] = (now, text)

    return text
