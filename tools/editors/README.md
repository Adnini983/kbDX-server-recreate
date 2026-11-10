# 题库 / 活动编辑器

两套编辑器均为 **GUI** 程序（Python 用 Tkinter，Java 用 Swing），界面语言支持中文与日语切换。

| 目录 | 程序 | 说明 |
|---|---|---|
| `python/` | `qbank_editor.py` | 题库编辑器（GUI，Tkinter） |
| `python/` | `activity_editor.py` | 活动模式编辑器（GUI，Tkinter） |
| `java/` | `QuestionEditor.java` | 题库编辑器（GUI，Swing） |
| `java/` | `ActivityEditor.java` | 活动模式编辑器（GUI，Swing） |

## 配置

两个编辑器都从**同目录的 `editor_config.properties`** 读取路径，代码里不写死。
把 `editor_config.properties.example` 复制为 `editor_config.properties` 并改成自己的路径。

键：

```
bank.cn / bank.jp                       题库
event.bank.cn / event.bank.jp           活动题库
event.texts.cn / event.texts.jp         活动文案
swf.cn / swf.jp                         游戏 SWF（一键重编用）
rebuild.*                               一键重编流水线（可选）
```

## 运行

### Python

```bash
cd tools/editors/python
python qbank_editor.py            # 中文界面
python qbank_editor.py --ja       # 日本語UI

python activity_editor.py                 # 中文界面 + 中文活动
python activity_editor.py --ja --content-jp   # 日文界面 + 日文活动
```

### Java

```bash
cd tools/editors/java
javac -encoding UTF-8 -d build Config.java QuestionEditor.java ActivityEditor.java
java -cp build QuestionEditor            # 中文
java -cp build QuestionEditor --ja       # 日本語
java -cp build ActivityEditor
java -cp build ActivityEditor --ja
```

Java 版的配置查找顺序：`-Deditor.config=...` → 当前目录 → class 所在目录 → 其父目录。

## 功能

- 题库编辑器：列表/搜索、题型与难度、题干/答案/干扰项/附加字段、单题校验与全量校验、难度与题型统计、新增/复制/删除/排序、保存（自动 `.bak` 备份）；
- 活动编辑器：活动题库编辑 + 活动文案编辑（key/chid/中文/日文）、导出文本补丁、一键重编本地 SWF（仅中文，需 `rebuild.*` 配置）。

## 注意

- 题库/活动文案的格式与校验规则见 `docs/TECHNICAL.md`；
- 编辑器只读写本地文件，不会上传任何服务器。
