#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AR 量子智慧戰情室 V5.4_AI → V5.5_AI
修正（來自實戰坑記錄）：
  A. MiniMax system message 合併（防止 error 2013 invalid chat setting）
  B. reasoning_split 僅在原廠端點才加（防止中轉商 HTTP 400）
  C. reasoning_details / reasoning_content 串流 & 非串流解析
  D. _arHandleFetchError 加強——localhost 也能偵測 CORS

執行：python patch_v55_minimax.py
輸出：AR 量子智慧戰情室 V5.5_AI.html
"""

import os

SRC  = os.path.join(os.path.dirname(__file__), 'AR 量子智慧戰情室 V5.4_AI.html')
DEST = os.path.join(os.path.dirname(__file__), 'AR 量子智慧戰情室 V5.5_AI.html')

with open(SRC, encoding='utf-8') as f:
    html = f.read()

patches = []

# ── Edit 1：_arHandleFetchError — 移除 file:// 判斷，所有 CORS 都給提示 ──
patches.append((
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
    "  }",
    "  function _arHandleFetchError(err, url) {\n"
    "    const msg = (err?.message || String(err)).toLowerCase();\n"
    "    const isCors = msg.includes('cors') || msg.includes('failed to fetch')\n"
    "                || msg.includes('network') || msg.includes('load')\n"
    "                || msg.includes('blocked');\n"
    "    if (isCors) {\n"
    "      appendAIError(\n"
    "        '⚠️ Failed to fetch — 常見原因與解法：\\n\\n' +\n"
    "        '① CORS 封鎖：中轉商未設定 Access-Control-Allow-Origin: *\\n' +\n"
    "        '   → 聯繫中轉商確認 CORS 設定，或換一個支援的端點\\n\\n' +\n"
    "        '② API Key 錯誤或已過期\\n' +\n"
    "        '   → 重新確認 Key 後按「💾 儲存設定」\\n\\n' +\n"
    "        '③ 端點 URL 不正確（只需填到 /v1）\\n' +\n"
    "        '   → 目前端點：' + url + '\\n\\n' +\n"
    "        '④ 若仍用 file:// 開啟：改用 python -m http.server 9090 啟動本機伺服器'\n"
    "      );\n"
    "    } else {\n"
    "      appendAIError('網路錯誤：' + (err?.message || err) + '\\n目標 URL：' + url);\n"
    "    }\n"
    "  }"
))

# ── Edit 2：_callOpenAI 完整替換（三大修正 A / B / C） ────────────────────
patches.append((
    "  async function _callOpenAI(messages, model, baseUrl, cfg, msgEl) {\n"
    "    const headers = { 'Content-Type': 'application/json', 'Authorization': `Bearer ${cfg.key}` };\n"
    "    // OpenRouter 必要標頭\n"
    "    if (arAiState.provider === 'openrouter') {\n"
    "      headers['HTTP-Referer'] = window.location.href || 'https://ar-dashboard.local';\n"
    "      headers['X-Title'] = 'AR 量子智慧戰情室';\n"
    "    }\n"
    "    const body = { model, messages, temperature: cfg.temp, max_tokens: cfg.maxTok, stream: cfg.stream };\n"
    "    // Minimax：thinking 模型需要 reasoning_split\n"
    "    if (arAiState.provider === 'minimax' &&\n"
    "        (model.includes('M2.7') || model.includes('M2.5') || model.includes('M2.1'))) {\n"
    "      body.reasoning_split = true;\n"
    "    }\n"
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
    "    if (!resp.ok) { await _arThrowAPIError(resp); }\n"
    "    let fullText = '';\n"
    "    if (cfg.stream) {\n"
    "      const reader  = resp.body.getReader();\n"
    "      const decoder = new TextDecoder();\n"
    "      let buf = '';\n"
    "      while (true) {\n"
    "        const { done, value } = await reader.read();\n"
    "        if (done) break;\n"
    "        buf += decoder.decode(value, { stream: true });\n"
    "        const lines = buf.split('\\n'); buf = lines.pop();\n"
    "        for (const line of lines) {\n"
    "          const t = line.trim();\n"
    "          if (!t.startsWith('data: ')) continue;\n"
    "          const data = t.slice(6);\n"
    "          if (data === '[DONE]') break;\n"
    "          try {\n"
    "            const delta = JSON.parse(data).choices?.[0]?.delta?.content || '';\n"
    "            fullText += delta; _arUpdateMsgEl(msgEl, fullText);\n"
    "          } catch {}\n"
    "        }\n"
    "      }\n"
    "    } else {\n"
    "      const json = await resp.json();\n"
    "      fullText = json.choices?.[0]?.message?.content || '';\n"
    "      _arUpdateMsgEl(msgEl, fullText);\n"
    "    }\n"
    "    return fullText;\n"
    "  }",

    "  async function _callOpenAI(messages, model, baseUrl, cfg, msgEl) {\n"
    "    // ── Fix A：MiniMax 嚴格規定 System 只能有一條，合併所有 system 訊息 ──\n"
    "    const cleanMsgs = [];\n"
    "    let sysContent = '';\n"
    "    for (const m of messages) {\n"
    "      if (m.role === 'system') sysContent += (sysContent ? '\\n\\n' : '') + m.content;\n"
    "      else cleanMsgs.push(m);\n"
    "    }\n"
    "    if (sysContent) cleanMsgs.unshift({ role: 'system', content: sysContent });\n"
    "\n"
    "    const headers = { 'Content-Type': 'application/json', 'Authorization': `Bearer ${cfg.key}` };\n"
    "    // OpenRouter 必要標頭\n"
    "    if (arAiState.provider === 'openrouter') {\n"
    "      headers['HTTP-Referer'] = window.location.href || 'https://ar-dashboard.local';\n"
    "      headers['X-Title'] = 'AR 量子智慧戰情室';\n"
    "    }\n"
    "\n"
    "    const body = {\n"
    "      model,\n"
    "      messages: cleanMsgs,\n"
    "      temperature: cfg.temp,\n"
    "      max_tokens: cfg.maxTok,\n"
    "      stream: cfg.stream\n"
    "    };\n"
    "\n"
    "    // ── Fix B：reasoning_split 僅在原廠端點才加（中轉商會 400）──\n"
    "    if (arAiState.provider === 'minimax' &&\n"
    "        (baseUrl.includes('minimaxi.com') || baseUrl.includes('minimax.chat'))) {\n"
    "      body.reasoning_split = true;\n"
    "    }\n"
    "\n"
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
    "    if (!resp.ok) { await _arThrowAPIError(resp); }\n"
    "\n"
    "    let fullText = '';\n"
    "    if (cfg.stream) {\n"
    "      const reader  = resp.body.getReader();\n"
    "      const decoder = new TextDecoder();\n"
    "      let buf = '';\n"
    "      while (true) {\n"
    "        const { done, value } = await reader.read();\n"
    "        if (done) break;\n"
    "        buf += decoder.decode(value, { stream: true });\n"
    "        const lines = buf.split('\\n'); buf = lines.pop();\n"
    "        for (const line of lines) {\n"
    "          const t = line.trim();\n"
    "          if (!t.startsWith('data: ')) continue;\n"
    "          const d = t.slice(6);\n"
    "          if (d === '[DONE]') break;\n"
    "          try {\n"
    "            const parsed = JSON.parse(d);\n"
    "            const delta  = parsed.choices?.[0]?.delta || {};\n"
    "            let newText  = '';\n"
    "            // ── Fix C：MiniMax reasoning_details 串流解析 ──\n"
    "            if (Array.isArray(delta.reasoning_details)) {\n"
    "              delta.reasoning_details.forEach(r => { if (r.text) newText += r.text; });\n"
    "            }\n"
    "            // DeepSeek / 其他模型 reasoning 相容\n"
    "            if (delta.reasoning_content) newText += delta.reasoning_content;\n"
    "            // 正文\n"
    "            if (delta.content) newText += delta.content;\n"
    "            if (newText) { fullText += newText; _arUpdateMsgEl(msgEl, fullText); }\n"
    "          } catch {}\n"
    "        }\n"
    "      }\n"
    "    } else {\n"
    "      // ── Fix C（非串流）：MiniMax reasoning_details 解析 ──\n"
    "      const json = await resp.json();\n"
    "      const msg  = json.choices?.[0]?.message || {};\n"
    "      let rText  = '';\n"
    "      if (Array.isArray(msg.reasoning_details)) {\n"
    "        msg.reasoning_details.forEach(r => { if (r.text) rText += r.text; });\n"
    "      }\n"
    "      if (msg.reasoning_content) rText += msg.reasoning_content;\n"
    "      fullText = rText + (msg.content || '');\n"
    "      _arUpdateMsgEl(msgEl, fullText);\n"
    "    }\n"
    "    return fullText;\n"
    "  }"
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
