# Sprint WMS Phase 1 - Implementation Plan
## Manhattan-Style UI & Stabilization

**Start Date:** October 19, 2025  
**Target Completion:** 7 days  
**Design Reference:** Manhattan Associates Active WMS  
**Language:** Serbian (Srpski)

---

## 🎯 Executive Summary

Transform Magacin Track WMS into an enterprise-grade system following Manhattan Active WMS UX/UI patterns:
- ✅ Clarity-first design with white backgrounds
- ✅ Team-based operations (2-person teams)
- ✅ Partial completion tracking with reasons
- ✅ Real catalog data (no mocks)
- ✅ Left rail navigation (Manhattan IA)
- ✅ Real-time sync < 2s latency
- ✅ Zebra Android device compatibility

---

## 📋 Implementation Checklist

### Phase 1.1: Backend Enhancements (Days 1-2)

#### 1.1.1 Partial Completion System
- [ ] Add `količina_pronađena` field to `trebovanje_stavka`
- [ ] Add `razlog` field (enum: nema_na_stanju, oštećeno, nije_pronađeno, drugo)
- [ ] Add `razlog_tekst` for custom reasons
- [ ] Create migration for new fields
- [ ] Update `TrebovanjeStavka` model
- [ ] Add `"Završeno (djelimično)"` status
- [ ] Create endpoint: `POST /api/worker/tasks/{id}/partial-complete`
- [ ] Calculate `% ispunjenja` (completion percentage)

**Files to modify:**
- `backend/services/task_service/app/models/trebovanje.py`
- `backend/services/task_service/app/models/enums.py`
- `backend/services/task_service/app/routers/worker_picking.py`
- `backend/services/task_service/alembic/versions/` (new migration)

#### 1.1.2 Team Real-Time Sync Enhancement
- [ ] Enhance Redis Pub/Sub for team-specific events
- [ ] Add `team_task_updated` event
- [ ] Implement WebSocket broadcast to team members
- [ ] Add audit trail for team member actions
- [ ] Track which team member updated what

**Files to modify:**
- `backend/services/realtime_worker/app/main.py`
- `backend/services/task_service/app/routers/teams.py`
- `backend/services/task_service/app/models/audit.py`

#### 1.1.3 Catalog Population
- [ ] Create Pantheon throttle service (5 req/s limit)
- [ ] Implement ETag/If-Modified-Since caching
- [ ] Add Admin JSON import endpoint (temporary)
- [ ] Create `needs_barcode` badge logic
- [ ] Add catalog search endpoint with filters

**Files to modify:**
- `backend/services/catalog_service/app/services/pantheon_catalog_sync.py`
- `backend/services/catalog_service/app/routers/catalog.py`
- `backend/app_common/pantheon_client.py`

---

### Phase 1.2: PWA Manhattan-Style Redesign (Days 3-4)

#### 1.2.1 Serbian Language Constants
- [ ] Create `frontend/pwa/src/i18n/sr.ts` (comprehensive)
- [ ] All UI strings in Serbian
- [ ] Date/time formatters for Serbian locale

**Serbian UI Labels:**
```typescript
{
  navigation: {
    zadaci: "Задаци",
    pretragaArtikla: "Претрага артикла",
    popisMagacina: "Попис магацина",
    podesavanja: "Подешавања",
    profil: "Профил"
  },
  task: {
    trazeno: "Тражено",
    pronadjeno: "Пронађено",
    zavrsenoDjelimicno: "Завршено (дјелимично)",
    razlog: "Разлог"
  },
  reasons: {
    nemaNaStanju: "Нема на стању",
    osteceno: "Оштећено",
    nijePronađeno: "Није пронађено",
    drugo: "Друго"
  }
}
```

#### 1.2.2 PWA Header Component (Manhattan-style)
- [ ] Create `Header.tsx` with:
  - Profile avatar (initials)
  - Ime i uloga (Name & role)
  - Smjena A/B display
  - Pause time info (10:00-10:30 or 14:00-14:30)
  - Online/Offline badge
  - Logout button
- [ ] White background, high contrast
- [ ] Sticky header behavior

**Component structure:**
```tsx
<Header>
  <Left>
    <Avatar>{user.initials}</Avatar>
    <UserInfo>
      <Name>{user.fullName}</Name>
      <Role>{user.role}</Role>
    </UserInfo>
  </Left>
  <Center>
    <ShiftBadge shift={team.shift}>
      Smjena {team.shift}
      <PauseInfo>Pauza: {pauseTime}</PauseInfo>
    </ShiftBadge>
  </Center>
  <Right>
    <OnlineIndicator />
    <LogoutButton />
  </Right>
</Header>
```

#### 1.2.3 PWA Home Page (Manhattan grid)
- [ ] White background design
- [ ] Grid layout with large tap targets (min 48px)
- [ ] Monochrome icons
- [ ] Cards: Zadaci, Pretraga, Popis, Podešavanja, Profil
- [ ] Task filter: "Samo moji / Tim"
- [ ] Responsive grid (2 columns mobile, 3 tablet)

**Card structure:**
```tsx
<HomeGrid>
  <Card icon={TaskIcon} label="Zadаци" badge={taskCount} />
  <Card icon={SearchIcon} label="Претрага артикла" />
  <Card icon={InventoryIcon} label="Попис магацина" />
  <Card icon={SettingsIcon} label="Подешавања" />
  <Card icon={ProfileIcon} label="Профил" />
</HomeGrid>
```

#### 1.2.4 Task Detail Page (Manhattan-style)
- [ ] Large quantity stepper (+/- buttons, direct input)
- [ ] "Markiraj preostalo = 0 + razlog" button
- [ ] Reason dropdown modal
- [ ] "Dovrši zadatak" button (allows partial)
- [ ] Show team member activity
- [ ] Real-time updates

**Layout:**
```tsx
<TaskDetail>
  <ItemHeader>
    <Code>{item.sifra}</Code>
    <Name>{item.naziv}</Name>
  </ItemHeader>
  
  <QuantitySection>
    <Label>Тражено: {item.trazeno}</Label>
    <Stepper>
      <Button size="large">-</Button>
      <Input value={pronađeno} />
      <Button size="large">+</Button>
    </Stepper>
  </QuantitySection>
  
  <PartialActions>
    <Button>Маркирај преостало = 0</Button>
  </PartialActions>
  
  <ActionBar>
    <Button type="primary">Доврши задатак</Button>
  </ActionBar>
</TaskDetail>
```

---

### Phase 1.3: Admin Manhattan-Style Redesign (Days 5-6)

#### 1.3.1 Left Rail Navigation
- [ ] Create `LeftNav.tsx` component
- [ ] Sections with icons:
  - **Operacije:** Trebovanja, Zadužnice, Import
  - **Katalog:** Artikli, Barkodovi
  - **Analitika:** KPI, Izveštaji, AI Asistent
  - **Uživo:** TV, Live Ops
  - **Administracija:** Korisnici i uloge, Podešavanja
- [ ] Collapsible sections
- [ ] Active state highlighting
- [ ] Logo at top

**Structure:**
```tsx
<LeftNav>
  <Logo />
  
  <Section title="Operacije">
    <NavItem icon={<DocumentIcon />} to="/trebovanja">Trebovanja</NavItem>
    <NavItem icon={<TaskIcon />} to="/zaduznice">Zadužnice</NavItem>
    <NavItem icon={<UploadIcon />} to="/import">Import</NavItem>
  </Section>
  
  <Section title="Katalog">
    <NavItem icon={<BoxIcon />} to="/artikli">Artikli</NavItem>
    <NavItem icon={<BarcodeIcon />} to="/barkodovi">Barkodovi</NavItem>
  </Section>
  
  {/* ... more sections */}
</LeftNav>
```

#### 1.3.2 Admin Top Bar
- [ ] Logo (left)
- [ ] Global search (center)
- [ ] Profile + logout (right)
- [ ] Breadcrumb navigation
- [ ] Sticky page titles

#### 1.3.3 Trebovanja/Zadužnice Tables
- [ ] Add "% ispunjenja" column
- [ ] Show "traženo vs. pronađeno" columns
- [ ] Reason chips display
- [ ] "Završeno (djelimično)" status badge
- [ ] Sticky table headers
- [ ] Server-side filtering
- [ ] CSV export button

**Table columns:**
```tsx
[
  { title: "Dok. broj", dataIndex: "dokument_broj" },
  { title: "Datum", dataIndex: "datum" },
  { title: "Status", dataIndex: "status", render: StatusBadge },
  { title: "Traženo", dataIndex: "ukupno_trazeno" },
  { title: "Pronađeno", dataIndex: "ukupno_pronadjeno" },
  { title: "% ispunjenja", dataIndex: "procenat_ispunjenja", render: PercentBar },
  { title: "Razlozi", dataIndex: "razlozi", render: ReasonChips },
  { title: "Akcije", render: ActionMenu }
]
```

---

### Phase 1.4: TV Dashboard Real Data (Day 6)

#### 1.4.1 Remove Mock Data
- [ ] Delete all demo/test cards
- [ ] Connect to real APIs via gateway
- [ ] Implement live Socket.IO updates

#### 1.4.2 Real-Time Metrics
- [ ] Today's completions
- [ ] Shift-based completions (A/B)
- [ ] Partial completion ratio
- [ ] Top team performance
- [ ] Top 3 reasons for partial completion
- [ ] Delta < 2s refresh

**Dashboard layout:**
```tsx
<TVDashboard>
  <MetricsRow>
    <KPICard title="Danas završeno" value={todayCompleted} />
    <KPICard title="Smjena A" value={shiftACompleted} />
    <KPICard title="Smjena B" value={shiftBCompleted} />
    <KPICard title="Djelimično %" value={partialRatio} trend />
  </MetricsRow>
  
  <TeamsRow>
    <TopTeam team={topTeam} />
    <TopReasons reasons={top3Reasons} />
  </TeamsRow>
  
  <LiveFeed events={liveEvents} />
</TVDashboard>
```

---

### Phase 1.5: Documentation (Day 7)

#### 1.5.1 Test Report Update
- [ ] Screenshot: Import document
- [ ] Screenshot: Assign to team
- [ ] Screenshot: PWA task detail
- [ ] Screenshot: Partial completion with reason
- [ ] Screenshot: TV live update
- [ ] Screenshot: Admin table with % ispunjenja

#### 1.5.2 README Update
- [ ] Real team/shift examples
- [ ] Local demo instructions
- [ ] Manhattan UI patterns documented
- [ ] Serbian language notes
- [ ] Zebra device compatibility notes

---

## 🎨 Manhattan Active WMS Design Tokens

### Typography
```css
--font-family-primary: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
--font-size-h1: 32px;
--font-size-h2: 24px;
--font-size-h3: 20px;
--font-size-body: 16px;
--font-size-small: 14px;
--font-weight-bold: 600;
--font-weight-medium: 500;
--font-weight-regular: 400;
--line-height-tight: 1.2;
--line-height-normal: 1.5;
```

### Colors (Clarity-First)
```css
--color-bg-primary: #FFFFFF;
--color-bg-secondary: #F8F9FA;
--color-bg-tertiary: #E9ECEF;
--color-text-primary: #212529;
--color-text-secondary: #6C757D;
--color-border: #DEE2E6;
--color-primary: #0D6EFD;
--color-success: #198754;
--color-warning: #FFC107;
--color-danger: #DC3545;
--color-info: #0DCAF0;
```

### Spacing (8px grid)
```css
--space-xs: 4px;
--space-sm: 8px;
--space-md: 16px;
--space-lg: 24px;
--space-xl: 32px;
--space-xxl: 48px;
```

### Interactive Elements
```css
--tap-target-min: 48px;
--button-height: 44px;
--input-height: 40px;
--border-radius-sm: 4px;
--border-radius-md: 8px;
--border-radius-lg: 12px;
--shadow-sm: 0 1px 2px rgba(0,0,0,0.05);
--shadow-md: 0 4px 6px rgba(0,0,0,0.1);
--shadow-lg: 0 10px 15px rgba(0,0,0,0.1);
```

---

## 📐 Layout Specifications

### PWA Mobile (360px - 768px)
- Grid: 2 columns, 16px gap
- Card min-height: 120px
- Header height: 64px
- Bottom nav: 56px

### PWA Tablet (768px - 1024px)
- Grid: 3 columns, 24px gap
- Card min-height: 140px

### Admin Desktop (1280px+)
- Left nav: 240px fixed
- Main content: fluid with max-width: 1600px
- Table row height: 56px
- Sidebar: 320px (when present)

---

## 🔧 Technical Implementation Notes

### Real-Time Sync Strategy
```typescript
// Team member updates trigger broadcast
redis.publish('team_task_updated', {
  team_id: task.team_id,
  task_id: task.id,
  updated_by: user.id,
  field: 'količina_pronađena',
  value: newValue
});

// All team members receive update
socket.on('team_task_updated', (data) => {
  if (data.team_id === currentUser.team_id) {
    updateTaskUI(data);
    showToast(`${data.updated_by_name} ажурирао задатак`);
  }
});
```

### Partial Completion Payload
```json
{
  "stavka_id": "uuid",
  "količina_pronađena": 7,
  "količina_tražena": 10,
  "razlog": "nema_na_stanju",
  "razlog_tekst": null,
  "operation_id": "partial-uuid-timestamp"
}
```

### Team Assignment Display
```typescript
const shiftInfo = {
  'A': {
    start: '08:00',
    end: '15:00',
    pause: '10:00-10:30'
  },
  'B': {
    start: '12:00',
    end: '19:00',
    pause: '14:00-14:30'
  }
};

const displayTeamInfo = (team) => {
  return `Tim ${team.name} — Smjena ${team.shift} (${shiftInfo[team.shift].start}–${shiftInfo[team.shift].end})`;
};
```

---

## ✅ Definition of Done

### Backend
- [ ] New migration applied successfully
- [ ] All existing tests pass
- [ ] New endpoints return correct data
- [ ] Redis Pub/Sub events firing
- [ ] Audit trail capturing team actions

### PWA
- [ ] All strings in Serbian
- [ ] Installable as PWA
- [ ] Works offline with queue
- [ ] Tested on Zebra TC21/MC3300
- [ ] Lighthouse score > 90
- [ ] Responsive 360px - 1024px

### Admin
- [ ] Left nav fully functional
- [ ] All routes accessible
- [ ] Tables showing new columns
- [ ] CSV export working
- [ ] No console errors

### TV
- [ ] No mock data visible
- [ ] Live updates < 2s
- [ ] All metrics from real API
- [ ] Socket.IO connected

### Documentation
- [ ] Test report with screenshots
- [ ] README updated
- [ ] API endpoints documented
- [ ] Serbian UI strings documented

---

## 🚀 Deployment Checklist

### Pre-Deployment
- [ ] Run all migrations
- [ ] Populate catalog (min 100 items)
- [ ] Create 2 test teams
- [ ] Clear Redis cache
- [ ] Restart all services

### Post-Deployment
- [ ] Verify PWA installable
- [ ] Test team sync (2 devices)
- [ ] Test partial completion flow
- [ ] Verify TV updates live
- [ ] Check audit logs

---

## 📊 Success Metrics

| Metric | Target | How to Measure |
|--------|--------|----------------|
| PWA Lighthouse Score | >90 | Chrome DevTools |
| Team Sync Latency | <2s | Network tab |
| Catalog Load Time | <500ms | API response time |
| TV Update Latency | <2s | WebSocket events |
| Mobile Tap Success | >95% | User testing |
| Offline Queue Success | 100% | PWA testing |

---

## 🐛 Risk Mitigation

### Risk 1: Real-time sync conflicts
**Mitigation:** Last-write-wins with timestamp; show conflict toast

### Risk 2: Zebra device compatibility
**Mitigation:** Test on actual TC21/MC3300; progressive enhancement

### Risk 3: Catalog sync throttling
**Mitigation:** Implement exponential backoff; queue system

### Risk 4: Performance with large datasets
**Mitigation:** Server-side pagination; virtual scrolling

---

## 📞 Support & Resources

### Manhattan Active WMS Reference
- UX Patterns: Clarity-first, white backgrounds, large tap targets
- Navigation: Left rail with grouped sections
- Tables: Sticky headers, server-side filters
- Feedback: Inline validation, toast notifications

### Serbian Language Resources
- Cyrillic/Latin support
- Date/time formatters
- Number formatting (European style)

### Zebra Documentation
- TC21/TC26 screen: 5.5" 1280x720
- MC3300 screen: 4" 800x480
- Touch target: min 48px
- Barcode scanner SDK integration

---

**Implementation Start:** October 19, 2025  
**Target Completion:** October 26, 2025  
**Sprint Duration:** 7 days  
**Team:** 1 developer + 1 QA  

**Status:** 🟡 Planning Complete - Ready to Start Implementation

