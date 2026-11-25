import os
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

# Endpoint do Gemini compatível com a API da OpenAI (dispensa o pacote google-genai)
GEMINI_OPENAI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"


def get_gemini_keys() -> List[str]:
    """
    Lê as chaves do Gemini do .env. Aceita uma ou várias, separadas por vírgula:
        GEMINI_API_KEY=chave1, chave2, chave3   (ou GEMINI_API_KEYS=...)
    Quando a cota de uma chave acaba, o sistema passa para a próxima.
    Cada chave deve ser de um projeto diferente do Google (a cota é por projeto).
    """
    bruto = os.getenv("GEMINI_API_KEYS") or os.getenv("GEMINI_API_KEY") or ""
    return [chave.strip() for chave in bruto.replace(";", ",").split(",") if chave.strip()]


def erro_de_cota(mensagem: str) -> bool:
    """Erro de limite de requisições do Gemini (por minuto ou por dia)."""
    m = mensagem.lower()
    return "429" in m or "resource_exhausted" in m or "quota" in m or "rate limit" in m


def erro_de_cota_diaria(mensagem: str) -> bool:
    """Erro de limite diário (o plano gratuito tem um número fixo de requisições por dia)."""
    m = mensagem.lower()
    return "perday" in m or "per day" in m


def erro_de_chave_invalida(mensagem: str) -> bool:
    """Chave inexistente, revogada, sem permissão ou sem acesso ao modelo configurado."""
    m = mensagem.lower()
    return (
        "api key not valid" in m or "api_key_invalid" in m or "permission_denied" in m
        or "error code: 401" in m
        # Projetos novos do Google não têm acesso a alguns modelos antigos (erro 404)
        or "no longer available" in m
    )


def get_llm_instance(provider: str, model_name: Optional[str] = None, api_key: Optional[str] = None):
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
        chaves = get_gemini_keys()
        api_key = api_key or (chaves[0] if chaves else None)
        if not api_key:
            raise ValueError("GEMINI_API_KEY não configurada no arquivo .env ou no painel.")
        chosen_model = model_name or os.getenv("GEMINI_MODEL_NAME", "gemini-2.5-flash")
        # O Gemini 2.5 "pensa" antes de responder por padrão, o que deixa cada
        # chamada bem mais lenta. "none" desliga esse raciocínio interno
        # (pode ser alterado no .env com GEMINI_REASONING_EFFORT=low/medium/high).
        reasoning_effort = os.getenv("GEMINI_REASONING_EFFORT", "none").strip() or None
        logger.info(f"Usando Google Gemini ({chosen_model}) via endpoint compatível com OpenAI, raciocínio: {reasoning_effort}")
        return LLM(
            model=f"openai/{chosen_model}",
            base_url=GEMINI_OPENAI_BASE_URL,
            api_key=api_key,
            temperature=0.3,
            reasoning_effort=reasoning_effort,
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
