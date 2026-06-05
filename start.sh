#!/bin/bash
echo "Starting UK49 Lotto Predictor..."
echo ""

cd "$(dirname "$0")"

# Detect local IP
IP=$(hostname -I 2>/dev/null | awk '{print $1}')
if [ -z "$IP" ]; then
  IP=$(ip route get 1 2>/dev/null | awk '{print $NF;exit}')
fi
if [ -z "$IP" ]; then
  IP="0.0.0.0"
fi

find_free_port() {
  local start_port="$1"
  local port="$start_port"
  while ss -ltn 2>/dev/null | awk '{print $4}' | grep -q ":$port$"; do
    port=$((port + 1))
  done
  echo "$port"
}

BACKEND_PORT=$(find_free_port 8000)
FRONTEND_PORT=$(find_free_port 4000)
export NEXT_PUBLIC_API_URL="http://$IP:$BACKEND_PORT"

# Start backend
echo "Starting FastAPI backend on port $BACKEND_PORT..."
cd backend
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port "$BACKEND_PORT" --reload &
BACKEND_PID=$!
cd ..

# Start frontend
echo "Starting Next.js frontend on port $FRONTEND_PORT..."
cd frontend
PORT="$FRONTEND_PORT" HOSTNAME=0.0.0.0 npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "Backend:  http://$IP:$BACKEND_PORT"
echo "Frontend: http://$IP:$FRONTEND_PORT"
echo ""
echo "Open http://$IP:$FRONTEND_PORT on your mobile device"
echo ""
echo "Press Ctrl+C to stop both servers"
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" EXIT
wait
