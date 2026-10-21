#!/usr/bin/env bash
# Carga el catalogo ampliado (database/catalog.sql) en la base de desarrollo
# definida en backend/.env (DATABASE_URL). Se puede correr varias veces.
#
# Uso: ./scripts/seed_catalog.sh
set -euo pipefail
cd "$(dirname "$0")/.."

DATABASE_URL=$(grep -E '^DATABASE_URL=' backend/.env | cut -d= -f2-)
if [ -z "$DATABASE_URL" ]; then
  echo "!! Falta DATABASE_URL en backend/.env" >&2
  exit 1
fi

echo "==> Aplicando migraciones pendientes"
(cd backend && venv/bin/flask --app app db upgrade)

echo "==> Cargando database/catalog.sql"
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -q -f database/catalog.sql
psql "$DATABASE_URL" -c "SELECT service_id, service_name, estimated_duration_minutes AS min, base_price FROM services ORDER BY service_id"
