"""Run with python3 app.py. Standard library only."""

import argparse
import json
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs
from experiment import run

ROOT = Path(__file__).parent / "static"


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def do_GET(self):
        route = urlparse(self.path)
        if route.path == "/api/experiment":
            try:
                q = parse_qs(route.query)
                result = run(
                    int(q.get("seed", ["42"])[0]),
                    int(q.get("budget", ["32"])[0]),
                    int(q.get("repeats", ["20"])[0]),
                )
                body = json.dumps(result, allow_nan=False).encode()
                self.send_response(200)
                if q.get("download") == ["1"]:
                    filename = f"simulated-results-seed-{result['seed']}-patches-{result['budget']}.json"
                    self.send_header(
                        "Content-Disposition", f'attachment; filename="{filename}"'
                    )
            except (ValueError, TypeError) as error:
                body = json.dumps({"error": str(error)}).encode()
                self.send_response(400)
            self.send_header("Content-Type", "application/json")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            super().do_GET()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print(f"Open http://127.0.0.1:{args.port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()
