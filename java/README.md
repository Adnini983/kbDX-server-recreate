# Java 服务端

- `src/KbdxServer.java`：单文件服务端（JDK 17，无第三方依赖）。
- `kbDX/`：数据描述文件（`.php` 键值）、题库、排行、活动数据。
- `server.properties`：端口 / 跑码模式 / 日志开关。

## 运行

```bash
./build.sh     # 或 build.bat
./run.sh       # 或 run.bat
```

需要 JDK 17+，仓库**不附带**运行时。
