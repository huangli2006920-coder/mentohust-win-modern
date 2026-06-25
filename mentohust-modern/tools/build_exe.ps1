param(
    [switch]$OneFile
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
$workspaceRoot = Split-Path -Parent $repoRoot
$python = Join-Path $workspaceRoot ".venv\Scripts\python.exe"
$iconPath = Join-Path $repoRoot "src\mentohust_modern\assets\app-icon.ico"
$entryPoint = Join-Path $repoRoot "launcher.py"
$vendorDir = Join-Path $workspaceRoot "Ruijie Supplicant"
$distPath = Join-Path $workspaceRoot "dist"
$workPath = Join-Path $workspaceRoot "build\pyinstaller"
$specPath = $workspaceRoot

if (-not (Test-Path $python)) {
    throw "找不到虚拟环境 Python: $python"
}

& $python -m pip install -e $repoRoot
& $python -m pip install "pyinstaller>=6.0"

$distMode = if ($OneFile) { "--onefile" } else { "--onedir" }

& $python -m PyInstaller `
    --noconfirm `
    --clean `
    --windowed `
    $distMode `
    --name "MentoHUST Win Modern" `
    --icon $iconPath `
    --distpath $distPath `
    --workpath $workPath `
    --specpath $specPath `
    --add-data "$($repoRoot)\src\mentohust_modern\assets;mentohust_modern\assets" `
    --add-data "$vendorDir;Ruijie Supplicant" `
    --collect-all ttkbootstrap `
    --collect-all pystray `
    $entryPoint
