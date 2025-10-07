# Implementacioni Plan

## Faza 0 — Inicijalno postavljanje
- Repo struktura (monorepo): `backend/`, `services/`, `frontend/`, `infrastructure/`, `docs/`.
- Definisati `.tool-versions` / `pyproject.toml` (Python 3.11), `package.json` za front.
- Postaviti precommit (black, isort, flake8, mypy) i ESLint + Prettier.
- Docker Compose za lokalni razvoj (Postgres, Redis, MinIO, servisni kontejneri).
- CI pipeline skeleton (GitHub Actions): lint, test stub.

## Faza 1 — Ručni uvoz i osnovni admin modul
1. **Import API & Service**
   - Endpoint `POST /imports/manual` (multipart upload) → stvara `import_job` (status `pending`).
   - Background task (import-service) parsira CSV/XLSX (usecase: `MP kalkulacija...`).
   - Parser normalizuje zaglavlje, mapira artikle (lookup po šifri, fallback kreira stub artikl).
   - Task Service endpoint `POST /trebovanja` prima payload.
   - Duplikat zaštita po `dokument_broj`.
2. **Admin UI**
   - Stranica "Uvoz trebovanja" sa tabelom job-ova.
   - Forme za upload, status badge (New, Processing, Done, Failed).
3. **Auth & RBAC baza**
   - Kreirati korisnike, role, login flow (JWT, refresh token, guard po ruti).
4. **Audit log**
   - Svaki import + kreiranje trebovanja logira event.

## Faza 2 — Dodjela zadataka i magacionerska aplikacija
1. **Task Service**
   - Endpointi: `GET /trebovanja`, `GET /trebovanja/{id}`, `POST /trebovanja/{id}/assign`.
   - Kreiranje `zaduznica` + `zaduznica_stavka` iz selektovanih artikala.
   - Status tranzicije (new → assigned → in_progress → done).
2. **Admin UI**
   - Detalj trebovanja: tabela stavki, multi-select, modal za dodjelu (magacioner, rok, prioritet, split quantity).
   - Pregled zadataka po magacioneru.
3. **PWA aplikacija**
   - Login, lista zadataka (status cards, progress).
   - Detalj zadatka: lista stavki, offline keš (IndexedDB), start/stop.
   - Barcode skeniranje (browser API) + ručna potvrda.
   - API pozivi: `POST /zadaci/{id}/scan`, `POST /zadaci/{id}/manual`.
   - Offline queue + sync endpoint `POST /sync`.
4. **Real-time**
   - Socket.IO namespaces: `/admin`, `/worker`, `/tv`.
   - Eventi: `trebovanje.updated`, `task.progress`, `leaderboard.update`.
   - Redis pub/sub + worker koji transformiše evente.

## Faza 3 — Automatski import i TV dashboard
1. **Automatski import**
   - Watcher koji skenira `/import` svakih 60s (watchdog).
   - Konfiguracija putem `.env` (`IMPORT_WATCH_PATH`, `IMPORT_ARCHIVE_PATH`).
   - Error handling i retry.
2. **TV Dashboard**
   - Full-screen layout, dark theme, auto-rotate sekcije.
   - Leaderboard data iz API-ja (cached) + Socket.IO.
   - Animacije za milestone (50/100/200 stavki) – event `worker.milestone`.
3. **Analitika & Izvještaji**
   - KPI agregacije (SQL materialized view ili background job).
   - Dashboard grafici (Victory/Antd charts).
   - Export CSV/PDF (`/reports/export` + server side PDF generation - WeasyPrint/Playwright).

## Faza 4 — Hardening & DevOps
- E2E testovi (Playwright) za admin i PWA.
- Load test Socket.IO (Locust + socketio-client).
- Monitoring integracija (Prometheus exporters, Grafana dashboards).
- Production pipeline: build Docker images, push, deploy na Hetzner K8s.
- Dokumentacija: SRS, User Guide, Runbook, Deployment guide, Test plan.

## Backlog dodataka
- Integracija sa kompanijskim AD/SSO.
- Mobile native wrapper (Capacitor) za PWA.
- Voice pick modul (hands-free).
- Warehouse slotting modul (replenishment).

## Sprint 1 (MVP jezgro) — Status
- ✅ Implementirani FastAPI servisi (gateway, task-service) sa Alembic migracijama, audit logom i RBAC guardovima.
- ✅ Import servis (ručni + poller) sa parsiranjem CSV/XLSX i idempotentnim kreiranjem `trebovanje` zapisa.
- ✅ Realtime worker i Socket.IO feed (`tv_delta`) sa Redis pub/sub.
- ✅ Frontendi: Admin (lista, detalj i dodjela), PWA (moji zadaci, sken/ručno), TV dashboard (leaderboard, queue, KPI).
- ✅ Observability: JSON logovi, `/metrics` endpointi, Socket.IO metrike.
- ✅ Testovi: parser validacije i statusni prelaz (scan → done) pokriveni PyTest-om.
