# Backend Servisi

Backend je organizovan kao Python monorepo koji sadrži nezavisne FastAPI servise i zajednički paket `app_common` sa modelima, konfiguracijama i util funkcijama.

## Servisi

- `services/api_gateway` — centralni ulaz za klijente, autentikacija, RBAC, proxy prema ostalim servisima.
- `services/task_service` — poslovna logika trebovanja, zadataka, audit log.
- `services/catalog_service` — master podaci i sinhronizacija kataloga.
- `services/import_service` — obrada Pantheon fajlova (ručno i automatski).
- `services/realtime_worker` — real-time emit i agregacije leaderboard-a.

## Razvoj

1. Aktiviraj Python 3.11 virtualno okruženje.
2. Instaliraj zavisnosti: `poetry install`.
3. Pokreni servis: `poetry run uvicorn services.api_gateway.app.main:app --reload`.

Svaki servis ima `.env.example` sa konfiguracionim varijablama.
