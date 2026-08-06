"""
Minimal cookie-based auth service for PanBot Docs.
Replaces nginx basic auth with a proper session cookie.
"""
import os
import secrets
from datetime import datetime, timedelta
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

DOCS_PASSWORD = os.environ.get("DOCS_PASSWORD", "changeme")
COOKIE_NAME = "panbot_docs_session"
COOKIE_MAX_AGE = 60 * 60 * 24 * 7  # 7 days

# In-memory session store (fine for single-instance)
valid_tokens: set[str] = set()

LOGIN_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>PanBot Docs — Login</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
      background: #0f172a;
      display: flex;
      align-items: center;
      justify-content: center;
      min-height: 100vh;
      color: #e2e8f0;
    }}
    .card {{
      background: #1e293b;
      border: 1px solid #334155;
      border-radius: 12px;
      padding: 40px;
      width: 100%;
      max-width: 360px;
      box-shadow: 0 20px 60px rgba(0,0,0,0.5);
    }}
    .logo {{
      font-size: 1.5rem;
      font-weight: 700;
      margin-bottom: 8px;
      color: #f8fafc;
    }}
    .logo span {{ color: #6366f1; }}
    .subtitle {{
      font-size: 0.875rem;
      color: #94a3b8;
      margin-bottom: 32px;
    }}
    label {{
      display: block;
      font-size: 0.875rem;
      font-weight: 500;
      margin-bottom: 6px;
      color: #cbd5e1;
    }}
    input[type=password] {{
      width: 100%;
      padding: 10px 14px;
      background: #0f172a;
      border: 1px solid #475569;
      border-radius: 8px;
      color: #f1f5f9;
      font-size: 1rem;
      outline: none;
      transition: border-color 0.15s;
    }}
    input[type=password]:focus {{ border-color: #6366f1; }}
    button {{
      width: 100%;
      margin-top: 20px;
      padding: 11px;
      background: #6366f1;
      color: white;
      border: none;
      border-radius: 8px;
      font-size: 1rem;
      font-weight: 600;
      cursor: pointer;
      transition: background 0.15s;
    }}
    button:hover {{ background: #4f46e5; }}
    .error {{
      margin-top: 16px;
      padding: 10px 14px;
      background: #450a0a;
      border: 1px solid #7f1d1d;
      border-radius: 8px;
      font-size: 0.875rem;
      color: #fca5a5;
    }}
  </style>
</head>
<body>
  <div class="card">
    <div class="logo">Pan<span>Bot</span> Docs</div>
    <div class="subtitle">Internal documentation — authorized access only</div>
    <form method="POST" action="/auth/login">
      <input type="hidden" name="next" value="{next}">
      <label for="password">Password</label>
      <input type="password" id="password" name="password" autofocus placeholder="Enter password">
      <button type="submit">Sign in →</button>
      {error}
    </form>
  </div>
</body>
</html>"""


class AuthHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # suppress access logs

    def _get_cookie_token(self):
        cookies = self.headers.get("Cookie", "")
        for part in cookies.split(";"):
            part = part.strip()
            if part.startswith(f"{COOKIE_NAME}="):
                return part[len(f"{COOKIE_NAME}="):]
        return None

    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path == "/auth/validate":
            token = self._get_cookie_token()
            if token and token in valid_tokens:
                self.send_response(200)
                self.end_headers()
            else:
                self.send_response(401)
                self.end_headers()
            return

        if parsed.path == "/auth/login":
            next_url = parse_qs(parsed.query).get("next", ["/"])[0]
            body = LOGIN_HTML.format(next=next_url, error="").encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        if self.path.startswith("/auth/login"):
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode()
            params = parse_qs(body)
            password = params.get("password", [""])[0]
            next_url = params.get("next", ["/"])[0]

            if password == DOCS_PASSWORD:
                token = secrets.token_urlsafe(32)
                valid_tokens.add(token)
                expires = (datetime.utcnow() + timedelta(seconds=COOKIE_MAX_AGE)).strftime(
                    "%a, %d %b %Y %H:%M:%S GMT"
                )
                self.send_response(302)
                self.send_header("Location", next_url or "/")
                self.send_header(
                    "Set-Cookie",
                    f"{COOKIE_NAME}={token}; Path=/; Expires={expires}; HttpOnly; SameSite=Lax"
                )
                self.end_headers()
            else:
                error_html = '<div class="error">Incorrect password. Please try again.</div>'
                html = LOGIN_HTML.format(next=next_url, error=error_html).encode()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(html)))
                self.end_headers()
                self.wfile.write(html)
            return

        self.send_response(404)
        self.end_headers()


if __name__ == "__main__":
    port = int(os.environ.get("AUTH_PORT", 4322))
    server = HTTPServer(("0.0.0.0", port), AuthHandler)
    print(f"Auth service running on :{port}")
    server.serve_forever()
