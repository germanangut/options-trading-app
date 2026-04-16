param(
    [switch]$IncludeStreamlit,
    [switch]$InstallFrontendDeps
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$venvPython = Join-Path $repoRoot "venv\Scripts\python.exe"
$frontendDir = Join-Path $repoRoot "frontend"
$streamlitApp = Join-Path $repoRoot "app.py"

if (-not (Test-Path $venvPython)) {
    throw "Python virtual environment not found at '$venvPython'."
}

if (-not (Test-Path $frontendDir)) {
    throw "Frontend directory not found at '$frontendDir'."
}

if (-not (Test-Path $streamlitApp)) {
    throw "Streamlit entrypoint not found at '$streamlitApp'."
}

$npmCommand = Get-Command "npm.cmd" -ErrorAction SilentlyContinue
if (-not $npmCommand) {
    $defaultNpm = "C:\Program Files\nodejs\npm.cmd"
    if (Test-Path $defaultNpm) {
        $npmCommand = Get-Item $defaultNpm
    } else {
        throw "npm.cmd was not found on PATH or at '$defaultNpm'."
    }
}

$npmPath = $npmCommand.Source
$frontendNodeModules = Join-Path $frontendDir "node_modules"
$shouldInstallFrontendDeps = $InstallFrontendDeps -or -not (Test-Path $frontendNodeModules)

function Start-DevWindow {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Title,
        [Parameter(Mandatory = $true)]
        [string]$WorkingDirectory,
        [Parameter(Mandatory = $true)]
        [string]$Command
    )

    $windowCommand = @"
`$Host.UI.RawUI.WindowTitle = '$Title'
Set-Location '$WorkingDirectory'
$Command
"@

    Start-Process powershell.exe -WorkingDirectory $WorkingDirectory -ArgumentList @(
        "-NoExit",
        "-ExecutionPolicy", "Bypass",
        "-Command", $windowCommand
    ) | Out-Null
}

$backendCommand = "& '$venvPython' -m uvicorn backend.api.main:app --host 127.0.0.1 --port 8000 --reload"
Start-DevWindow -Title "Options Backend" -WorkingDirectory $repoRoot -Command $backendCommand

if ($shouldInstallFrontendDeps) {
    $frontendCommand = "& '$npmPath' install; if (`$LASTEXITCODE -ne 0) { exit `$LASTEXITCODE }; & '$npmPath' run dev"
} else {
    $frontendCommand = "& '$npmPath' run dev"
}
Start-DevWindow -Title "Options Frontend" -WorkingDirectory $frontendDir -Command $frontendCommand

if ($IncludeStreamlit) {
    $streamlitCommand = "& '$venvPython' -m streamlit run app.py"
    Start-DevWindow -Title "Options Streamlit" -WorkingDirectory $repoRoot -Command $streamlitCommand
}

Write-Host ""
Write-Host "Launched development windows:" -ForegroundColor Cyan
Write-Host "- FastAPI backend: http://127.0.0.1:8000" -ForegroundColor Green
Write-Host "- React frontend:  http://127.0.0.1:5173" -ForegroundColor Green

if ($IncludeStreamlit) {
    Write-Host "- Streamlit app:   http://127.0.0.1:8501" -ForegroundColor Green
}

Write-Host ""
Write-Host "Usage examples:" -ForegroundColor Cyan
Write-Host "  .\run-dev.ps1"
Write-Host "  .\run-dev.ps1 -IncludeStreamlit"
Write-Host "  .\run-dev.ps1 -InstallFrontendDeps"
