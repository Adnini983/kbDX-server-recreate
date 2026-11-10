# 原始 SWF 审计

对 `ori.swf/main.swf`（SHA-256 `a77cfcf6…`）的静态审计结果。

| 文件 | 内容 |
|---|---|
| `report.md` | 审计报告（概览、标签、资源、时间轴、脚本、移植评估） |
| `summary.json` | 机器可读汇总 |
| `tags.tsv` | 全量标签树（含 sprite 内嵌） |
| `classes.csv` | 133 个类与行数 |
| `symbols.csv` | SymbolClass 导出映射 |
| `assets_images.csv` | 1049 张图片清单 |
| `assets_sounds.csv` | 18 个声音清单 |
| `fonts.txt` | 字体与字形数 |

完整反编译源码与文本导出未放入仓库（避免分发游戏内容），
需要时在本地对原始 SWF 运行 FFDec 导出即可。