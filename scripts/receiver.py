from http.server import BaseHTTPRequestHandler, HTTPServer
import json

count = 0
last_body = ""

class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        global count, last_body
        length = int(self.headers.get("Content-Length", "0"))
        last_body = self.rfile.read(length).decode("utf-8")
        count += 1
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"ok":true}')

    def do_GET(self):
        if self.path != "/count":
            self.send_response(404); self.end_headers(); return
        body = json.dumps({"count": count, "last_body": last_body}).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        pass

HTTPServer(("0.0.0.0", 9000), Handler).serve_forever()
