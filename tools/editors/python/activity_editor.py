# -*- coding: utf-8 -*-
"""活动模式编辑器：活动题库 + 活动文案（本地，支持中/日界面语言）。"""

import os
import shutil
import subprocess
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from collections import Counter

import os as _os
import sys as _sys

_CFG_NAME = "editor_config.properties"


def _find_cfg():
    here = _os.path.dirname(_os.path.abspath(__file__))
    for c in (_os.path.join(here, _CFG_NAME), _os.path.join(_os.getcwd(), _CFG_NAME)):
        if _os.path.exists(c):
            return c
    return _os.path.join(here, _CFG_NAME)


def _load_cfg():
    p = _find_cfg()
    if not _os.path.exists(p):
        _sys.stderr.write("缺少配置文件: %s\n" % p)
        raise SystemExit(1)
    d = {}
    with open(p, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            d[k.strip()] = v.strip()
    return d


CFG = _load_cfg()


def cfg(key):
    if key not in CFG or not CFG[key]:
        raise SystemExit("配置项缺失: %s" % key)
    return CFG[key]


CN_EVT = cfg("event.bank.cn")
JP_EVT = cfg("event.bank.jp")
CN_TXT = cfg("event.texts.cn")
JP_TXT = cfg("event.texts.jp")

JAVA = cfg("rebuild.java")
FFDEC = cfg("rebuild.ffdec")
TEXT_CLASSES = cfg("rebuild.texttool")
TEXT_MAP = cfg("rebuild.textmap")
BASE_SWF = cfg("rebuild.base")
PATCH_DIR = cfg("rebuild.patch")
TMP_DIR = cfg("rebuild.tmp")
CN_SWF = cfg("swf.cn")

KINDS = ["choice", "ox", "typing", "order", "line", "group", "multityping"]

# key, chid, 中文, 日本語
DEFAULT_TEXTS = [
    ("goto", "97", "前往活动模式", "イベントモードへ"),
    ("running", "100", "举办中的活动", "開催中のイベント"),
    ("none", "101", "当前没有举办中的活动。", "現在開催中のイベントはありません。"),
    ("past", "111", "过去的活动", "過去のイベント"),
    ("title", "174", "第１届活动模式", "第１回イベントモード"),
    ("desc_off", "52", "根据主题进一步缩小出题范围的模式（　＾ω＾）", "テーマで出題範囲を絞るモード（　＾ω＾）"),
    ("desc_on", "53", "活动期间每游玩一次分数都会增加哦！", "イベント期間中はプレイするたびにスコアが増えます！"),
    ("rank_hint", "3441", "活动期间每游玩一次分数都会增加！（＊＾ω＾）", "イベント期間中はプレイするたびにスコアが増えます！（＊＾ω＾）"),
    ("rank_line", "3413", "本次排名　|||总参加人数||", "今回の順位　|||総参加人数||"),
]

T = {
    "zh": {
        "title": "卡比检定DX 活动模式编辑器（本地）",
        "ui": "界面语言",
        "content": "内容语言",
        "cn": "中文", "jp": "日文",
        "tab_bank": "活动题库", "tab_text": "活动文案",
        "save": "保存", "reload": "重新载入",
        "add": "新增", "del": "删除", "apply": "应用到当前",
        "kind": "题型", "diff": "难度", "text": "题干", "ans": "正确答案", "wrong": "干扰/右列", "extra": "附加",
        "key": "键", "chid": "文本ID", "value": "文案",
        "status_bank": "活动题库：%d 题",
        "status_text": "活动文案：%d 条",
        "saved": "已保存",
        "save_msg": "%s\n（旧文件备份为 .bak）",
        "export": "导出文本补丁",
        "export_msg": "已写出：\n%s\n\n把它合并进 text_map 后重新编译 SWF 即可生效。",
        "pick": "先在列表里选一项",
        "check": "校验",
        "empty_text": "文案不能为空",
        "rebuild": "一键重编本地 SWF",
        "rebuild_running": "正在重编 SVF，请稍候…（约 3–6 分钟）",
        "rebuild_ok": "重编完成，已替换：\n%s\n旧文件备份：%s.bak",
        "rebuild_fail": "重编失败：\n%s",
        "rebuild_jp": "日文版没有独立的 text_map，暂不支持一键重编。",
    },
    "ja": {
        "title": "カービィ検定DX イベントモードエディタ（ローカル）",
        "ui": "表示言語",
        "content": "内容言語",
        "cn": "中国語", "jp": "日本語",
        "tab_bank": "イベント問題", "tab_text": "イベント文言",
        "save": "保存", "reload": "再読み込み",
        "add": "追加", "del": "削除", "apply": "選択行に適用",
        "kind": "種類", "diff": "難易度", "text": "問題文", "ans": "正解", "wrong": "ダミー/右列", "extra": "追加",
        "key": "キー", "chid": "テキストID", "value": "文言",
        "status_bank": "イベント問題：%d 問",
        "status_text": "イベント文言：%d 件",
        "saved": "保存しました",
        "save_msg": "%s\n（旧ファイルは .bak にバックアップ）",
        "export": "文言パッチを書き出す",
        "export_msg": "書き出しました：\n%s\n\ntext_map に反映して SWF を再ビルドすると有効になります。",
        "pick": "一覧から選んでください",
        "check": "検証",
        "empty_text": "文言が空です",
        "rebuild": "ローカルSWFを再ビルド",
        "rebuild_running": "SWF を再ビルド中…（約3〜6分）",
        "rebuild_ok": "再ビルド完了、置き換えました：\n%s\nバックアップ：%s.bak",
        "rebuild_fail": "再ビルド失敗：\n%s",
        "rebuild_jp": "日本語版には専用 text_map がないため、一括再ビルドは未対応です。",
    },
}


def read_tsv(path, ncol=7):
    rows = []
    if not os.path.exists(path):
        return rows
    for line in open(path, encoding="utf-8"):
        line = line.rstrip("\n")
        if not line.strip() or line.startswith("#"):
            continue
        c = line.split("\t")
        while len(c) < ncol:
            c.append("")
        rows.append(c[:ncol])
    return rows


def write_tsv(path, rows):
    if os.path.exists(path):
        shutil.copyfile(path, path + ".bak")
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        for r in rows:
            f.write("\t".join(r) + "\n")


def ensure_texts(path):
    if os.path.exists(path):
        return read_tsv(path, 4)
    rows = [[k, c, zh, ja] for k, c, zh, ja in DEFAULT_TEXTS]
    write_tsv(path, rows)
    return rows


class ActivityEditor(tk.Tk):
    def __init__(self, ui="zh", content="cn"):
        super().__init__()
        self.state("zoomed")
        self.ui = ui
        self.content = content
        self.bank = []
        self.texts = []
        self._build()
        self.apply_ui()
        self.load_all()

    def t(self, k):
        return T[self.ui].get(k, k)

    def _build(self):
        bar = ttk.Frame(self, padding=6)
        bar.pack(fill="x")
        self.lbl_ui = ttk.Label(bar, text="")
        self.lbl_ui.pack(side="left")
        self.var_ui = tk.StringVar(value=self.ui)
        for val, txt in (("zh", "中文"), ("ja", "日本語")):
            ttk.Radiobutton(bar, text=txt, value=val, variable=self.var_ui,
                            command=self.switch_ui).pack(side="left", padx=(6, 0))
        ttk.Separator(bar, orient="vertical").pack(side="left", fill="y", padx=10)
        self.lbl_content = ttk.Label(bar, text="")
        self.lbl_content.pack(side="left")
        self.var_content = tk.StringVar(value=self.content)
        self.rb_cn = ttk.Radiobutton(bar, text="", value="cn", variable=self.var_content, command=self.switch_content)
        self.rb_jp = ttk.Radiobutton(bar, text="", value="jp", variable=self.var_content, command=self.switch_content)
        self.rb_cn.pack(side="left", padx=(6, 0))
        self.rb_jp.pack(side="left")
        self.btn_save = ttk.Button(bar, text="", command=self.save_all)
        self.btn_save.pack(side="right")
        self.btn_reload = ttk.Button(bar, text="", command=self.load_all)
        self.btn_reload.pack(side="right", padx=6)
        self.btn_export = ttk.Button(bar, text="", command=self.export_patch)
        self.btn_export.pack(side="right", padx=6)
        self.btn_rebuild = ttk.Button(bar, text="", command=self.rebuild_swf)
        self.btn_rebuild.pack(side="right", padx=6)

        self.nb = ttk.Notebook(self)
        self.nb.pack(fill="both", expand=True, padx=6, pady=6)

        # ---- bank tab ----
        bankf = ttk.Frame(self.nb, padding=6)
        self.nb.add(bankf, text="")
        self.bank_tab = bankf
        left = ttk.Frame(bankf)
        left.pack(side="left", fill="both", expand=True)
        self.tree = ttk.Treeview(left, columns=("no", "kind", "diff", "text"), show="headings", selectmode="browse")
        for c, w in (("no", 44), ("kind", 78), ("diff", 44), ("text", 420)):
            self.tree.column(c, width=w, anchor="w")
            self.tree.heading(c, text=c)
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.on_bank_select)

        form = ttk.Frame(bankf, padding=(8, 0, 0, 0))
        form.pack(side="right", fill="y")
        self.lbl_kind = ttk.Label(form, text="")
        self.lbl_kind.grid(row=0, column=0, sticky="w")
        self.cmb_kind = ttk.Combobox(form, values=KINDS, state="readonly", width=14)
        self.cmb_kind.grid(row=0, column=1, sticky="w", padx=4)
        self.lbl_diff = ttk.Label(form, text="")
        self.lbl_diff.grid(row=1, column=0, sticky="w")
        self.cmb_diff = ttk.Combobox(form, values=["1", "2", "3"], state="readonly", width=4)
        self.cmb_diff.grid(row=1, column=1, sticky="w", padx=4)
        self.lbl_text = ttk.Label(form, text="")
        self.lbl_text.grid(row=2, column=0, sticky="nw")
        self.txt_text = tk.Text(form, width=42, height=4, wrap="word")
        self.txt_text.grid(row=2, column=1, sticky="w", pady=2)
        self.lbl_ans = ttk.Label(form, text="")
        self.lbl_ans.grid(row=3, column=0, sticky="w")
        self.ent_ans = ttk.Entry(form, width=44)
        self.ent_ans.grid(row=3, column=1, sticky="w", pady=2)
        self.lbl_wrong = ttk.Label(form, text="")
        self.lbl_wrong.grid(row=4, column=0, sticky="w")
        self.ent_wrong = ttk.Entry(form, width=44)
        self.ent_wrong.grid(row=4, column=1, sticky="w", pady=2)
        self.lbl_extra = ttk.Label(form, text="")
        self.lbl_extra.grid(row=5, column=0, sticky="w")
        self.ent_extra = ttk.Entry(form, width=44)
        self.ent_extra.grid(row=5, column=1, sticky="w", pady=2)
        btns = ttk.Frame(form)
        btns.grid(row=6, column=0, columnspan=2, sticky="w", pady=6)
        self.btn_apply = ttk.Button(btns, text="", command=self.apply_bank)
        self.btn_apply.pack(side="left")
        self.btn_add = ttk.Button(btns, text="", command=self.add_bank)
        self.btn_add.pack(side="left", padx=6)
        self.btn_del = ttk.Button(btns, text="", command=self.del_bank)
        self.btn_del.pack(side="left")
        self.lbl_bank_status = ttk.Label(form, text="")
        self.lbl_bank_status.grid(row=7, column=0, columnspan=2, sticky="w")

        # ---- text tab ----
        textf = ttk.Frame(self.nb, padding=6)
        self.nb.add(textf, text="")
        self.text_tab = textf
        lt = ttk.Frame(textf)
        lt.pack(side="left", fill="both", expand=True)
        self.tree2 = ttk.Treeview(lt, columns=("key", "chid", "val"), show="headings", selectmode="browse")
        for c, w in (("key", 110), ("chid", 80), ("val", 560)):
            self.tree2.column(c, width=w, anchor="w")
            self.tree2.heading(c, text=c)
        self.tree2.pack(fill="both", expand=True)
        self.tree2.bind("<<TreeviewSelect>>", self.on_text_select)
        ft = ttk.Frame(textf, padding=(8, 0, 0, 0))
        ft.pack(side="right", fill="y")
        self.lbl_val = ttk.Label(ft, text="")
        self.lbl_val.pack(anchor="w")
        self.txt_val = tk.Text(ft, width=40, height=5, wrap="word")
        self.txt_val.pack(fill="x", pady=4)
        self.btn_apply_text = ttk.Button(ft, text="", command=self.apply_text)
        self.btn_apply_text.pack(anchor="w")
        self.lbl_text_status = ttk.Label(ft, text="")
        self.lbl_text_status.pack(anchor="w", pady=6)

    # ---------- language ----------
    def switch_ui(self):
        self.ui = self.var_ui.get()
        self.apply_ui()

    def apply_ui(self):
        self.title(self.t("title"))
        self.lbl_ui.config(text=self.t("ui"))
        self.lbl_content.config(text=self.t("content"))
        self.rb_cn.config(text=self.t("cn"))
        self.rb_jp.config(text=self.t("jp"))
        self.btn_save.config(text=self.t("save"))
        self.btn_reload.config(text=self.t("reload"))
        self.btn_export.config(text=self.t("export"))
        self.btn_rebuild.config(text=self.t("rebuild"))
        self.nb.tab(self.bank_tab, text=self.t("tab_bank"))
        self.nb.tab(self.text_tab, text=self.t("tab_text"))
        self.lbl_kind.config(text=self.t("kind"))
        self.lbl_diff.config(text=self.t("diff"))
        self.lbl_text.config(text=self.t("text"))
        self.lbl_ans.config(text=self.t("ans"))
        self.lbl_wrong.config(text=self.t("wrong"))
        self.lbl_extra.config(text=self.t("extra"))
        self.btn_apply.config(text=self.t("apply"))
        self.btn_add.config(text=self.t("add"))
        self.btn_del.config(text=self.t("del"))
        self.lbl_val.config(text=self.t("value"))
        self.btn_apply_text.config(text=self.t("apply"))
        self.tree.heading("no", text="#")
        self.tree.heading("kind", text=self.t("kind"))
        self.tree.heading("diff", text=self.t("diff"))
        self.tree.heading("text", text=self.t("text"))
        self.tree2.heading("key", text=self.t("key"))
        self.tree2.heading("chid", text=self.t("chid"))
        self.tree2.heading("val", text=self.t("value"))
        self.refresh_texts()

    def switch_content(self):
        self.content = self.var_content.get()
        self.load_all()

    # ---------- data ----------
    def paths(self):
        if self.content == "cn":
            return CN_EVT, CN_TXT
        return JP_EVT, JP_TXT

    def load_all(self):
        evt, txt = self.paths()
        self.bank = read_tsv(evt, 7)
        self.texts = ensure_texts(txt)
        self.refresh_bank()
        self.refresh_texts()

    def refresh_bank(self):
        self.tree.delete(*self.tree.get_children())
        for i, r in enumerate(self.bank):
            self.tree.insert("", "end", iid=str(i), values=(i + 1, r[0], r[1], r[2]))
        self.lbl_bank_status.config(text=self.t("status_bank") % len(self.bank))

    def refresh_texts(self):
        if not hasattr(self, "tree2"):
            return
        col = 2 if self.content == "cn" else 3
        self.tree2.delete(*self.tree2.get_children())
        for i, r in enumerate(self.texts):
            self.tree2.insert("", "end", iid=str(i), values=(r[0], r[1], r[col]))
        if hasattr(self, "lbl_text_status"):
            self.lbl_text_status.config(text=self.t("status_text") % len(self.texts))

    # ---------- bank ----------
    def on_bank_select(self, _e=None):
        s = self.tree.selection()
        if not s:
            return
        r = self.bank[int(s[0])]
        self.cmb_kind.set(r[0] if r[0] in KINDS else "choice")
        self.cmb_diff.set(r[1] if r[1] in ("1", "2", "3") else "1")
        self.txt_text.delete("1.0", "end")
        self.txt_text.insert("1.0", r[2])
        self.ent_ans.delete(0, "end"); self.ent_ans.insert(0, r[3])
        self.ent_wrong.delete(0, "end"); self.ent_wrong.insert(0, r[4])
        self.ent_extra.delete(0, "end"); self.ent_extra.insert(0, r[5])

    def current_bank_row(self):
        return [self.cmb_kind.get(), self.cmb_diff.get(),
                self.txt_text.get("1.0", "end").rstrip("\n"),
                self.ent_ans.get().strip(), self.ent_wrong.get().strip(),
                self.ent_extra.get().strip(), ""]

    def apply_bank(self):
        s = self.tree.selection()
        if not s:
            messagebox.showinfo(self.t("check"), self.t("pick"))
            return
        i = int(s[0])
        self.bank[i] = self.current_bank_row()
        self.refresh_bank()
        self.tree.selection_set(str(i))

    def add_bank(self):
        self.bank.append(self.current_bank_row())
        self.refresh_bank()
        self.tree.selection_set(str(len(self.bank) - 1))

    def del_bank(self):
        s = self.tree.selection()
        if not s:
            return
        i = int(s[0])
        del self.bank[i]
        self.refresh_bank()

    # ---------- texts ----------
    def on_text_select(self, _e=None):
        s = self.tree2.selection()
        if not s:
            return
        r = self.texts[int(s[0])]
        col = 2 if self.content == "cn" else 3
        self.txt_val.delete("1.0", "end")
        self.txt_val.insert("1.0", r[col])

    def apply_text(self):
        s = self.tree2.selection()
        if not s:
            messagebox.showinfo(self.t("check"), self.t("pick"))
            return
        val = self.txt_val.get("1.0", "end").rstrip("\n")
        if not val.strip():
            messagebox.showwarning(self.t("check"), self.t("empty_text"))
            return
        i = int(s[0])
        col = 2 if self.content == "cn" else 3
        self.texts[i][col] = val
        self.refresh_texts()
        self.tree2.selection_set(str(i))

    # ---------- rebuild ----------
    def rebuild_swf(self):
        if self.content != "cn":
            messagebox.showinfo(self.t("rebuild"), self.t("rebuild_jp"))
            return
        if not messagebox.askyesno(self.t("rebuild"), self.t("rebuild_running")):
            return
        self.btn_rebuild.config(state="disabled")
        threading.Thread(target=self._rebuild_job, daemon=True).start()

    def _rebuild_job(self):
        try:
            msg = self._do_rebuild()
            self.after(0, lambda: self._rebuild_done(True, msg))
        except Exception as ex:
            self.after(0, lambda: self._rebuild_done(False, str(ex)))

    def _rebuild_done(self, ok, msg):
        self.btn_rebuild.config(state="normal")
        if ok:
            messagebox.showinfo(self.t("rebuild"), self.t("rebuild_ok") % (CN_SWF, CN_SWF))
        else:
            messagebox.showerror(self.t("rebuild"), self.t("rebuild_fail") % msg)

    def _merge_map(self):
        col = 2
        values = {r[1].strip(): r[col] for r in self.texts if r[1].strip()}
        lines = open(TEXT_MAP, encoding="utf-8").read().splitlines()
        out, hit = [], set()
        for ln in lines:
            c = ln.split("\t", 1)
            if len(c) == 2 and c[0].strip() in values:
                out.append(c[0] + "\t" + values[c[0].strip()])
                hit.add(c[0].strip())
            else:
                out.append(ln)
        open(TEXT_MAP, "w", encoding="utf-8", newline="\n").write("\n".join(out) + "\n")
        missing = sorted(set(values) - hit)
        return missing

    def _do_rebuild(self):
        os.makedirs(TMP_DIR, exist_ok=True)
        missing = self._merge_map()
        text_swf = os.path.join(TMP_DIR, "text.swf")
        out_swf = os.path.join(TMP_DIR, "main_new.swf")
        r1 = subprocess.run([JAVA, "-Xmx4g", "-cp", FFDEC + ";" + TEXT_CLASSES, "KbdxText5",
                             BASE_SWF, text_swf, TEXT_MAP], capture_output=True, text=True, timeout=1200)
        if r1.returncode != 0 or not os.path.exists(text_swf):
            raise RuntimeError("KbdxText5 失败\n" + r1.stdout[-800:] + r1.stderr[-800:])
        r2 = subprocess.run([JAVA, "-Xmx4g", "-jar", FFDEC, "-importScript", text_swf, out_swf, PATCH_DIR],
                            capture_output=True, text=True, timeout=1800)
        if r2.returncode != 0 or not os.path.exists(out_swf):
            raise RuntimeError("FFDec 失败\n" + r2.stdout[-800:] + r2.stderr[-800:])
        if os.path.exists(CN_SWF):
            shutil.copyfile(CN_SWF, CN_SWF + ".bak")
        shutil.copyfile(out_swf, CN_SWF)
        return "ok" if not missing else ("未在 text_map 中匹配到 chid: " + ",".join(missing))

    # ---------- save ----------
    def save_all(self):
        evt, txt = self.paths()
        write_tsv(evt, self.bank)
        write_tsv(txt, self.texts)
        messagebox.showinfo(self.t("saved"), self.t("save_msg") % (evt + "\n" + txt))

    def export_patch(self):
        evt, txt = self.paths()
        col = 2 if self.content == "cn" else 3
        out = os.path.join(r"X:\work", "evt_text_map_%s.txt" % self.content)
        with open(out, "w", encoding="utf-8", newline="\n") as f:
            for r in self.texts:
                f.write("%s\t%s\n" % (r[1], r[col]))
        messagebox.showinfo(self.t("export"), self.t("export_msg") % out)


if __name__ == "__main__":
    import sys
    ui = "ja" if "--ja" in sys.argv else "zh"
    content = "jp" if "--content-jp" in sys.argv else "cn"
    ActivityEditor(ui, content).mainloop()
