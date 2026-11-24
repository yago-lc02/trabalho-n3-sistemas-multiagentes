import os
import io
import sys
import json
import logging

# Evita erro 'charmap' no console do Windows com os emojis dos logs do CrewAI
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
from typing import Optional
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel

from backend.services.pdf_extractor import extract_text_from_pdf
from backend.services.crew_orchestrator import run_study_crew
from backend.services.demo_data import DEMO_DATA

# Carrega backend/.env pelo caminho absoluto (independe do diretório de execução)
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("api")

app = FastAPI(
    title="Gestor Inteligente de Estudos e Simulador de Provas Multiagentes",
    description="API do Sistema Multiagentes para Síntese, Simulação Avaliativa e Cronograma de Estudos para o Workshop FASOFT UniRV.",
    version="1.0.0"
)

# Habilita CORS para o frontend Vite em desenvolvimento
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def _erro_http(e: Exception, prefixo: str = "") -> HTTPException:
    """Converte erros do LLM em respostas claras para o usuário."""
    msg = str(e)
    if "429" in msg or "RESOURCE_EXHAUSTED" in msg or "quota" in msg.lower() or "rate limit" in msg.lower():
        return HTTPException(
            status_code=429,
            detail="Limite de requisições do Gemini atingido (o plano gratuito permite 5 por minuto). "
                   "Aguarde cerca de 1 minuto e tente novamente."
        )
    return HTTPException(status_code=500, detail=f"{prefixo}{msg}")

class StudyTextRequest(BaseModel):
    disciplina: str
    dias_ate_prova: int = 5
    horas_por_dia: float = 2.0
    num_questoes: int = 5
    texto_material: str
    provider: Optional[str] = None
    model_name: Optional[str] = None

@app.get("/api/config")
async def get_system_config():
    """Retorna o estado da configuração de LLMs (nuvem vs local vs demo) para a barra superior."""
    env_provider = os.getenv("LLM_PROVIDER", "demo").lower()
    has_openai = bool(os.getenv("OPENAI_API_KEY"))
    has_gemini = bool(os.getenv("GEMINI_API_KEY"))
    ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    ollama_model = os.getenv("OLLAMA_MODEL", "llama3.2")
    
    return {
        "current_provider": env_provider,
        "has_openai_key": has_openai,
        "has_gemini_key": has_gemini,
        "openai_model": os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini"),
        "gemini_model": os.getenv("GEMINI_MODEL_NAME", "gemini-1.5-flash"),
        "ollama_base_url": ollama_url,
        "ollama_model": ollama_model,
        "available_modes": [
            {"id": "demo", "label": "Modo Demonstração Instantâneo (Garantia do Evento)", "ready": True},
            {"id": "ollama", "label": f"Ollama Local/Offline ({ollama_model})", "ready": True},
            {"id": "gemini", "label": "Google Gemini (Nuvem)", "ready": has_gemini}
        ]
    }

@app.get("/api/demo-data")
async def get_demo_data():
    """Retorna os dados demonstrativos pré-carregados para renderização imediata da interface."""
    return DEMO_DATA

@app.post("/api/processar-texto")
async def processar_texto(payload: StudyTextRequest):
    """Processa o material acadêmico enviado como texto puro através da orquestração CrewAI."""
    try:
        provider = payload.provider or os.getenv("LLM_PROVIDER", "demo")
        model = payload.model_name
        
        # CrewAI é síncrono: executa em thread separada para não bloquear o event loop
        resultado = await run_in_threadpool(
            run_study_crew,
            texto_material=payload.texto_material,
            disciplina=payload.disciplina,
            dias_ate_prova=payload.dias_ate_prova,
            horas_por_dia=payload.horas_por_dia,
            num_questoes=payload.num_questoes,
            provider=provider,
            model_name=model
        )
        return resultado
    except Exception as e:
        logger.error(f"Erro ao processar texto com CrewAI: {e}", exc_info=True)
        raise _erro_http(e)

@app.post("/api/processar-pdf")
async def processar_pdf(
    disciplina: str = Form(...),
    dias_ate_prova: int = Form(5),
    horas_por_dia: float = Form(2.0),
    num_questoes: int = Form(5),
    provider: Optional[str] = Form(None),
    model_name: Optional[str] = Form(None),
    arquivo: UploadFile = File(...)
):
    """Processa arquivo PDF recebido por upload, extrai o conteúdo e executa a Crew."""
    try:
        content_bytes = await arquivo.read()
        if not content_bytes:
            raise HTTPException(status_code=400, detail="Arquivo PDF vazio enviado.")
        
        texto_extraido = extract_text_from_pdf(content_bytes)
        if not texto_extraido:
            raise HTTPException(status_code=400, detail="Não foi possível extrair texto do PDF (pode ser imagem digitalizada sem OCR).")
        
        chosen_provider = provider or os.getenv("LLM_PROVIDER", "demo")
        resultado = await run_in_threadpool(
            run_study_crew,
            texto_material=texto_extraido,
            disciplina=disciplina,
            dias_ate_prova=dias_ate_prova,
            horas_por_dia=horas_por_dia,
            num_questoes=num_questoes,
            provider=chosen_provider,
            model_name=model_name
        )
        return resultado
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao processar PDF: {e}", exc_info=True)
        raise _erro_http(e, "Erro interno ao processar material: ")

# Monta diretório estático do frontend
static_path = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_path):
    app.mount("/static", StaticFiles(directory=static_path), name="static")

    @app.get("/")
    async def serve_index():
        return FileResponse(os.path.join(static_path, "index.html"))

    @app.get("/favicon.ico", include_in_schema=False)
    async def serve_favicon():
        return FileResponse(os.path.join(static_path, "favicon.ico"))

# Se o frontend Vite estiver compilado em frontend/dist, disponibiliza como alternativa
dist_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "dist")
if os.path.exists(dist_path):
    app.mount("/assets", StaticFiles(directory=os.path.join(dist_path, "assets")), name="assets")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
