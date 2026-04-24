# AR 量子智慧戰情室 — 一鍵推送到 GitHub
# 雙擊或在 PowerShell 執行：.\push_to_github.ps1

$ErrorActionPreference = "Stop"
$REPO_DIR  = "C:\Users\jamic\應收帳款"
$REMOTE    = "https://github.com/jamic710808/ar-quantum-dashboard.git"
$BRANCH    = "main"
$V56       = "AR 量子智慧戰情室 V5.6_AI.html"

Set-Location $REPO_DIR
Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  AR 量子智慧戰情室 — GitHub 推送工具" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# ── 步驟 0：環境檢查 ─────────────────────────────────────────────
Write-Host "[1/5] 環境檢查..." -ForegroundColor Yellow

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host "  ❌ Git 未安裝。請先安裝：winget install --id Git.Git" -ForegroundColor Red
    Read-Host "按 Enter 結束"; exit 1
}
Write-Host "  ✅ Git：$(git --version)"

$ghOK = Get-Command gh -ErrorAction SilentlyContinue
if ($ghOK) { Write-Host "  ✅ GitHub CLI：$(gh --version | Select-Object -First 1)" }
else        { Write-Host "  ⚠️  GitHub CLI 未安裝（不影響推送，僅供參考）" -ForegroundColor DarkYellow }

# ── 步驟 1：建立 index.html ──────────────────────────────────────
Write-Host ""
Write-Host "[2/5] 建立 index.html..." -ForegroundColor Yellow

if (-not (Test-Path $V56)) {
    Write-Host "  ❌ 找不到 $V56" -ForegroundColor Red
    Read-Host "按 Enter 結束"; exit 1
}
Copy-Item $V56 "index.html" -Force
Write-Host "  ✅ index.html 已建立（來源：$V56）"

# ── 步驟 2：確認部署檔案存在 ─────────────────────────────────────
Write-Host ""
Write-Host "[3/5] 確認部署檔案..." -ForegroundColor Yellow

$missing = @()
if (-not (Test-Path "index.html"))                     { $missing += "index.html" }
if (-not (Test-Path "vercel.json"))                    { $missing += "vercel.json" }
if (-not (Test-Path "api\proxy\[...path].js"))         { $missing += "api/proxy/[...path].js" }

if ($missing.Count -gt 0) {
    Write-Host "  ❌ 缺少以下檔案：$($missing -join ', ')" -ForegroundColor Red
    Read-Host "按 Enter 結束"; exit 1
}
Write-Host "  ✅ index.html"
Write-Host "  ✅ vercel.json"
Write-Host "  ✅ api/proxy/[...path].js"

# ── 步驟 3：初始化 / 設定 Git repo ───────────────────────────────
Write-Host ""
Write-Host "[4/5] 設定 Git repo..." -ForegroundColor Yellow

if (-not (Test-Path ".git")) {
    git init
    git remote add origin $REMOTE
    Write-Host "  ✅ 已初始化並設定 remote"
} else {
    $existingRemote = git remote get-url origin 2>$null
    if ($existingRemote -ne $REMOTE) {
        git remote set-url origin $REMOTE
        Write-Host "  ✅ Remote URL 已更新"
    } else {
        Write-Host "  ✅ Git repo 已存在，remote 正確"
    }
}

# ── 步驟 4：Commit & Push ─────────────────────────────────────────
Write-Host ""
Write-Host "[5/5] Commit 並推送..." -ForegroundColor Yellow

git add index.html vercel.json "api/"
$status = git status --short
if (-not $status) {
    Write-Host "  ℹ️  沒有新的變更需要推送" -ForegroundColor DarkYellow
} else {
    Write-Host "  異動檔案："
    git status --short | ForEach-Object { Write-Host "    $_" }
    git commit -m "feat: Add V5.7 Vercel CORS proxy (Edge Function + auto-detect)"
    Write-Host "  ✅ Commit 完成"
}

try {
    git push origin $BRANCH
    Write-Host ""
    Write-Host "============================================" -ForegroundColor Green
    Write-Host "  ✅ 推送成功！" -ForegroundColor Green
    Write-Host "  GitHub：https://github.com/jamic710808/ar-quantum-dashboard" -ForegroundColor Green
    Write-Host "  Vercel：https://ar-quantum-dashboard.vercel.app" -ForegroundColor Green
    Write-Host "  Vercel 約 30 秒後自動重新部署" -ForegroundColor Green
    Write-Host "============================================" -ForegroundColor Green
} catch {
    Write-Host ""
    Write-Host "  ❌ 推送失敗：$_" -ForegroundColor Red
    Write-Host ""
    Write-Host "  如果是登入問題，請先執行：" -ForegroundColor Yellow
    Write-Host "    gh auth login --web --git-protocol https" -ForegroundColor White
    Write-Host "  再重新執行此腳本" -ForegroundColor Yellow
}

Write-Host ""
Read-Host "按 Enter 結束"
