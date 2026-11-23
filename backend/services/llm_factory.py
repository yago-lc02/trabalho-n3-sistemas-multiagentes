import os
import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

def get_llm_instance(provider: str, model_name: Optional[str] = None):
    """
    Retorna a instância LLM compatível com CrewAI/LangChain com base no provedor escolhido.
    Suporta:
    - 'gemini' (Nuvem Google)
    - 'openai' (Nuvem OpenAI)
    - 'ollama' (Local / 100% Offline)
    - 'demo' (Mock / Cache instantâneo para workshops)
    """
    provider = provider.lower().strip()
    
    if provider == "demo":
        return None

    if provider == "ollama":
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        chosen_model = model_name or os.getenv("OLLAMA_MODEL", "llama3.2")
        logger.info(f"Conectando ao Ollama Local em {base_url} com o modelo {chosen_model}")
        try:
            # Langchain OpenAI client compatível com o endpoint do Ollama (/v1)
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(
                model=chosen_model,
                base_url=f"{base_url.rstrip('/')}/v1",
                api_key="ollama", # Ollama local não requer chave real
                temperature=0.3
            )
        except Exception as e:
            logger.warning(f"Erro ao instanciar ChatOpenAI para Ollama: {e}. Tentando ChatOllama.")
            from langchain_community.chat_models import ChatOllama
            return ChatOllama(
                model=chosen_model,
                base_url=base_url,
                temperature=0.3
            )

    elif provider == "gemini":
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY não configurada no arquivo .env ou no painel.")
        
        chosen_model = model_name or os.getenv("GEMINI_MODEL_NAME", "gemini-1.5-flash")
        
        # Pode ser utilizado ChatGoogleGenerativeAI se instalado ou wrapper
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            return ChatGoogleGenerativeAI(
                model=chosen_model,
                google_api_key=api_key,
                temperature=0.3
            )
        except ImportError:
            # Fallback transparente via OpenAI compatibility endpoint do Gemini se necessário
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(
                model=chosen_model,
                base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
                api_key=api_key,
                temperature=0.3
            )

    elif provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY não configurada no arquivo .env ou no painel.")
        
        chosen_model = model_name or os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini")
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=chosen_model,
            api_key=api_key,
            temperature=0.3
        )

    else:
        raise ValueError(f"Provedor LLM desconhecido: '{provider}'. Utilize 'demo', 'ollama', 'gemini' ou 'openai'.")
