# 启动知卷（默认 http://127.0.0.1:8123）
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path

$py = "python"
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    $cand = Join-Path $env:USERPROFILE ".dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe"
    if (Test-Path $cand) { $py = $cand } else { throw "未找到 python，请安装 Python 3.10+ 或修改本脚本" }
}

$env:PYTHONIOENCODING = "utf-8"
Push-Location (Join-Path $root "backend")
try {
    & $py run.py
} finally {
    Pop-Location
}
