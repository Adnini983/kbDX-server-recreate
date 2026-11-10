#!/usr/bin/env bash
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$here/build/classes"
javac -encoding UTF-8 -d "$here/build/classes" "$here/src/KbdxServer.java"
echo "built: $here/build/classes"
