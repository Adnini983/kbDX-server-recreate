#!/usr/bin/env bash
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
cd "$here"
if [ ! -f build/classes/KbdxServer.class ]; then
  "$here/build.sh"
fi
exec java -cp "$here/build/classes" KbdxServer
