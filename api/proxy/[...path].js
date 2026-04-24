/**
 * AR 量子智慧戰情室 — Vercel Edge Function CORS Proxy
 *
 * 路徑：api/proxy/[...path].js
 * 執行環境：Vercel Edge Runtime（全球低延遲，支援 SSE Streaming）
 *
 * 運作原理：
 *   瀏覽器  →  POST /api/proxy/chat/completions  (X-Proxy-Target: https://api.nengpa.com/v1)
 *           →  Vercel Edge Function 轉發至 https://api.nengpa.com/v1/chat/completions
 *           →  回應直接串流回瀏覽器（無 CORS 問題，因為是同域請求）
 */

export const config = { runtime: 'edge' };

/** 不轉傳的 hop-by-hop / proxy-specific headers */
const SKIP_REQ = new Set([
  'host', 'content-length', 'connection', 'transfer-encoding',
  'te', 'trailer', 'upgrade', 'x-proxy-target',
  'x-forwarded-for', 'x-forwarded-host', 'x-forwarded-proto',
]);

/** 不從上游複製回來的 headers（避免 CORS 重複） */
const SKIP_RESP = new Set([
  'access-control-allow-origin',
  'access-control-allow-headers',
  'access-control-allow-methods',
  'access-control-allow-credentials',
  'transfer-encoding',
  'connection',
]);

const CORS_HEADERS = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
  'Access-Control-Allow-Headers':
    'Authorization, Content-Type, x-api-key, anthropic-version, ' +
    'HTTP-Referer, X-Title, X-Proxy-Target',
};

export default async function handler(req) {
  // ── OPTIONS preflight ────────────────────────────────────────────────────
  if (req.method === 'OPTIONS') {
    return new Response(null, {
      status: 200,
      headers: { ...CORS_HEADERS, 'Content-Length': '0' },
    });
  }

  // ── 取得目標 Base URL ────────────────────────────────────────────────────
  const targetBase = req.headers.get('x-proxy-target')?.trim().replace(/\/$/, '');
  if (!targetBase) {
    return new Response(
      JSON.stringify({ error: 'X-Proxy-Target header 未提供，無法轉發' }),
      { status: 400, headers: { 'Content-Type': 'application/json', ...CORS_HEADERS } }
    );
  }

  // ── 組合完整目標 URL（/api/proxy/chat/completions → /chat/completions）───
  const url = new URL(req.url);
  const restPath = url.pathname.replace(/^\/api\/proxy/, '') || '';
  const targetUrl = targetBase + restPath;

  // ── 轉傳 Headers ─────────────────────────────────────────────────────────
  const forwardHeaders = {};
  for (const [k, v] of req.headers.entries()) {
    if (!SKIP_REQ.has(k.toLowerCase())) {
      forwardHeaders[k] = v;
    }
  }

  // ── Request Body ─────────────────────────────────────────────────────────
  const body =
    req.method !== 'GET' && req.method !== 'HEAD'
      ? await req.arrayBuffer()
      : undefined;

  // ── 發出請求至上游 ────────────────────────────────────────────────────────
  let upstream;
  try {
    upstream = await fetch(targetUrl, {
      method: req.method,
      headers: forwardHeaders,
      body: body && body.byteLength > 0 ? body : undefined,
    });
  } catch (err) {
    console.error('[AR-Proxy] fetch error:', err);
    return new Response(
      JSON.stringify({ error: '連線失敗：' + String(err) }),
      { status: 502, headers: { 'Content-Type': 'application/json', ...CORS_HEADERS } }
    );
  }

  // ── 組合回應 Headers（過濾重複 CORS）────────────────────────────────────
  const respHeaders = new Headers(CORS_HEADERS);
  for (const [k, v] of upstream.headers.entries()) {
    if (!SKIP_RESP.has(k.toLowerCase())) {
      respHeaders.set(k, v);
    }
  }

  // ── 直接串流回瀏覽器（支援 SSE / chunked）────────────────────────────────
  return new Response(upstream.body, {
    status: upstream.status,
    headers: respHeaders,
  });
}
