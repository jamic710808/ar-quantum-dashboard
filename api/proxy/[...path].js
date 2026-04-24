/**
 * AR 量子智慧戰情室 — Vercel Edge Function CORS Proxy
 * 路徑：api/proxy/[...path].js
 * 執行環境：Vercel Edge Runtime
 */

export const config = { runtime: 'edge' };

const SKIP_REQ = new Set([
  'host', 'content-length', 'connection', 'transfer-encoding',
  'te', 'trailer', 'upgrade', 'x-proxy-target',
  'x-forwarded-for', 'x-forwarded-host', 'x-forwarded-proto',
]);

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
  if (req.method === 'OPTIONS') {
    return new Response(null, {
      status: 200,
      headers: { ...CORS_HEADERS, 'Content-Length': '0' },
    });
  }

  const targetBase = req.headers.get('x-proxy-target')?.trim().replace(/\/$/, '');
  if (!targetBase) {
    return new Response(
      JSON.stringify({ error: 'X-Proxy-Target header 未提供' }),
      { status: 400, headers: { 'Content-Type': 'application/json', ...CORS_HEADERS } }
    );
  }

  const url = new URL(req.url);
  const restPath = url.pathname.replace(/^\/api\/proxy/, '') || '';
  const targetUrl = targetBase + restPath;

  const forwardHeaders = {};
  for (const [k, v] of req.headers.entries()) {
    if (!SKIP_REQ.has(k.toLowerCase())) {
      forwardHeaders[k] = v;
    }
  }

  const body =
    req.method !== 'GET' && req.method !== 'HEAD'
      ? await req.arrayBuffer()
      : undefined;

  let upstream;
  try {
    upstream = await fetch(targetUrl, {
      method: req.method,
      headers: forwardHeaders,
      body: body && body.byteLength > 0 ? body : undefined,
    });
  } catch (err) {
    return new Response(
      JSON.stringify({ error: '連線失敗：' + String(err), target: targetUrl }),
      { status: 502, headers: { 'Content-Type': 'application/json', ...CORS_HEADERS } }
    );
  }

  const respHeaders = new Headers(CORS_HEADERS);
  for (const [k, v] of upstream.headers.entries()) {
    if (!SKIP_RESP.has(k.toLowerCase())) {
      respHeaders.set(k, v);
    }
  }

  return new Response(upstream.body, {
    status: upstream.status,
    headers: respHeaders,
  });
}
