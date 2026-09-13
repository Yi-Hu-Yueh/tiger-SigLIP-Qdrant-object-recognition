. "$PSScriptRoot\_common.ps1"
Push-Location $ProjectRoot
try {
    & $Python -m app.cli.status
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}
finally {
    Pop-Location
}
