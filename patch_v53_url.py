#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AR 量子智慧戰情室 V5.2_AI → V5.3_AI
新功能：所有供應商均顯示並可修改端點 URL
  - 端點 URL 欄位對全部 8 個供應商常駐顯示
  - 切換供應商時自動填入預設 URL
  - 提供「↺」按鈕可一鍵還原至預設值
  - 每個供應商的 URL 覆寫值分開儲存至 localStorage

執行：python patch_v53_url.py
輸出：AR 量子智慧戰情室 V5.3_AI.html
"""

import os

SRC  = os.path.join(os.path.dirname(__file__), 'AR 量子智慧戰情室 V5.2_AI.html')
DEST = os.path.join(os.path.dirname(__file__), 'AR 量子智慧戰情室 V5.3_AI.html')

with open(SRC, encoding='utf-8') as f:
    html = f.read()

patches = []

# ── Edit 1：arAiState 加入 customBaseUrls 欄位 ────────────────────────────
patches.append((
    "    savedKeys: {}, apiFormat: 'openai',\n"
    "    customBaseUrl: '', temperature: 0.3, maxTokens: 4096, useStream: true\n"
    "  };",
    "    savedKeys: {}, apiFormat: 'openai',\n"
    "    customBaseUrl: '', customBaseUrls: {}, temperature: 0.3, maxTokens: 4096, useStream: true\n"
    "  };"
))

# ── Edit 2：HTML 端點 URL 列 — 改為常駐顯示，加重置按鈕，移除 display:none ─
patches.append((
    '      <div class="ai-settings-row" id="ai-custom-url-row" style="display:none;">\n'
    '        <label>端點URL</label>\n'
    '        <input type="text" id="ai-custom-url" placeholder="https://…/v1">\n'
    '      </div>',
    '      <div class="ai-settings-row" id="ai-custom-url-row">\n'
    '        <label>端點 URL</label>\n'
    '        <input type="text" id="ai-custom-url" placeholder="https://…/v1"\n'
    '               oninput="_arMarkUrlModified()">\n'
    '        <button id="ai-url-reset-btn" onclick="_arResetUrlToDefault()"\n'
    '                title="還原至預設端點 URL"\n'
    '                style="flex:none;padding:2px 7px;font-size:0.75rem;\n'
    '                       background:rgba(255,255,255,0.06);border:1px solid rgba(255,255,255,0.15);\n'
    '                       color:var(--text-dim);border-radius:5px;cursor:pointer;">↺</button>\n'
    '      </div>'
))

# ── Edit 3：ai-custom-model-row 及 ai-api-format-row 維持 display:none ─────
#   (已是 custom/ollama 限定，無需改動)

# ── Edit 4：_arToggleCustomRows — URL 列改為常駐，只控制 model/format 列 ──
patches.append((
    "  function _arToggleCustomRows(provider) {\n"
    "    const isCustom = provider === 'custom';\n"
    "    const isOllama = provider === 'ollama';\n"
    "    const urlRow = document.getElementById('ai-custom-url-row');\n"
    "    const mdlRow = document.getElementById('ai-custom-model-row');\n"
    "    const fmtRow = document.getElementById('ai-api-format-row');\n"
    "    const mdlSel = document.getElementById('ai-model');\n"
    "    // Ollama：顯示 URL 列（可自訂端點）+ 模型名稱列，不顯示 API 格式列\n"
    "    if (urlRow) urlRow.style.display = (isCustom || isOllama) ? 'flex' : 'none';\n"
    "    if (mdlRow) mdlRow.style.display = (isCustom || isOllama) ? 'flex' : 'none';\n"
    "    if (fmtRow) fmtRow.style.display = isCustom ? 'flex' : 'none';\n"
    "    if (mdlSel) mdlSel.style.display = (isCustom || isOllama) ? 'none' : 'block';\n"
    "  }",
    "  function _arToggleCustomRows(provider) {\n"
    "    const isCustom = provider === 'custom';\n"
    "    const isOllama = provider === 'ollama';\n"
    "    // 端點 URL 列：所有供應商常駐顯示\n"
    "    // 模型名稱列：custom / ollama 才顯示（其他用 select）\n"
    "    // API 格式列：custom 才顯示\n"
    "    const mdlRow = document.getElementById('ai-custom-model-row');\n"
    "    const fmtRow = document.getElementById('ai-api-format-row');\n"
    "    const mdlSel = document.getElementById('ai-model');\n"
    "    if (mdlRow) mdlRow.style.display = (isCustom || isOllama) ? 'flex' : 'none';\n"
    "    if (fmtRow) fmtRow.style.display = isCustom ? 'flex' : 'none';\n"
    "    if (mdlSel) mdlSel.style.display = (isCustom || isOllama) ? 'none' : 'block';\n"
    "  }"
))

# ── Edit 5：onProviderChange — 切換供應商時填入對應端點 URL ─────────────────
patches.append((
    "  function onProviderChange() {\n"
    "    const sel = document.getElementById('ai-provider');\n"
    "    if (!sel) return;\n"
    "    arAiState.provider = sel.value;\n"
    "    _arToggleCustomRows(arAiState.provider);\n"
    "    arUpdateModelOptions();\n"
    "    _arFillKeyForProvider(arAiState.provider);\n"
    "  }",
    "  function onProviderChange() {\n"
    "    const sel = document.getElementById('ai-provider');\n"
    "    if (!sel) return;\n"
    "    arAiState.provider = sel.value;\n"
    "    _arToggleCustomRows(arAiState.provider);\n"
    "    arUpdateModelOptions();\n"
    "    _arFillKeyForProvider(arAiState.provider);\n"
    "    // 填入此供應商的端點 URL（用儲存的覆寫值，或預設值）\n"
    "    _arFillUrlForProvider(arAiState.provider);\n"
    "  }"
))

# ── Edit 6：initAIProviderUI — 初始化時填入 URL ──────────────────────────
patches.append((
    "    const urlInp = document.getElementById('ai-custom-url');\n"
    "    if (urlInp && arAiState.customBaseUrl) urlInp.value = arAiState.customBaseUrl;\n"
    "    else if (urlInp && arAiState.provider === 'ollama')\n"
    "      urlInp.value = AR_AI_PROVIDERS.ollama.baseUrl;",
    "    _arFillUrlForProvider(arAiState.provider);"
))

# ── Edit 7：新增 _arFillUrlForProvider / _arResetUrlToDefault / _arMarkUrlModified
#   插入於 _arFillKeyForProvider 之後
patches.append((
    "  function arUpdateModelOptions() {",
    "  // 填入供應商端點 URL（優先用已儲存的覆寫值）\n"
    "  function _arFillUrlForProvider(provider) {\n"
    "    const urlInp = document.getElementById('ai-custom-url');\n"
    "    if (!urlInp) return;\n"
    "    const prov = AR_AI_PROVIDERS[provider] || {};\n"
    "    const saved = (arAiState.customBaseUrls || {})[provider];\n"
    "    urlInp.value = saved || prov.baseUrl || '';\n"
    "    _arRefreshUrlResetBtn(provider);\n"
    "  }\n"
    "\n"
    "  // 偵測 URL 是否已被修改（顯示重置按鈕醒目樣式）\n"
    "  function _arMarkUrlModified() {\n"
    "    const urlInp = document.getElementById('ai-custom-url');\n"
    "    const btn    = document.getElementById('ai-url-reset-btn');\n"
    "    if (!urlInp || !btn) return;\n"
    "    const prov = AR_AI_PROVIDERS[arAiState.provider] || {};\n"
    "    const isModified = urlInp.value.trim() !== (prov.baseUrl || '').trim();\n"
    "    btn.style.color  = isModified ? 'var(--accent)' : 'var(--text-dim)';\n"
    "    btn.style.borderColor = isModified ? 'rgba(255,215,0,0.4)' : 'rgba(255,255,255,0.15)';\n"
    "  }\n"
    "\n"
    "  // 還原為預設端點 URL\n"
    "  function _arResetUrlToDefault() {\n"
    "    const urlInp = document.getElementById('ai-custom-url');\n"
    "    if (!urlInp) return;\n"
    "    const prov = AR_AI_PROVIDERS[arAiState.provider] || {};\n"
    "    urlInp.value = prov.baseUrl || '';\n"
    "    // 清除此供應商的覆寫記錄\n"
    "    if (arAiState.customBaseUrls) delete arAiState.customBaseUrls[arAiState.provider];\n"
    "    _arMarkUrlModified();\n"
    "    _arShowToast('已還原為預設端點 URL');\n"
    "  }\n"
    "\n"
    "  // 更新重置按鈕外觀\n"
    "  function _arRefreshUrlResetBtn(provider) {\n"
    "    const urlInp = document.getElementById('ai-custom-url');\n"
    "    const btn    = document.getElementById('ai-url-reset-btn');\n"
    "    if (!urlInp || !btn) return;\n"
    "    const prov = AR_AI_PROVIDERS[provider] || {};\n"
    "    const isModified = urlInp.value.trim() !== (prov.baseUrl || '').trim();\n"
    "    btn.style.color  = isModified ? 'var(--accent)' : 'var(--text-dim)';\n"
    "    btn.style.borderColor = isModified ? 'rgba(255,215,0,0.4)' : 'rgba(255,255,255,0.15)';\n"
    "  }\n"
    "\n"
    "  function arUpdateModelOptions() {"
))

# ── Edit 8：callAI — 所有供應商都使用 URL 輸入欄位的值（空則 fallback 預設）
patches.append((
    "    const prov    = AR_AI_PROVIDERS[arAiState.provider];\n"
    "    const baseUrl = ((arAiState.provider === 'custom' || _isOllamaProv) && cfg.customUrl)\n"
    "      ? cfg.customUrl.replace(/\\/$/, '')\n"
    "      : prov.baseUrl;",
    "    const prov    = AR_AI_PROVIDERS[arAiState.provider];\n"
    "    // 優先使用使用者設定的 URL（所有供應商），空值時 fallback 至預設\n"
    "    const baseUrl = (cfg.customUrl ? cfg.customUrl.replace(/\\/$/, '') : null)\n"
    "      || prov.baseUrl;"
))

# ── Edit 9：saveAISettings — 同時儲存各供應商 URL 覆寫值 ─────────────────
patches.append((
    "    const payload = {\n"
    "      provider: arAiState.provider, model: cfg.model,\n"
    "      customBaseUrl: cfg.customUrl, temperature: cfg.temp,\n"
    "      maxTokens: cfg.maxTok, useStream: cfg.stream,\n"
    "      apiFormat: cfg.apiFormat, savedKeys: saved\n"
    "    };",
    "    // 記錄當前供應商的 URL 覆寫（僅在與預設不同時才儲存）\n"
    "    const _urlOverrides = Object.assign({}, arAiState.customBaseUrls || {});\n"
    "    const _curProv = AR_AI_PROVIDERS[arAiState.provider] || {};\n"
    "    if (cfg.customUrl && cfg.customUrl.trim() !== (_curProv.baseUrl || '').trim()) {\n"
    "      _urlOverrides[arAiState.provider] = cfg.customUrl.trim();\n"
    "    } else {\n"
    "      delete _urlOverrides[arAiState.provider];\n"
    "    }\n"
    "    arAiState.customBaseUrls = _urlOverrides;\n"
    "    const payload = {\n"
    "      provider: arAiState.provider, model: cfg.model,\n"
    "      customBaseUrl: cfg.customUrl, customBaseUrls: _urlOverrides,\n"
    "      temperature: cfg.temp, maxTokens: cfg.maxTok, useStream: cfg.stream,\n"
    "      apiFormat: cfg.apiFormat, savedKeys: saved\n"
    "    };"
))

# ── Edit 10：loadAISettings — 還原 customBaseUrls ────────────────────────
patches.append((
    "      if (s.apiFormat)   arAiState.apiFormat     = s.apiFormat;\n"
    "      if (s.savedKeys)   arAiState.savedKeys     = s.savedKeys;",
    "      if (s.apiFormat)      arAiState.apiFormat      = s.apiFormat;\n"
    "      if (s.savedKeys)      arAiState.savedKeys      = s.savedKeys;\n"
    "      if (s.customBaseUrls) arAiState.customBaseUrls = s.customBaseUrls;"
))

# ── Edit 11：loadAISettings applyToUI — 填入 URL ─────────────────────────
patches.append((
    "        const urlInp = document.getElementById('ai-custom-url');\n"
    "        if (urlInp && s.customBaseUrl) urlInp.value = s.customBaseUrl;",
    "        // 填入此供應商的 URL（優先用儲存的覆寫值）\n"
    "        _arFillUrlForProvider(arAiState.provider);"
))

# ── 套用所有 patch ──────────────────────────────────────────────────────────
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
