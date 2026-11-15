"""Local-only HTTP receiver used while the cloud service is unavailable."""

import json
from http.server import BaseHTTPRequestHandler, HTTPServer


class Receiver(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            length = int(self.headers["Content-Length"])
            payload = json.loads(self.rfile.read(length))
        except (KeyError, ValueError, UnicodeDecodeError) as error:
            print(f"Invalid request: {error}", flush=True)
            self.send_response(400)
        else:
            print(f"Local telemetry: {json.dumps(payload)}", flush=True)
            self.send_response(200)
        self.end_headers()


HTTPServer(("0.0.0.0", 18080), Receiver).serve_forever()
