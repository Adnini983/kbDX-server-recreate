# -*- coding: utf-8 -*-
"""协议回归测试：验证 Java / Python 服务端字段映射一致，并覆盖主要接口。

无需第三方依赖；需要 java 与 python3 在 PATH 中。
用法：python tests/protocol_test.py
"""

import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CHRS = "1BU8kTlE6dZ9.Dz-Afe2gF5hvi4wOmjq3xpuGIXsJL7cMrRSnN0CKoPyHbVtQaY_W"

FIXTURE = """choice\t1\t测试四选一\t甲\t乙||丙||丁\t\t
ox\t1\t测试判断\tＯ\t\t\t
typing\t1\t测试打字\t１９９２\t\t\t
order\t1\t测试排序\tA||B||C\t\t0\t
line\t1\t测试连线\t甲||乙||丙\t一||二||三\t\t
group\t1\t测试分组\t组一||组二\t甲/乙||丙/丁\t4\t
multityping\t1\t测试多答\t1992/2018\t\t4\t
"""

EXPECTED_TYPE = {
    "测试四选一": ("2", "2"),
    "测试判断": ("1", "2"),
    "测试打字": ("7", "2"),
    "测试排序": ("13", "2"),
    "测试连线": ("11", "2"),
    "测试分组": ("14", "2"),
    "测试多答": ("17", "2"),
}


def decode65(s):
    out = []
    for i in range(0, len(s) - 2, 3):
        out.append(chr(CHRS.index(s[i]) * 4225 + CHRS.index(s[i + 1]) * 65 + CHRS.index(s[i + 2])))
    return "".join(out)


def free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


def post(port, path, data):
    body = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request("http://127.0.0.1:%d%s" % (port, path), data=body)
    return urllib.request.urlopen(req, timeout=15).read().decode("utf-8")


def wait_up(port, proc, timeout=25):
    end = time.time() + timeout
    while time.time() < end:
        if proc.poll() is not None:
            raise RuntimeError("server exited early: %s" % proc.stdout.read() if proc.stdout else "exit")
        try:
            post(port, "/cn/kbDX/T.php", {})
            return
        except Exception:
            time.sleep(0.5)
    raise RuntimeError("server did not start on %d" % port)


class Server:
    def __init__(self, kind, port):
        self.kind = kind
        self.port = port
        self.proc = None
        self.tmp = tempfile.mkdtemp(prefix="kbdx_test_")

    def prepare(self):
        if self.kind == "python":
            src = os.path.join(ROOT, "python")
            dst = os.path.join(self.tmp, "python")
            shutil.copytree(src, dst)
            bank = os.path.join(dst, "public", "cn", "kbDX", "SKR", "questions.tsv")
            os.makedirs(os.path.dirname(bank), exist_ok=True)
            open(bank, "w", encoding="utf-8").write(FIXTURE)
            # 题库内嵌在 data_cn.py 的 DATA 字典里，追加覆盖
            with open(os.path.join(dst, "data_cn.py"), "a", encoding="utf-8") as f:
                f.write("\nDATA[\"cn/kbDX/SKR/questions.tsv\"] = %r\n" % FIXTURE)
            cfg = os.path.join(dst, "server.properties")
            open(cfg, "w", encoding="utf-8").write("server.port=%d\nserver.debug=false\nserver.log=false\n" % self.port)
            self.cwd = dst
            cmd = [sys.executable, "dev_server.py"]
        else:
            src = os.path.join(ROOT, "java")
            dst = os.path.join(self.tmp, "java")
            shutil.copytree(src, dst)
            bank = os.path.join(dst, "data", "cn", "kbDX", "SKR", "questions.tsv")
            open(bank, "w", encoding="utf-8").write(FIXTURE)
            q = os.path.join(dst, "data", "cn", "kbDX", "Qgene.php")
            open(q, "w", encoding="utf-8").write("type=questions\ndata=SKR/questions.tsv\ncount=25\nauthor=管理人\ndate=2026/11/08\nqns=DX2026\nevtdata=SKR/questions_evt.tsv\ntoken=1\n")
            open(os.path.join(dst, "server.properties"), "w", encoding="utf-8").write("server.port=%d\nserver.debug=false\nserver.log=false\n" % self.port)
            self.cwd = dst
            cmd = ["java", "-cp", os.path.join(dst, "build", "classes"), "KbdxServer"]
        return cmd

    def start(self):
        cmd = self.prepare()
        self.proc = subprocess.Popen(cmd, cwd=self.cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        wait_up(self.port, self.proc)

    def stop(self):
        if self.proc:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=5)
            except Exception:
                self.proc.kill()
        shutil.rmtree(self.tmp, ignore_errors=True)


def check_qgene(port):
    resp = post(port, "/cn/kbDX/Qgene.php", {"NUM": "1", "MOD": "1", "VER": "24"})
    segs = resp.split("?")
    assert len(segs) == 27, "Qgene 段数应为 27，实际 %d" % len(segs)
    assert segs[25], "缺少 QNs"
    seen = {}
    for seg in segs[:25]:
        f = seg.split(",")
        assert len(f) == 11, "题目字段应为 11，实际 %d" % len(f)
        text = decode65(f[6])
        d1, d2, d3, d4 = (decode65(x) for x in f[7:11])
        seen[text] = (f[2], f[0], d1, d2, d3, d4)
    for text, (etype, ehnum) in EXPECTED_TYPE.items():
        assert text in seen, "缺少题目: " + text
        jtype, hnum, d1, d2, d3, d4 = seen[text]
        assert jtype == etype, "%s type=%s != %s" % (text, jtype, etype)
        assert hnum == ehnum, "%s hnum=%s != %s" % (text, hnum, ehnum)
        if text == "测试四选一":
            opts = d1.split("||")
            assert len(opts) == 4 and opts[0] == "甲", "四选一选项=%r" % d1
        elif text == "测试判断":
            assert d1 == "Ｏ", "判断题 data1=%r" % d1
        elif text == "测试打字":
            assert d1 == "１９９２", "打字 data1=%r" % d1
        elif text == "测试排序":
            assert d1 == "A/B/C" and d2 == "0", "排序 data1=%r data2=%r" % (d1, d2)
        elif text == "测试连线":
            assert d1 == "甲||乙||丙" and d2 == "一||二||三", "连线 data1=%r data2=%r" % (d1, d2)
        elif text == "测试分组":
            assert d1 == "组一||组二" and d2 == "甲/乙||丙/丁" and d3 == "4", "分组 data=%r %r %r" % (d1, d2, d3)
        elif text == "测试多答":
            assert d1 == "1992/2018" and d2 == "4", "多答 data1=%r data2=%r" % (d1, d2)
    return segs


def check_ranking(port):
    pair = lambda v: CHRS[v // 65] + CHRS[v % 65]
    dat = pair(2500) + pair(2500) + "0" + "1"
    assert post(port, "/cn/kbDX/Ranking/RnkSet.php", {"NAM": "测试玩家", "DAT": dat, "NUM": "1"}) == "1,1"
    assert post(port, "/cn/kbDX/Ranking/RnkRed.php", {"SCR": "4000"}) == "2,1"
    data = json.loads(post(port, "/cn/kbDX/Ranking/RnkList.php", {}))
    assert data["total"] == 1 and data["scores"][0]["score"] == 5000
    assert post(port, "/cn/kbDX/T.php", {}) == "1"


def check_stats(port, segs):
    qns = segs[25]
    red = post(port, "/cn/kbDX/SKR/SKRred.php", {"QNs": qns}).split("|")
    assert len(red) == 25, "SKRred 应返回 25 条"
    digits = "3" * 27
    enc = "".join(CHRS[int(digits[i]) * 16 + int(digits[i + 1]) * 4 + int(digits[i + 2])] for i in range(0, 27, 3))
    assert post(port, "/cn/kbDX/SKR/SKRset.php", {"DAT": qns + "|" + enc}) == " "
    red2 = post(port, "/cn/kbDX/SKR/SKRred.php", {"QNs": qns}).split("|")
    for item in red2:
        m, n = (int(x) for x in item.split(","))
        assert n % 10000 == m, "全对时 n%%10000 应等于 m: " + item
    return red2


def check_events(port):
    assert post(port, "/cn/kbDX/evt/dtset.php", {"NAM": "n", "DAT": "00"}) == " "
    assert post(port, "/cn/kbDX/evt/distred.php", {"SCR": "Ev"}) == " "


def main():
    results = {}
    for kind in ("python", "java"):
        srv = Server(kind, free_port())
        try:
            srv.start()
            segs = check_qgene(srv.port)
            check_ranking(srv.port)
            stats = check_stats(srv.port, segs)
            check_events(srv.port)
            results[kind + "_stats"] = stats
            results[kind] = "ok"
            print("[%s] ok (port %d)" % (kind, srv.port))
        finally:
            srv.stop()
    assert results["python_stats"] == results["java_stats"], "Java/Python 统计结果不一致"
    print("protocol tests passed:", {k: v for k, v in results.items() if k in ("python", "java")})


if __name__ == "__main__":
    main()
