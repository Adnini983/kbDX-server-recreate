# -*- coding: utf-8 -*-
"""单文件 SWF 补丁程序（无需 FFDec / 字体 / 额外文件，只需原始 SWF）。

用法：
    python3 patch_swf.py --original main.swf --out ./out [--only jp|cn]

产出：
    out/jp/full/main.swf  + out/jp/split/main.swf.partNN
    out/cn/full/main.swf  + out/cn/split/main.swf.partNN
"""

import argparse
import hashlib

import os
import struct
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
CHUNK = 18 * 1024 * 1024


def sha256(b):
    return hashlib.sha256(b).hexdigest()


def decompress(swf):
    if swf[:3] == b"FWS":
        return swf
    if swf[:3] != b"CWS":
        raise SystemExit("不支持的 SWF 签名: %r" % swf[:3])
    body = zlib.decompress(swf[8:])
    return b"FWS" + swf[3:4] + struct.pack("<I", 8 + len(body)) + body


def compress(fws):
    body = fws[8:]
    return b"CWS" + fws[3:4] + struct.pack("<I", 8 + len(body)) + zlib.compress(body, 9)


def apply_patch(base, patch_bytes):
    raw = zlib.decompress(patch_bytes)
    if raw[:4] != b"KBP1":
        raise SystemExit("补丁格式错误")
    src_len, dst_len, nops = struct.unpack_from("<III", raw, 4)
    if src_len != len(base):
        raise SystemExit("原始 SWF 长度不匹配（需要 %d，实际 %d）" % (src_len, len(base)))
    out = bytearray()
    pos = 16
    for _ in range(nops):
        op = raw[pos]; pos += 1
        if op == 0:
            off, ln = struct.unpack_from("<II", raw, pos); pos += 8
            out += base[off:off + ln]
        elif op == 1:
            ln, = struct.unpack_from("<I", raw, pos); pos += 4
            out += raw[pos:pos + ln]; pos += ln
        else:
            raise SystemExit("未知补丁操作")
    if len(out) != dst_len:
        raise SystemExit("补丁结果长度不匹配")
    return bytes(out)


def split(path, outdir):
    os.makedirs(outdir, exist_ok=True)
    data = open(path, "rb").read()
    n = (len(data) + CHUNK - 1) // CHUNK
    for i in range(n):
        with open(os.path.join(outdir, "main.swf.part%02d" % (i + 1)), "wb") as f:
            f.write(data[i * CHUNK:(i + 1) * CHUNK])
    return n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--original", required=True)
    ap.add_argument("--out", default="out")
    ap.add_argument("--only", choices=["jp", "cn"])
    a = ap.parse_args()

    man = {}
    for line in open(os.path.join(DATA, "manifest.properties"), encoding="utf-8"):
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            man[k.strip()] = v.strip()
    raw = open(a.original, "rb").read()
    if sha256(raw) != man["original.sha256"]:
        raise SystemExit("原始 SWF 校验失败：这不是受支持的原始文件。")
    base = decompress(raw)
    if sha256(base) != man["base.sha256"]:
        raise SystemExit("原始 SWF 解压后校验失败。")

    out_root = os.path.abspath(a.out)
    for name in ("jp", "cn"):
        if a.only and a.only != name:
            continue
        patch = open(os.path.join(DATA, name + ".kbp"), "rb").read()
        target = apply_patch(base, patch)
        if sha256(target) != man[name + ".sha256"]:
            raise SystemExit("%s 补丁结果校验失败" % name)
        swf = compress(target)
        full = os.path.join(out_root, name, "full", "main.swf")
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "wb") as f:
            f.write(swf)
        parts = split(full, os.path.join(out_root, name, "split"))
        print("%s: %d bytes, %d parts -> %s" % (name, len(swf), parts, full))


if __name__ == "__main__":
    main()
