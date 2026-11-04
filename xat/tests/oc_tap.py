#!/usr/bin/env python3
"""Logging proxy between OpenClicky and Ollama (test only): records the assembled model reply of each /v1/responses call
(including the private [POINT:...] / [RECT:...] control tags) to /tmp/oc-tap.log.  Usage: oc_tap.py [listen=127.0.0.1:11436]
Run OpenClicky against it:  open --env OPENAI_BASE_URL=http://127.0.0.1:11436/v1 OpenClicky.app"""
import json, sys, time, urllib.request, urllib.error
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
UP = "http://127.0.0.1:11434"; LOG = "/tmp/oc-tap.log"
class H(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.0"
    def log_message(self, *a): pass
    def _fwd(self, body):
        req = urllib.request.Request(UP + self.path, data=body, method=self.command)
        for h in ("Content-Type", "Authorization", "Accept"):
            if self.headers.get(h): req.add_header(h, self.headers[h])
        try: resp = urllib.request.urlopen(req, timeout=600)
        except urllib.error.HTTPError as e: resp = e
        self.send_response(resp.status if hasattr(resp, "status") else resp.code)
        for h in ("Content-Type", "Cache-Control"):
            if resp.headers.get(h): self.send_header(h, resp.headers[h])
        self.end_headers(); text = ""; t0 = time.time(); whole = b""
        for raw in resp:
            self.wfile.write(raw); self.wfile.flush(); whole += raw
            line = raw.decode("utf-8", "replace").strip()
            if line.startswith("data:") and "output_text.delta" in line:
                try: text += json.loads(line[5:]).get("delta", "")
                except ValueError: pass
        if not text and whole.lstrip().startswith(b"{"):          # non-streaming JSON response
            try:
                d = json.loads(whole)
                text = "".join(c.get("text", "") for o in d.get("output", []) for c in o.get("content", []) if isinstance(c, dict))
            except ValueError: pass
        if text:
            with open(LOG, "a") as f: f.write(json.dumps({"t": time.strftime("%H:%M:%S"), "secs": round(time.time() - t0, 1), "reply": text}) + "\n")
    def do_GET(self): self._fwd(None)
    def do_POST(self): self._fwd(self.rfile.read(int(self.headers.get("Content-Length", 0))))
host, port = (sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1:11436").rsplit(":", 1)
ThreadingHTTPServer((host, int(port)), H).serve_forever()
