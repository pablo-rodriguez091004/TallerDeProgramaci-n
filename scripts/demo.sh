#!/usr/bin/env bash
# Levanta la demo de la Guia 6 para grabar el video.
#
#   ./scripts/demo.sh                    backend (:5000) + frontend (:5500) normales
#   ./scripts/demo.sh --breaker-abierto  DEMOSTRACION CONTROLADA: datos.gov.co apunta a un host .invalid,
#                                        asi "Actualizar datos" abre su circuit breaker (el DANE sigue normal)
#   ./scripts/demo.sh --ciclo            solo terminal: ciclo completo CLOSED -> OPEN -> HALF_OPEN -> CLOSED
#                                        y tiempos reales del retry (scripts/demo_resilience.py)
#
# Usuario dueño de prueba: carlos.owner@tallermecanico.com / test1234 (ver README).
# Ctrl+C detiene los servidores.
set -euo pipefail
cd "$(dirname "$0")/.."
MODE="${1:-normal}"

if [ "$MODE" = "--ciclo" ]; then
  exec backend/venv/bin/python scripts/demo_resilience.py
fi

for port in 5000 5500; do
  if (exec 3<>"/dev/tcp/127.0.0.1/$port") 2>/dev/null; then
    echo "!! El puerto $port ya esta en uso. Deten ese servidor y vuelve a intentar." >&2; exit 1
  fi
done

EXTRA=()
if [ "$MODE" = "--breaker-abierto" ]; then
  EXTRA=(MARKET_SOCRATA_BASE_URL=https://datos-gov-co.invalid/resource MARKET_MAX_RETRIES=1)
  echo "==> DEMOSTRACION CONTROLADA: datos.gov.co -> https://datos-gov-co.invalid (el DANE usa su URL real)"
elif [ "$MODE" != "normal" ]; then
  echo "Uso: $0 [--breaker-abierto | --ciclo]" >&2; exit 2
fi

(cd backend && exec env "${EXTRA[@]}" FLASK_DEBUG=0 venv/bin/flask --app app run --host 127.0.0.1 --port 5000) &
BACKEND_PID=$!
(cd frontend && exec python3 -m http.server 5500 --bind 127.0.0.1 > /dev/null 2>&1) &
FRONTEND_PID=$!
trap 'kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true' EXIT INT TERM

for _ in $(seq 60); do curl -s -o /dev/null http://127.0.0.1:5000/openapi.json && break; sleep 0.5; done
cat <<MSG

==> Demo lista (Ctrl+C para detener)
    Mercado:  http://127.0.0.1:5500/pages/mercado.html   (login: carlos.owner@tallermecanico.com / test1234)
    Swagger:  http://127.0.0.1:5000/docs
    Guion:    docs/video_script_EN.md
MSG
wait $BACKEND_PID
