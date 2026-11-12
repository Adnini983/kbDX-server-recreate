# Java 服务端

- `src/KbdxServer.java`：单文件服务端（JDK 17，无第三方依赖）。
- `data/cn/kbDX/`、`data/jp/kbDX/`：中日双语言数据（协议描述、题库、排行、活动）。
- `server.properties`：端口 / 跑码模式 / 日志开关。

## 运行

```bash
./build.sh     # 或 build.bat
./run.sh       # 或 run.bat
```

请求路径：`/cn/kbDX/...` 与 `/jp/kbDX/...`。

需要 JDK 17+，仓库**不附带**运行时。
