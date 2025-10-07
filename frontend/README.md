# Frontend Aplikacije

Repozitorij sadrži tri Vite + React aplikacije:

- `admin` — web admin za uvoz i upravljanje trebovanjima, zadacima i analitikom.
- `pwa` — offline-first aplikacija za magacionere (skener, ručna potvrda, sync).
- `tv` — TV dashboard za leaderboard i KPI u realnom vremenu.

## Brzi start

```bash
cd frontend
npm install
npm run dev --workspace admin
npm run dev --workspace pwa
npm run dev --workspace tv
```

Svi projekti proxy-iraju API pozive na `http://localhost:8000` (API Gateway).
