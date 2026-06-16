#!/usr/bin/env bash
# start_local_pipeline.sh — Start local Redis + Celery worker for AI pipeline
#
# Use this when you want to process recordings that were uploaded via the
# cloud dashboard. The worker connects to the same Neon DB and R2 storage
# as the cloud API.
#
# Prerequisites:
#   brew install redis    (for local Redis broker)
#   uv sync in apps/api   (Python dependencies)
#   apps/api/.env.local-pipeline configured
#
# Usage:
#   ./start_local_pipeline.sh
#
# Then in another terminal:
#   cd apps/api && uv run python process_uploaded.py
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
API_DIR="${SCRIPT_DIR}/apps/api"

echo "=== CXSAMAA Local Pipeline Worker ==="
echo ""

# ── Step 1: Start Redis if not running ───────────────────────────────────────
echo "[1/3] Checking Redis..."
if redis-cli ping 2>/dev/null | grep -q PONG; then
    echo "  Redis is already running."
else
    echo "  Starting Redis..."
    if command -v brew &>/dev/null; then
        brew services start redis 2>/dev/null || redis-server --daemonize yes
    else
        redis-server --daemonize yes
    fi
    sleep 2
    if redis-cli ping 2>/dev/null | grep -q PONG; then
        echo "  Redis started."
    else
        echo "  ERROR: Redis failed to start. Install with: brew install redis"
        exit 1
    fi
fi

# ── Step 2: Verify Python environment ────────────────────────────────────────
echo "[2/3] Checking Python environment..."
cd "${API_DIR}"

if [ ! -f ".venv/bin/python" ]; then
    echo "  Creating virtual environment..."
    uv venv
fi

source .venv/bin/activate
echo "  Python: $(python --version)"

# ── Step 3: Load env and start Celery ────────────────────────────────────────
echo "[3/3] Starting Celery worker..."

ENV_FILE="${API_DIR}/.env.local-pipeline"
if [ ! -f "${ENV_FILE}" ]; then
    echo ""
    echo "  WARNING: ${ENV_FILE} not found!"
    echo "  Copy the example and fill in your credentials:"
    echo "    cp apps/api/.env.local-pipeline.example apps/api/.env-local-pipeline"
    echo ""
    echo "  Falling back to .env (dev config)..."
    ENV_FILE="${API_DIR}/.env"
fi

# Export env vars from the env file
set -a
grep -v '^\s*#' "${ENV_FILE}" | grep -v '^\s*$' | while IFS='=' read -r key value; do
    export "${key}=${value}" 2>/dev/null || true
done
set +a

echo "  APP_ENV:        ${APP_ENV:-not set}"
echo "  PIPELINE_MODE:  ${PIPELINE_MODE:-full}"
echo "  STORAGE_BACKEND: ${STORAGE_BACKEND:-not set}"
echo "  DB:             ${DATABASE_URL%%@*}@..."
echo ""
echo "  Starting Celery worker (pool=solo for macOS gRPC compatibility)..."
echo "  Press Ctrl+C to stop."
echo ""

celery -A src.workers.celery_app worker \
    --loglevel=info \
    --pool=solo \
    --concurrency=2 \
    --max-tasks-per-child=10
