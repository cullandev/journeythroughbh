#!/usr/bin/env python3
"""
Tiny no-Node preview server for public/. Mimics Workers' auto-trailing-slash
HTML handling (/about -> about.html), serves 404.html for unknown paths, and
fakes POST /api/contact so the form can be exercised without wrangler.

    python scripts/preview.py            # http://localhost:8788

For the real thing (Turnstile verification, email delivery) use `wrangler dev`.
"""
import http.server
import json
import socketserver
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1] / "public"
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8788


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(ROOT), **kw)

    def translate_path(self, path):
        p = urlparse(path).path
        if p == "/":
            return str(ROOT / "index.html")
        candidate = ROOT / p.lstrip("/")
        if candidate.is_file():
            return str(candidate)
        if not candidate.suffix and (ROOT / (p.strip("/") + ".html")).is_file():
            return str(ROOT / (p.strip("/") + ".html"))
        return str(ROOT / "__missing__")

    def send_head(self):
        if self.translate_path(self.path).endswith("__missing__"):
            body = (ROOT / "404.html").read_bytes()
            self.send_response(404)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            import io
            return io.BytesIO(body)
        return super().send_head()

    def do_POST(self):
        if urlparse(self.path).path != "/api/contact":
            self.send_error(404)
            return
        length = int(self.headers.get("Content-Length") or 0)
        self.rfile.read(length)  # discard; nothing is validated in preview mode
        if "application/json" in (self.headers.get("Accept") or ""):
            body = json.dumps({"ok": True}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(303)
            self.send_header("Location", "/thank-you")
            self.end_headers()

    def log_message(self, fmt, *args):
        sys.stderr.write("%s %s\n" % (self.command, self.path))


socketserver.TCPServer.allow_reuse_address = True
with socketserver.TCPServer(("127.0.0.1", PORT), Handler) as httpd:
    print(f"preview: http://localhost:{PORT}  (Ctrl+C to stop)")
    httpd.serve_forever()
