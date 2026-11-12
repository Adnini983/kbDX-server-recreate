# -*- coding: utf-8 -*-
"""kbDX 服务端协议实现（Python，Java 端与之一致）。

协议依据：原始 SWF 中 MainTimeline / リザルト / イベント 的调用与解析逻辑。
"""

import hashlib
import random
import time
from urllib.parse import parse_qs

CHRS = "1BU8kTlE6dZ9.Dz-Afe2gF5hvi4wOmjq3xpuGIXsJL7cMrRSnN0CKoPyHbVtQaY_W"
VER = 24

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


def decode65(s):
    out = []
    for i in range(0, len(s) - 2, 3):
        out.append(chr(CHRS.index(s[i]) * 4225 + CHRS.index(s[i + 1]) * 65 + CHRS.index(s[i + 2])))
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


def qkey(row):
    raw = "\t".join(row[:4])
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


def new_token(n=8):
    return "".join(random.choice(CHRS) for _ in range(n))


def build_qgene(bank_text, mod, p, count, qns):
    """返回 (响应文本, 题目 key 列表)。"""
    rows = []
    for line in bank_text.splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        cols = line.split("\t")
        if len(cols) < 4:
            continue
        rows.append(cols)
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
    use = [pool[i % len(pool)] if pool else ["choice", "1", "（无题目）", "（空）", ""] for i in range(count)]
    out = []
    for q in use:
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
            d1, d2 = c4, c3
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
    return "?".join(out) + "?" + qns + "?" + p.get("token", "1"), [qkey(q) for q in use]


def parse_kv(text):
    """session/统计存储：key<TAB>value。"""
    d = {}
    for line in str(text or "").splitlines():
        if "\t" in line:
            k, v = line.split("\t", 1)
            d[k] = v
    return d


def dump_kv(d):
    return "\n".join("%s\t%s" % (k, v) for k, v in d.items())


def load_stats(raw):
    stats = {}
    for k, v in parse_kv(raw).items():
        parts = v.split(",")
        try:
            stats[k] = [int(parts[0]), int(parts[1]), int(parts[2]) if len(parts) > 2 else 0]
        except Exception:
            stats[k] = [0, 0, 0]
    return stats


def save_stats(stats):
    return dump_kv({k: "%d,%d,%d" % tuple(v) for k, v in stats.items()})


def decode_hist(enc):
    digits = []
    for ch in enc:
        if ch not in CHRS:
            continue
        idx = CHRS.index(ch)
        digits.extend([idx // 16, (idx // 4) % 4, idx % 4])
    return digits


def decode_score(dat, token_len):
    """DAT = 分数增量（2 字符/个）+ 活动标志(1) + token。"""
    body = dat[:-(1 + token_len)] if len(dat) > 1 + token_len else dat
    total = 0
    for i in range(0, len(body) - 1, 2):
        a, b = body[i], body[i + 1]
        if a in CHRS and b in CHRS:
            total += CHRS.index(a) * 65 + CHRS.index(b)
    return total


def ranking_result(recs, scr=None):
    scores = [r["score"] for r in recs]
    total = len(scores)
    rank = 1
    if scr is not None and scr > 0:
        rank = 1 + sum(1 for s in scores if s > scr)
        total = max(total, 1)
    return max(1, rank), max(1, total)


def parse_records(raw):
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


def _now():
    return time.strftime("%Y/%m/%d")


def event_rows(text):
    rows = []
    for line in str(text or "").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        p = line.split("\t")
        if len(p) < 3:
            continue
        rows.append(p)
    return rows


def active_event(text, today):
    for p in event_rows(text):
        if p[1] <= today <= p[2]:
            mult = p[3].split(",") if len(p) > 3 else []
            return p[0], mult
    return None, []


def event_payload(event_id, mult):
    arr = ["0"] * 101
    for i, v in enumerate(mult[:100]):
        arr[i] = v.strip() or "0"
    arr[100] = str(event_id)
    return ",".join(arr)


def parse_body(body):
    try:
        q = parse_qs(body or "", keep_blank_values=True)
        return {k: v[0] for k, v in q.items()}
    except Exception:
        return {}


def handle(lang, path, method, body, data, storage):
    """返回 (status, content_type, text) 或 None（静态文件）。"""
    root = "/" + lang + "/kbDX/"
    if not path.startswith(root):
        return None
    rel = path[len(root):]
    if not rel.lower().endswith(".php"):
        return None
    params = parse_body(body)

    def text(p):
        return data.get(lang + "/kbDX/" + p, "")

    def get(key):
        return storage.get(lang + ":" + key) if storage else None

    def put(key, val):
        if storage:
            storage.set(lang + ":" + key, val)

    try:
        p = props(text(rel))

        if rel == "T.php":
            players = set()
            for r in parse_records(get("scores") or text("Ranking/scores.txt")):
                if r["name"]:
                    players.add(r["name"])
            return 200, "text/plain; charset=utf-8", str(len(players))

        if rel == "Qgene.php":
            if p.get("maintenance") == "1":
                return 200, "text/plain; charset=utf-8", "M"
            if params.get("VER") and params["VER"].strip() != str(p.get("ver", VER)):
                return 200, "text/plain; charset=utf-8", "V"
            try:
                mod = int(params.get("MOD", "1"))
            except Exception:
                mod = 1
            bank = text(p.get("evtdata", "SKR/questions.tsv")) if mod >= 3 and p.get("evtdata") else text(p.get("data", "SKR/questions.tsv"))
            try:
                count = int(p.get("count", "25"))
            except Exception:
                count = 25
            qns = new_token()
            resp, keys = build_qgene(bank, mod, p, count, qns)
            sessions = parse_kv(get("sessions"))
            sessions[qns] = ",".join(keys)
            put("sessions", dump_kv(sessions))
            return 200, "text/plain; charset=utf-8", resp

        if rel == "SKR/SKRred.php":
            qns = params.get("QNs", "").strip()
            keys = parse_kv(get("sessions")).get(qns, "")
            if not keys:
                return 200, "text/plain; charset=utf-8", " "
            stats = load_stats(get("stats"))
            out = []
            for k in keys.split(","):
                m, c, pf = stats.get(k, [0, 0, 0])
                out.append("%d,%d" % (m, pf * 10000 + c))
            return 200, "text/plain; charset=utf-8", "|".join(out)

        if rel == "SKR/SKRset.php":
            dat = params.get("DAT", "")
            if "|" not in dat:
                return 200, "text/plain; charset=utf-8", " "
            qns, enc = dat.split("|", 1)
            keys = parse_kv(get("sessions")).get(qns, "")
            if not keys:
                return 200, "text/plain; charset=utf-8", " "
            digits = decode_hist(enc)
            stats = load_stats(get("stats"))
            for i, k in enumerate(keys.split(",")):
                d = digits[i] if i < len(digits) else 0
                m, c, pf = stats.get(k, [0, 0, 0])
                m += 1
                if d >= 2:
                    c += 1
                if d == 3:
                    pf += 1
                stats[k] = [m, min(c, 9999), pf]
            put("stats", save_stats(stats))
            return 200, "text/plain; charset=utf-8", " "

        if rel == "Ranking/RnkList.php":
            raw = get("scores") or text("Ranking/scores.txt")
            return 200, "application/json; charset=utf-8", records_json(parse_records(raw))

        if rel == "Ranking/RnkRed.php":
            raw = get("scores") or text("Ranking/scores.txt")
            recs = parse_records(raw)
            scr = None
            try:
                scr = int(params.get("SCR", ""))
            except Exception:
                scr = None
            rank, total = ranking_result(recs, scr)
            return 200, "text/plain; charset=utf-8", "%d,%d" % (rank, total)

        if rel == "Ranking/RnkSet.php":
            raw = get("scores") or text("Ranking/scores.txt")
            recs = parse_records(raw)
            nam = params.get("NAM", "").strip()
            dat = params.get("DAT", "")
            score = decode_score(dat, len(p.get("token", "1")))
            if nam and score > 0:
                recs.append({"score": score, "name": nam[:24], "date": _now()})
                put("scores", records_text(recs))
            rank, total = ranking_result(recs)
            return 200, "text/plain; charset=utf-8", "%d,%d" % (rank, total)

        if rel == "evt/distred.php":
            ev_id, mult = active_event(text("evt/events.tsv"), _now())
            if ev_id is None:
                return 200, "text/plain; charset=utf-8", " "
            return 200, "text/plain; charset=utf-8", event_payload(ev_id, mult)

        if rel == "evt/DtSet.php":
            ent = parse_kv(get("entries"))
            key = new_token(10)
            ent[key] = "%s\t%s\t%s" % (params.get("NAM", ""), params.get("DAT", ""), _now())
            put("entries", dump_kv(ent))
            return 200, "text/plain; charset=utf-8", " "

        return 200, "text/plain; charset=utf-8", p.get("body", " ")
    except Exception:
        return 200, "text/plain; charset=utf-8", " "
