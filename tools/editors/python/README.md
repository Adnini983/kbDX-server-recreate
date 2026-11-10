# Python 编辑器

- `qbank_editor.py`：题库编辑器（Tkinter GUI）。
- `activity_editor.py`：活动模式编辑器（Tkinter GUI）。

## 运行

```bash
cp editor_config.properties.example editor_config.properties
# 编辑 editor_config.properties 里的路径

python qbank_editor.py [--ja]
python activity_editor.py [--ja] [--content-jp]
```

需要 Python 3.9+ 和 tkinter（Windows 官方 Python 自带）。
