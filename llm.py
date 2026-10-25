"""
Cliente LLM unificado (OpenAI-compatible)
Funciona com xAI, OpenAI, DeepSeek, Gemini, Ollama, etc.
"""
from openai import OpenAI
from config import get_llm_config
from typing import Optional, List, Dict, Any
import json


class LLMClient:
    def __init__(self):
        cfg = get_llm_config()
        self.client = OpenAI(
            api_key=cfg["api_key"],
            base_url=cfg["base_url"],
        )
        self.model = cfg["model"]
        self.provider = cfg["provider"]

    def chat(
        self,
        system: str,
        user: str,
        temperature: float = 0.3,
        max_tokens: int = 1500,
        json_mode: bool = False,
    ) -> str:
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]
        kwargs: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        try:
            response = self.client.chat.completions.create(**kwargs)
            return response.choices[0].message.content or ""
        except Exception as e:
            return f"[ERRO LLM] {type(e).__name__}: {str(e)}"

    def structured_decision(self, system: str, user: str) -> Dict[str, Any]:
        """Pede resposta em JSON e tenta parsear."""
        raw = self.chat(system, user, temperature=0.2, json_mode=True)
        try:
            # Limpa possíveis markdown
            cleaned = raw.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("```")[1]
                if cleaned.startswith("json"):
                    cleaned = cleaned[4:]
            return json.loads(cleaned)
        except Exception:
            return {
                "action": "HOLD",
                "confidence": 0.0,
                "reasoning": raw[:500],
                "error": "Falha ao parsear JSON",
            }


# Instância global
llm = LLMClient()
