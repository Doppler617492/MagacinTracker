# Test Plan i Report

## 1. Strategija testiranja
- Jedinični testovi (FastAPI endpoints, parseri, repositoriji).
- Integracioni testovi (import → task service DB, Socket.IO eventovi).
- E2E testovi (Playwright scenarija za admin, PWA, TV).
- Load test za Socket.IO (Locust scenariji).

## 2. Okruženja
- `dev` (Docker Compose)
- `staging` (K8s namespace sa realnim podacima)
- `prod`

## 3. Test slučajevi (primjeri)
- `TP-IMPORT-01`: Uvoz validnog CSV fajla.
- `TP-IMPORT-02`: Uvoz duplikata `dokument_broj`.
- `TP-TASK-01`: Dodjela stavki magacioneru.
- `TP-PWA-01`: Offline unos i kasniji sync.
- `TP-TV-01`: Socket update prikazan u 2s.

## 4. Automatizacija
- Pytest + httpx za backend (`poetry run pytest`).
- Playwright test suite (`/tests/e2e`).
- GitHub Actions pipeline.

## 5. Reporting
- Generisati HTML report (Allure/pytest-html).
- SLA: 0 blocker/critical bugova prije produkcije.

> **TODO:** Popuniti detaljne test korake i očekivane rezultate tokom implementacije.
