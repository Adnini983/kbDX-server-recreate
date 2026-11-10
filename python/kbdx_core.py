# -*- coding: utf-8 -*-
"""Cloudflare Workers Python 版的接口逻辑（纯 Python，可在本地 CPython 测试）。"""

import random
from urllib.parse import parse_qs

CHRS = "1BU8kTlE6dZ9.Dz-Afe2gF5hvi4wOmjq3xpuGIXsJL7cMrRSnN0CKoPyHbVtQaY_W"

KIND_TYPE = {
    "ox": 1, "choice": 2, "renso": 3, "panel": 5, "typing": 7,
    "line": 11, "order": 13, "group": 14, "multityping": 17, "fill": 18, "image": 10,
}


def encode65(s):
    out = []
    for ch in s:
        v = ord(ch)
        out.append(CHRS[v // 4225] + CHRS[(v // 65) % 65] + CHRS[v % 65])
    return "".join(out)


def wrap(text, width=13):
    br = "]、。 ？！!！?"
    rest, first, out = text, True, []
    while len(rest) > width:
        lo = max(4, int(width * 0.6))
        hi = min(len(rest), int(width * 1.6) + 1)
        cut = -1
        for c in br:
            idx = rest.rfind(c, 0, hi)
            if idx >= lo and idx > cut:
                cut = idx
        if cut < 0:
            cut = width - 1
        if not first:
            out.append("%%")
        out.append(rest[:cut + 1])
        first = False
        rest = rest[cut + 1:].lstrip()
    if rest:
        if not first:
            out.append("%%")
        out.append(rest)
    return "".join(out) if out else text


def props(text):
    d = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith(";"):
            continue
        if "=" in line:
            k, v = line.split("=", 1)
            d[k.strip().lower()] = v.strip()
    return d


def _wrongs(s):
    ws = [x for x in s.split("||") if x.strip()]
    random.shuffle(ws)
    return "||".join(ws)


def _blank0(s):
    return s.strip() if s and s.strip() else "0"


def build_qgene(bank_text, mod, p, count=25):
    rows = []
    for line in bank_text.splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        cols = line.split("\t")
        if len(cols) < 4:
            continue
        rows.append(cols)
    if mod >= 3 and p.get("evtdata"):
        pass  # 由调用方决定用哪个题库文本
    pool = []
    for q in rows:
        try:
            diff = int(q[1].strip())
        except Exception:
            continue
        if mod <= 1:
            ok = diff == 1
        elif mod == 2:
            ok = diff <= 2
        else:
            ok = True
        if ok:
            pool.append(q)
    if len(pool) < count:
        extra = [q for q in rows if q not in pool]
        random.shuffle(extra)
        pool += extra
    random.shuffle(pool)

    author = p.get("author", "管理人")
    date = p.get("date", "2026/11/08")
    out = []
    for i in range(count):
        q = pool[i % len(pool)] if pool else ["choice", "1", "（无题目）", "（空）", ""]
        kind = q[0].strip().lower()
        qtype = KIND_TYPE.get(kind, 2)
        try:
            hnum = 2 if int(q[1]) == 1 else (3 if int(q[1]) == 2 else 4)
        except Exception:
            hnum = 2
        c3 = q[3] if len(q) > 3 else ""
        c4 = q[4] if len(q) > 4 else ""
        e1 = q[5].strip() if len(q) > 5 else ""
        e2 = q[6].strip() if len(q) > 6 else ""
        d1 = d2 = d3 = d4 = "0"
        if kind == "ox":
            d1 = c3
        elif kind == "renso":
            d1 = (c3 + "||" + _wrongs(c4)).rstrip("|")
        elif kind == "panel":
            d1 = c4
            d2 = c3
            d3 = "0"
            if e2.startswith("res/"):
                d4 = e2
        elif kind == "typing":
            d1 = c3
            if e1.startswith("res/"):
                d2, d4 = "0", e1
            else:
                d2 = _blank0(e1)
        elif kind == "line":
            d1, d2 = c3, c4
        elif kind == "order":
            d1 = c3.replace("||", "/")
            d2 = _blank0(e1)
        elif kind == "group":
            d1, d2, d3 = c3, c4, e1
        elif kind == "multityping":
            d1 = c3.replace("||", "/")
            d2 = _blank0(e1)
            if e2.startswith("res/"):
                d3, d4 = "0", e2
            else:
                d3 = _blank0(e2)
        elif kind == "fill":
            d1 = c3 + "||" + c4
            if e1.startswith("res/"):
                d2, d4 = "0", e1
            else:
                d2 = _blank0(e1)
        elif kind == "image":
            d1 = c3
        else:
            d1 = c3 + "||" + _wrongs(c4)
            if e1.startswith("res/"):
                d2, d4 = "0", e1
            else:
                d2 = _blank0(e1)
        text = q[2].replace("&&", "%%") if kind == "renso" else wrap(q[2], 13)
        out.append(",".join([
            str(hnum), "0", str(qtype), "-",
            encode65(author), encode65(date), encode65(text),
            encode65(d1), encode65(d2), encode65(d3), encode65(d4),
        ]))
    return "?".join(out) + "?" + p.get("qns", "DX2026") + "?" + p.get("token", "1")


def build_stats(stats_text):
    rows = []
    for line in stats_text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(",")
        if len(parts) >= 2:
            rows.append(parts[0].strip() + "," + parts[1].strip() + ",0")
    if not rows:
        rows = ["1000,600,0"]
    return "|".join(rows[i % len(rows)] for i in range(25))


def ranking(scores, scr):
    if scr and scr > 0:
        scores.append(scr)
    total = max(1, len(scores))
    top = 80000
    rank = 1
    for s in scores:
        if s > top:
            top = s
        if scr and scr > 0 and s > scr:
            rank += 1
    return "%d,%d,%d" % (max(1, rank), total, top), scores


def parse_records(raw):
    """把存储内容解析成 [{score,name,date}]；兼容纯数字行。"""
    recs = []
    for line in str(raw or "").splitlines():
        parts = line.split("\t")
        try:
            sc = int(parts[0].strip())
        except Exception:
            continue
        name = parts[1].strip() if len(parts) > 1 else ""
        date = parts[2].strip() if len(parts) > 2 else ""
        recs.append({"score": sc, "name": name, "date": date})
    return recs


def records_text(recs):
    out = []
    for r in recs:
        name = str(r.get("name", "")).replace("\t", " ").replace("\n", " ")
        date = str(r.get("date", "")).replace("\t", " ").replace("\n", " ")
        out.append("%d\t%s\t%s" % (int(r["score"]), name, date))
    return "\n".join(out)


def records_json(recs, limit=50):
    recs = sorted(recs, key=lambda r: r["score"], reverse=True)
    total = len(recs)
    top = recs[0]["score"] if recs else 0
    items = ", ".join('{"score": %d, "name": "%s"}' % (
        r["score"], str(r.get("name", "")).replace("\\", "\\\\").replace('"', '\\"')) for r in recs[:limit])
    return '{"total": %d, "top": %d, "scores": [%s]}' % (total, top, items)


def event_data(p):
    try:
        ev = int(p.get("eventid", "3"))
    except Exception:
        ev = 3
    arr = ["0"] * 101
    arr[100] = str(ev)
    return ",".join(arr)


def parse_body(body):
    """解析 application/x-www-form-urlencoded。"""
    try:
        q = parse_qs(body or "", keep_blank_values=True)
        return {k: v[0] for k, v in q.items()}
    except Exception:
        return {}


def handle(lang, path, method, body, data, storage):
    """data: dict(relpath->text)；storage: dict 提供 get/set。

    返回 (status, content_type, text) 或 None（表示静态文件）。
    """
    root = "/" + lang + "/kbDX/"
    if not path.startswith(root):
        return None
    rel = path[len(root):]
    name = rel.lower()
    if not name.endswith(".php"):
        return None
    params = parse_body(body)

    def text(p):
        return data.get(lang + "/kbDX/" + p, "")

    try:
        if rel == "T.php":
            return 200, "text/plain; charset=utf-8", props(text("T.php")).get("body", "1")
        if rel == "Qgene.php":
            p = props(text("Qgene.php"))
            try:
                mod = int(params.get("MOD", "1"))
            except Exception:
                mod = 1
            bank = text(p.get("evtdata", "SKR/questions.tsv")) if mod >= 3 and p.get("evtdata") else text(p.get("data", "SKR/questions.tsv"))
            if mod >= 3 and p.get("evtdata"):
                bank = text(p["evtdata"])
            try:
                count = int(p.get("count", "25"))
            except Exception:
                count = 25
            return 200, "text/plain; charset=utf-8", build_qgene(bank, mod, p, count)
        if rel == "SKR/SKRred.php":
            p = props(text("SKR/SKRred.php"))
            return 200, "text/plain; charset=utf-8", build_stats(text(p.get("data", "stats.tsv")))
        if rel == "Ranking/RnkList.php":
            key = lang + ":scores"
            raw = storage.get(key) if storage else None
            if raw is None:
                raw = text("Ranking/scores.txt")
            return 200, "application/json; charset=utf-8", records_json(parse_records(raw))

        if rel in ("Ranking/RnkRed.php", "Ranking/RnkSet.php"):
            key = lang + ":scores"
            raw = storage.get(key) if storage else None
            if raw is None:
                raw = text("Ranking/scores.txt")
            recs = parse_records(raw)
            scr = 0
            if params.get("SCR", "").isdigit():
                scr = int(params["SCR"])
            if rel.endswith("RnkSet.php") and scr > 0 and params.get("NAM") is not None:
                recs.append({"score": scr, "name": params.get("NAM", ""), "date": params.get("DAT", "")})
                if storage is not None:
                    storage.set(key, records_text(recs))
            scores = [r["score"] for r in recs]
            total = max(1, len(scores))
            top = 80000
            rank = 1
            for sc in scores:
                if sc > top:
                    top = sc
                if scr > 0 and sc > scr:
                    rank += 1
            return 200, "text/plain; charset=utf-8", "%d,%d,%d" % (max(1, rank), total, top)
        if rel.startswith("evt/"):
            p = props(text(rel))
            if p.get("type") == "event":
                return 200, "text/plain; charset=utf-8", event_data(p)
            return 200, "text/plain; charset=utf-8", p.get("body", " ")
        p = props(text(rel))
        return 200, "text/plain; charset=utf-8", p.get("body", " ")
    except Exception:
        return 200, "text/plain; charset=utf-8", " "
