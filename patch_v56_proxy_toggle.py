#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AR 量子智慧戰情室 V5.5_AI → V5.6_AI
新功能：面板新增「CORS 本機代理」開關
  - 端點 URL 繼續填 https://api.nengpa.com/v1（不用改）
  - 開啟開關後，系統自動透過 http://localhost:8765 轉發
  - Proxy Port 可自訂，預設 8765
  - 開關狀態與 Port 隨「💾 儲存設定」持久化

執行：python patch_v56_proxy_toggle.py
輸出：AR 量子智慧戰情室 V5.6_AI.html
"""

import os

SRC  = os.path.join(os.path.dirname(__file__), 'AR 量子智慧戰情室 V5.5_AI.html')
DEST = os.path.join(os.path.dirname(__file__), 'AR 量子智慧戰情室 V5.6_AI.html')

with open(SRC, encoding='utf-8') as f:
    html = f.read()

patches = []

# ── Edit 1：arAiState 加入 proxyEnabled / proxyPort ───────────────────────
patches.append((
    "    customBaseUrl: '', customBaseUrls: {}, temperature: 0.3, maxTokens: 4096, useStream: true",
    "    customBaseUrl: '', customBaseUrls: {}, temperature: 0.3, maxTokens: 4096, useStream: true,\n"
    "    proxyEnabled: false, proxyPort: 8765"
))

# ── Edit 2：HTML 設定區加入 CORS 代理列（插入於 API Key 列之前）────────────
patches.append((
    '      <div class="ai-settings-row">\n'
    '        <label>API Key</label>',
    '      <div class="ai-settings-row" id="ai-proxy-row">\n'
    '        <label>CORS 代理</label>\n'
    '        <label style="display:flex;align-items:center;gap:6px;cursor:pointer;">\n'
    '          <input type="checkbox" id="ai-proxy-toggle"\n'
    '                 onchange="onProxyToggle()"\n'
    '                 style="width:15px;height:15px;accent-color:var(--accent);">\n'
    '          <span style="font-size:0.75rem;color:var(--text-dim);">本機代理（解決 CORS）</span>\n'
    '        </label>\n'
    '        <input type="number" id="ai-proxy-port" value="8765" min="1024" max="65535"\n'
    '               title="Proxy Port"\n'
    '               style="width:68px;flex:none;font-size:0.72rem;padding:2px 5px;"\n'
    '               placeholder="8765">\n'
    '      </div>\n'
    '      <div class="ai-settings-row">\n'
    '        <label>API Key</label>'
))

# ── Edit 3：onProviderChange 後加 onProxyToggle 函式 ──────────────────────
patches.append((
    "  function _arFillKeyForProvider(provider) {",
    "  function onProxyToggle() {\n"
    "    const cb   = document.getElementById('ai-proxy-toggle');\n"
    "    const port = document.getElementById('ai-proxy-port');\n"
    "    if (!cb) return;\n"
    "    arAiState.proxyEnabled = cb.checked;\n"
    "    if (port) arAiState.proxyPort = parseInt(port.value) || 8765;\n"
    "    const hint = cb.checked\n"
    "      ? `✅ 代理已啟用 → 請確認已執行：python ar_cors_proxy.py ${arAiState.proxyPort}`\n"
    "      : '⚪ 代理已關閉，直接連接 API';\n"
    "    _arShowToast(hint);\n"
    "  }\n"
    "\n"
    "  function _arFillKeyForProvider(provider) {"
))

# ── Edit 4：initAIProviderUI 加入代理 UI 還原 ─────────────────────────────
patches.append((
    "    _arFillUrlForProvider(arAiState.provider);",
    "    _arFillUrlForProvider(arAiState.provider);\n"
    "    const proxyCb = document.getElementById('ai-proxy-toggle');\n"
    "    if (proxyCb) proxyCb.checked = arAiState.proxyEnabled || false;\n"
    "    const proxyPt = document.getElementById('ai-proxy-port');\n"
    "    if (proxyPt) proxyPt.value = arAiState.proxyPort || 8765;"
))

# ── Edit 5：callAI — 若代理啟用，URL 改走本機，並加 X-Proxy-Target ─────────
patches.append((
    "    // _arNormalizeBaseUrl：移除空白字元 + 尾端多餘路徑，空值 fallback 至預設\n"
    "    const baseUrl = _arNormalizeBaseUrl(\n"
    "      (cfg.customUrl ? cfg.customUrl : '') || prov.baseUrl\n"
    "    );",
    "    // _arNormalizeBaseUrl：移除空白字元 + 尾端多餘路徑，空值 fallback 至預設\n"
    "    const _realBaseUrl = _arNormalizeBaseUrl(\n"
    "      (cfg.customUrl ? cfg.customUrl : '') || prov.baseUrl\n"
    "    );\n"
    "    // 若代理啟用，請求走本機 Proxy；Header 帶原始目標供 Proxy 轉發\n"
    "    const _proxyPort = arAiState.proxyPort || 8765;\n"
    "    const baseUrl = arAiState.proxyEnabled\n"
    "      ? `http://localhost:${_proxyPort}/ar-proxy`\n"
    "      : _realBaseUrl;\n"
    "    // 傳遞原始目標給 Proxy\n"
    "    arAiState._proxyTargetUrl = arAiState.proxyEnabled ? _realBaseUrl : null;"
))

# ── Edit 6：_callOpenAI — 代理模式加 X-Proxy-Target header ───────────────
patches.append((
    "    const headers = { 'Content-Type': 'application/json', 'Authorization': `Bearer ${cfg.key}` };\n"
    "    // OpenRouter 必要標頭\n"
    "    if (arAiState.provider === 'openrouter') {\n"
    "      headers['HTTP-Referer'] = window.location.href || 'https://ar-dashboard.local';\n"
    "      headers['X-Title'] = 'AR 量子智慧戰情室';\n"
    "    }",
    "    const headers = { 'Content-Type': 'application/json', 'Authorization': `Bearer ${cfg.key}` };\n"
    "    // 代理模式：告訴本機 Proxy 要轉發到哪裡\n"
    "    if (arAiState.proxyEnabled && arAiState._proxyTargetUrl) {\n"
    "      headers['X-Proxy-Target'] = arAiState._proxyTargetUrl;\n"
    "    }\n"
    "    // OpenRouter 必要標頭\n"
    "    if (arAiState.provider === 'openrouter') {\n"
    "      headers['HTTP-Referer'] = window.location.href || 'https://ar-dashboard.local';\n"
    "      headers['X-Title'] = 'AR 量子智慧戰情室';\n"
    "    }"
))

# ── Edit 7：saveAISettings 加入 proxy 設定 ────────────────────────────────
patches.append((
    "      provider: arAiState.provider, model: cfg.model,\n"
    "      customBaseUrl: cfg.customUrl, customBaseUrls: _urlOverrides,\n"
    "      temperature: cfg.temp, maxTokens: cfg.maxTok, useStream: cfg.stream,\n"
    "      apiFormat: cfg.apiFormat, savedKeys: saved",
    "      provider: arAiState.provider, model: cfg.model,\n"
    "      customBaseUrl: cfg.customUrl, customBaseUrls: _urlOverrides,\n"
    "      temperature: cfg.temp, maxTokens: cfg.maxTok, useStream: cfg.stream,\n"
    "      apiFormat: cfg.apiFormat, savedKeys: saved,\n"
    "      proxyEnabled: arAiState.proxyEnabled,\n"
    "      proxyPort: arAiState.proxyPort || 8765"
))

# ── Edit 8：loadAISettings 還原 proxy 設定 ────────────────────────────────
patches.append((
    "      if (s.customBaseUrls) arAiState.customBaseUrls = s.customBaseUrls;",
    "      if (s.customBaseUrls)  arAiState.customBaseUrls  = s.customBaseUrls;\n"
    "      if (s.proxyEnabled != null) arAiState.proxyEnabled = s.proxyEnabled;\n"
    "      if (s.proxyPort)        arAiState.proxyPort        = s.proxyPort;"
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

print(f'\n{"="*55}')
if errors:
    print(f'完成（{len(patches)-len(errors)}/{len(patches)} 項）— 失敗 Edit: {errors}')
else:
    print(f'全部 {len(patches)} 項修改套用成功 ✅')
print(f'輸出檔案：{DEST}')
