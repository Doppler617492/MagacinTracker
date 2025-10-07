# Deployment Uputstvo — Hetzner / Kubernetes

## 1. Priprema
- Izgraditi Docker image za svaki servis i push-ovati na container registry (npr. `registry.gitlab.com/cungu/wms`).
- Konfigurisati Secrets (`JWT_SECRET_KEY`, DB kredencijali, Redis URL, Socket.IO ključ).

## 2. Infrastrukturа
- Provision Hetzner Kubernetes klaster (via Terraform ili Hetzner Cloud Console).
- Kreirati PostgreSQL i Redis managed servise (ili koristiti Helm chart).
- Postaviti S3-kompatibilni storage (Hetzner StorageBox ili MinIO) za arhivu import fajlova.

## 3. Deploy pipeline (GitHub Actions / GitLab CI)
1. Checkout koda
2. Run lint/test
3. Build Docker image (`docker buildx build ...`)
4. Push image
5. Deploy pomoću `kubectl` ili Helm-a:
   - `helm upgrade --install api-gateway deploy/api-gateway`
   - `helm upgrade --install task-service deploy/task-service`
   - ...

## 4. Konfiguracija K8s resursa
- `Deployment`, `Service` i `HorizontalPodAutoscaler` za svaki servis.
- `Ingress` (NGINX) sa TLS certifikatom (Let's Encrypt / Cert-Manager).
- `ConfigMap` za neosjetljive konfiguracije; `Secret` za osjetljive.
- `PersistentVolumeClaim` za `/import` folder (import-service).

## 5. Post-deploy provjere
- `kubectl get pods -n wms`
- Provjeriti `/health` rute preko Ingress-a.
- Izvršiti end-to-end test: import → assign → scan → TV.

## 6. Rollback strategija
- Helm `rollback` komanda.
- Database backup restore (pg_dump / WAL).

## 7. Observability
- Deploy Prometheus + Grafana (Helm `kube-prometheus-stack`).
- Loki za logove, Alertmanager za notifikacije (Slack/Email).

> **TODO:** Dodati konkretne Helm chart primjere i CI fajl nakon implementacije.
