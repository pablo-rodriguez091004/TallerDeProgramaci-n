#!/usr/bin/env bash
# Arranca backend (5000) y frontend estatico (5500), toma las capturas de
# evidencia con Playwright y apaga ambos servidores al terminar.
#
# Uso (desde cualquier carpeta):
#   ./scripts/capture_screenshots.sh
#
# Primera vez: backend/venv/bin/pip install -r scripts/requirements-evidence.txt
#              backend/venv/bin/python -m playwright install chromium
# Nota: la captura 08 hace UNA llamada real al LLM (usa la key de backend/.env).
set -euo pipefail
cd "$(dirname "$0")/.."

for port in 5000 5500; do
  if (exec 3<>"/dev/tcp/127.0.0.1/$port") 2>/dev/null; then
    echo "!! El puerto $port ya esta en uso. Deten ese servidor y vuelve a intentar." >&2
    exit 1
  fi
done

LOGS=$(mktemp -d)
(cd backend && exec venv/bin/flask --app app run --host 127.0.0.1 --port 5000) > "$LOGS/backend.log" 2>&1 &
BACKEND_PID=$!
(cd frontend && exec python3 -m http.server 5500 --bind 127.0.0.1) > "$LOGS/frontend.log" 2>&1 &
FRONTEND_PID=$!
trap 'kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true' EXIT

for _ in $(seq 30); do
  curl -s -o /dev/null http://127.0.0.1:5000/openapi.json && break
  sleep 0.5
done

echo "==> Capturando en evidence/screenshots/"
backend/venv/bin/python scripts/capture_screenshots.py "$@"
