#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

echo "==================================================================="
echo " Launching Vanguard ClaimOS: Backend + Next.js UI"
echo "==================================================================="

if [ -f "$DIR/.venv/bin/python" ]; then
    PYTHON_CMD="$DIR/.venv/bin/python"
else
    PYTHON_CMD="python3"
fi

# Start Backend in background
"$PYTHON_CMD" -m uvicorn api:app --app-dir backend --host 127.0.0.1 --port 8000 &
BACKEND_PID=$!

sleep 2

# Start Frontend in background
cd "$DIR/frontend"
npm run dev &
FRONTEND_PID=$!

echo "==================================================================="
echo " Vanguard ClaimOS is running!"
echo " Backend:  http://127.0.0.1:8000/docs (PID: $BACKEND_PID)"
echo " Frontend: http://localhost:3000 (PID: $FRONTEND_PID)"
echo "==================================================================="

# Trap SIGINT/SIGTERM to kill child processes cleanly
cleanup() {
    echo "Stopping servers..."
    kill "$BACKEND_PID" 2>/dev/null
    kill "$FRONTEND_PID" 2>/dev/null
    exit
}
trap cleanup SIGINT SIGTERM

wait
