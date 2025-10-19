# AI Predictive Restocking (Prediktivno dopunjavanje)

## Overview

AI Predictive Restocking uses time-series analysis to forecast stock needs and automatically generate restocking suggestions before stockouts occur.

## Purpose

- **Prevent stockouts** by predicting demand 7-14 days ahead
- **Optimize inventory levels** (60-80% utilization target)
- **Automate replenishment** with confidence-scored suggestions
- **Reduce manual planning** effort

## Algorithm (EMA v1)

### Input Data
- Historical pick data (last 30 days from zaduznica_stavka)
- Current stock levels (sum across all bin locations)
- Article metadata (class, UoM)

### Calculation Steps

**1. Average Daily Usage**
```
avg_daily_usage = Σ(picks in last 30 days) / 30
```

**2. Reorder Point**
```
reorder_point = (avg_daily_usage × lead_time_days) + safety_stock
lead_time_days = 3 (default)
safety_stock = avg_daily_usage × 1.5
```

**3. Optimal Stock**
```
optimal_stock = avg_daily_usage × horizon_days
horizon_days = 7-14 (user-selected)
```

**4. Suggested Quantity**
```
suggested_qty = max(optimal_stock - current_stock, 0)
```

**5. Deadline**
```
days_until_stockout = current_stock / avg_daily_usage
deadline = today + min(days_until_stockout, lead_time_days)
```

### Confidence Scoring

Based on **Coefficient of Variation (CV)**:
```
CV = std_dev(daily_usage) / mean(daily_usage)
```

**Confidence Mapping:**
- CV < 0.3 → 0.9 (consistent usage, high confidence)
- CV < 0.5 → 0.8 (moderate variance)
- CV < 0.7 → 0.7 (some variance)
- CV < 1.0 → 0.6 (high variance)
- CV ≥ 1.0 → 0.4 (erratic usage, low confidence)

## API Endpoints

### Generate Suggestions

```http
POST /api/ai/restock/suggest
Authorization: Bearer <token>
Content-Type: application/json

{
  "magacin_id": "uuid",
  "horizon_days": 7
}
```

**Response:**
```json
{
  "suggestions": [
    {
      "id": "uuid",
      "article_code": "ART001",
      "article_name": "Proizvod 1",
      "current_stock": 50.0,
      "suggested_quantity": 150.0,
      "target_zone": "A",
      "confidence": 0.85,
      "reason": "Prosečna dnevna potrošnja: 20.5 | Trenutno stanje: 50.0 | Reorder point: 92.3 | Rok: 2 dana",
      "deadline": "2025-10-21T10:00:00Z"
    }
  ],
  "total_count": 15,
  "model_version": "ema_v1"
}
```

### Approve Suggestions

```http
POST /api/ai/restock/approve
Authorization: Bearer <token>
Content-Type: application/json

{
  "suggestion_ids": ["uuid1", "uuid2"]
}
```

**Action:** Creates internal trebovanje (dopuna) for each approved suggestion

**Response:**
```json
{
  "message": "2 predloga odobreno",
  "trebovanje_ids": ["uuid1", "uuid2"]
}
```

### Reject Suggestion

```http
POST /api/ai/restock/reject
Authorization: Bearer <token>
Content-Type: application/json

{
  "suggestion_id": "uuid",
  "reason": "Već naručeno kod dobavljača"
}
```

## Admin UI

### Dopuna (AI) Module

**Path:** Admin → AI → Dopuna

**Table Columns:**
- Article (code + name)
- Trenutno stanje
- Predložena količina
- Target zona
- Confidence (0-1.0, color-coded)
- Razlog (hover for details)
- Rok (deadline, red if < 3 days)
- Status (Pending / Approved / Rejected)
- Actions (Odobri / Odbij / Detalji)

**Filters:**
- Magacin (dropdown)
- Article class (dropdown)
- Min confidence (slider: 0.5-1.0)
- Status (all / pending / approved / rejected)
- Deadline (< 3 days / < 7 days / all)

**Bulk Actions:**
- Select multiple (checkboxes)
- "Odobri izabrane" button
- Confirmation modal with total quantity

**Export:** CSV with all fields + calculation details

## Cron Job

### Schedule
```cron
0 */1 * * *  # Every hour
```

### Logic
```python
async def restock_cron_job():
    for magacin in warehouses:
        suggestions = await AIRestockingService.generate_suggestions(
            magacin_id=magacin.id,
            horizon_days=7
        )
        # Save to database
        # Send email notification to managers (optional)
```

### Monitoring
- Prometheus metric: `ai_restock_cron_duration_seconds`
- Alert if job fails or takes > 5 minutes

## Metrics & KPIs

### Prediction Accuracy
- **Stockout prevention rate:** Did predicted items actually run out?
- **Over-ordering rate:** Suggested too much?
- **Target:** 90% accuracy

### Operational Impact
- **Manual planning time saved:** Target: 2 hours/day
- **Stockout incidents:** Before vs After (target: 50% reduction)
- **Inventory holding cost:** Optimize 60-80% utilization

### Suggestion Metrics
- **Approval rate:** Target: > 60%
- **Avg confidence of approved:** Target: > 0.7
- **Time to action:** From suggestion to approval (target: < 24h)

## Audit Trail

**Events:**
- `AI_RESTOCK_SUGGESTED` - Suggestions generated (system)
- `AI_RESTOCK_APPROVED` - Manager approved (creates trebovanje)
- `AI_RESTOCK_REJECTED` - Manager rejected with reason

**Audit fields:**
- `user_id` - Manager who approved/rejected
- `entity_id` - Suggestion ID
- `details` - Article, quantity, confidence, trebovanje_id

## Feature Flag

**Environment Variable:** `FF_AI_RESTOCKING=true`

**Behavior when disabled:**
- API returns 404
- Admin UI hides "Dopuna (AI)" module
- Cron job skipped

## RBAC Access

| Role | Generate | Approve | Reject | View |
|------|----------|---------|--------|------|
| ADMIN | ✅ | ✅ | ✅ | ✅ |
| MENADŽER | ✅ | ✅ | ✅ | ✅ |
| ŠEF | ✅ | ✅ | ✅ | ✅ |
| MAGACIONER | ❌ | ❌ | ❌ | ❌ |
| KOMERCIJALISTA | ❌ | ❌ | ❌ | ❌ |

## Testing

See `test-report-phase4.md` for:
- EMA calculation tests
- Confidence scoring tests
- Cron job tests (hourly trigger)
- Approval workflow (trebovanje creation)
- Export CSV tests

## Future Enhancements

- **Seasonal patterns:** Adjust for holidays, promotions
- **Supplier lead time tracking:** Dynamic lead_time_days per article
- **Multi-location optimization:** Stock transfers between warehouses
- **ML-based forecasting:** Prophet, ARIMA models
- **Auto-approval:** High-confidence suggestions (>0.9) auto-approved

