#!/bin/zsh
set -e
cd "$(dirname "$0")"
task_python=""
for candidate in python3.12 python3; do
  if command -v "$candidate" >/dev/null 2>&1 && "$candidate" -c 'import sys; raise SystemExit(sys.version_info < (3, 10))'; then
    task_python="$candidate"
    break
  fi
done
if [[ -z "$task_python" ]]; then
  echo 'Python 3.10 or higher is required. Install Python, then run this file again.'
  read '?Press Return to close.'
  exit 1
fi
if [[ ! -x .venv/bin/python ]]; then
  "$task_python" -m venv .venv
fi
.venv/bin/python -m pip install -r requirements-dev.txt
echo ''
echo 'WealthPilot: http://127.0.0.1:8000'
echo 'Keep this Terminal window open during recording. Press Control-C to stop.'
echo 'If the browser opens before the server is ready, refresh once.'
echo 'If port 8000 is occupied, stop the previous WealthPilot server first.'
(sleep 2; open 'http://127.0.0.1:8000') &
exec .venv/bin/python app.py --serve
