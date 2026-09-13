. "$PSScriptRoot\_common.ps1"
Push-Location $ProjectRoot
try {
    Write-Host "Project : $ProjectRoot"
    Write-Host "Venv    : $env:VIRTUAL_ENV"
    Write-Host "Python  : $Python"
    & $Python --version
    & $Python -c "import torch; print('torch:', torch.__version__); print('cuda_available:', torch.cuda.is_available()); print('cuda_device:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU')"
    & $Python -c "import transformers, qdrant_client, fastapi; from PIL import Image; print('transformers:', transformers.__version__); print('qdrant_client: OK'); print('fastapi:', fastapi.__version__); print('Pillow: OK')"
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    Write-Host "Environment check: PASS" -ForegroundColor Green
}
finally { Pop-Location }
