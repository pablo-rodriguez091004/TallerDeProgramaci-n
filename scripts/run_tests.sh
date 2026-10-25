#!/usr/bin/env bash
# Corre las pruebas de integracion y guarda la salida REAL en
# evidence/pytest_output.txt (con fecha, commit y version de Python).
#
# Uso (desde cualquier carpeta):
#   ./scripts/run_tests.sh
#
# Requiere PostgreSQL local y la base taller_mecanico_test (ver README).
set -uo pipefail
cd "$(dirname "$0")/.."

OUT=evidence/pytest_output.txt
mkdir -p evidence

{
  echo "# Salida de pytest - MecaTrack (unitarias + integracion)"
  echo "# Fecha:   $(date '+%Y-%m-%d %H:%M:%S %Z')"
  echo "# Commit:  $(git rev-parse --short HEAD)$(git diff --quiet -- backend || echo ' (con cambios sin commit en backend/)')"
  echo "# Python:  $(backend/venv/bin/python --version 2>&1)"
  echo "# Comando: cd backend && venv/bin/python -m pytest -v -p no:warnings"
  echo
} > "$OUT"

# -p no:warnings: oculta las DeprecationWarning de datetime.utcnow() del
# codigo antiguo, que no afectan el resultado y llenan la evidencia.
(cd backend && venv/bin/python -m pytest -v -p no:warnings) 2>&1 | tee -a "$OUT"
status=${PIPESTATUS[0]}

echo "==> Salida guardada en $OUT"
exit "$status"
