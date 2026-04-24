/**
 * AR 量子智慧戰情室 — Vercel Serverless CORS Proxy
 *
 * 路徑：api/proxy/[...path].js
 * 執行環境：Vercel Serverless Function（新加坡 / 香港節點）
 * 指定亞洲節點，確保可連到 nengpa.com 等亞洲 API
 */

const TIMEOUT_MS = 25000;

/** 不轉傳的 hop-by-hop headers */
const SKIP_REQ = new Set([
  'host', 'content-length', 'connection', 'transfer-encoding',
  'te', 'trailer', 'upgrade', 'x-proxy-target',
  'x-forwarded-for', 'x-forwarded-host', 'x-forwarded-proto',
]);

/** 不從上游複製回來的 CORS headers */
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

export default async function handler(req, res) {
  // ── CORS preflight ───────────────────────────────────────────────────────
  Object.entries(CORS_HEADERS).forEach(([k, v]) => res.setHeader(k, v));

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  // ── 取得目標 Base URL ────────────────────────────────────────────────────
  const targetBase = (req.headers['x-proxy-target'] || '').trim().replace(/\/$/, '');
  if (!targetBase) {
    return res.status(400).json({ error: 'X-Proxy-Target header 未提供，無法轉發' });
  }

  // ── 組合目標 URL ─────────────────────────────────────────────────────────
  const restPath = (req.url || '').replace(/^\/api\/proxy/, '') || '';
  const targetUrl = targetBase + restPath;

  // ── 轉傳 Headers ─────────────────────────────────────────────────────────
  const forwardHeaders = {};
  for (const [k, v] of Object.entries(req.headers)) {
    if (!SKIP_REQ.has(k.toLowerCase())) {
      forwardHeaders[k] = v;
    }
  }

  // ── 讀取 Request Body ────────────────────────────────────────────────────
  let bodyBuffer;
  if (req.method !== 'GET' && req.method !== 'HEAD') {
    bodyBuffer = await new Promise((resolve, reject) => {
      const chunks = [];
      req.on('data', chunk => chunks.push(chunk));
      req.on('end', () => resolve(Buffer.concat(chunks)));
      req.on('error', reject);
    });
  }

  // ── 逾時控制 ─────────────────────────────────────────────────────────────
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), TIMEOUT_MS);

  // ── 發出請求至上游 ────────────────────────────────────────────────────────
  let upstream;
  try {
    upstream = await fetch(targetUrl, {
      method: req.method,
      headers: forwardHeaders,
      body: bodyBuffer && bodyBuffer.length > 0 ? bodyBuffer : undefined,
      signal: controller.signal,
    });
    clearTimeout(timeoutId);
  } catch (err) {
    clearTimeout(timeoutId);
    console.error('[AR-Proxy] fetch error:', err.name, String(err));
    const isTimeout = err.name === 'AbortError';
    return res.status(isTimeout ? 504 : 502).json({
      error: isTimeout
        ? `上游 API 逾時（>${TIMEOUT_MS / 1000}s）：${targetUrl}`
        : `連線失敗：${String(err)}`,
      target: targetUrl,
    });
  }

  // ── 回傳上游的 Status & Headers ──────────────────────────────────────────
  res.status(upstream.status);
  upstream.headers.forEach((v, k) => {
    if (!SKIP_RESP.has(k.toLowerCase())) {
      res.setHeader(k, v);
    }
  });

  // ── 串流回應 ──────────────────────────────────────────────────────────────
  const reader = upstream.body.getReader();
  const stream = new ReadableStream({
    start(controller) {
      const push = () => {
        reader.read().then(({ done, value }) => {
          if (done) { controller.close(); return; }
          controller.enqueue(value);
          push();
        }).catch(e => controller.error(e));
      };
      push();
    }
  });

  const { Readable } = await import('node:stream');
  const nodeStream = Readable.fromWeb(stream);
  nodeStream.pipe(res);
}
