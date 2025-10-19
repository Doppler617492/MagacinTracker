# 👥 Team Management Guide - Magacin Track

**Kompletni vodič za upravljanje timovima**

---

## 🎯 **PREGLED**

Sistem Magacin Track podržava upravljanje timovima radnika, omogućavajući menadžerima da:
- ✅ Kreiraju nove timove (parovi radnika)
- ✅ Dodijele timove smjenama (A ili B)
- ✅ Uređuju postojeće timove
- ✅ Deaktiviraju timove
- ✅ Prate performanse timova

---

## 🔑 **KO MOŽE UPRAVLJATI TIMOVIMA**

### **Dozvole:**
- **ADMIN** - Sve operacije (create, update, delete)
- **SEF** - Sve operacije (create, update, delete)
- **MENADZER** - Create i update (ne može delete)

---

## 📱 **GDJE SE UPRAVLJA TIMOVIMA**

### **Admin Panel:**
```
http://localhost:5130/teams
```

### **Funkcionalnosti:**
1. **Pregled svih timova** - tabela sa članovima, smjenom, i statusom
2. **Kreiranje novih timova** - dugme "Dodaj Tim"
3. **Uređivanje timova** - dugme "Uredi" u akcijama
4. **Brisanje timova** - dugme "Obriši" (samo ako nema aktivnih zadataka)
5. **Pregled performansi** - dugme "Performanse"

---

## 🆕 **KREIRANJE NOVOG TIMA**

### **Koraci:**

1. **Otvorite Teams stranicu:**
   - http://localhost:5130/teams

2. **Kliknite "Dodaj Tim":**
   - Otvara se modal

3. **Popunite formu:**
   ```
   Naziv Tima:    Team B1
   Radnik 1:      [Select magacionera]
   Radnik 2:      [Select drugog magacionera]
   Smjena:        B (12:00 - 19:00)
   ```

4. **Kliknite "Kreiraj"**

### **Validacije:**
- ✅ Naziv tima mora biti jedinstven
- ✅ Oba radnika moraju biti aktivni magacioneri
- ✅ Radnici ne smiju već biti u drugom aktivnom timu
- ✅ Smjena mora biti A ili B

### **Primjer putem API:**
```bash
TOKEN="<admin-token>"

curl -X POST http://localhost:8123/api/teams \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Team B1",
    "worker1_id": "<worker1-uuid>",
    "worker2_id": "<worker2-uuid>",
    "shift": "B"
  }'
```

**Response:**
```json
{
  "id": "uuid-here",
  "name": "Team B1",
  "shift": "B",
  "active": true,
  "worker1": {
    "id": "worker1-uuid",
    "first_name": "John",
    "last_name": "Doe",
    "email": "john@example.com"
  },
  "worker2": {
    "id": "worker2-uuid",
    "first_name": "Jane",
    "last_name": "Smith",
    "email": "jane@example.com"
  },
  "created_at": "2025-10-16T10:00:00Z"
}
```

---

## ✏️ **UREĐIVANJE TIMA**

### **Koraci:**

1. **Na Teams stranici, kliknite "Uredi" pored tima**

2. **Promijenite željene podatke:**
   - Naziv tima
   - Radnik 1
   - Radnik 2
   - Smjena (A/B)

3. **Kliknite "Ažuriraj"**

### **Napomena:**
- Možete promijeniti samo neke podatke (ostali ostaju isti)
- Ne možete dodjeliti radnika koji je već u drugom aktivnom timu

### **Primjer putem API:**
```bash
TEAM_ID="<team-uuid>"

# Promjena naziva
curl -X PUT http://localhost:8123/api/teams/$TEAM_ID \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Team Alpha 1"}'

# Promjena smjene
curl -X PUT http://localhost:8123/api/teams/$TEAM_ID \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"shift": "B"}'

# Promjena radnika
curl -X PUT http://localhost:8123/api/teams/$TEAM_ID \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"worker2_id": "<new-worker-uuid>"}'
```

---

## 🗑️ **BRISANJE (DEAKTIVIRANJE) TIMA**

### **Koraci:**

1. **Na Teams stranici, kliknite "Obriši" pored tima**

2. **Potvrdite brisanje**

### **Napomena:**
- ⚠️ **NE MOŽETE** obrisati tim koji ima aktivne zadatke!
- Tim se **deaktivira**, ne briše potpuno iz baze
- Deaktivirani timovi se ne prikazuju u listi aktivnih timova

### **Zaštita:**
```
❌ "Cannot delete team with 3 active tasks. Complete or reassign tasks first."
```

Prije brisanja tima, svi zadaci moraju biti:
- Završeni (`done`)
- Otkazani (`cancelled`)
- Ili reassigned drugom timu/radniku

### **Primjer putem API:**
```bash
TEAM_ID="<team-uuid>"

curl -X DELETE http://localhost:8123/api/teams/$TEAM_ID \
  -H "Authorization: Bearer $TOKEN"
```

**Response:** 204 No Content (uspješno)

---

## 📊 **PREGLED PERFORMANSI TIMA**

### **Koraci:**

1. **Kliknite "Performanse" pored tima**

2. **Vidjet ćete:**
   - Ukupno zadataka
   - Završenih zadataka
   - Zadataka u toku
   - Stopu završetka (%)
   - Ukupno skeniranja
   - Prosječnu brzinu (stavki/sat)

### **Primjer putem API:**
```bash
TEAM_ID="<team-uuid>"

curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8123/api/teams/$TEAM_ID/performance"
```

**Response:**
```json
{
  "team_id": "uuid",
  "team_name": "Team A1",
  "total_tasks": 15,
  "completed_tasks": 12,
  "in_progress_tasks": 3,
  "completion_rate": 0.8,
  "total_scans": 234,
  "average_speed_per_hour": 45.5
}
```

---

## 🔄 **SCHEDULER - TIMSKO DODJELJIVANJE**

### **Kako radi:**

Kada kreirate zadužnicu u Scheduleru:

1. **Pojedinačno dodjeljivanje:**
   - Odaberete jednog radnika
   - Kreira se 1 zadužnica
   - Ako radnik pripada timu, automatski se postavlja `team_id`

2. **Timsko dodjeljivanje:**
   - Odaberete tim
   - Kreira se 2 zadužnice (za oba člana tima)
   - Oba radnika vide dokument u PWA

### **UI:**
```
[ Pojedinačno ] [ Tim ]

Kada je "Tim" odabran:
  Tim: [Team A1 (Sabin & Gezim) - Smjena A ▼]
```

### **Backend logika:**
- Pri kreiranju zadužnice, sistem automatski traži da li radnik pripada timu
- Ako da, postavlja `team_id` u zadužnicu
- Omogućava team-based analitiku i progress tracking

---

## 🎯 **PRIMJERI KORIŠTENJA**

### **Scenario 1: Kreiranje tima za Smjenu B**

**Situacija:**  
Dobili ste 2 nova radnika koji će raditi podne smjene (12:00-19:00)

**Koraci:**
1. Kreirajte 2 korisnika sa rolom `MAGACIONER`
2. Otvorite http://localhost:5130/teams
3. Kliknite "Dodaj Tim"
4. Unesite:
   - Naziv: "Team B1"
   - Radnik 1: [Novi radnik 1]
   - Radnik 2: [Novi radnik 2]
   - Smjena: B
5. Kreiraj

**Rezultat:**
- Tim B1 kreiran
- Prikazuje se u Teams tablici
- Dodjeljivanje u Scheduleru sada pokazuje i Team B1

---

### **Scenario 2: Zamjena člana tima**

**Situacija:**  
Jedan radnik je otišao na godišnji, treba ga zamijenit

**Koraci:**
1. Otvorite Teams stranicu
2. Kliknite "Uredi" pored tima
3. Odaberite novog radnika za Radnik 1 ili Radnik 2
4. Ažuriraj

**Rezultat:**
- Tim sada ima novog člana
- Stari član može biti dodijeljen drugom timu
- Aktiv ni zadaci ostaju sa starim team_id (historija)

---

### **Scenario 3: Deaktiviranje tima (kraj sezone)**

**Situacija:**  
Sezonski radnici završili, tim više nije potreban

**Koraci:**
1. Provjerite da tim nema aktivnih zadataka
2. Kliknite "Obriši"
3. Potvrdite

**Rezultat:**
- Tim se deaktivira (`active = false`)
- Ne prikazuje se u listama aktivnih timova
- Historijski podaci ostaju u bazi

---

## 🛠️ **API REFERENCE**

### **Endpoints:**

| Method | Endpoint | Opis | Dozvole |
|--------|----------|------|---------|
| GET | `/api/teams` | Lista svih timova | ADMIN, SEF, MENADZER |
| GET | `/api/teams/{id}` | Detalji tima | ADMIN, SEF, MENADZER |
| GET | `/api/teams/{id}/performance` | Performanse tima | ADMIN, SEF, MENADZER |
| POST | `/api/teams` | Kreiraj tim | ADMIN, SEF, MENADZER |
| PUT | `/api/teams/{id}` | Ažuriraj tim | ADMIN, SEF, MENADZER |
| DELETE | `/api/teams/{id}` | Deaktiviraj tim | ADMIN, SEF |

### **Request Body (Create):**
```typescript
{
  name: string;           // "Team A1"
  worker1_id: string;     // UUID
  worker2_id: string;     // UUID
  shift: "A" | "B";       // Smjena
}
```

### **Request Body (Update):**
```typescript
{
  name?: string;          // Opciono
  worker1_id?: string;    // Opciono
  worker2_id?: string;    // Opciono
  shift?: "A" | "B";      // Opciono
  active?: boolean;       // Opciono
}
```

---

## 💻 **FRONTEND KOMPONENTE**

### **TeamsPage.tsx** (Admin)

**Glavne funkcionalnosti:**
- Prikaz svih timova
- Modal za kreiranje/uređivanje
- Popconfirm za brisanje
- Real-time refresh (svakih 30s)

**Key Hooks:**
```typescript
const { data: teams } = useQuery(['teams'], getTeams);
const createMutation = useMutation({ mutationFn: createTeam });
const updateMutation = useMutation({ mutationFn: updateTeam });
const deleteMutation = useMutation({ mutationFn: deleteTeam });
```

**Modal Forma:**
- Input za naziv
- 2x Select za radnike (sa search funkcijom)
- Select za smjenu
- Submit dugme

---

### **SchedulerPage.tsx** (Admin)

**Team Assignment:**
```typescript
<Radio.Group value={assignmentMode}>
  <Radio.Button value="individual">Pojedinačno</Radio.Button>
  <Radio.Button value="team">Tim</Radio.Button>
</Radio.Group>

{assignmentMode === 'team' && (
  <Form.Item label="Tim" name="teamId">
    <Select options={TEAMS} />
  </Form.Item>
)}
```

---

## 🗄️ **DATABASE SCHEMA**

### **Team Table:**
```sql
CREATE TABLE team (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) UNIQUE NOT NULL,
    worker1_id UUID NOT NULL REFERENCES users(id),
    worker2_id UUID NOT NULL REFERENCES users(id),
    shift VARCHAR(1) NOT NULL CHECK (shift IN ('A', 'B')),
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_team_worker1 ON team(worker1_id);
CREATE INDEX idx_team_worker2 ON team(worker2_id);
CREATE INDEX idx_team_active ON team(active);
```

### **Zaduznica Table (Updated):**
```sql
ALTER TABLE zaduznica 
ADD COLUMN team_id UUID REFERENCES team(id);

CREATE INDEX idx_zaduznica_team ON zaduznica(team_id);
```

---

## 🔄 **AUTOMATSKA INTEGRACIJA**

### **Kada se kreira zadužnica:**

**Backend automatski:**
1. Traži tim kojem radnik pripada
2. Postavlja `team_id` u zadužnicu
3. Omogućava team-based analytics

**Kod:**
```python
# U zaduznice.py - create_zaduznice()
team_stmt = select(Team.id).where(
    ((Team.worker1_id == assignment.magacioner_id) | 
     (Team.worker2_id == assignment.magacioner_id))
    & (Team.active == True)
)
team_id = (await session.execute(team_stmt)).scalar_one_or_none()

zaduznica = Zaduznica(
    # ... ostala polja ...
    team_id=team_id,  # Automatski postavljen!
)
```

---

## ✅ **VALIDACIJE I PRAVILA**

### **Pri kreiranju tima:**
1. ✅ Naziv mora biti jedinstven
2. ✅ Oba radnika moraju postojati
3. ✅ Oba radnika moraju imati rolu `MAGACIONER`
4. ✅ Radnici ne smiju biti u drugom aktivnom timu
5. ✅ Smjena mora biti 'A' ili 'B'

### **Pri uređivanju tima:**
1. ✅ Novi naziv mora biti jedinstven (ako se mijenja)
2. ✅ Novi radnici moraju biti validni magacioneri
3. ✅ Novi radnici ne smiju biti u drugom timu

### **Pri brisanju tima:**
1. ✅ Tim ne smije imati aktivne zadatke
2. ✅ Samo ADMIN i SEF mogu brisati

**Aktivni zadaci = zadaci sa statusom:**
- `assigned`
- `in_progress`

**Neaktivni zadaci** (`done`, `cancelled`) **ne blokiraju brisanje**

---

## 📊 **TEAM PERFORMANCE METRICS**

### **Metrike koje se prate:**

| Metrika | Opis |
|---------|------|
| Total Tasks | Ukupno dodijeljenih zadataka timu |
| Completed Tasks | Završeni zadaci |
| In Progress | Zadaci u toku |
| Completion Rate | Stopa završetka (0.0 - 1.0) |
| Total Scans | Ukupno barcode skeniranja oba člana |
| Avg Speed | Prosječna brzina (stavki po satu) |

### **Kako se računaju:**

**Total Tasks:**
```sql
SELECT COUNT(*) FROM zaduznica WHERE team_id = <team_id>
```

**Completed Tasks:**
```sql
SELECT COUNT(*) FROM zaduznica 
WHERE team_id = <team_id> AND status = 'done'
```

**Completion Rate:**
```
completed_tasks / total_tasks
```

**Total Scans:**
```sql
SELECT COUNT(*) FROM scanlog 
WHERE user_id IN (worker1_id, worker2_id)
```

---

## 🎨 **UI FEATURES**

### **Teams Table Columns:**
1. **Tim** - Naziv sa ikonom
2. **Članovi** - Imena oba radnika (vertikalno)
3. **Smjena** - Tag (plavi za A, zeleni za B)
4. **Progres** - Progress bar sa brojem zadataka
5. **Status** - Badge (🟢 Radi, ⚪ Neaktivan)
6. **Akcije** - Performanse, Uredi, Obriši

### **Shift Status Header:**
- Aktivna smjena
- Status (Radi / Pauza / Završeno)
- Odbrojavanje (HH:MM:SS)

### **KPI Cards:**
- Ukupno zadataka danas
- Završenih zadataka
- Aktivni timovi
- Prosječna završenost (%)

---

## 🧪 **TESTIRANJE**

### **Test 1: Kreiranje tima**
```bash
# 1. Login kao admin
TOKEN=$(curl -s -X POST http://localhost:8123/api/auth/device-token \
  -H "Content-Type: application/json" \
  -d '{"device_id": "tv-dashboard-001", "device_secret": "service-local"}' \
  | jq -r '.access_token')

# 2. Kreiraj tim (ako imate slobodne radnike)
curl -X POST http://localhost:8123/api/teams \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Team B1",
    "worker1_id": "<uuid1>",
    "worker2_id": "<uuid2>",
    "shift": "B"
  }' | jq .

# 3. Verifikuj u bazi
docker-compose exec db psql -U wmsops -d wmsops_local -c \
  "SELECT name, shift FROM team WHERE active = true;"
```

---

### **Test 2: Uređivanje tima**
```bash
TEAM_ID="<uuid>"

# Promijeni naziv
curl -X PUT http://localhost:8123/api/teams/$TEAM_ID \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Team Alpha 1"}' | jq '{name, shift}'

# Verifikuj
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8123/api/teams/$TEAM_ID" | jq '.name'
```

---

### **Test 3: Pokušaj brisanja tima sa aktivnim zadacima**
```bash
TEAM_ID="<uuid>"

# Assign task to team first
# ... (use scheduler)

# Try to delete
curl -X DELETE http://localhost:8123/api/teams/$TEAM_ID \
  -H "Authorization: Bearer $TOKEN"

# Expected: HTTP 400 with error message
```

---

## 📚 **BEST PRACTICES**

### **1. Imenovanje timova:**
- ✅ Koristite konzistentnu šemu: "Team A1", "Team A2", "Team B1"
- ✅ Uključite smjenu u naziv za lakše prepoznavanje
- ❌ Izbjegavajte generičke nazive: "Tim 1", "Grupa A"

### **2. Dodjeljivanje radnika:**
- ✅ Timove kreirajte sa radnicima koji rade zajedno
- ✅ Koristite radnike iste smjene
- ✅ Uravnotežite opterećenje između timova

### **3. Smjene:**
- **Smjena A:** 08:00-15:00 (pauza 10:00-10:30)
- **Smjena B:** 12:00-19:00 (pauza 14:00-14:30)
- **Overlap:** 12:00-15:00 (oba tima aktivna)

### **4. Lifecycle timova:**
```
Kreiran → Aktivan → Zadaci dodijeljeni → Završeni → Deaktiviran
```

---

## 🚨 **TROUBLESHOOTING**

### **Problem: Ne mogu kreirati tim**
**Greška:** "One or both workers are already in an active team"

**Rješenje:**
1. Provjerite koji timovi su aktivni
2. Deaktivirajte stari tim ili odaberite druge radnike

---

### **Problem: Ne mogu obrisati tim**
**Greška:** "Cannot delete team with X active tasks"

**Rješenje:**
1. Provjerite aktivne zadatke:
   ```sql
   SELECT z.id, z.status FROM zaduznica z
   WHERE z.team_id = '<team-uuid>'
   AND z.status IN ('assigned', 'in_progress');
   ```
2. Završite ili reassign-ujte zadatke
3. Pokušajte ponovo

---

### **Problem: Radnik ne vidi tim u PWA**
**Mogući uzroci:**
- Radnik nije član nijednog aktivnog tima
- Tim je deaktiviran

**Rješenje:**
```sql
-- Provjerite team membership
SELECT t.name, t.shift, t.active
FROM team t
WHERE t.worker1_id = '<user-uuid>' 
   OR t.worker2_id = '<user-uuid>';
```

---

## 📈 **STATISTIKE I ANALITIKA**

### **Team Dashboard:**
```
GET /api/dashboard/live?scope=day
```

**Response sadrži:**
- `total_tasks_today` - Ukupno zadataka danas
- `completed_tasks` - Završeni zadaci
- `active_teams` - Broj aktivnih timova
- `team_progress` - Niz sa progress svakog tima:
  ```json
  {
    "team": "Team A1",
    "team_id": "uuid",
    "members": ["Sabin", "Gezim"],
    "completion": 0.75,
    "shift": "A",
    "tasks_total": 10,
    "tasks_completed": 7
  }
  ```

---

## 🎯 **KLJUČNE PREDNOSTI TEAM MANAGEMENTA**

### **Za menadžere:**
1. ✅ Centralizovano upravljanje parovima radnika
2. ✅ Brza dodjela zadataka cijelom timu
3. ✅ Team-based analytics
4. ✅ Shift-based organizacija

### **Za radnike:**
5. ✅ Vide ko je njihov partner
6. ✅ Dijele napredak na zadacima
7. ✅ Bolja koordinacija

### **Za sistem:**
8. ✅ Konzistentni podaci
9. ✅ Automatsko postavljanje team_id
10. ✅ Lako proširenje (dodavanje novih timova)

---

## 🎊 **TEAM MANAGEMENT JE KOMPLETAN!**

**Sve funkcionalnosti implementirane:**
- ✅ CRUD operacije (Create, Read, Update, Delete)
- ✅ Validacije i zaštite
- ✅ UI sa modalima i formama
- ✅ API endpoints
- ✅ Automatska integracija u Scheduler
- ✅ Performance tracking
- ✅ Real-time updates

**Možete odmah početi koristiti:**
http://localhost:5130/teams

**Uživajte!** 🚀✨

