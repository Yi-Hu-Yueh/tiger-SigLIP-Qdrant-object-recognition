. "$PSScriptRoot\_common.ps1"
Push-Location $ProjectRoot
try {
    Write-Host "Using active virtual environment: $env:VIRTUAL_ENV"
    Write-Host "Python: $Python"
    & $Python --version

    New-Item -ItemType Directory -Force -Path (Join-Path $ProjectRoot "rawpics") | Out-Null
    New-Item -ItemType Directory -Force -Path (Join-Path $ProjectRoot "data") | Out-Null
    New-Item -ItemType Directory -Force -Path (Join-Path $ProjectRoot "models\hf_cache") | Out-Null

    $EnvFile = Join-Path $ProjectRoot ".env"
    $EnvExample = Join-Path $ProjectRoot ".env.example"
    if (-not (Test-Path $EnvFile)) {
        Copy-Item $EnvExample $EnvFile
        Write-Host "Created .env from .env.example"
    }

    Write-Host "`nInstalling project dependencies..."
    & $Python -m pip install -r (Join-Path $ProjectRoot "requirements-project.txt")
    if ($LASTEXITCODE -ne 0) { throw "Dependency installation failed." }

    Write-Host "`nChecking core imports..."
    & $Python -c "import torch, transformers, fastapi, qdrant_client, PIL, dotenv, multipart; print('Core packages: OK')"
    if ($LASTEXITCODE -ne 0) { throw "Core package import failed." }

    Write-Host "`nPyTorch runtime smoke test..."
    & $Python -c "import torch; x=torch.tensor([1.0,2.0]); print('torch', torch.__version__, 'sum=', float(x.sum()), 'cuda=', torch.cuda.is_available()); print('device=', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU')"
    if ($LASTEXITCODE -ne 0) { throw "PyTorch runtime smoke test failed." }

    Write-Host "`nSetup: PASS" -ForegroundColor Green
    Write-Host "Next: add images under rawpics\<class_name>\ and run .\scripts\validate_rawpics.ps1"
}
finally { Pop-Location }
