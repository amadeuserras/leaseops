#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
LEASECLEAR_ROOT="$(cd "$ROOT/../leaseclear" && pwd)"

API_PID=""
LEASECLEAR_PID=""
cleanup() {
  echo ""
  echo "🛑  Shutting down…"
  kill "$API_PID" 2>/dev/null || true
  kill "$LEASECLEAR_PID" 2>/dev/null || true
  docker compose -f "$ROOT/docker-compose.yml" stop
  docker compose -f "$LEASECLEAR_ROOT/docker-compose.yml" stop
}
trap cleanup EXIT INT TERM

wait_for_health() {
  local url="$1"
  local label="$2"
  for _ in $(seq 1 60); do
    if curl -sf "$url" > /dev/null; then
      echo "✅  $label"
      return 0
    fi
    sleep 0.5
  done
  echo "❌  $label did not become ready in time." >&2
  exit 1
}

# 1. Postgres (both projects)
echo ""
echo "🐘  LeaseOps Postgres"
docker compose -f "$ROOT/docker-compose.yml" up -d

echo ""
echo "🐘  LeaseClear Postgres"
docker compose -f "$LEASECLEAR_ROOT/docker-compose.yml" up -d

# 2. LeaseClear API (:8001)
echo ""
echo "📄  LeaseClear API  →  :8001"
cd "$LEASECLEAR_ROOT/backend"
uv run uvicorn leaseclear.api.main:app --reload --port 8001 &
LEASECLEAR_PID=$!
wait_for_health "http://127.0.0.1:8001/health" "LeaseClear healthy"

# 3. LeaseOps API (:8000)
echo ""
echo "📬  LeaseOps API  →  :8000"
cd "$ROOT/backend"
uv run uvicorn leaseops.api.main:app --reload --port 8000 &
API_PID=$!
wait_for_health "http://127.0.0.1:8000/health" "LeaseOps healthy"

# 4. Frontend - not implemented yet

echo ""
echo "🚀  All set   LeaseOps :8000  ·  LeaseClear :8001"
echo "   Press Ctrl-C to stop."
wait "$API_PID" "$LEASECLEAR_PID"
