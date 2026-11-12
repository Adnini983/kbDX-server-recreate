# kbDX Server Recreate

《卡比检定DX》（カービィ検定DX）同人游戏的**服务端重制实现**，提供 Java 与 Python 两套可独立运行的版本，以及一个基于原始 SWF 的补丁工具。

> **声明**
> 本项目的代码由 **DeepSeek** 编写；需求提示词与测试环境均由用户提供。
> 项目仅包含服务端与补丁工具源码，**不包含**游戏 SWF、Java/Python 运行时、Ruffle 客户端或任何编译好的 `.jar`。

## 目录

```
java/             Java 17 服务端（单文件，无第三方依赖）
  src/            KbdxServer.java
  kbDX/           数据描述文件与题库
  server.properties
python/           Python 3 服务端（标准库）
tools/patch/      原始 SWF → 4 种修改版 SWF（CLI）
tools/editors/    题库 / 活动编辑器（GUI，Java + Python）
docs/banks/       题库副本（中/日，含活动题库与文案）
docs/audit/       原始 SWF 审计报告与资源清单
docs/TECHNICAL.md 协议、数据格式、补丁流程、编辑器说明
.github/workflows/ci.yml
```

## 已实现的功能（仅这些）

| 接口 | 说明 |
|---|---|
| `POST /{cn,jp}/kbDX/Qgene.php` | 出题（25 题）；返回 25 题 + QNs 会话 token + 结尾 token；校验 VER |
| `GET/POST /{cn,jp}/kbDX/SKR/stats.php` | 题目正确率统计 |
| `POST /{cn,jp}/kbDX/Ranking/RnkList.php` | 排行榜读取 |
| `POST /{cn,jp}/kbDX/Ranking/RnkSet.php` | 排行榜写入（`分数\t名字\t日期`） |
| `POST /{cn,jp}/kbDX/T.php` | 服务端时间/令牌占位 |
| `GET /{cn,jp}/kbDX/evt/DtSet.php` | 活动状态 |
| `GET /{cn,jp}/kbDX/evt/distred.php` | 活动分发占位 |

### 状态说明

| 状态 | 内容 |
|---|---|
| 已实现 | Qgene（含 panel/renso/image 字段分支）、T.php、SKRred/SKRset、RnkRed/RnkSet、DtSet、distred |
| 部分实现 | 活动分数倍率与奖励数据（格式已确认，数值未知）；统计中 hist 数字语义为推断 |
| 占位/扩展 | `RnkList.php` 为本项目扩展接口；活动文案文件需人工维护 |
| 未调查 | 原版是否还有其它接口（已扫描 AS3，仅上述调用点） |

### 语言隔离

SWF 内的所有接口都是**相对路径**（`Qgene.php`、`./SKR/SKRred.php`、`./Ranking/...`、`./evt/...`），
所以语言由 SWF 所在目录决定。部署必须保持：

```
/cn/kbDX/main.swf   -> 读 /cn/kbDX/Qgene.php  -> data/cn
/jp/kbDX/main.swf   -> 读 /jp/kbDX/Qgene.php  -> data/jp
```

服务端只接受 `/cn/kbDX/` 与 `/jp/kbDX/` 前缀；其他路径返回空格（Java）或 404（Python）。
排行榜、统计、会话都按语言分开存放；启动时会自检两份题库是否存在、是否内容相同。

回归测试会验证：中文端只出现中文标记、日文端只出现日文标记、中文会话查不到日文统计、
中文成绩不进日文排行、请求带错 `LANG` 会被拒绝。

> 注意：服务器无法识别“被放错目录的 SWF”。如果把中文 SWF 放到 `/jp/kbDX/`，
> 它仍会读日文题库。要彻底杜绝，需要让 SWF 请求携带 `LANG` 参数；服务端已支持校验，
> 等补丁版 SWF 启用即可。

### 协议依据

字段映射与参数来自原始 SWF 的调用与解析逻辑，详见 `docs/TECHNICAL.md` 第 3 节：

- `MainTimeline`：Qgene 响应按 `?` 拆分，第 25 项是 QNs；随后 `SKRred` 以 `QNs` 取统计；
- `リザルト_193`：`RnkRed`/`RnkSet` 响应按 `,` 拆分，只取前两项（排名、总人数）；`DAT` 是分数增量编码；
- `イベントのリザルト_196`：`DtSet` 成功返回空格；`SKRset` 的 `DAT=QNs|hist`；
- `イベント開催中_18`：`distred` 返回 101 个逗号字段，第 101 项是活动 ID。

### 测试

```bash
python tests/protocol_test.py   # 同时验证 Java 与 Python，含字段映射与两端口径一致性
```


## 快速开始

### Java

需要 JDK 17+（仓库不带运行时）。

```bash
cd java
./build.sh        # Windows: build.bat
./run.sh          # Windows: run.bat
```

### Python

需要 Python 3.9+。

```bash
cd python
./run.sh          # 或 python3 dev_server.py
```

### 配置

两端同目录的 `server.properties`：

```properties
server.port=8700      # 本地端口
server.debug=false    # 跑码模式：打印每个请求
server.log=false      # 是否写 logs/requests.log
```

修改后重启服务端生效。文件需为无 BOM 的 UTF-8。

## 题库编辑器 / 活动编辑器（GUI）

`tools/editors/` 提供 Java（Swing）与 Python（Tkinter）两套 GUI 编辑器，界面语言可切换中文 / 日本語：

| 程序 | 作用 |
|---|---|
| `QuestionEditor` / `qbank_editor.py` | 题库编辑、校验、统计 |
| `ActivityEditor` / `activity_editor.py` | 活动题库 + 活动文案 + 一键重编 |

两个编辑器都从同目录的 `editor_config.properties` 读取路径（见 `.example`），代码中不写死路径。

题库参考副本放在 `docs/banks/`（中/日主题库、活动题库、活动文案）。

详见 `tools/editors/README.md`。

## SWF 补丁（命令行程序）

`tools/patch/` 提供 **Python 与 Java 各一个补丁程序，都是 CLI（命令行），没有 GUI**，采用二进制补丁，不需要 FFDec、字体或其他第三方文件。

用户只需提供原始 SWF（SHA-256 `a77cfcf6…`）：

```bash
# Python（CLI）
python3 tools/patch/patch_swf.py --original /path/to/main.swf --out ./out

# Java（CLI）
javac -encoding UTF-8 -d tools/patch/build tools/patch/PatchSwf.java
java -cp tools/patch/build PatchSwf --original /path/to/main.swf --out ./out
```

生成：

- `out/jp/full/main.swf`、`out/jp/split/main.swf.partNN`（日文修改版）
- `out/cn/full/main.swf`、`out/cn/split/main.swf.partNN`（未完全汉化版）

补丁数据在 `tools/patch/data/`，随仓库提供；原始 SWF 需要用户自备。

## CI

`.github/workflows/ci.yml` 在 Ubuntu 上：

1. `javac` 编译 Java 服务端；
2. `py_compile` 检查 Python；
3. 启动 Python 服务端并请求 `Qgene.php`；
4. 启动 Java 服务端并请求 `Qgene.php`。

## Linux / WSL

`java/run.sh`、`python/run.sh` 为 Linux/macOS 脚本，可直接在 WSL2（Ubuntu）中运行。

## 免责

仅供学习与个人研究；游戏原作版权归原作者所有。'请自行准备合法获得的原始 SWF。

仓库**不包含** `public/` 静态资源与 SWF，运行时需自行放置补丁产物。'
