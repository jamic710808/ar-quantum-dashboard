#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AR 量子智慧戰情室 V5.3_AI → V5.4_AI
修正：
  1. baseUrl 路徑重複（/chat/completions/chat/completions）
  2. URL 中含空白字元（copy-paste 帶入的空格，如 v1%20/…）
     — _arNormalizeBaseUrl() 移除所有空白並去除尾端路徑
  3. CORS / file:// 錯誤偵測，顯示中文建議訊息
  4. 端點 URL placeholder 更新為清楚提示

執行：python patch_v54_bugfix.py
輸出：AR 量子智慧戰情室 V5.4_AI.html
"""

import os

SRC  = os.path.join(os.path.dirname(__file__), 'AR 量子智慧戰情室 V5.3_AI.html')
DEST = os.path.join(os.path.dirname(__file__), 'AR 量子智慧戰情室 V5.4_AI.html')

with open(SRC, encoding='utf-8') as f:
    html = f.read()

patches = []

# ── Edit 1：HTML 端點 URL placeholder ────────────────────────────────────
patches.append((
    '        <input type="text" id="ai-custom-url" placeholder="https://…/v1"\n'
    '               oninput="_arMarkUrlModified()">',
    '        <input type="text" id="ai-custom-url"\n'
    '               placeholder="https://api.example.com/v1  （只填到 /v1，勿含 /chat/completions）"\n'
    '               oninput="_arMarkUrlModified()">'
))

# ── Edit 2：callAI — 套用 _arNormalizeBaseUrl ─────────────────────────────
patches.append((
    "    const prov    = AR_AI_PROVIDERS[arAiState.provider];\n"
    "    // 優先使用使用者設定的 URL（所有供應商），空值時 fallback 至預設\n"
    "    const baseUrl = (cfg.customUrl ? cfg.customUrl.replace(/\\/$/, '') : null)\n"
    "      || prov.baseUrl;",
    "    const prov    = AR_AI_PROVIDERS[arAiState.provider];\n"
    "    // _arNormalizeBaseUrl：移除空白字元 + 尾端多餘路徑，空值 fallback 至預設\n"
    "    const baseUrl = _arNormalizeBaseUrl(\n"
    "      (cfg.customUrl ? cfg.customUrl : '') || prov.baseUrl\n"
    "    );"
))

# ── Edit 3：_callOpenAI fetch — 加入錯誤捕獲 ─────────────────────────────
patches.append((
    "    const resp = await fetch(`${baseUrl}/chat/completions`, {\n"
    "      method: 'POST',\n"
    "      headers,\n"
    "      body: JSON.stringify(body),\n"
    "      signal: arAiState.abortController.signal\n"
    "    });\n"
    "    if (!resp.ok) { await _arThrowAPIError(resp); }",
    "    let resp;\n"
    "    try {\n"
    "      resp = await fetch(`${baseUrl}/chat/completions`, {\n"
    "        method: 'POST', headers,\n"
    "        body: JSON.stringify(body),\n"
    "        signal: arAiState.abortController.signal\n"
    "      });\n"
    "    } catch(fetchErr) {\n"
    "      _arHandleFetchError(fetchErr, `${baseUrl}/chat/completions`);\n"
    "      throw fetchErr;\n"
    "    }\n"
    "    if (!resp.ok) { await _arThrowAPIError(resp); }"
))

# ── Edit 4：在 _callOpenAI 前插入兩個工具函式 ────────────────────────────
patches.append((
    "  async function _callOpenAI(messages, model, baseUrl, cfg, msgEl) {",
    "  /**\n"
    "   * 清理 baseUrl\n"
    "   * - 移除所有空白（含 copy-paste 帶入的空格，如 v1%20/…）\n"
    "   * - 去除尾端多餘的 API 路徑（/chat/completions、/messages 等）\n"
    "   * 例：'https://api.x.com/v1 '         → 'https://api.x.com/v1'\n"
    "   *     'https://api.x.com/v1/chat/completions' → 'https://api.x.com/v1'\n"
    "   */\n"
    "  function _arNormalizeBaseUrl(url) {\n"
    "    if (!url) return '';\n"
    "    // 移除所有空白字元（空格、tab、全形空白等）\n"
    "    url = url.replace(/[\\s\\u3000]+/g, '');\n"
    "    // 去除尾端常見 API 路徑後綴\n"
    "    url = url\n"
    "      .replace(/\\/chat\\/completions\\/?$/, '')\n"
    "      .replace(/\\/messages\\/?$/, '')\n"
    "      .replace(/\\/completions\\/?$/, '')\n"
    "      .replace(/\\/$/, '');\n"
    "    return url;\n"
    "  }\n"
    "\n"
    "  /**\n"
    "   * 偵測 CORS / file:// 錯誤並顯示中文建議\n"
    "   */\n"
    "  function _arHandleFetchError(err, url) {\n"
    "    const isFileOrigin = window.location.protocol === 'file:';\n"
    "    const msg = (err?.message || String(err)).toLowerCase();\n"
    "    const isCors = msg.includes('cors') || msg.includes('failed to fetch')\n"
    "                || msg.includes('network') || msg.includes('load');\n"
    "    if (isFileOrigin && isCors) {\n"
    "      appendAIError(\n"
    "        '⚠️ CORS 封鎖（file:// 限制）\\n' +\n"
    "        '直接用瀏覽器開啟 .html 檔時，API 請求常被 CORS 擋下。\\n\\n' +\n"
    "        '解決方式（擇一）：\\n' +\n"
    "        '① 命令列執行：npx serve .  然後用 http://localhost:3000 開啟\\n' +\n"
    "        '② VS Code 安裝 Live Server 擴充套件後右鍵 → Open with Live Server\\n' +\n"
    "        '③ 確認中轉商後端已設定 Access-Control-Allow-Origin: *'\n"
    "      );\n"
    "    } else {\n"
    "      appendAIError('網路錯誤：' + (err?.message || err) + '\\n目標 URL：' + url);\n"
    "    }\n"
    "  }\n"
    "\n"
    "  async function _callOpenAI(messages, model, baseUrl, cfg, msgEl) {"
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
