"""Local HTTP status-code practice server; stop with Ctrl+C."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = self.path.split("?", 1)[0]
        routes = {
            "/ok": (200, b"OK\n", {}),
            "/redirect": (302, b"Go to /ok\n", {"Location": "/ok"}),
            "/limited": (429, b"Demo rate limit\n", {"Retry-After": "30"}),
            "/error": (500, b"Demo server error\n", {}),
        }
        code, body, headers = routes.get(path, (404, b"Not found\n", {}))
        self.send_response(code)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        for name, value in headers.items():
            self.send_header(name, value)
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    with ThreadingHTTPServer(("127.0.0.1", 8766), Handler) as server:
        print("Demo: http://127.0.0.1:8766/ok (Ctrl+C to stop)", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
