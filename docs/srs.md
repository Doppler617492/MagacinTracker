# Specifikacija Softverskih Zahtjeva (SRS)

**Projekat:** Interni WMS Operativni Sloj — Uvoz Pantheon trebovanja

## 1. Uvod
- **Namjena dokumenta:** Definiše funkcionalne i ne-funkcionalne zahtjeve.
- **Opseg sistema:** Import Pantheon dokumenta, task management, PWA za magacionere, TV dashboard, analitika.
- **Akteri:** Komercijalista, Šef magacina, Magacioner, Menadžer, Sistem integracije.

## 2. Opšti opis
- Procesni tokovi (import, assign, izvršenje, TV live, analitika).
- Pretpostavke i zavisnosti (Pantheon export format, internet konekcija, bar kod skeneri, offline režim).

## 3. Funkcionalni zahtjevi
- Raspoređeni po modulima (Import, Trebovanja, Zadaci, PWA interakcija, TV, Analitika, RBAC).
- Svaki zahtjev označen ID-jem (npr. `F-IMPORT-01`).

## 4. Ne-funkcionalni zahtjevi
- Performanse (latencija < 2s za import, < 250ms za socket update).
- Pouzdanost (retry, idempotencija).
- Sigurnost (JWT, audit log, šifrovanje).
- Offline podrška.

## 5. API interfejsi
- Referenca na OpenAPI specifikaciju (`docs/openapi/api-gateway.yaml`, TODO).

## 6. Baza podataka
- Upućivanje na ERD (`docs/erd.md`).

## 7. Dodatni zahtjevi
- Lokalizacija (srpski/engleski).
- Logging i observability.

> **TODO:** Popuniti detaljne zahtjeve po akterima i procesima tokom implementacije.
