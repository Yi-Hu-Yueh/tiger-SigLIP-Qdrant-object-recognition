param(
    [switch]$Reload
)
. "$PSScriptRoot\_common.ps1"
Push-Location $ProjectRoot
try {
    $ArgsList = @("-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "18080")
    if ($Reload) { $ArgsList += "--reload" }
    & $Python @ArgsList
}
finally {
    Pop-Location
}
