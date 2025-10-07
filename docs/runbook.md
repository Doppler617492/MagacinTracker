# Runbook — Pokretanje Sistema

## 1. Preduslovi
- Docker i Docker Compose
- Node.js 20 (za lokalni razvoj frontenda)
- Python 3.11 + Poetry (za lokalni razvoj backend-a)

## 2. Lokalne varijable okruženja
- Kopirati `.env.example` fajlove u `.env` unutar svakog servisa i prilagoditi vrijednosti.

## 3. Pokretanje preko Docker Compose
```bash
cd infrastructure
docker compose up --build
```
- Provjeriti `/health` rute:
  - `http://localhost:8000/health`
  - `http://localhost:8001/api/health`
  - `http://localhost:8002/health`
  - `http://localhost:8003/health`

## 4. Pokretanje u development modu (bez dockera)
1. `poetry install`
2. Pokrenuti servise:
   - `poetry run uvicorn services.api_gateway.app.main:app --reload --port 8000`
   - `poetry run uvicorn services.task_service.app.main:app --reload --port 8001`
   - `poetry run uvicorn services.catalog_service.app.main:app --reload --port 8002`
   - `poetry run uvicorn services.import_service.app.main:app --reload --port 8003`
   - `poetry run python -m services.realtime_worker.app`
3. Migracije i seed podaci:
   - `poetry run alembic -c backend/services/task_service/alembic.ini upgrade head`
   - `poetry run python backend/services/task_service/app/seed.py`
4. Frontend:
   - `cd frontend && npm install`
   - `npm run dev --workspace admin`
   - `npm run dev --workspace pwa`
   - `npm run dev --workspace tv`

## 5. Testiranje
- Backend unit testovi: `poetry run pytest`
- Frontend smoke: `npm run build --workspace admin` (po potrebi)

## 6. Troubleshooting
- Provjeriti `docker compose logs <service>`.
- Provjeriti Redis konekciju (`redis-cli PING`).
- Za import greške: pogledati `/import/failed` i logove import servisa.
- Prometheus metrike dostupne na `http://localhost:8000/metrics` (gateway) i `http://localhost:8001/metrics` (task-service).
