# 技术文档

## 1. 运行模型

两套服务端都实现同一套 HTTP 协议，路径形如 `/{cn,jp}/kbDX/...`：

- Java：`KbdxServer` 读取 `kbDX/*.php` 键值描述文件，按 `type` 分派；
- Python：`kbdx_core.handle()` 直接实现，题库内嵌在 `data_cn.py` / `data_jp.py`。

## 2. 配置

`server.properties`（与启动脚本同目录）：

| 键 | 类型 | 说明 |
|---|---|---|
| `server.port` | int | 监听端口（默认 8700） |
| `server.debug` | bool | 跑码模式，逐请求打印方法/路径/参数 |
| `server.log` | bool | 追加写入 `logs/requests.log` |

Java 从**当前工作目录**读取；Python 从脚本目录或当前目录读取。缺文件或缺少 `server.port` 时启动失败。

## 2b. 语言隔离

| 层 | 机制 |
|---|---|
| 请求 | SWF 全部使用相对路径（`Qgene.php` 等），语言 = SWF 所在目录 |
| 路由 | Java/Python 都只接受 `/{cn,jp}/kbDX/` 前缀，其他路径拒绝 |
| 数据 | Java：`data/cn`、`data/jp` 独立目录；Python：`DATA` 以 `cn/`、`jp/` 为键 |
| 状态 | 排行、统计、会话按语言分文件/分键 |
| 防御 | 请求若带 `LANG=cn|jp` 且与路径不符，直接返回空格（为补丁版 SWF 预留） |
| 自检 | 启动时检查两份题库是否存在、SHA-256 是否相同并告警 |
| 测试 | `tests/protocol_test.py` 覆盖标记隔离、会话隔离、排行隔离、LANG 校验 |

**SWF 侧**：补丁生成的中文/日文 SWF 会在全部 URLVariables 请求里带上 `LANG=cn` / `LANG=jp`
（每版 9 处）。服务端发现 `LANG` 与路径不一致时返回空格，因此放错目录的补丁版 SWF
也无法读取另一种语言的题库；只有未打补丁的旧 SWF 才完全依赖目录。

## 3. Qgene 协议

请求：`POST /cn/kbDX/Qgene.php`，`application/x-www-form-urlencoded`

| 参数 | 说明 |
|---|---|
| `NUM` | 固定 1 |
| `MOD` | 0/1=清淡，2=适中，3=全难度（活动） |
| `VER` | 版本号 |

响应：25 道题以 `?` 分隔，末尾附 `qns` 与 `token`。每题 11 个逗号分隔字段：

```
hnum,0,type,-,author,date,text,data1,data2,data3,data4
```

其中 `author/date/text/data*` 用 65 字符表做 3 字符/码点的编码：

```
CHRS = "1BU8kTlE6dZ9.Dz-Afe2gF5hvi4wOmjq3xpuGIXsJL7cMrRSnN0CKoPyHbVtQaY_W"
```

`type` 与题型：

| type | 题型 | 数据字段 |
|---|---|---|
| 1 | ○× | `data1` = Ｏ/Ｘ |
| 2 | 四选一 | `data1` = 正确项，`data2` = 干扰项 `||` 分隔 |
| 7 | 打字 | `data1` = 答案 |
| 11 | 连线 | `data1` = 左列 `||`，`data2` = 右列 `||` |
| 13 | 排序 | `data1` = 正确顺序 `||` |
| 14 | 分组 | `data1` = 组名 `||`，`data2` = 各组条目，`data3` = 条目数 |
| 17 | 多答打字 | `data1` = 答案 `/` 分隔，`data2` = 每格字数 |

`pct` 字段（`全国正确率`）由统计接口提供。

## 4. 题库格式

`SKR/questions.tsv`，UTF-8、Tab 分隔：

```
kind  diff  text  answer  wrong  data1  data2
```

- `kind`：`choice|ox|typing|order|line|group|multityping`
- `diff`：1 清淡 / 2 适中 / 3 困难
- `choice` 的 `wrong` 为 3 个干扰项（`||`）
- `order` 的 `answer` 为正确顺序（`||`）
- `line` 的 `answer`/`wrong` 为左右列（`||`，数量相同）
- `group` 的 `answer` 为组名（`||`），`wrong` 为各组条目（组内 `/`，组间 `||`），`data1` 为条目总数
- `multityping` 的 `answer` 为 `/` 分隔答案，`data1` 为每格字数

## 5. 补丁流程（二进制补丁）

`tools/patch/` 不再调用 FFDec，而是用 CDC（内容定义分块）二进制补丁：

1. 读取原始 SWF，校验 SHA-256（`original.sha256`）；
2. 若是 CWS，先解压成 FWS 并校验（`base.sha256`）；
3. 读取 `data/<variant>.kbp`（zlib 压缩的 KBP1 格式），按 copy/literal 指令重建 FWS；
4. 校验目标 FWS 的 SHA-256（`<variant>.sha256`）；
5. 重新压缩成 CWS（zlib level 9），写入 `full/main.swf`；
6. 按 18 MiB 切片为 `split/main.swf.partNN`。

KBP1 格式：

```
"KBP1" | u32 srcLen | u32 dstLen | u32 opCount
op 0: u8=0, u32 offset, u32 length   （从原始 FWS 复制）
op 1: u8=1, u32 length, bytes        （字面量）
```

补丁只覆盖受支持的原始 SWF（SHA-256 `a77cfcf6…`），其他版本会被拒绝。

## 6. 文件切片

大文件切片规则：每片 18 MiB，命名 `main.swf.part01`、`part02`……；服务端按序号顺序拼接后整体返回。

## 7. CI

GitHub Actions：`ubuntu-latest` + Temurin JDK 17 + Python 3.11。

- `javac` 编译；
- `python -m py_compile`；
- 启动 Python 服务端（临时端口），`curl` 请求 Qgene；
- 启动 Java 服务端（临时端口），`curl` 请求 Qgene。

'## 8. 题库副本

`docs/banks/` 保存题库的只读副本：

| 文件 | 说明 |
|---|---|
| `questions_cn.tsv` / `questions_jp.tsv` | 主题库 |
| `questions_evt_cn.tsv` / `questions_evt_jp.tsv` | 活动题库 |
| `evt_texts_cn.tsv` / `evt_texts_jp.tsv` | 活动文案（key/chid/zh/ja） |

它们不参与服务端运行，供编辑器加载与人工查阅。

## 9. 编辑器（GUI）

| 语言 | 题库编辑器 | 活动编辑器 | 配置 |
|---|---|---|---|
| Java（Swing） | `QuestionEditor.java` | `ActivityEditor.java` | `editor_config.properties` |
| Python（Tkinter） | `qbank_editor.py` | `activity_editor.py` | 同左 |

- 界面语言：中文 / 日本語，独立于内容语言（中文题库 / 日文题库、中文活动 / 日文活动）；
- 配置键：`bank.*`、`event.bank.*`、`event.texts.*`、`swf.*`、`rebuild.*`；
- Java 查找顺序：`-Deditor.config` → 当前目录 → class 目录 → 父目录；Python：脚本目录 → 当前目录；
- 校验规则与题库格式同第 4 节；活动文案见 `docs/banks/evt_texts_*.tsv`。

## 10. 补丁程序形态

`tools/patch/patch_swf.py` 与 `tools/patch/PatchSwf.java` 均为 **CLI 程序**（参数：`--original`、`--out`、`--only`），没有图形界面。

## 11. 静态资源

- `python/dev_server.py` 会从 `python/public/` 提供 SWF 与页面静态文件；
  该目录**不在仓库中**（SWF 被排除），需要用户自行放置补丁产物。
- `java/kbDX/` 仅包含协议描述与题库；SWF 同样由用户放入 `java/kbDX/`。

## 12. 已知限制'

- 不含游戏 SWF、运行时、Ruffle、编译 jar；
- 文字面板/联想/画像题型未实现；
- 活动文案修改需重新补丁 SWF；
- 排行榜存储为文本文件（Java）或进程内 KV（Python dev server），非生产级数据库。
