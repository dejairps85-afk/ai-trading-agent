"""
llm.py - WRAPPER de compatibilidade
Seu technical.py importa "from llm import llm"
Esse arquivo faz ponte para o novo llm_client.py
"""
from llm_client import call_llama

class LLMClient:
    def __init__(self):
        # Não exige mais chave no __init__, só quando chamar
        pass
    
    def chat(self, prompt: str, system: str = "Você é um assistente.", temperature: float = 0.3):
        return call_llama(prompt, system=system, temperature=temperature)
    
    def generate(self, prompt: str, system: str = "Você é um assistente."):
        return call_llama(prompt, system=system)
    
    # Compatibilidade com chamadas antigas tipo llm(prompt)
    def __call__(self, prompt: str, system: str = "Você é um assistente."):
        return call_llama(prompt, system=system)

# Instância global que seu technical.py espera
llm = LLMClient()
