# Smart KPI & Benchmarking (Pametni KPI i benchmarking)

## Overview

Smart KPI extends standard warehouse metrics with AI-powered insights, shift/team comparisons, and visual heatmaps for optimization.

## Purpose

- **Shift performance tracking** (Smena A vs Smena B)
- **Team benchmarking** for healthy competition
- **Bin heatmap** to identify problem locations
- **Predictive insights** for staffing and training

## Features

### 1. Shift Summary (Produktivnost smena)

**Shifts Defined:**
- **Smena A:** 08:00-15:00 (pauza 10:00-10:30)
- **Smena B:** 12:00-19:00 (pauza 14:00-14:30)

**Metrics Per Shift:**
- Tasks completed (total)
- Tasks partial (count + %)
- Avg completion time (minutes)
- Picks per hour
- Accuracy percentage (completed vs partial)
- Workers count

**API Endpoint:**
```http
GET /api/ai/kpi/shift-summary?date=2025-10-19
Authorization: Bearer <token>
```

**Response:**
```json
[
  {
    "shift_name": "Smena A (08-15)",
    "date": "2025-10-19",
    "tasks_completed": 245,
    "tasks_partial": 18,
    "avg_completion_time_minutes": 3.8,
    "picks_per_hour": 35.0,
    "accuracy_percentage": 92.7,
    "workers_count": 8
  },
  {
    "shift_name": "Smena B (12-19)",
    "date": "2025-10-19",
    "tasks_completed": 198,
    "tasks_partial": 22,
    "avg_completion_time_minutes": 4.2,
    "picks_per_hour": 28.3,
    "accuracy_percentage": 88.9,
    "workers_count": 6
  }
]
```

### 2. Team vs Team Comparison

**Metrics Per Team:**
- Total tasks assigned
- Tasks completed
- Completion rate (%)
- Avg time per task
- Productivity score (0-100)

**Productivity Score Formula:**
```
productivity = (
  completion_rate * 0.5 +
  (1 - (avg_time / benchmark_time)) * 0.3 +
  accuracy * 0.2
) * 100
```

**API Endpoint:**
```http
GET /api/ai/kpi/team-vs-team?from=2025-10-13&to=2025-10-20
Authorization: Bearer <token>
```

**Use Cases:**
- Weekly team rankings
- Training need identification (low productivity = training gap)
- Reward high-performing teams

### 3. Bin Heatmap (Problematični binovi)

**Purpose:** Identify slow-moving, problematic bin locations

**Metrics Per Bin:**
- Occupancy percentage
- Turnover rate (picks per day)
- Avg pick time (seconds)
- Problem score (0-100, higher = worse)

**Problem Score Formula:**
```
problem_score = (
  occupancy * 0.4 +              # High occupancy = harder to pick
  (1 - turnover_normalized) * 0.3 +  # Low turnover = slow mover
  (avg_pick_time / benchmark) * 0.3  # Slow picks = bad location
) * 100
```

**API Endpoint:**
```http
GET /api/ai/kpi/bin-heatmap?zona=A
Authorization: Bearer <token>
```

**Response:**
```json
{
  "bins": [
    {
      "location_id": "uuid",
      "location_code": "ZA-R01-P01-B01",
      "occupancy_percentage": 95.0,
      "turnover_rate": 2.5,
      "avg_pick_time_seconds": 180.0,
      "problem_score": 72.5
    }
  ],
  "zona": "A",
  "total_count": 48
}
```

**Use Cases:**
- Identify bins needing slotting optimization
- Find overstocked locations
- Highlight bins with access issues (narrow aisle, high shelf)

## Admin UI

### Analytics → Smart KPI

**Page Layout:**

**1. Shift Productivity Card**
- Bar chart: Tasks completed per shift (last 7 days)
- Line chart: Avg completion time trend
- Summary table: Smena A vs Smena B

**2. Team Comparison Card**
- Leaderboard table: Top 5 teams by productivity score
- Horizontal bar chart: Completion rates
- Filter: Period (last week / last month)

**3. Bin Heatmap Visualization**
- 2D grid view (color-coded by problem_score)
  - Green: Score < 30 (good)
  - Yellow: Score 30-60 (watch)
  - Red: Score > 60 (problem)
- Hover tooltip: Location code, occupancy, turnover, avg pick time
- Click bin: Drill-down with recommendations

**4. Recommendations Panel**
- AI-generated suggestions based on KPIs:
  - "Smena B accuracy dropped 5% this week - consider retraining"
  - "Bin ZA-R01-P01-B05 has 95% occupancy + low turnover - consider moving articles"
  - "Tim A3 productivity down 15% - check for staffing issues"

**Filters:**
- Magacin (dropdown)
- Period (last week / last month / custom range)
- Zona (for heatmap)

**Export:** CSV / PDF report with all charts

## Metrics & KPIs

### Shift Metrics
- **Avg picks per hour:** Target > 30
- **Avg accuracy:** Target > 95%
- **Shift balance:** Smena A vs B should be within 10%

### Team Metrics
- **Productivity score:** Target > 70
- **Completion rate:** Target > 90%
- **Avg time per task:** Compare to benchmark (2-4 min)

### Bin Metrics
- **Problem bins count:** Target < 10% of total bins
- **Avg occupancy:** Target 60-80% across all bins
- **Turnover rate:** Track by article class (fast/standard/slow)

## Dashboard Widgets (Admin Homepage)

**1. Aktivne smene (Current Shifts)**
- Who's working now
- Real-time task count
- Pause status

**2. Top 5 Problem Bins**
- Location code
- Problem score
- Quick action: "Schedule recount" / "Suggest slotting"

**3. Team Performance Summary**
- This week vs last week
- Top performer highlight
- Improvement opportunities

## Feature Flag

**Environment Variable:** `FF_SMART_KPI=true`

**Behavior when disabled:**
- API returns 404
- Admin UI hides "Smart KPI" module

## RBAC Access

| Role | View Shift | View Team | View Heatmap | Export |
|------|------------|-----------|--------------|--------|
| ADMIN | ✅ | ✅ | ✅ | ✅ |
| MENADŽER | ✅ | ✅ | ✅ | ✅ |
| ŠEF | ✅ | ✅ | ✅ | ❌ |
| MAGACIONER | ❌ | ❌ | ❌ | ❌ |
| KOMERCIJALISTA | ❌ | ❌ | ❌ | ❌ |

## Testing

See `test-report-phase4.md` for:
- Shift summary calculation tests
- Team productivity score tests
- Bin problem score tests
- Chart rendering tests
- Export tests (CSV/PDF)

## Future Enhancements

- **Predictive staffing:** ML model to forecast needed workers per shift
- **Real-time dashboard:** WebSocket updates every 30s
- **Mobile KPI app:** View KPIs on mobile devices
- **Gamification:** Badges, achievements for teams
- **Voice announcements:** "Smena A is leading today!"
- **Integration with payroll:** Performance-based bonuses

