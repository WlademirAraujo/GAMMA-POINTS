# executar_dashboard.ps1
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   Gamma Points Dashboard" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Iniciando o servidor Streamlit..." -ForegroundColor Yellow
Write-Host ""

Set-Location $PSScriptRoot

# Abrir navegador automaticamente
Start-Process "http://localhost:8501"

# Executar Streamlit
python -m streamlit run app.py

Read-Host "`nPressione Enter para sair..."