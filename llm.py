"""
llm.py - WRAPPER de compatibilidade
Seu technical.py importa "from llm import llm"
Esse arquivo faz ponte para o novo llm_client.py
"""
import json
from llm_client import call_llama

class LLMClient:
    def __init__(self):
        # Não exige mais chave no __init__, só quando chamar
        pass
    
    def chat(self, prompt: str, system: str = "Você é um assistente.", temperature: float = 0.3):
        return call_llama(prompt, system=system, temperature=temperature)
    
    def generate(self, prompt: str, system: str = "Você é um assistente."):
        return call_llama(prompt, system=system)
    
    def structured_decision(self, system: str, prompt: str):
        """Retorna JSON como dict; resposta inválida bloqueia a operação."""
        raw = self.chat(prompt=prompt, system=system, temperature=0.1)
        cleaned = raw.replace("```json", "").replace("```", "").strip()
        try:
            result = json.loads(cleaned)
            if not isinstance(result, dict):
                raise ValueError("A resposta JSON precisa ser um objeto")
            return result
        except (json.JSONDecodeError, ValueError, TypeError):
            return {
                "approved": False,
                "position_size_pct": 0.0,
                "stop_loss_pct": 0.0,
                "take_profit_pct": 0.0,
                "confidence": 0.0,
                "max_risk_reason": "Resposta da IA inválida; operação bloqueada.",
                "summary": "Falha ao interpretar a resposta estruturada. Mantendo HOLD.",
            }

    # Compatibilidade com chamadas antigas tipo llm(prompt)
    def __call__(self, prompt: str, system: str = "Você é um assistente."):
        return call_llama(prompt, system=system)

# Instância global que seu technical.py espera
llm = LLMClient()
