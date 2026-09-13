$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot

if (-not $env:VIRTUAL_ENV) {
    throw "No Python virtual environment is active. Activate a venv first, then retry."
}

$Python = (Get-Command python -ErrorAction Stop).Source
$ActiveVenv = (Resolve-Path $env:VIRTUAL_ENV).Path.TrimEnd('\')
$PythonPrefix = (& $Python -c "import sys; print(sys.prefix)").Trim()
$ResolvedPrefix = (Resolve-Path $PythonPrefix).Path.TrimEnd('\')

if ($ActiveVenv.ToLowerInvariant() -ne $ResolvedPrefix.ToLowerInvariant()) {
    throw "The python command is not from the active virtual environment. Active venv: $ActiveVenv ; Python prefix: $ResolvedPrefix"
}
