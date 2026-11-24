@echo off
chcp 65001 > nul
cls
echo ===============================================================================
echo   GESTOR INTELIGENTE DE ESTUDOS E SIMULADOR DE PROVAS (CREWAI MULTIAGENTE)
echo   Workshop FASOFT - UniRV (Engenharia de Software)
echo ===============================================================================
echo.

cd /d "%~dp0"

echo [1/3] Verificando ambiente Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRO] Python nao encontrado no PATH do sistema. Instale o Python 3.11+.
    pause
    exit /b
)

if not exist "venv" (
    echo [2/3] Criando ambiente virtual Python ^(venv^)...
    python -m venv venv
    call venv\Scripts\activate.bat
    echo Instalando dependencias essenciais do backend...
    pip install -r backend\requirements.txt
) else (
    echo [2/3] Ativando ambiente virtual venv existente...
    call venv\Scripts\activate.bat
)

if not exist "backend\.env" (
    echo Criando arquivo backend\.env a partir de .env.example...
    copy backend\.env.example backend\.env >nul
)

echo.
echo [3/3] Iniciando servidor do Gestor Inteligente de Estudos...
echo -------------------------------------------------------------------------------
echo O sistema estara acessivel no seu navegador em:
echo http://localhost:8000
echo.
echo Pressione CTRL+C nesta janela para encerrar o servidor quando desejar.
echo -------------------------------------------------------------------------------
echo.

REM Inicia o navegador automaticamente apos 2 segundos
start "" cmd /c "timeout /t 2 /nobreak >nul && start http://localhost:8000"

python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

pause
