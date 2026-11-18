# 用本机 git 推送（本机没有 git 时请用 scripts/publish.mjs）
param(
  [string]$Repo = "zujuan"
)
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Push-Location $root
try {
  if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    throw '本机没有 git，改用：$env:GITHUB_TOKEN="ghp_xxx"; node scripts\publish.mjs'
  }
  if (-not (Test-Path .git)) { git init -b main | Out-Null }
  git add -A
  git commit -m "initial commit: zujuan" 2>$null | Out-Null
  $user = git config user.name
  if (-not $user) { throw "先设置 git config --global user.name / user.email" }
  $remote = "https://github.com/$user/$Repo.git"
  git remote remove origin 2>$null | Out-Null
  git remote add origin $remote
  git push -u origin main
  Write-Host "已推送到 $remote"
} finally {
  Pop-Location
}
