# -*- coding: utf-8 -*-
"""本地开发服务器：模拟 build.cfworkers 在 Cloudflare Workers 上的行为。

用法：python dev_server.py [port]
- /cn/... /jp/... 的 .php 走 kbdx_core（与 Worker 同一套逻辑）
- /cn/kbDX/main.swf、/jp/kbDX/main.swf 来自 swf/ 目录
- 其它文件来自 public/
"""

import http.server
import os
import socketserver
import sys
from urllib.parse import urlparse

import kbdx_core
import data_cn
import data_jp

ROOT = os.path.dirname(os.path.abspath(__file__))


def _load_cfg():
    path = os.path.join(ROOT, "server.properties")
    if not os.path.isfile(path):
        path = os.path.join(os.getcwd(), "server.properties")
    if not os.path.isfile(path):
        sys.stderr.write("missing config: server.properties\n")
        raise SystemExit(2)
    d = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or line.startswith(";") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            d[k.strip()] = v.strip()
    if not d.get("server.port"):
        sys.stderr.write("server.port missing in %s\n" % path)
        raise SystemExit(2)
    return d


CFG = _load_cfg()
PORT = int(CFG["server.port"])
DEBUG = CFG.get("server.debug", "false").lower() == "true"
LOGFILE = CFG.get("server.log", "false").lower() == "true"


def _log(line):
    if DEBUG:
        print(line, flush=True)
    if LOGFILE:
        try:
            os.makedirs(os.path.join(ROOT, "logs"), exist_ok=True)
            with open(os.path.join(ROOT, "logs", "requests.log"), "a", encoding="utf-8") as f:
                f.write(line + "\n")
        except Exception:
            pass
DATA = {}
DATA.update(data_cn.DATA)
DATA.update(data_jp.DATA)

_STORE = {}


class Store:
    """按语言隔离的持久化存储：cn:scores -> public/cn/kbDX/Ranking/scores.txt"""

    def _path(self, key):
        lang = key.split(":", 1)[0]
        return os.path.join(ROOT, "public", lang, "kbDX", "Ranking", "scores.txt")

    def get(self, key):
        if key in _STORE:
            return _STORE[key]
        p = self._path(key)
        if os.path.isfile(p):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    v = f.read()
                _STORE[key] = v
                return v
            except Exception:
                return None
        return None

    def set(self, key, value):
        _STORE[key] = value
        p = self._path(key)
        try:
            os.makedirs(os.path.dirname(p), exist_ok=True)
            with open(p, "w", encoding="utf-8") as f:
                f.write(value)
        except Exception:
            pass


STORE = Store()
CTYPES = {
    ".html": "text/html; charset=utf-8",
    ".swf": "application/x-shockwave-flash",
    ".js": "application/javascript; charset=utf-8",
    ".wasm": "application/wasm",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".tsv": "text/plain; charset=utf-8",
    ".php": "text/plain; charset=utf-8",
    ".txt": "text/plain; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".map": "application/json; charset=utf-8",
}


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=ROOT, **kw)

    def log_message(self, fmt, *args):
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))

    def do_GET(self):
        self.handle_any("GET", False)

    def do_HEAD(self):
        self.handle_any("GET", True)

    def do_POST(self):
        self.handle_any("POST", False)

    def handle_any(self, method, head_only):
        parsed = urlparse(self.path)
        path = parsed.path
        body = ""
        if method == "POST":
            n = int(self.headers.get("Content-Length", "0") or "0")
            body = self.rfile.read(n).decode("utf-8") if n else ""

        if DEBUG or LOGFILE:
            _log("%s %s %s" % (method, path, body))
        lang = "cn" if path.startswith("/cn/") else ("jp" if path.startswith("/jp/") else None)

        # SWF：优先读单文件，否则把 main.swf.partNN 合并后返回
        if path.endswith("/kbDX/main.swf"):
            single = os.path.join(ROOT, "public", lang or "cn", "kbDX", "main.swf")
            if os.path.isfile(single):
                self.send_file(single, "application/x-shockwave-flash", head_only)
                return
            base = os.path.join(ROOT, "public", lang or "cn", "kbDX")
            parts = []
            i = 1
            while True:
                f = os.path.join(base, "main.swf.part%02d" % i)
                if not os.path.isfile(f):
                    break
                parts.append(f)
                i += 1
            if parts:
                data = b"".join(open(f, "rb").read() for f in parts)
                self.send_response(200)
                self.send_header("Content-Type", "application/x-shockwave-flash")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                if not head_only:
                    self.wfile.write(data)
                return

        # PHP 接口
        if lang:
            r = kbdx_core.handle(lang, path, method, body, DATA, STORE)
            if r is not None:
                status, ctype, text = r
                data = text.encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", ctype)
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                if not head_only:
                    self.wfile.write(data)
                return

        # 静态文件
        rel = path.lstrip("/")
        f = os.path.join(ROOT, "public", rel) if rel else os.path.join(ROOT, "public", "index.html")
        if os.path.isdir(f):
            f = os.path.join(f, "index.html")
        if os.path.isfile(f):
            ext = os.path.splitext(f)[1].lower()
            self.send_file(f, CTYPES.get(ext, "application/octet-stream"), head_only)
            return
        self.send_error(404, "not found: " + path)

    def send_file(self, f, ctype, head_only=False):
        size = os.path.getsize(f)
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(size))
        self.end_headers()
        if head_only:
            return
        with open(f, "rb") as fh:
            while True:
                chunk = fh.read(256 * 1024)
                if not chunk:
                    break
                self.wfile.write(chunk)


def main():
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("127.0.0.1", PORT), Handler) as httpd:
        print("kbDX cfworkers dev server: http://127.0.0.1:%d/" % PORT)
        print("  中文: http://127.0.0.1:%d/cn/" % PORT)
        print("  日文: http://127.0.0.1:%d/jp/" % PORT)
        print("  debug=%s log=%s" % (DEBUG, LOGFILE))
        httpd.serve_forever()


if __name__ == "__main__":
    main()
