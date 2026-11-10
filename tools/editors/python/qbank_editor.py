# -*- coding: utf-8 -*-
"""卡比检定DX 题库编辑器（Tkinter，本地，支持中/日界面语言）。"""

import os
import shutil
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
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
        _sys.stderr.write("缺少配置文件: %s\n请把 editor_config.properties 放到编辑器同目录。\n" % p)
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
        raise SystemExit("配置项缺失: %s（%s）" % (key, _find_cfg()))
    return CFG[key]

CN_PATH = cfg("bank.cn")
JP_PATH = cfg("bank.jp")

KINDS = ["choice", "ox", "typing", "order", "line", "group", "multityping"]
UNSUPPORTED = {"panel", "renso", "image", "fill"}

T = {
    "zh": {
        "title": "卡比检定DX 题库编辑器（本地）",
        "ui_lang": "界面语言",
        "bank_cn": "中文题库",
        "bank_jp": "日文题库",
        "open_other": "打开其他文件…",
        "stats": "统计",
        "validate_all": "校验全部",
        "kind": "题型",
        "diff": "难度",
        "question": "题干",
        "answer": "正确答案",
        "wrong": "干扰项",
        "extra": "附加",
        "apply": "应用到当前",
        "add": "新增",
        "dup": "复制",
        "del": "删除",
        "up": "↑",
        "down": "↓",
        "save": "保存 (Ctrl+S)",
        "reload": "重新载入",
        "choose_first": "先在左侧选一题",
        "check_fail": "校验失败",
        "no_save": "未保存",
        "switch_ask": "当前修改还没保存，确定切换吗？",
        "del_ask": "确定删除第 %d 题？",
        "validate_title": "校验结果",
        "all_ok": "全部 %d 题通过",
        "bad_prefix": "第 %d 题 [%s] %s",
        "stats_title": "统计",
        "stats_total": "总题数：%d",
        "stats_diff": "清淡 %d / 适中 %d / 困难 %d",
        "stats_warn": "⚠ %s不足（%d/%d）",
        "easy": "清淡", "normal": "适中", "hard": "困难",
        "save_ask_bad": "有 %d 题未通过校验，仍要保存？",
        "saved": "已保存",
        "saved_msg": "%s\n（旧文件已备份为 .bak）",
        "exit_ask": "有未保存修改，确定退出？",
        "status": "共 %d 题　难度 1/2/3 = %d/%d/%d　题型 %s%s",
        "dirty": "　（有未保存修改）",
        "desc": {
            "choice": "四选一：正确答案 + 3 个干扰项（用 || 分隔）",
            "ox": "判断题：正确答案填 Ｏ / Ｘ（也接受 ○ / ×）",
            "typing": "打字题：正确答案为输入文本",
            "order": "顺序排列：正确答案按正确顺序写，用 || 分隔",
            "line": "连线：正确答案=左列（|| 分隔），干扰项=右列（|| 分隔，数量相同）",
            "group": "分组：正确答案=组名（|| 分隔），干扰项=各组条目（组内 / 分隔，组间 ||）",
            "multityping": "多答打字：正确答案=答案（/ 分隔），附加=每格字数",
        },
        "f": {
            "choice": ("正确答案", "干扰项（a||b||c）", "附加（留空）"),
            "ox": ("正确答案（Ｏ/Ｘ）", "干扰项（留空）", "附加（留空）"),
            "typing": ("正确答案", "干扰项（留空）", "附加（留空）"),
            "order": ("正确顺序（a||b||c）", "干扰项（留空）", "附加（图片帧，一般 0）"),
            "line": ("左列（a||b||c）", "右列（x||y||z）", "附加（留空）"),
            "group": ("组名（组1||组2）", "各组条目（条目/条目||条目/条目）", "附加（条目总数）"),
            "multityping": ("答案（答案1/答案2）", "干扰项（留空）", "附加（每格字数）"),
        },
        "err": {
            "unsupported": "该题型客户端不支持，不要使用",
            "unknown": "未知题型",
            "diff": "难度必须是 1/2/3",
            "text": "题干为空",
            "answer": "正确答案为空",
            "choice3": "干扰项至少 3 个（|| 分隔）",
            "ox": "判断题答案必须是 Ｏ / Ｘ（或 ○ / ×）",
            "order2": "顺序项至少 2 个（|| 分隔）",
            "line": "左列/右列数量必须相同且 ≥2",
            "group": "分组必须是 2 组：组名 2 个、条目 2 段",
            "groupn": "附加里的条目总数（%s）与实际（%d）不一致",
            "groupnum": "附加必须是条目总数",
            "multi2": "多答至少 2 个答案（/ 分隔）",
            "multinum": "附加必须是每格字数",
        },
    },
    "ja": {
        "title": "カービィ検定DX 問題エディタ（ローカル）",
        "ui_lang": "表示言語",
        "bank_cn": "中国語問題",
        "bank_jp": "日本語問題",
        "open_other": "他のファイルを開く…",
        "stats": "統計",
        "validate_all": "すべて検証",
        "kind": "種類",
        "diff": "難易度",
        "question": "問題文",
        "answer": "正解",
        "wrong": "ダミー",
        "extra": "追加",
        "apply": "選択行に適用",
        "add": "追加",
        "dup": "複製",
        "del": "削除",
        "up": "↑",
        "down": "↓",
        "save": "保存 (Ctrl+S)",
        "reload": "再読み込み",
        "choose_first": "左側で問題を選んでください",
        "check_fail": "検証エラー",
        "no_save": "未保存",
        "switch_ask": "保存していない変更があります。切り替えますか？",
        "del_ask": "%d 番目の問題を削除しますか？",
        "validate_title": "検証結果",
        "all_ok": "全 %d 問が合格",
        "bad_prefix": "%d 問目 [%s] %s",
        "stats_title": "統計",
        "stats_total": "合計：%d 問",
        "stats_diff": "やさしい %d / ふつう %d / むずかしい %d",
        "stats_warn": "⚠ %sが不足（%d/%d）",
        "easy": "やさしい", "normal": "ふつう", "hard": "むずかしい",
        "save_ask_bad": "%d 問が検証に失敗しました。それでも保存しますか？",
        "saved": "保存しました",
        "saved_msg": "%s\n（旧ファイルは .bak にバックアップ）",
        "exit_ask": "保存していない変更があります。終了しますか？",
        "status": "全 %d 問　難易度 1/2/3 = %d/%d/%d　種類 %s%s",
        "dirty": "　（未保存の変更あり）",
        "desc": {
            "choice": "四択：正解 + ダミー3つ（|| 区切り）",
            "ox": "○×：正解は Ｏ / Ｘ（○ / × も可）",
            "typing": "タイピング：正解を入力",
            "order": "並べ替え：正しい順に || で区切る",
            "line": "線結び：正解=左列（||）、ダミー=右列（||、同数）",
            "group": "グループ分け：正解=組名（||）、ダミー=各組の項目（組内 /、組間 ||）",
            "multityping": "多答タイピング：正解=答え（/ 区切り）、追加=1欄の文字数",
        },
        "f": {
            "choice": ("正解", "ダミー（a||b||c）", "追加（空欄）"),
            "ox": ("正解（Ｏ/Ｘ）", "ダミー（空欄）", "追加（空欄）"),
            "typing": ("正解", "ダミー（空欄）", "追加（空欄）"),
            "order": ("正しい順（a||b||c）", "ダミー（空欄）", "追加（画像フレーム、通常 0）"),
            "line": ("左列（a||b||c）", "右列（x||y||z）", "追加（空欄）"),
            "group": ("組名（組1||組2）", "各組の項目（項目/項目||項目/項目）", "追加（項目数）"),
            "multityping": ("答え（答え1/答え2）", "ダミー（空欄）", "追加（1欄の文字数）"),
        },
        "err": {
            "unsupported": "この種類はクライアント非対応です",
            "unknown": "不明な種類",
            "diff": "難易度は 1/2/3",
            "text": "問題文が空です",
            "answer": "正解が空です",
            "choice3": "ダミーは3つ以上（|| 区切り）",
            "ox": "○×の正解は Ｏ / Ｘ（または ○ / ×）",
            "order2": "並べ替えは2項目以上（|| 区切り）",
            "line": "左列と右列の数が同じで2組以上",
            "group": "グループは2組：組名2つ、項目2段",
            "groupn": "追加の項目数（%s）と実際（%d）が不一致",
            "groupnum": "追加は項目数",
            "multi2": "多答は2つ以上（/ 区切り）",
            "multinum": "追加は1欄の文字数",
        },
    },
}


def load_rows(path):
    rows = []
    if not os.path.exists(path):
        return rows
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if not line.strip() or line.startswith("#"):
                continue
            c = line.split("\t")
            while len(c) < 7:
                c.append("")
            rows.append(c[:7])
    return rows


def save_rows(path, rows):
    if os.path.exists(path):
        shutil.copyfile(path, path + ".bak")
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        for r in rows:
            f.write("\t".join(r[:7]) + "\n")


class Editor(tk.Tk):
    def __init__(self, initial_lang="zh"):
        super().__init__()
        self.state("zoomed")
        self.lang = initial_lang
        self.rows = []
        self.path = CN_PATH
        self.dirty = False
        self.sel = -1
        self._build()
        self.apply_lang()
        self.after(80, lambda: self.load_lang("cn"))

    def t(self, key):
        v = T[self.lang].get(key, key)
        return v

    def _build(self):
        self.top = ttk.Frame(self, padding=6)
        self.top.pack(fill="x")

        self.ui_lang_lbl = ttk.Label(self.top, text="")
        self.ui_lang_lbl.pack(side="left")
        self.var_ui = tk.StringVar(value=self.lang)
        self.rb_ui_zh = ttk.Radiobutton(self.top, text="中文", value="zh", variable=self.var_ui, command=lambda: self.set_lang("zh"))
        self.rb_ui_ja = ttk.Radiobutton(self.top, text="日本語", value="ja", variable=self.var_ui, command=lambda: self.set_lang("ja"))
        self.rb_ui_zh.pack(side="left", padx=(6, 0))
        self.rb_ui_ja.pack(side="left")

        ttk.Separator(self.top, orient="vertical").pack(side="left", fill="y", padx=10)

        self.var_bank = tk.StringVar(value="cn")
        self.rb_cn = ttk.Radiobutton(self.top, text="", value="cn", variable=self.var_bank, command=lambda: self.load_lang("cn"))
        self.rb_jp = ttk.Radiobutton(self.top, text="", value="jp", variable=self.var_bank, command=lambda: self.load_lang("jp"))
        self.rb_cn.pack(side="left")
        self.rb_jp.pack(side="left", padx=(8, 12))

        self.btn_other = ttk.Button(self.top, text="", command=self.open_other)
        self.btn_other.pack(side="left")
        self.lbl_path = ttk.Label(self.top, text="", foreground="#555")
        self.lbl_path.pack(side="left", padx=12)
        self.btn_stats = ttk.Button(self.top, text="", command=self.show_stats)
        self.btn_stats.pack(side="right")
        self.btn_validate = ttk.Button(self.top, text="", command=self.validate_all)
        self.btn_validate.pack(side="right", padx=6)

        self.savebar = ttk.Frame(self)
        self.savebar.pack(side="bottom", fill="x", padx=6, pady=(0, 6))
        self.btn_save = ttk.Button(self.savebar, text="", command=self.save)
        self.btn_save.pack(side="right")
        self.btn_reload = ttk.Button(self.savebar, text="", command=lambda: self.load_lang(self.var_bank.get()))
        self.btn_reload.pack(side="right", padx=6)
        self.status = ttk.Label(self.savebar, text="", foreground="#333")
        self.status.pack(side="left")

        self.pan = ttk.Panedwindow(self, orient="horizontal")
        self.pan.pack(fill="both", expand=True, padx=6, pady=6)

        self.left = ttk.Frame(self.pan)
        self.tree = ttk.Treeview(self.left, columns=("no", "kind", "diff", "text"), show="headings", selectmode="browse")
        for col, w in (("no", 44), ("kind", 78), ("diff", 44), ("text", 420)):
            self.tree.column(col, width=w, anchor="w")
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.on_select)
        self.pan.add(self.left, weight=3)

        self.right = ttk.Frame(self.pan, padding=(8, 0, 0, 0))
        self.pan.add(self.right, weight=2)

        r1 = ttk.Frame(self.right)
        r1.pack(fill="x", pady=2)
        self.lbl_kind = ttk.Label(r1, text="")
        self.lbl_kind.pack(side="left")
        self.cmb_kind = ttk.Combobox(r1, values=KINDS, state="readonly", width=14)
        self.cmb_kind.pack(side="left", padx=(6, 16))
        self.cmb_kind.bind("<<ComboboxSelected>>", lambda e: self.sync_labels())
        self.lbl_diff = ttk.Label(r1, text="")
        self.lbl_diff.pack(side="left")
        self.cmb_diff = ttk.Combobox(r1, values=["1", "2", "3"], state="readonly", width=4)
        self.cmb_diff.pack(side="left", padx=(6, 0))

        self.lbl_desc = ttk.Label(self.right, text="", foreground="#0a5", wraplength=360, justify="left")
        self.lbl_desc.pack(fill="x", pady=(4, 8))

        self.lbl_text = ttk.Label(self.right, text="")
        self.lbl_text.pack(anchor="w")
        self.txt_text = tk.Text(self.right, height=4, wrap="word")
        self.txt_text.pack(fill="x", pady=(2, 8))

        self.lbl_ans = ttk.Label(self.right, text="")
        self.lbl_ans.pack(anchor="w")
        self.ent_ans = ttk.Entry(self.right)
        self.ent_ans.pack(fill="x", pady=(2, 8))

        self.lbl_wrong = ttk.Label(self.right, text="")
        self.lbl_wrong.pack(anchor="w")
        self.txt_wrong = tk.Text(self.right, height=3, wrap="word")
        self.txt_wrong.pack(fill="x", pady=(2, 8))

        self.lbl_extra = ttk.Label(self.right, text="")
        self.lbl_extra.pack(anchor="w")
        self.ent_extra = ttk.Entry(self.right)
        self.ent_extra.pack(fill="x", pady=(2, 8))

        btns = ttk.Frame(self.right)
        btns.pack(fill="x", pady=6)
        self.btn_apply = ttk.Button(btns, text="", command=self.apply_current)
        self.btn_apply.pack(side="left")
        self.btn_add = ttk.Button(btns, text="", command=self.add_new)
        self.btn_add.pack(side="left", padx=6)
        self.btn_dup = ttk.Button(btns, text="", command=self.duplicate)
        self.btn_dup.pack(side="left")
        self.btn_del = ttk.Button(btns, text="", command=self.delete)
        self.btn_del.pack(side="left", padx=6)
        self.btn_up = ttk.Button(btns, text="", width=3, command=lambda: self.move(-1))
        self.btn_up.pack(side="left")
        self.btn_down = ttk.Button(btns, text="", width=3, command=lambda: self.move(1))
        self.btn_down.pack(side="left")

        self.bind("<Control-s>", lambda e: self.save())
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def set_lang(self, lang):
        self.lang = lang
        self.apply_lang()
        self.refresh_tree()
        self.update_status()

    def apply_lang(self):
        self.title(self.t("title"))
        self.ui_lang_lbl.config(text=self.t("ui_lang"))
        self.rb_cn.config(text=self.t("bank_cn"))
        self.rb_jp.config(text=self.t("bank_jp"))
        self.btn_other.config(text=self.t("open_other"))
        self.btn_stats.config(text=self.t("stats"))
        self.btn_validate.config(text=self.t("validate_all"))
        self.btn_save.config(text=self.t("save"))
        self.btn_reload.config(text=self.t("reload"))
        self.lbl_kind.config(text=self.t("kind"))
        self.lbl_diff.config(text=self.t("diff"))
        self.lbl_text.config(text=self.t("question"))
        self.lbl_extra.config(text=self.t("extra"))
        self.btn_apply.config(text=self.t("apply"))
        self.btn_add.config(text=self.t("add"))
        self.btn_dup.config(text=self.t("dup"))
        self.btn_del.config(text=self.t("del"))
        self.btn_up.config(text=self.t("up"))
        self.btn_down.config(text=self.t("down"))
        self.tree.heading("no", text="#")
        self.tree.heading("kind", text=self.t("kind"))
        self.tree.heading("diff", text=self.t("diff"))
        self.tree.heading("text", text=self.t("question"))
        self.sync_labels()

    # ---------- data ----------
    def load_lang(self, lang):
        if self.dirty and not messagebox.askyesno(self.t("no_save"), self.t("switch_ask")):
            return
        self.var_bank.set(lang)
        self.path = CN_PATH if lang == "cn" else JP_PATH
        self.rows = load_rows(self.path)
        self.dirty = False
        self.sel = -1
        self.lbl_path.config(text=self.path)
        self.refresh_tree()
        self.clear_form()
        self.update_status()

    def open_other(self):
        p = filedialog.askopenfilename(title=self.t("open_other"),
                                       filetypes=[("TSV", "*.tsv"), ("*", "*.*")])
        if not p:
            return
        self.path = p
        self.rows = load_rows(p)
        self.dirty = False
        self.sel = -1
        self.lbl_path.config(text=p)
        self.refresh_tree()
        self.clear_form()
        self.update_status()

    def refresh_tree(self):
        self.tree.delete(*self.tree.get_children())
        for i, r in enumerate(self.rows):
            self.tree.insert("", "end", iid=str(i), values=(i + 1, r[0], r[1], r[2]))

    def update_status(self):
        c = Counter(r[1] for r in self.rows)
        k = Counter(r[0] for r in self.rows)
        kinds = " ".join("%s:%d" % (x, k[x]) for x in KINDS if k.get(x))
        self.status.config(text=self.t("status") % (
            len(self.rows), c.get("1", 0), c.get("2", 0), c.get("3", 0), kinds,
            self.t("dirty") if self.dirty else ""))

    # ---------- form ----------
    def clear_form(self):
        self.cmb_kind.set("choice")
        self.cmb_diff.set("1")
        self.txt_text.delete("1.0", "end")
        self.ent_ans.delete(0, "end")
        self.txt_wrong.delete("1.0", "end")
        self.ent_extra.delete(0, "end")
        self.sync_labels()

    def sync_labels(self):
        k = self.cmb_kind.get()
        self.lbl_desc.config(text=self.t("desc").get(k, self.t("err")["unsupported"]))
        a, w, e = self.t("f").get(k, (self.t("answer"), self.t("wrong"), self.t("extra")))
        self.lbl_ans.config(text=a)
        self.lbl_wrong.config(text=w)
        self.lbl_extra.config(text=e)

    def on_select(self, _e=None):
        s = self.tree.selection()
        if not s:
            return
        i = int(s[0])
        self.sel = i
        r = self.rows[i]
        self.cmb_kind.set(r[0] if r[0] in KINDS else "choice")
        self.cmb_diff.set(r[1] if r[1] in ("1", "2", "3") else "1")
        self.txt_text.delete("1.0", "end")
        self.txt_text.insert("1.0", r[2])
        self.ent_ans.delete(0, "end")
        self.ent_ans.insert(0, r[3])
        self.txt_wrong.delete("1.0", "end")
        self.txt_wrong.insert("1.0", r[4])
        self.ent_extra.delete(0, "end")
        self.ent_extra.insert(0, r[5])
        self.sync_labels()

    def form_row(self):
        return [self.cmb_kind.get(), self.cmb_diff.get(),
                self.txt_text.get("1.0", "end").rstrip("\n"),
                self.ent_ans.get().strip(),
                self.txt_wrong.get("1.0", "end").rstrip("\n"),
                self.ent_extra.get().strip(), ""]

    def apply_current(self):
        if self.sel < 0:
            messagebox.showinfo(self.t("check_fail"), self.t("choose_first"))
            return
        r = self.form_row()
        errs = self.validate(r)
        if errs:
            messagebox.showwarning(self.t("check_fail"), "\n".join(errs))
            return
        self.rows[self.sel] = r
        self.dirty = True
        self.refresh_tree()
        self.tree.selection_set(str(self.sel))
        self.update_status()

    def add_new(self):
        r = self.form_row()
        errs = self.validate(r)
        if errs:
            messagebox.showwarning(self.t("check_fail"), "\n".join(errs))
            return
        self.rows.append(r)
        self.dirty = True
        self.refresh_tree()
        self.sel = len(self.rows) - 1
        self.tree.selection_set(str(self.sel))
        self.tree.see(str(self.sel))
        self.update_status()

    def duplicate(self):
        if self.sel < 0:
            return
        self.rows.insert(self.sel + 1, list(self.rows[self.sel]))
        self.dirty = True
        self.refresh_tree()
        self.sel += 1
        self.tree.selection_set(str(self.sel))
        self.update_status()

    def delete(self):
        if self.sel < 0:
            return
        if not messagebox.askyesno(self.t("del"), self.t("del_ask") % (self.sel + 1)):
            return
        del self.rows[self.sel]
        self.dirty = True
        self.sel = -1
        self.refresh_tree()
        self.clear_form()
        self.update_status()

    def move(self, delta):
        if self.sel < 0:
            return
        j = self.sel + delta
        if j < 0 or j >= len(self.rows):
            return
        self.rows[self.sel], self.rows[j] = self.rows[j], self.rows[self.sel]
        self.sel = j
        self.dirty = True
        self.refresh_tree()
        self.tree.selection_set(str(j))
        self.tree.see(str(j))
        self.update_status()

    # ---------- validation ----------
    def validate(self, row):
        e = T[self.lang]["err"]
        kind, diff, text, ans, wrong, extra = row[0], row[1], row[2], row[3], row[4], row[5]
        errs = []
        if kind in UNSUPPORTED:
            errs.append(e["unsupported"])
        elif kind not in KINDS:
            errs.append(e["unknown"])
        if diff not in ("1", "2", "3"):
            errs.append(e["diff"])
        if not text.strip():
            errs.append(e["text"])
        if kind == "choice":
            if not ans.strip():
                errs.append(e["answer"])
            if len([x for x in wrong.split("||") if x.strip()]) < 3:
                errs.append(e["choice3"])
        elif kind == "ox":
            if ans.strip() not in ("Ｏ", "Ｘ", "○", "×", "是", "否"):
                errs.append(e["ox"])
        elif kind == "typing":
            if not ans.strip():
                errs.append(e["answer"])
        elif kind == "order":
            if len([x for x in ans.split("||") if x.strip()]) < 2:
                errs.append(e["order2"])
        elif kind == "line":
            l = len([x for x in ans.split("||") if x.strip()])
            r = len([x for x in wrong.split("||") if x.strip()])
            if l < 2 or l != r:
                errs.append(e["line"])
        elif kind == "group":
            groups = [g for g in ans.split("||") if g.strip()]
            buckets = [b for b in wrong.split("||") if b.strip()]
            if len(groups) != 2 or len(buckets) != 2:
                errs.append(e["group"])
            else:
                total = sum(len([x for x in b.split("/") if x.strip()]) for b in buckets)
                try:
                    if str(int(extra.strip())) != str(total):
                        errs.append(e["groupn"] % (extra.strip(), total))
                except Exception:
                    errs.append(e["groupnum"])
        elif kind == "multityping":
            parts = [x for x in ans.split("/") if x.strip()]
            if len(parts) < 2:
                errs.append(e["multi2"])
            try:
                int(extra.strip())
            except Exception:
                errs.append(e["multinum"])
        return errs

    def validate_all(self):
        bad = []
        for i, r in enumerate(self.rows):
            errs = self.validate(r)
            if errs:
                bad.append(self.t("bad_prefix") % (i + 1, r[0], "；".join(errs)))
        if bad:
            messagebox.showwarning(self.t("validate_title"), "\n".join(bad[:40]) + ("\n…" if len(bad) > 40 else ""))
        else:
            messagebox.showinfo(self.t("validate_title"), self.t("all_ok") % len(self.rows))

    def show_stats(self):
        c = Counter(r[1] for r in self.rows)
        k = Counter(r[0] for r in self.rows)
        lines = [self.t("stats_total") % len(self.rows),
                 self.t("stats_diff") % (c.get("1", 0), c.get("2", 0), c.get("3", 0)), ""]
        lines += ["%s：%d" % (x, k.get(x, 0)) for x in KINDS]
        warn = []
        for d, name, need in (("1", self.t("easy"), 50), ("2", self.t("normal"), 100), ("3", self.t("hard"), 100)):
            if c.get(d, 0) < need:
                warn.append(self.t("stats_warn") % (name, c.get(d, 0), need))
        if warn:
            lines += ["", "；".join(warn)]
        messagebox.showinfo(self.t("stats_title"), "\n".join(lines))

    def save(self):
        bad = sum(1 for r in self.rows if self.validate(r))
        if bad and not messagebox.askyesno(self.t("saved"), self.t("save_ask_bad") % bad):
            return
        save_rows(self.path, self.rows)
        self.dirty = False
        self.update_status()
        messagebox.showinfo(self.t("saved"), self.t("saved_msg") % self.path)

    def on_close(self):
        if self.dirty and not messagebox.askyesno(self.t("no_save"), self.t("exit_ask")):
            return
        self.destroy()


if __name__ == "__main__":
    import sys
    Editor("ja" if "--ja" in sys.argv else "zh").mainloop()
