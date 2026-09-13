. "$PSScriptRoot\_common.ps1"
Push-Location $ProjectRoot
try {
    & $Python -m pytest -q
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}
finally {
    Pop-Location
}
