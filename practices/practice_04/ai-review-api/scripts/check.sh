#!/bin/sh
# Единый runner проверок проекта. Его запускают человек, агент и hook
# после каждой правки. Не ослабляйте его ради зелёного результата.
set -eu
cd "$(dirname "$0")/.."

if [ -x .venv/Scripts/python.exe ]; then
  PY=.venv/Scripts/python.exe      # Windows
elif [ -x .venv/bin/python ]; then
  PY=.venv/bin/python              # Linux / macOS
else
  PY="${PYTHON:-python3}"
fi

"$PY" -m unittest discover -s tests -t . 2>&1
