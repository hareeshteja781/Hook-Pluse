from http.server import BaseHTTPRequestHandler, HTTPServer

class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length).decode("utf-8")
        print("RECEIVER_BODY", body, flush=True)
        print("RECEIVER_EVENT", self.headers.get("X-Hook-Event-ID"), flush=True)
        print("RECEIVER_SIGNATURE", self.headers.get("X-Hook-Signature"), flush=True)
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ok")

    def log_message(self, format, *args):
        return

HTTPServer(("127.0.0.1", 8999), Handler).handle_request()
