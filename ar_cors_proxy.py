#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AR 量子智慧戰情室 — 一體化本機伺服器 v2
  ① 靜態檔案服務（開啟儀表板 HTML）
  ② 智慧 CORS Proxy（轉發至任意 API，目標由 X-Proxy-Target header 決定）

使用方式（只需一個指令）：
  python ar_cors_proxy.py            # 預設 Port 8765
  python ar_cors_proxy.py 9000       # 指定 Port

啟動後：
  1. 瀏覽器開啟 http://localhost:8765
  2. 點選 HTML 儀表板
  3. 端點 URL 照填原本的 https://api.xxx.com/v1
  4. 面板開啟「CORS 本機代理」開關即可（系統自動處理）
"""

import sys, ssl, json, os, mimetypes
import urllib.request, urllib.error
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, unquote

PORT      = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
SERVE_DIR = os.path.dirname(os.path.abspath(__file__))
PROXY_PATH = '/ar-proxy'   # 儀表板固定打這個路徑


class ARServerHandler(BaseHTTPRequestHandler):

    def _cors(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers',
                         'Authorization, Content-Type, x-api-key, '
                         'anthropic-version, HTTP-Referer, X-Title, X-Proxy-Target')

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors()
        self.send_header('Content-Length', '0')
        self.end_headers()

    def do_GET(self):
        if self.path.startswith(PROXY_PATH):
            self._proxy('GET')
        else:
            self._serve_static()

    def do_POST(self):
        if self.path.startswith(PROXY_PATH):
            self._proxy('POST')
        else:
            self.send_error(405)

    # ── 靜態檔案 ─────────────────────────────────────────────────────
    def _serve_static(self):
        path = unquote(self.path.split('?')[0])
        local = os.path.normpath(SERVE_DIR + path)
        if not local.startswith(SERVE_DIR):
            self.send_error(403); return
        if os.path.isdir(local):
            self._dir_listing(local, path); return
        if not os.path.isfile(local):
            self.send_error(404); return
        mime, _ = mimetypes.guess_type(local)
        mime = mime or 'application/octet-stream'
        with open(local, 'rb') as f:
            data = f.read()
        self.send_response(200)
        self.send_header('Content-Type', mime + ('; charset=utf-8' if 'text' in mime else ''))
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _dir_listing(self, local_dir, url_path):
        files = sorted(os.listdir(local_dir))
        rows = []
        for f in files:
            full  = os.path.join(local_dir, f)
            href  = (url_path.rstrip('/') + '/' + f).replace('//', '/')
            icon  = '📁 ' if os.path.isdir(full) else '📄 '
            size  = f'{os.path.getsize(full):,} B' if os.path.isfile(full) else '—'
            rows.append(
                f'<tr><td><a href="{href}">{icon}{f}</a></td>'
                f'<td style="color:#888">{size}</td></tr>'
            )
        rows = ''.join(rows)
        html = f'''<!DOCTYPE html><html><head><meta charset="utf-8"><title>AR 儀表板</title>
<style>body{{font-family:sans-serif;padding:24px;background:#0d0d1a;color:#ddd}}
h2{{color:#ffd700}}a{{color:#7ec8e3;text-decoration:none}}a:hover{{color:#ffd700}}
table{{border-collapse:collapse;width:100%}}td{{padding:7px 14px;border-bottom:1px solid #222}}
</style></head><body>
<h2>📁 AR 量子智慧戰情室 — 儀表板目錄</h2>
<table>{rows}</table>
<hr style="border-color:#333;margin-top:24px">
<small style="color:#555">AR CORS Proxy v2 · Port {PORT} · 端點填原始 URL，開啟面板「CORS 代理」即可</small>
</body></html>'''
        data = html.encode()
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    # ── CORS Proxy ────────────────────────────────────────────────────
    def _proxy(self, method):
        # 從 X-Proxy-Target header 取得真實目標
        target_base = self.headers.get('X-Proxy-Target', '').strip().rstrip('/')
        if not target_base:
            err = json.dumps({'error': 'X-Proxy-Target header 未提供，無法轉發'}).encode()
            self.send_response(400); self._cors()
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(err)))
            self.end_headers(); self.wfile.write(err); return

        # 路徑：移除 /ar-proxy 前綴，保留後面的 /v1/chat/completions 等
        rest = self.path[len(PROXY_PATH):]   # e.g. /chat/completions
        target_url = target_base + rest

        length = int(self.headers.get('Content-Length', 0))
        body   = self.rfile.read(length) if length else None

        parsed = urlparse(target_base)

        # 明確列出需要轉傳的 header（避免 urllib 自動剝除 Authorization）
        SKIP = {'host', 'content-length', 'connection',
                'transfer-encoding', 'te', 'trailer', 'x-proxy-target'}
        fwd_headers = {}
        for k, v in self.headers.items():
            if k.lower() not in SKIP:
                fwd_headers[k] = v
        fwd_headers['Host'] = parsed.netloc

        # ── Debug：印出轉傳的關鍵 headers ──
        auth_val = fwd_headers.get('Authorization') or fwd_headers.get('authorization', '')
        print(f'  [PROXY] → {target_url}')
        print(f'  [AUTH ] {"✅ Bearer …" + auth_val[-6:] if auth_val else "❌ 缺少 Authorization header"}')

        ctx = ssl.create_default_context()
        req = urllib.request.Request(target_url, data=body, method=method)
        for k, v in fwd_headers.items():
            req.add_unredirected_header(k, v)
        try:
            with urllib.request.urlopen(req, context=ctx, timeout=120) as r:
                self.send_response(r.status)
                self._cors()
                for k, v in r.headers.items():
                    if k.lower() in ('access-control-allow-origin',
                                     'access-control-allow-headers',
                                     'access-control-allow-methods',
                                     'transfer-encoding', 'connection'):
                        continue
                    self.send_header(k, v)
                self.end_headers()
                while True:
                    chunk = r.read(4096)
                    if not chunk: break
                    try: self.wfile.write(chunk); self.wfile.flush()
                    except BrokenPipeError: break

        except urllib.error.HTTPError as e:
            body_err = e.read()
            self.send_response(e.code); self._cors()
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(body_err)))
            self.end_headers(); self.wfile.write(body_err)

        except Exception as ex:
            msg = json.dumps({'error': str(ex)}).encode()
            self.send_response(502); self._cors()
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(msg)))
            self.end_headers(); self.wfile.write(msg)

    def log_message(self, fmt, *args):
        try:
            status = args[1]
            path   = args[0].split('"')[1] if '"' in args[0] else args[0]
            print(f'  [{status}] {path}')
        except Exception:
            pass


if __name__ == '__main__':
    print('=' * 58)
    print(f'  AR 量子智慧戰情室 — 本機伺服器 v2')
    print(f'  服務目錄：{SERVE_DIR}')
    print()
    print(f'  瀏覽器開啟：http://localhost:{PORT}')
    print()
    print(f'  ✅ 端點 URL 照填原本的 https://api.xxx.com/v1')
    print(f'     面板開啟「CORS 本機代理」開關，系統自動轉發')
    print('=' * 58)
    server = HTTPServer(('', PORT), ARServerHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\n伺服器已停止。')
