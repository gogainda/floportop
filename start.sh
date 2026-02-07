#!/bin/bash
# Start unified FastAPI service (API + static HTML frontend)
set -euo pipefail

export PYTHONUNBUFFERED=1
export PYTHONPATH="/app/src:/app"
PORT="${PORT:-8501}"

exec uvicorn apps.api.app:app --host 0.0.0.0 --port "${PORT}" --log-level info
