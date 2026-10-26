import os
import time
import hashlib
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    base_url=os.getenv("LLM_BASE_URL", "https://api.llama.com/compat/v1"),
    api_key=os.getenv("LLM_API_KEY"),
)

MODEL = os.getenv("LLM_MODEL", "Llama-4-Maverick-17B-128E-Instruct-FP8")

# Cache simples em memória com TTL
_cache = {}
CACHE_TTL = int(os.getenv("LLM_CACHE_TTL", "300"))  # 5 min padrão

def _cache_key(prompt: str, system: str):
    h = hashlib.md5(f"{system}|{prompt}|{MODEL}".encode()).hexdigest()
    return h

def call_llama(prompt: str, system: str = "Você é um analista de trading.", temperature: float = 0.3, use_cache: bool = True):
    key = _cache_key(prompt, system)
    now = time.time()

    if use_cache and key in _cache:
        ts, resp = _cache[key]
        if now - ts < CACHE_TTL:
            return resp

    completion = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt}
        ],
        temperature=temperature,
        max_tokens=600,
    )
    text = completion.choices[0].message.content.strip()

    if use_cache:
        _cache[key] = (now, text)
        # limpa cache velho
        if len(_cache) > 200:
            _cache.clear()

    return text
