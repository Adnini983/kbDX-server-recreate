# Python 服务端

- `dev_server.py`：本地 HTTP 服务，接口与 Worker/Java 服务端一致。
- `kbdx_core.py`：协议实现（Qgene / 排行 / 活动等）。
- `data_cn.py` / `data_jp.py`：内嵌的中日题库与页面资源。
- `server.properties`：端口 / 跑码模式 / 日志开关。

## 运行

```bash
./run.sh          # 需要 python3
# 或
python3 dev_server.py
```

仓库不自带 Python 运行时。
