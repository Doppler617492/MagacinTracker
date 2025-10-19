# 📋 Scheduler Team Assignment Feature

## ✅ **IMPLEMENTACIJA KOMPLETNA**

Scheduler sada podržava **dvostruko dodjeljivanje**: pojedinačno i po timu!

---

## 🎯 **ŠTA JE DODANO**

### **Frontend (Scheduler Page)**
1. ✅ Radio toggle: "Pojedinačno" / "Tim"
2. ✅ Select za magacionere (pojedinačno)
3. ✅ Select za timove (timsko)
   - Prikazuje: "Team A1 (Sabin & Gezim) - Smjena A"
4. ✅ Logika dodjeljivanja:
   - **Pojedinačno:** Kreira 1 zadužnicu za odabranog radnika
   - **Tim:** Kreira 2 zadužnice za oba člana tima

### **Backend (Zaduznice Service)**
1. ✅ Automatsko pronalaženje `team_id` za radnika
2. ✅ Postavljanje `team_id` u zadužnicu prilikom kreiranja
3. ✅ Cache za `team_id` unutar jednog requesta (optimizacija)

---

## 🔄 **KAKO RADI**

### **Scenario 1: Pojedinačno dodjeljivanje**
1. Admin otvori Scheduler
2. Klikne "Ručno dodeli"
3. Ostavi "Pojedinačno" selektovano
4. Odabere magacionera iz liste
5. Odabere prioritet i rok
6. Klikne "Kreiraj zadužnicu"

**Rezultat:**
- Kreira se 1 zadužnica za odabranog radnika
- Ako radnik pripada timu, automatski se postavlja `team_id`

---

### **Scenario 2: Timsko dodjeljivanje**
1. Admin otvori Scheduler
2. Klikne "Ručno dodeli"
3. Prebaci na "Tim"
4. Odabere tim iz liste (npr. "Team A1 (Sabin & Gezim) - Smjena A")
5. Odabere prioritet i rok
6. Klikne "Kreiraj zadužnicu"

**Rezultat:**
- Kreira se 2 zadužnice:
  - Zadužnica 1 → worker1 (Sabin), sa `team_id`
  - Zadužnica 2 → worker2 (Gezim), sa `team_id`
- Oba radnika vide isti dokument u svojim task listama
- Obojica mogu skenirati i raditi zajedno

---

## 🛠️ **TEHNIČKA IMPLEMENTACIJA**

### **Frontend Izmjene**

#### **SchedulerPage.tsx**
```typescript
// Dodati imports
import { Radio } from "antd";
import { getTeams } from "../api";

// State za mode
const [assignmentMode, setAssignmentMode] = useState<'individual' | 'team'>('individual');

// Query za teams
const { data: teams } = useQuery<Team[]>({
  queryKey: ["teams"],
  queryFn: getTeams,
  staleTime: 30000,
});

// Lista timova
const TEAMS = useMemo(() => {
  if (!teams) return [];
  return teams.map((team) => ({
    value: team.id,
    label: `${team.name} (${team.worker1.first_name} & ${team.worker2.first_name}) - Smjena ${team.shift}`,
    team: team
  }));
}, [teams]);

// Forma sa toggle
<Radio.Group value={assignmentMode} onChange={(e) => setAssignmentMode(e.target.value)}>
  <Radio.Button value="individual">Pojedinačno</Radio.Button>
  <Radio.Button value="team">Tim</Radio.Button>
</Radio.Group>

{assignmentMode === 'individual' ? (
  <Form.Item label="Magacioner" name="magacionerId">
    <Select options={MAGACIONERI} />
  </Form.Item>
) : (
  <Form.Item label="Tim" name="teamId">
    <Select options={TEAMS} />
  </Form.Item>
)}
```

#### **handleOverrideAssignment logic**
```typescript
if (assignmentMode === 'individual') {
  assignments = [{
    magacioner_id: values.magacionerId,
    priority: values.priority,
    due_at: dueAtIso,
    items
  }];
} else {
  const selectedTeam = TEAMS.find(t => t.value === values.teamId)?.team;
  assignments = [
    {
      magacioner_id: selectedTeam.worker1.id,
      priority: values.priority,
      due_at: dueAtIso,
      items
    },
    {
      magacioner_id: selectedTeam.worker2.id,
      priority: values.priority,
      due_at: dueAtIso,
      items
    }
  ];
}
```

---

### **Backend Izmjene**

#### **zaduznice.py**
```python
from ..models import Team

# U create_zaduznice funkciji:
team_id_cache: dict[UUID, UUID | None] = {}

for assignment in payload.assignments:
    # Find team for this worker
    if assignment.magacioner_id not in team_id_cache:
        team_stmt = select(Team.id).where(
            ((Team.worker1_id == assignment.magacioner_id) | 
             (Team.worker2_id == assignment.magacioner_id))
            & (Team.active == True)
        )
        team_result = await session.execute(team_stmt)
        team_id = team_result.scalar_one_or_none()
        team_id_cache[assignment.magacioner_id] = team_id
    else:
        team_id = team_id_cache[assignment.magacioner_id]

    zaduznica = Zaduznica(
        id=zaduznica_id,
        trebovanje_id=trebovanje.id,
        magacioner_id=assignment.magacioner_id,
        team_id=team_id,  # ⭐ Automatski postavljen
        prioritet=assignment.priority,
        rok=assignment.due_at,
        status=ZaduznicaStatus.assigned,
    )
```

---

## 📊 **PRIMJERI**

### **Primjer 1: Dodjeljivanje po timu**
**Input:**
- Dokument: DOK-001
- Tim: Team A1 (Sabin & Gezim)
- Prioritet: Normal
- Rok: 4h

**Output (baza):**
```sql
-- Zadužnica 1
INSERT INTO zaduznica (id, trebovanje_id, magacioner_id, team_id, prioritet, rok, status)
VALUES (uuid1, 'dok-001', 'sabin-id', 'team-a1-id', 'normal', '4h', 'assigned');

-- Zadužnica 2
INSERT INTO zaduznica (id, trebovanje_id, magacioner_id, team_id, prioritet, rok, status)
VALUES (uuid2, 'dok-001', 'gezim-id', 'team-a1-id', 'normal', '4h', 'assigned');
```

**PWA prikaz:**
- Sabin vidi: "Trebovanje DOK-001" + team banner "Team A1 | Partner: Gezim"
- Gezim vidi: "Trebovanje DOK-001" + team banner "Team A1 | Partner: Sabin"

---

### **Primjer 2: Pojedinačno dodjeljivanje (sa team_id)**
**Input:**
- Dokument: DOK-002
- Magacioner: Sabin (pripada Team A1)
- Prioritet: High
- Rok: 2h

**Output (baza):**
```sql
INSERT INTO zaduznica (id, trebovanje_id, magacioner_id, team_id, prioritet, rok, status)
VALUES (uuid3, 'dok-002', 'sabin-id', 'team-a1-id', 'high', '2h', 'assigned');
```

**PWA prikaz:**
- Sabin vidi: "Trebovanje DOK-002" + team banner
- Gezim NE vidi ovaj dokument (nije mu dodijeljen)

---

## ✅ **TESTIRANJE**

### **Test 1: Timsko dodjeljivanje**
1. Otvorite: http://localhost:5130/scheduler
2. Selektujte dokument
3. Kliknite "Ručno dodeli"
4. Prebacite na "Tim"
5. Odaberite "Team A1 (Sabin & Gezim) - Smjena A"
6. Kliknite "Kreiraj zadužnicu"

**Očekivano:**
- ✅ Poruka: "Dodjeljivanje timu: Team A1 (Sabin & Gezim)"
- ✅ 2 zadužnice kreirane
- ✅ Oba radnika vide dokument u PWA

**Verifikacija:**
```bash
docker-compose exec -T db psql -U wmsops -d wmsops_local -c \
  "SELECT z.id, u.first_name, t.name as team 
   FROM zaduznica z 
   JOIN users u ON z.magacioner_id = u.id 
   LEFT JOIN team t ON z.team_id = t.id 
   ORDER BY z.created_at DESC LIMIT 5;"
```

---

### **Test 2: Pojedinačno dodjeljivanje**
1. Otvorite: http://localhost:5130/scheduler
2. Selektujte dokument
3. Kliknite "Ručno dodeli"
4. Ostanite na "Pojedinačno"
5. Odaberite Sabin Maku
6. Kliknite "Kreiraj zadužnicu"

**Očekivano:**
- ✅ 1 zadužnica kreirana za Sabin
- ✅ `team_id` automatski postavljen (ako Sabin pripada timu)
- ✅ Samo Sabin vidi dokument u PWA

---

### **Test 3: team_id automatski postavljen**
```bash
# Kreirajte zadužnicu za Sabin (pojedinačno)
# Provjerite da li je team_id postavljen

docker-compose exec -T db psql -U wmsops -d wmsops_local -c \
  "SELECT z.id, u.first_name, z.team_id, t.name 
   FROM zaduznica z 
   JOIN users u ON z.magacioner_id = u.id 
   LEFT JOIN team t ON z.team_id = t.id 
   WHERE u.first_name = 'Sabin' 
   ORDER BY z.created_at DESC LIMIT 1;"
```

**Očekivano:**
```
        id         | first_name | team_id | name
-------------------+------------+---------+--------
 <uuid>            | Sabin      | <uuid>  | Team A1
```

---

## 🎯 **KLJUČNE PREDNOSTI**

### **Za menadžere:**
1. ✅ Brzo dodjeljivanje cijelom timu (1 klik umjesto 2)
2. ✅ Automatsko postavljanje team_id (ne može se zaboraviti)
3. ✅ Fleksibilnost: izbor između tim/pojedinačno

### **Za radnike:**
4. ✅ Vide ko je njihov partner
5. ✅ Rade zajedno na istom dokumentu
6. ✅ Zajednički progres vidljiv u TV dashboardu

### **Za sistem:**
7. ✅ Konzistentnost podataka (team_id uvijek tačan)
8. ✅ Performance optimizacija (cache za team lookup)
9. ✅ Lako proširenje (dodavanje novih timova)

---

## 🚀 **DEPLOYMENT STATUS**

### **Frontend:**
- ✅ SchedulerPage.tsx - Updated
- ✅ api.js - getTeams() added
- ✅ api.ts - Team interfaces added
- ✅ Build successful

### **Backend:**
- ✅ zaduznice.py - Auto team_id logic
- ✅ Team model imported
- ✅ SQL query optimized
- ✅ Build successful

### **Deployed:**
- ✅ admin service restarted
- ✅ task-service restarted
- ✅ All services running

---

## 📚 **DOKUMENTACIJA**

### **API Endpoints (postojeći):**
```
POST /api/zaduznice
{
  "trebovanje_id": "<uuid>",
  "assignments": [
    {
      "magacioner_id": "<uuid>",
      "priority": "normal",
      "due_at": "2025-10-16T12:00:00Z",
      "items": [...]
    }
  ]
}
```

**Nova logika:**
- Ako se pošalje 1 assignment → 1 zadužnica (pojedinačno)
- Ako se pošalje 2 assignmenta → 2 zadužnice (tim)
- Backend automatski popunjava `team_id` za oba slučaja

### **Team Query:**
```
GET /api/teams
```

**Response:**
```json
[
  {
    "id": "<uuid>",
    "name": "Team A1",
    "shift": "A",
    "active": true,
    "worker1": {
      "id": "<uuid>",
      "first_name": "Sabin",
      "last_name": "Maku",
      "email": "sabin.maku@cungu.com"
    },
    "worker2": {
      "id": "<uuid>",
      "first_name": "Gezim",
      "last_name": "Maku",
      "email": "gezim.maku@cungu.com"
    },
    "created_at": "2025-10-16T..."
  }
]
```

---

## ✅ **FINAL CHECKLIST**

- [x] Frontend toggle (Pojedinačno / Tim)
- [x] Select za magacionere
- [x] Select za timove
- [x] Logika kreiranja 2 zadužnice za tim
- [x] Backend auto team_id lookup
- [x] Cache optimizacija
- [x] Build uspješan (frontend + backend)
- [x] Servisi deployovani
- [x] Dokumentacija kreirana

---

## 🎊 **IMPLEMENTACIJA ZAVRŠENA!**

Scheduler sada podržava **i pojedinačno i timsko dodjeljivanje**!

**Možete testirati odmah na:**
http://localhost:5130/scheduler

**Uživajte!** 🚀✨

