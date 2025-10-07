#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$PROJECT_ROOT"

if ! command -v docker &>/dev/null; then
  echo "Docker is required. Please install Docker Desktop." >&2
  exit 1
fi

COMPOSE_CMD="docker compose"

echo "[dev] Building and starting containers..."
$COMPOSE_CMD up -d --build

echo "[dev] Running database migrations..."
$COMPOSE_CMD exec task-service alembic upgrade head

echo "[dev] Seeding reference data..."
$COMPOSE_CMD exec task-service python -m app.seed

ADMIN_URL=${PUBLIC_BASE_URL:-http://localhost:${API_GATEWAY_PORT:-8123}}

cat <<MSG

Services are up and seeded.
- API Gateway: ${PUBLIC_BASE_URL:-http://localhost:${API_GATEWAY_PORT:-8123}}
- Admin UI: http://localhost:${ADMIN_PORT:-5130}
- PWA: http://localhost:${PWA_PORT:-5131}
- TV Dashboard: http://localhost:${TV_PORT:-5132}

To follow logs: docker compose logs -f
To stop services: docker compose down
MSG
