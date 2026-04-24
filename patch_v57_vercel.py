#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AR 量子智慧戰情室 V5.6_AI → V5.7_AI
新功能：自動偵測部署環境，智慧切換 Proxy 路徑
  - 本機（localhost / 127.0.0.1）→ 繼續用 http://localhost:8765/ar-proxy
  - Vercel / 遠端部署           → 自動改用 /api/proxy（同域，無 CORS 問題）
  - CORS 代理開關提示文字依環境調整

執行：python patch_v57_vercel.py
輸出：
  AR 量子智慧戰情室 V5.7_AI.html  （含版本號）
  index.html                        （Vercel 部署用，與 V5.7 內容相同）
"""

import os
import shutil

SRC  = os.path.join(os.path.dirname(__file__), 'AR 量子智慧戰情室 V5.6_AI.html')
DEST = os.path.join(os.path.dirname(__file__), 'AR 量子智慧戰情室 V5.7_AI.html')
IDX  = os.path.join(os.path.dirname(__file__), 'index.html')

with open(SRC, encoding='utf-8') as f:
    html = f.read()

patches = []

# ── Edit 1：callAI — 自動偵測環境，智慧選擇 Proxy Base URL ─────────────────
patches.append((
    "    // 若代理啟用，請求走本機 Proxy；Header 帶原始目標供 Proxy 轉發\n"
    "    const _proxyPort = arAiState.proxyPort || 8765;\n"
    "    const baseUrl = arAiState.proxyEnabled\n"
    "      ? `http://localhost:${_proxyPort}/ar-proxy`\n"
    "      : _realBaseUrl;\n"
    "    // 傳遞原始目標給 Proxy\n"
    "    arAiState._proxyTargetUrl = arAiState.proxyEnabled ? _realBaseUrl : null;",

    "    // 若代理啟用，自動偵測環境：\n"
    "    //   本機（localhost / 127.0.0.1）→ Python 本機 Proxy (http://localhost:PORT/ar-proxy)\n"
    "    //   Vercel / 遠端部署           → 同域 Edge Function (/api/proxy)\n"
    "    const _proxyPort = arAiState.proxyPort || 8765;\n"
    "    const _isRemote  = window.location.hostname !== 'localhost'\n"
    "                    && window.location.hostname !== '127.0.0.1';\n"
    "    const _proxyBase = _isRemote\n"
    "      ? '/api/proxy'\n"
    "      : `http://localhost:${_proxyPort}/ar-proxy`;\n"
    "    const baseUrl = arAiState.proxyEnabled ? _proxyBase : _realBaseUrl;\n"
    "    // 傳遞原始目標給 Proxy\n"
    "    arAiState._proxyTargetUrl = arAiState.proxyEnabled ? _realBaseUrl : null;"
))

# ── Edit 2：onProxyToggle — 依環境顯示不同提示 ────────────────────────────
patches.append((
    "    const hint = cb.checked\n"
    "      ? `✅ 代理已啟用 → 請確認已執行：python ar_cors_proxy.py ${arAiState.proxyPort}`\n"
    "      : '⚪ 代理已關閉，直接連接 API';\n"
    "    _arShowToast(hint);",

    "    const _isRemoteToggle = window.location.hostname !== 'localhost'\n"
    "                         && window.location.hostname !== '127.0.0.1';\n"
    "    const hint = cb.checked\n"
    "      ? (_isRemoteToggle\n"
    "          ? '✅ 代理已啟用（Vercel 模式）→ 請求透過 /api/proxy 轉發'\n"
    "          : `✅ 代理已啟用（本機模式）→ 請確認已執行：python ar_cors_proxy.py ${arAiState.proxyPort}`)\n"
    "      : '⚪ 代理已關閉，直接連接 API';\n"
    "    _arShowToast(hint);"
))

# ── Edit 3：面板 Proxy Port 輸入欄 — 補充 Vercel 模式說明 ──────────────────
patches.append((
    '        <input type="number" id="ai-proxy-port" value="8765" min="1024" max="65535"\n'
    '               title="Proxy Port"\n'
    '               style="width:68px;flex:none;font-size:0.72rem;padding:2px 5px;"\n'
    '               placeholder="8765">',

    '        <input type="number" id="ai-proxy-port" value="8765" min="1024" max="65535"\n'
    '               title="本機代理 Port（Vercel 部署時無需此設定）"\n'
    '               style="width:68px;flex:none;font-size:0.72rem;padding:2px 5px;"\n'
    '               placeholder="8765">\n'
    '        <span id="ai-proxy-env-hint"\n'
    '              style="font-size:0.68rem;color:var(--text-dim);flex:none;white-space:nowrap;">\n'
    '        </span>'
))

# ── Edit 4：initAIProviderUI — 初始化時顯示當前環境 Hint ──────────────────
patches.append((
    "    const proxyCb = document.getElementById('ai-proxy-toggle');\n"
    "    if (proxyCb) proxyCb.checked = arAiState.proxyEnabled || false;\n"
    "    const proxyPt = document.getElementById('ai-proxy-port');\n"
    "    if (proxyPt) proxyPt.value = arAiState.proxyPort || 8765;",

    "    const proxyCb = document.getElementById('ai-proxy-toggle');\n"
    "    if (proxyCb) proxyCb.checked = arAiState.proxyEnabled || false;\n"
    "    const proxyPt = document.getElementById('ai-proxy-port');\n"
    "    if (proxyPt) proxyPt.value = arAiState.proxyPort || 8765;\n"
    "    // 顯示環境提示\n"
    "    const _envHint = document.getElementById('ai-proxy-env-hint');\n"
    "    if (_envHint) {\n"
    "      const _isR = window.location.hostname !== 'localhost'\n"
    "               && window.location.hostname !== '127.0.0.1';\n"
    "      _envHint.textContent = _isR ? '🌐 Vercel 模式' : '💻 本機模式';\n"
    "      _envHint.style.color = _isR ? '#7ec8e3' : 'var(--text-dim)';\n"
    "    }"
))

# ── 套用 ──────────────────────────────────────────────────────────────────
errors = []
for i, (old, new) in enumerate(patches, 1):
    if old in html:
        html = html.replace(old, new, 1)
        print(f'  ✅ Edit {i} 套用成功')
    else:
        errors.append(i)
        print(f'  ❌ Edit {i} 找不到比對字串')

with open(DEST, 'w', encoding='utf-8') as f:
    f.write(html)

# 複製一份為 index.html（Vercel 部署用）
shutil.copy2(DEST, IDX)
print(f'\n{"="*58}')
if errors:
    print(f'完成（{len(patches)-len(errors)}/{len(patches)} 項）— 失敗 Edit: {errors}')
else:
    print(f'全部 {len(patches)} 項修改套用成功 ✅')
print(f'輸出：{DEST}')
print(f'輸出：{IDX}  （Vercel 部署用）')
