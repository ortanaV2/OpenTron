"""
http_server.py – Statischer HTTP-Server
Liefert index.html und game.js an den Browser aus.
"""

import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

HTTP_PORT = 8080

MIME = {
    ".html": "text/html; charset=utf-8",
    ".js":   "application/javascript; charset=utf-8",
    ".css":  "text/css; charset=utf-8",
    ".ico":  "image/x-icon",
}

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_GET(self):
        path = self.path.split("?")[0]
        if path == "/":
            path = "/index.html"

        base_dir  = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(base_dir, path.lstrip("/"))

        if not os.path.isfile(file_path):
            self.send_error(404, "Not Found")
            return

        ext      = os.path.splitext(file_path)[1]
        mimetype = MIME.get(ext, "application/octet-stream")

        with open(file_path, "rb") as f:
            data = f.read()

        self.send_response(200)
        self.send_header("Content-Type",   mimetype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def start(port: int = HTTP_PORT):
    srv = HTTPServer(("0.0.0.0", port), Handler)
    t   = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    return srv