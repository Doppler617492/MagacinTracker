# Interni WMS Operativni Sloj — Arhitektura Sistema

## 1. Pregled
Sistem je podijeljen u više nezavisnih servisa i klijentskih aplikacija koje komuniciraju preko HTTP/REST i Socket.IO veza. Servisi su implementirani u FastAPI, dok frontend koristi React (Vite + TypeScript + Ant Design). Podaci se centralno skladište u PostgreSQL 16. Redis 7 služi kao keš i message broker za real-time obavještenja, task queue, kao i offline sinhronizaciju.

```
Pantheon Export (CSV/PDF/Excel)
        |
   Import Service  <---->  Filesystem (/import)
        |
   Catalog Service (artikli, radnje)
        |
   Task Service (trebovanja, zadaci, audit)
        |
   API Gateway (REST + Socket.IO) <----> Frontend Admin (React)
                                             <----> Mobile PWA (magacioneri)
                                             <----> TV Dashboard (TV UI)
        |
   Redis (pub/sub, cache)    PostgreSQL (glavna baza)
```

## 2. Servisi

### 2.1 API Gateway
- Jedinstvena ulazna tačka za sve klijente (web-admin, PWA, TV, integracije).
- Rute: autentikacija (JWT), users, trebovanja, zadaci, analitika, Socket.IO endpoint za real-time stream.
- Proxy prema Task i Catalog servisima putem internog REST/GraphQL sloja (async HTTP klijent) i event trigger-a preko Redis kanala.
- Validacija zahtjeva, centralni RBAC (role: `komercijalista`, `sef`, `magacioner`, `menadzer`).
- Generiše OpenAPI šemu.

### 2.2 Task Service
- Jezgro poslovne logike: upravljanje trebovanjima, stavkama, zadacima, statusima i audit logom.
- Gdje su tabele `trebovanje`, `trebovanje_stavka`, `zaduznica`, `zaduznica_stavka`, `audit_log`, `worker_session`.
- Emituje događaje prema Redis pub/sub kada se status promijeni (npr. `task.assigned`, `task.progress`, `task.completed`).
- API Gateway koristi ove događaje za push ka Socket.IO klijentima.

### 2.3 Catalog Service
- Upravljanje master podacima (artikli, radnje, magacini, korisnici).
- Sinhronizacija sa Pantheon katalozima (ručno ili via import).
- Servisi se oslanjaju na standardizovane entitete (npr. artikli sa bar-kodom, fallback bez bar-koda).

### 2.4 Import Service
- Python servis koji monitoriše `/import` direktorij (lokalno ili NFS mount).
- Detektuje nove fajlove (CSV, XLSX, PDF). Za PDF koristi OCR/template parser (npr. pdfplumber + regex, custom map).
- Normalizuje podatke, poziva Task Service API (stremljani JSON) za kreiranje `trebovanje` i stavki.
- Manipuliše fajlovima: `processed` i `failed` direktorijumi, loguje detalje (u DB i log fajl).
- Može se pokrenuti i ručno iz admin UI: upload → request API.

### 2.5 Notification/Real-time Worker
- Background worker (FastAPI + redis queue ili Celery/Arq) koji sluša na Redis streamove i šalje Socket.IO emit.
- Računa KPI (npr. top 10 radnika, broj završenih stavki) i kešira u Redis za TV ekran.

## 3. Klijentske aplikacije

### 3.1 Admin Web (React)
- Modul "Uvoz trebovanja" (upload form, pregled statusa).
- Lista trebovanja sa filterima, quick search.
- Detalj trebovanja: tabela stavki, dodjela magacionerima, postavljanje prioriteta/rokova, kreiranje zadataka.
- Dashboard za menadžera (analitika, grafovi, eksport PDF/CSV).

### 3.2 PWA za Magacionere
- Offline-first (IndexedDB + service worker; sync queue).
- Lista zadataka po prioritetu.
- Detalji zadatka uključuju bar-kod skener (WebRTC) i ručno potvrđivanje.
- Real-time update stanja (Socket.IO + fallback na offline sync).

### 3.3 TV Dashboard
- Full-screen React app (može reuse admin frontenda sa zasebnim route).
- Dark mode vizualizacija, leaderboard, KPI cards, animacije (CSS/Framer Motion).
- Osvježavanje preko Socket.IO i 15s rotacija sekcija.

## 4. Podaci i Skladište
- Primarna baza: PostgreSQL 16. Koristimo SQLAlchemy ORM, Alembic migracije.
- Redis 7: session store (PWA offline sync tokens), pub/sub, rate limiting, task queue.
- `files` tabela za referencu na originalni dokument (path, hash, status).
- Redis pub/sub kanali: `tv:delta` (TV feed), `import:*` (eventualno proširenje za monitoring).

## 5. Integracioni tokovi

### 5.1 Ručni uvoz
1. Korisnik upload-uje fajl preko admin UI.
2. API Gateway validira, snima fajl (S3 ili lokalno).
3. Import Service (async job) parsira fajl → generiše strukturu → zove Task Service API.
4. Task Service kreira `trebovanje` + stavke, status `new`.
5. Event `trebovanje.created` emitovan → admin UI se osvježi.

### 5.2 Automatski uvoz
1. Cron job import servisa skenira `/import`.
2. Novi fajl → parse → Task Service.
3. Uspjeh → fajl premješten u `/import/processed`.
4. Greška → `/import/failed` + audit entry.

### 5.3 Zadaci i izvršenje
1. Šef otvara trebovanje, dodjeljuje artikle radnicima → Task Service kreira `zaduznica` i `zaduznica_stavka`, status `assigned`.
2. Magacioner PWA prima zadatak (Socket.IO). Offline fallback: sync endpoint.
3. Svaki scan/ručna potvrda → Task Service validira bar-kod, update status, log.
4. Završetak zadatka → `done`, emituje se progress.
5. TV Dashboard preuzima KPI iz Redis keša i prikazuje animacije.

## 6. Sigurnost i RBAC
- JWT token izdaje Auth modul (unutar API Gateway-a) uz refresh tokene.
- Roles i permissions definisani u tabelama `role`, `role_permission`, `user_role`.
- Audit log (task_service) hvata akcije: import, assign, scan, manual complete, status promjene.
- OTP/2FA za prijavu šefova (opcioni enhancement).

## 7. Offline strategija (PWA)
- Service Worker kešira osnovne rute i zadatke.
- IndexedDB čuva zadatke i izmjene.
- Sync engine šalje queue prema API Gateway-u kad je mreža dostupna.
- Konfliktni slučajevi: server prioritet, klijent se obavještava.

## 8. DevOps i Deploy
- Docker Compose za dev: `api-gateway`, `task-service`, `catalog-service`, `import-service`, `realtime-worker`, `frontend-admin`, `frontend-pwa`, `frontend-tv`, `postgres`, `redis`.
- CI/CD pipeline (GitHub Actions): lint, test, build image, push, deploy.
- Production: Hetzner + Kubernetes. Svaki servis kao Deployment + HPA. Ingress za API/Socket/Front. PostgreSQL managed (Hetzner Cloud), Redis (Redis Stack). Shared volume za import.

## 9. Observability
- Centralizovano logovanje (JSON logs, Loki/ELK).
- Metrics: Prometheus + Grafana (task throughput, import errors, websocket connections).
- Alerts: Slack/Email.

## 10. Dalji koraci
- Definisati detaljan ERD i migracije (vidi `docs/erd.md`).
- Pripremiti SRS (detaljan use case i user story opis).
- Postaviti skeleton koda za servise i frontende.
