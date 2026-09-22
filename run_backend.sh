#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

echo "==================================================================="
echo " Starting Vanguard ClaimOS Backend Service (Port 8000)"
echo "==================================================================="

if [ -f "$DIR/.venv/bin/python" ]; then
    PYTHON_CMD="$DIR/.venv/bin/python"
else
    PYTHON_CMD="python3"
fi

"$PYTHON_CMD" -m uvicorn api:app --app-dir backend --host 127.0.0.1 --port 8000 --reload
