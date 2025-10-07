# Infrastrukturа

## Docker Compose (dev)

```bash
cd infrastructure
docker compose up --build
```

Servisi:
- `postgres:5432`
- `redis:6379`
- `api-gateway:8000`
- `task-service:8001`
- `catalog-service:8002`
- `import-service:8003`
- `admin-frontend:4173`
- `pwa-frontend:4174`
- `tv-frontend:4175`

Shared volumeni:
- `postgres_data` — trajni podaci baze.
- `import_files` — Pantheon fajlovi (`/import`, `/import/processed`, `/import/failed`).

## Kubernetes (TODO)

- Pripremiti Helm chart ili Kustomize manifest za svaki servis.
- Konfigurisati Secrets za `.env` varijable.
- Postaviti Horizontal Pod Autoscaler za gateway i task service.
