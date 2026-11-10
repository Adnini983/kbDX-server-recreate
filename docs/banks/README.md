# 题库副本

这里存放当前题库的**只读参考副本**，不参与服务端运行（服务端使用 `java/kbDX/SKR/` 或 `python/data_*.py`）。

| 文件 | 内容 |
|---|---|
| `questions_cn.tsv` / `questions_jp.tsv` | 主题库（279 题/语言） |
| `questions_evt_cn.tsv` / `questions_evt_jp.tsv` | 活动题库 |
| `evt_texts_cn.tsv` / `evt_texts_jp.tsv` | 活动文案（key/chid/中文/日文） |

格式说明见 `docs/TECHNICAL.md` 第 4 节；活动文案格式见第 10 节。

这些副本可以直接被编辑器加载（在 `editor_config.properties` 里指向它们即可），
修改后请自行拷贝回实际运行目录，或把配置指向实际目录。
