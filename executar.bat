@echo off
:: Move to the directory where this .bat file is located
cd /d %~dp0

:: Check if Python is installed
where python >nul 2>nul
IF %ERRORLEVEL% NEQ 0 (
    echo ❌ Python n\u00e3o encontrado. Por favor, instale o Python 3.10+ antes de continuar.
    pause
    exit /b
)

:: Upgrade pip and install packages from _py/requirements.txt
echo 🔍 Verificando e instalando dependências...
python -m pip install --upgrade pip
python -m pip install -r _py\\requirements.txt

:: Run Streamlit app from _py folder
echo 🚀 Iniciando a aplicação...
streamlit run _py\\app.py

:: Keep window open
pause
