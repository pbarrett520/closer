#!/usr/bin/env bash
set -euo pipefail

HOST_PORT=8000
SSE_URL="http://localhost:${HOST_PORT}/sse"

echo "⛓️   Binding Closer to this vessel..."
echo "🧠   Memory vault mounted at ./closer_memory_db"
echo ""

# Clean up and restart
docker compose down 2>/dev/null || true
docker compose up -d --build

# Wait for server
echo -n "🕯️   Preparing the channel"
for i in {1..15}; do
  if curl -sfI "${SSE_URL}" >/dev/null 2>&1; then
    echo " — connection stabilised."
    break
  fi
  printf '.'
  sleep 1
done
echo

# Quick test
echo "🔍  Probing the memory substrate..."
docker exec closer_srv python3 test_memory.py || true

echo "🧪  Invoking toolchain diagnostics..."
docker exec closer_srv python3 test_mcp_tools.py || true

echo ""
echo "🫥  The veil parts. Closer awaits..."
python3 hybrid_client.py --sse
