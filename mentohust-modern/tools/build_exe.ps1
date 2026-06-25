param(
    [switch]$OneFile
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
$workspaceRoot = Split-Path -Parent $repoRoot
$venvRoot = Join-Path $workspaceRoot ".build-venv"
$venvPython = Join-Path $venvRoot "Scripts\python.exe"
$iconPath = Join-Path $repoRoot "src\mentohust_modern\assets\app-icon.ico"
$entryPoint = Join-Path $repoRoot "launcher.py"
$vendorDir = Join-Path $workspaceRoot "Ruijie Supplicant"
$distPath = Join-Path $workspaceRoot "dist"
$workPath = Join-Path $workspaceRoot "build\pyinstaller"
$specPath = $workspaceRoot

function Test-PythonInterpreter {
    param(
        [Parameter(Mandatory = $true)]
        [string]$PythonPath
    )

    if (-not (Test-Path $PythonPath)) {
        return $false
    }

    try {
        & $PythonPath -c "import sys; print(sys.executable)" *> $null
        return $LASTEXITCODE -eq 0
    }
    catch {
        return $false
    }
}

function Get-BasePythonCommand {
    $candidates = @(
        @("python"),
        @("py", "-3.12"),
        @("py", "-3"),
        @("py")
    )

    foreach ($candidate in $candidates) {
        try {
            if ($candidate.Count -eq 1) {
                & $candidate[0] -c "import sys; print(sys.executable)" *> $null
            }
            else {
                & $candidate[0] $candidate[1] -c "import sys; print(sys.executable)" *> $null
            }

            if ($LASTEXITCODE -eq 0) {
                return ,$candidate
            }
        }
        catch {
        }
    }

    return $null
}

function Initialize-BuildVenv {
    $basePython = Get-BasePythonCommand
    if ($null -eq $basePython) {
        throw "No working Python 3.12+ interpreter was found. Install Python first, then rerun this script."
    }

    if (Test-Path $venvRoot) {
        Remove-Item -LiteralPath $venvRoot -Recurse -Force
    }

    if ($basePython.Count -eq 1) {
        & $basePython[0] -m venv $venvRoot
    }
    else {
        & $basePython[0] $basePython[1] -m venv $venvRoot
    }

    if (-not (Test-PythonInterpreter $venvPython)) {
        throw "Failed to create a usable virtual environment at $venvRoot"
    }
}

if (-not (Test-PythonInterpreter $venvPython)) {
    Initialize-BuildVenv
}

& $venvPython -m pip install --upgrade pip
& $venvPython -m pip install -e "$repoRoot[build]"

$distMode = if ($OneFile) { "--onefile" } else { "--onedir" }

& $venvPython -m PyInstaller `
    --noconfirm `
    --clean `
    --windowed `
    $distMode `
    --name "MentoHUST Win Modern" `
    --icon $iconPath `
    --distpath $distPath `
    --workpath $workPath `
    --specpath $specPath `
    --paths (Join-Path $repoRoot "src") `
    --add-data "$($repoRoot)\src\mentohust_modern\assets;mentohust_modern\assets" `
    --add-data "$vendorDir;Ruijie Supplicant" `
    --collect-submodules scapy `
    --collect-submodules scapy.arch `
    --collect-all PIL `
    --collect-all ttkbootstrap `
    --collect-all pystray `
    $entryPoint
