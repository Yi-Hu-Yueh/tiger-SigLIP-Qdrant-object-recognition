. "$PSScriptRoot\_common.ps1"
Push-Location $ProjectRoot
try {
    Write-Host "Building SigLIP -> Qdrant index from: $ProjectRoot\rawpics"
    & $Python -m app.cli.build_index
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}
finally { Pop-Location }
