@echo off
title Gamma Points Dashboard
echo ========================================
echo    Gamma Points Dashboard
echo ========================================
echo.
echo Iniciando o servidor Streamlit...
echo.

cd /d "%~dp0"

python -m streamlit run app.py --server.headless true

pause