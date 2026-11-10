#!/usr/bin/env bash
# 在 WSL2 / Linux 下启动 Python 服务端并做一次冒烟测试。
set -u
here="$(cd "$(dirname "$0")/.." && pwd)"
work="/tmp/kbdx_py_test"
rm -rf "$work"
cp -r "$here/python" "$work"
cd "$work" || exit 1
sed -i 's/^server.port=.*/server.port=18830/' server.properties
python3 dev_server.py > /tmp/kbdx.log 2>&1 &
PID=$!
sleep 5
echo "--- server log ---"
cat /tmp/kbdx.log
echo -n "CN Qgene: "
curl --noproxy '*' -s -o /dev/null -w '%{http_code}\n' -X POST -d 'NUM=1&MOD=0&VER=24' http://127.0.0.1:18830/cn/kbDX/Qgene.php
echo -n "JP Qgene: "
curl --noproxy '*' -s -o /dev/null -w '%{http_code}\n' -X POST -d 'NUM=1&MOD=0&VER=24' http://127.0.0.1:18830/jp/kbDX/Qgene.php
kill $PID 2>/dev/null