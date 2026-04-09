import http.server
import socketserver
import urllib.request
import urllib.error
import json

PORT = 8000
FD_TOKEN = "869ec877a0d54c8ba4cd34ca18bcefe1"
FD_BASE   = "https://api.football-data.org"

class ProxyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):

    def _json(self, data, status=200):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type",  "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        # Proxy /v4/... → football-data.org/v4/...
        if self.path.startswith("/v4/"):
            url = FD_BASE + self.path
            try:
                req = urllib.request.Request(url, headers={"X-Auth-Token": FD_TOKEN})
                with urllib.request.urlopen(req, timeout=10) as resp:
                    body = resp.read()
                    self.send_response(resp.status)
                    for k, v in resp.getheaders():
                        if k.lower() not in ("access-control-allow-origin",
                                             "transfer-encoding", "connection",
                                             "content-encoding"):
                            self.send_header(k, v)
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.end_headers()
                    self.wfile.write(body)
            except urllib.error.HTTPError as e:
                body = e.read()
                self.send_response(e.code)
                self.send_header("Content-Type",  "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(body)
            except Exception as e:
                self.send_response(500)
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(str(e).encode())
        else:
            super().do_GET()

    def log_message(self, fmt, *args):
        print(f"[{self.date_time_string()}] {fmt % args}")

socketserver.TCPServer.allow_reuse_address = True
with socketserver.TCPServer(("", PORT), ProxyHTTPRequestHandler) as httpd:
    print(f"✅  FootballIQ proxy running at http://localhost:{PORT}")
    print(f"    Source: football-data.org  |  Competitions: PL CL BL1 SA PD FL1 DED PPL ELC BSA")
    httpd.serve_forever()
