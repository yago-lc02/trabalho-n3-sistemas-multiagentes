import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Endpoint do Gemini compatível com a API da OpenAI (dispensa o pacote google-genai)
GEMINI_OPENAI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"


def get_llm_instance(provider: str, model_name: Optional[str] = None):
    """
    Retorna a instância de LLM nativa do CrewAI (crewai.LLM) com base no provedor escolhido.
    O CrewAI 1.x não aceita mais objetos do LangChain (ChatOpenAI etc.) como `llm` do Agent.
    Suporta:
    - 'gemini' (Nuvem Google)
    - 'openai' (Nuvem OpenAI)
    - 'ollama' (Local / 100% Offline)
    - 'demo' (Mock / Cache instantâneo para workshops)
    """
    from crewai import LLM

    provider = provider.lower().strip()

    if provider == "demo":
        return None

    if provider == "ollama":
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        chosen_model = model_name or os.getenv("OLLAMA_MODEL", "llama3.2")
        logger.info(f"Conectando ao Ollama Local em {base_url} com o modelo {chosen_model}")
        return LLM(
            model=f"ollama/{chosen_model}",
            base_url=f"{base_url.rstrip('/')}/v1",
            api_key="ollama",  # Ollama local não requer chave real
            temperature=0.3,
        )

    if provider == "gemini":
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY não configurada no arquivo .env ou no painel.")
        chosen_model = model_name or os.getenv("GEMINI_MODEL_NAME", "gemini-2.5-flash")
        logger.info(f"Usando Google Gemini ({chosen_model}) via endpoint compatível com OpenAI")
        return LLM(
            model=f"openai/{chosen_model}",
            base_url=GEMINI_OPENAI_BASE_URL,
            api_key=api_key,
            temperature=0.3,
        )

    if provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY não configurada no arquivo .env ou no painel.")
        chosen_model = model_name or os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini")
        return LLM(
            model=f"openai/{chosen_model}",
            api_key=api_key,
            temperature=0.3,
        )

    raise ValueError(f"Provedor LLM desconhecido: '{provider}'. Utilize 'demo', 'ollama', 'gemini' ou 'openai'.")
