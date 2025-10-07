# Interni WMS Operativni Sloj

Modularni sistem za uvoz Pantheon trebovanja, dodjelu zadataka magacionerima, real-time praćenje izvršenja i prikaz rezultata na TV ekranima. Repo uključuje backend servise (FastAPI), frontend aplikacije (React + Vite + TypeScript + Ant Design) i infrastrukturu (Docker Compose, K8s manifesti).

## Struktura

- `backend/` — FastAPI servisi (`api-gateway`, `task-service`, `catalog-service`, `import-service`, `realtime-worker`) i zajednički paketi.
- `frontend/` — Vite aplikacije (`admin`, `pwa`, `tv`) sa shared komponentama.
- `infrastructure/` — Docker Compose, deployment i runbook skripte.
- `docs/` — arhitektura, ERD, implementacioni plan i ostala dokumentacija.
- `scripts/` — pomoćne skripte za razvoj, migracije i testiranje.

## Brzi start (Docker Compose)

```bash
cd infrastructure
docker compose up --build
```

Servisi će biti dostupni na:
- API Gateway: http://localhost:8000
- Task Service: http://localhost:8001
- Catalog Service: http://localhost:8002
- Import Service: http://localhost:8003
- Admin UI: http://localhost:4173
- PWA: http://localhost:4174
- TV Dashboard: http://localhost:4175

## Lokalni razvoj (bez dockera)

```bash
poetry install
poetry run scripts/dev.sh
# u drugom terminalu
cd frontend && npm install
npm run dev --workspace admin
```

### Migracije, seed i testovi

```bash
poetry run alembic -c backend/services/task_service/alembic.ini upgrade head
poetry run python backend/services/task_service/app/seed.py
poetry run pytest
```

Dodatne informacije: `docs/architecture.md`, `docs/implementation-plan.md`, `docs/runbook.md`.
