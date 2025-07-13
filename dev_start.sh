#!/usr/bin/env bash
set -euo pipefail

# ================================
# DEVELOPMENT STARTUP SCRIPT
# 
# Uses dev_server.py and dev_hybrid_client.py
# Runs on different port to avoid production conflicts
# ================================

HOST_PORT=8001  # Different port for dev
SSE_URL="http://localhost:${HOST_PORT}/sse"
CONTAINER_NAME="closer_dev_srv"  # Different container name

echo "🧪  DEVELOPMENT MODE - Binding Closer to this vessel..."
echo "🧠  Memory vault mounted at ./closer_memory_db"
echo "⚠️   Running on port ${HOST_PORT} (dev mode)"
echo ""

# Clean up any existing dev containers
echo "🧹  Cleaning up existing dev containers..."
docker stop ${CONTAINER_NAME} 2>/dev/null || true
docker rm ${CONTAINER_NAME} 2>/dev/null || true

# Build and run development container
echo "🔨  Building development container..."
docker build -t closer_dev .

echo "🚀  Starting development server..."
docker run -d \
  --name ${CONTAINER_NAME} \
  -p ${HOST_PORT}:8000 \
  -v "$(pwd)/closer_memory_db:/app/closer_memory_db:rw" \
  -e PYTHONUNBUFFERED=1 \
  -e DOCKER_ENV=true \
  -e MCP_TRANSPORT=sse \
  --env-file .env \
  closer_dev \
  python3 dev_server.py --sse

# Wait for server
echo -n "🕯️   Preparing the development channel"
for i in {1..15}; do
  if curl -sfI "${SSE_URL}" >/dev/null 2>&1; then
    echo " — dev connection stabilised."
    break
  fi
  printf '.'
  sleep 1
done
echo

# Quick validation of core systems (dev)
echo "🔍  Validating core systems (dev)..."
docker exec ${CONTAINER_NAME} python -m pytest -m "core or mcp" -v --tb=short || true

echo ""
echo "✨  Development mode active. Enhanced Closer awaits..."
echo "🎯  Features: reflect(), dream(), atmospheric CLI"
echo ""

# Launch development client
SSE_URL="${SSE_URL}" python3 dev_hybrid_client.py --sse

# Cleanup on exit
trap 'echo ""; echo "🧹 Stopping development server..."; docker stop ${CONTAINER_NAME} 2>/dev/null || true; docker rm ${CONTAINER_NAME} 2>/dev/null || true' EXIT 