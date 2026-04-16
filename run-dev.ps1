param(
    [switch]$IncludeStreamlit,
    [switch]$InstallFrontendDeps
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$venvPython = Join-Path $repoRoot "venv\Scripts\python.exe"
$frontendDir = Join-Path $repoRoot "frontend"
$streamlitApp = Join-Path $repoRoot "app.py"
$defaultNodeDir = "C:\Program Files\nodejs"

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
    $defaultNpm = Join-Path $defaultNodeDir "npm.cmd"
    if (Test-Path $defaultNpm) {
        $npmCommand = Get-Item $defaultNpm
    } else {
        throw "npm.cmd was not found on PATH or at '$defaultNpm'."
    }
}

if ($npmCommand.PSObject.Properties["Source"] -and $npmCommand.Source) {
    $npmPath = [string]$npmCommand.Source
} elseif ($npmCommand.PSObject.Properties["Path"] -and $npmCommand.Path) {
    $npmPath = [string]$npmCommand.Path
} elseif ($npmCommand.PSObject.Properties["FullName"] -and $npmCommand.FullName) {
    $npmPath = [string]$npmCommand.FullName
} else {
    throw "Unable to resolve npm executable path from command metadata."
}

$npmPath = (Resolve-Path $npmPath).Path
$frontendNodeModules = Join-Path $frontendDir "node_modules"
$shouldInstallFrontendDeps = $InstallFrontendDeps -or -not (Test-Path $frontendNodeModules)
$backendUrl = "http://127.0.0.1:8000/docs"
$frontendUrl = "http://127.0.0.1:5173"
$streamlitUrl = "http://127.0.0.1:8501"

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

function New-KeepOpenCommand {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Command,
        [Parameter(Mandatory = $true)]
        [string]$FailureMessage
    )

    return @"
try {
    $Command
} catch {
    Write-Host ''
    Write-Host '$FailureMessage' -ForegroundColor Red
    Write-Host `$_.Exception.Message -ForegroundColor Red
}
Write-Host ''
Read-Host 'Press Enter to close this window'
"@
}

function Test-UrlReady {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Url
    )

    try {
        $response = Invoke-WebRequest -UseBasicParsing -Method Get -Uri $Url -TimeoutSec 2
        return $response.StatusCode -ge 200 -and $response.StatusCode -lt 500
    } catch {
        return $false
    }
}

function Wait-ForUrlReady {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Name,
        [Parameter(Mandatory = $true)]
        [string]$Url,
        [int]$Attempts = 20,
        [int]$DelaySeconds = 1
    )

    for ($attempt = 1; $attempt -le $Attempts; $attempt++) {
        if (Test-UrlReady -Url $Url) {
            Write-Host "- $Name ready: $Url" -ForegroundColor Green
            return $true
        }

        Start-Sleep -Seconds $DelaySeconds
    }

    Write-Host "- $Name not confirmed yet: $Url" -ForegroundColor Yellow
    Write-Host "  Check the spawned '$Name' window for startup errors." -ForegroundColor Yellow
    return $false
}

$backendCommand = "& '$venvPython' -m uvicorn backend.api.main:app --host 127.0.0.1 --port 8000 --reload"
Start-DevWindow -Title "Options Backend" -WorkingDirectory $repoRoot -Command $backendCommand

if ($shouldInstallFrontendDeps) {
    $frontendCommand = New-KeepOpenCommand -Command @"
`$env:Path = '$defaultNodeDir;' + `$env:Path
`$env:NPM_CONFIG_OFFLINE = 'false'
& '$npmPath' install
if (`$LASTEXITCODE -ne 0) { throw 'npm install failed.' }
& '$npmPath' run dev
if (`$LASTEXITCODE -ne 0) { throw 'npm run dev failed.' }
"@ -FailureMessage "Frontend startup failed."
} else {
    $frontendCommand = New-KeepOpenCommand -Command @"
`$env:Path = '$defaultNodeDir;' + `$env:Path
`$env:NPM_CONFIG_OFFLINE = 'false'
& '$npmPath' run dev
if (`$LASTEXITCODE -ne 0) { throw 'npm run dev failed.' }
"@ -FailureMessage "Frontend startup failed."
}
Start-DevWindow -Title "Options Frontend" -WorkingDirectory $frontendDir -Command $frontendCommand

if ($IncludeStreamlit) {
    $streamlitCommand = "& '$venvPython' -m streamlit run app.py"
    Start-DevWindow -Title "Options Streamlit" -WorkingDirectory $repoRoot -Command $streamlitCommand
}

Write-Host ""
Write-Host "Launched development windows:" -ForegroundColor Cyan
Write-Host "- FastAPI backend target: http://127.0.0.1:8000" -ForegroundColor Cyan
Write-Host "- React frontend target:  http://127.0.0.1:5173" -ForegroundColor Cyan

if ($IncludeStreamlit) {
    Write-Host "- Streamlit target:       http://127.0.0.1:8501" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "Verifying service startup..." -ForegroundColor Cyan
Wait-ForUrlReady -Name "FastAPI backend" -Url $backendUrl | Out-Null
if ($shouldInstallFrontendDeps) {
    Wait-ForUrlReady -Name "React frontend" -Url $frontendUrl -Attempts 120 -DelaySeconds 1 | Out-Null
} else {
    Wait-ForUrlReady -Name "React frontend" -Url $frontendUrl -Attempts 45 -DelaySeconds 1 | Out-Null
}

if ($IncludeStreamlit) {
    Wait-ForUrlReady -Name "Streamlit app" -Url $streamlitUrl -Attempts 45 -DelaySeconds 1 | Out-Null
}

Write-Host ""
Write-Host "Usage examples:" -ForegroundColor Cyan
Write-Host "  .\run-dev.ps1"
Write-Host "  .\run-dev.ps1 -IncludeStreamlit"
Write-Host "  .\run-dev.ps1 -InstallFrontendDeps"
