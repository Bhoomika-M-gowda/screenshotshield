#!/usr/bin/env bash
# One-command demo: builds the frontend (if needed) and serves everything on http://localhost:8000
set -e
cd "$(dirname "$0")"
python3 -m pip install -q -r backend/requirements.txt
[ -d frontend/node_modules ] || (cd frontend && npm install --no-audit --no-fund)
[ -d frontend/dist ] || (cd frontend && npm run build)
cd backend && python3 -m uvicorn main:app --host 127.0.0.1 --port 8000
