# AI Anomaly Detection (Otkrivanje anomalija)

## Overview

AI Anomaly Detection automatically identifies operational issues (stock drift, scan errors, latency spikes) and alerts managers for investigation.

## Purpose

- **Early detection** of systemic problems
- **Reduce inventory errors** through stock drift monitoring
- **Improve scan accuracy** by detecting mismatch spikes
- **Identify bottlenecks** via latency spike detection

## Anomaly Types

### 1. Stock Drift (Odstupanje zaliha)

**Definition:** Bins with frequent stock discrepancies after cycle counts

**Detection Logic:**
- Analyze cycle count variances for last 7 days
- Calculate error rate: `Σ|variance| / Σ(system_quantity)`
- Flag if error rate > 20%

**Severity Levels:**
- **Critical (🔴):** Error rate > 50%
- **High (🟠):** Error rate > 35%
- **Medium (🟡):** Error rate > 25%
- **Low (🟢):** Error rate > 20%

**Typical Causes:**
- Incorrect put-away
- Theft/loss
- Damaged goods not reported
- System data entry errors

**Resolution Steps:**
1. Acknowledge anomaly
2. Recount affected bins
3. Train workers on proper procedures
4. Update system if data error
5. Mark as resolved with note

### 2. Scan Mismatch Spike (Povećan broj grešaka skeniranja)

**Definition:** High barcode scan error rate in recent shift

**Detection Logic:**
- Analyze audit logs for last 4 hours
- Calculate mismatch rate: `SCAN_MISMATCH / (SCAN_OK + SCAN_MISMATCH)`
- Flag if mismatch rate > 15%

**Severity Levels:**
- **Critical:** Rate > 30%
- **High:** Rate > 25%
- **Medium:** Rate > 20%
- **Low:** Rate > 15%

**Typical Causes:**
- Damaged barcode labels
- Scanner hardware issues
- Wrong article picked
- Training gaps

**Resolution Steps:**
1. Check scanner devices
2. Replace damaged labels
3. Retrain workers
4. Update article master data if incorrect

### 3. Task Latency Spike (Povećano vreme izvršavanja)

**Definition:** P95 task execution time increased significantly

**Detection Logic:**
- Compare current shift P95 (last 4h) to 7-day baseline
- Calculate increase: `(P95_current - P95_baseline) / P95_baseline`
- Flag if increase > 30%

**Severity Levels:**
- **Critical:** Increase > 70%
- **High:** Increase > 50%
- **Medium:** Increase > 40%
- **Low:** Increase > 30%

**Typical Causes:**
- Congestion in aisles
- Equipment failures
- Understaffing
- Poor bin locations (need slotting optimization)

**Resolution Steps:**
1. Review shift activity logs
2. Check equipment status
3. Redistribute tasks if understaffed
4. Consider slotting optimization

## API Endpoints

### List Anomalies

```http
GET /api/ai/anomalies?type=stock_drift&status=new&from=2025-10-15&to=2025-10-20
Authorization: Bearer <token>
```

**Response:**
```json
[
  {
    "id": "uuid",
    "type": "stock_drift",
    "severity": "high",
    "status": "new",
    "title": "Odstupanje zaliha u ZA-R01-P01-B01",
    "description": "Lokacija ZA-R01-P01-B01 ima 42.5% greške u poslednjih 7 dana.",
    "confidence": 0.85,
    "detected_at": "2025-10-19T10:30:00Z",
    "acknowledged_at": null,
    "resolved_at": null
  }
]
```

### Get Anomaly Details

```http
GET /api/ai/anomalies/{id}
Authorization: Bearer <token>
```

**Response includes:**
- Full details (error_rate, count_total, location_code, etc.)
- Time-to-acknowledge, time-to-resolve metrics
- Acknowledgment and resolution info

### Acknowledge Anomaly

```http
POST /api/ai/anomalies/{id}/ack
Authorization: Bearer <token>
```

**Action:** Sets status to "acknowledged", records user_id and timestamp

### Resolve Anomaly

```http
POST /api/ai/anomalies/{id}/resolve
Authorization: Bearer <token>
Content-Type: application/json

{
  "resolution_note": "Bin prebrojano ponovo. Oštećenje robe, ispravljena evidencija."
}
```

**Action:** Sets status to "resolved", records note and timestamp

## Admin UI

### Anomalies Dashboard

**Path:** Admin → AI → Anomalije

**Dashboard Widgets:**

1. **Aktivne anomalije (Active Anomalies)**
   - Count by severity (Critical: 2, High: 5, Medium: 8, Low: 12)
   - Count by type (Stock Drift: 10, Scan Mismatch: 5, Task Latency: 2)

2. **Top 5 Recent**
   - Table with: Type, Title, Severity, Detected At, Status

3. **Mean Time Metrics**
   - Avg Time to Acknowledge: 2.5h
   - Avg Time to Resolve: 8.2h

**Table Columns:**
- Type (icon + label)
- Severity (color badge)
- Title
- Confidence
- Detected At
- Status (badge)
- Acknowledged By
- Resolved By
- Actions (ACK / Resolve / Details)

**Filters:**
- Type (all / stock_drift / scan_mismatch / task_latency)
- Severity (all / critical / high / medium / low)
- Status (all / new / acknowledged / in_progress / resolved)
- Date range

**Detail Modal:**
- Full description
- Details (JSONB as key-value table)
- Timeline (detected → acknowledged → resolved)
- Resolution note
- Action buttons (ACK / Resolve)

**Export:** CSV with all fields

## TV Dashboard (Optional)

**Discrete Overlay:**
- Corner badge: "⚠️ 3 nove anomalije"
- No sound
- Click to expand brief list
- Link to Admin dashboard

## Batch Job

### Schedule
```cron
*/15 * * * *  # Every 15 minutes
```

### Logic
```python
async def anomaly_detection_job():
    # Stock drift (daily check)
    if current_time.hour == 6:  # 6 AM
        await AIAnomalyDetectionService.detect_stock_drift_anomalies()
    
    # Scan mismatch (hourly check)
    await AIAnomalyDetectionService.detect_scan_mismatch_anomalies(hours_window=4)
    
    # Task latency (every 15 min)
    await AIAnomalyDetectionService.detect_task_latency_anomalies()
```

### Monitoring
- Prometheus metric: `ai_anomaly_detection_duration_seconds`
- Alert if job fails

## Metrics & KPIs

### Anomaly Metrics
- **New anomalies per day:** Track trend
- **Mean time to acknowledge:** Target < 4h
- **Mean time to resolve:** Target < 24h
- **False positive rate:** Target < 10%

### Business Impact
- **Stock accuracy improvement:** Before vs After (target: +5%)
- **Scan error reduction:** Before vs After (target: -30%)
- **Task latency improvement:** Before vs After (target: -20%)

## Audit Trail

**Events:**
- `AI_ANOMALY_DETECTED` - System detected anomaly
- `AI_ANOMALY_ACK` - Manager acknowledged
- `AI_ANOMALY_RESOLVED` - Manager resolved

**Audit fields:**
- `user_id` - Manager (null for detected)
- `entity_id` - Anomaly ID
- `details` - Type, severity, resolution_note

## Feature Flag

**Environment Variable:** `FF_AI_ANOMALY=true`

**Behavior when disabled:**
- API returns 404
- Batch job skipped
- Admin UI hides "Anomalije" module

## RBAC Access

| Role | View | ACK | Resolve | Export |
|------|------|-----|---------|--------|
| ADMIN | ✅ | ✅ | ✅ | ✅ |
| MENADŽER | ✅ | ✅ | ✅ | ✅ |
| ŠEF | ✅ | ✅ | ✅ | ❌ |
| MAGACIONER | ❌ | ❌ | ❌ | ❌ |
| KOMERCIJALISTA | ❌ | ❌ | ❌ | ❌ |

## Testing

See `test-report-phase4.md` for:
- Detection algorithm tests (3 types)
- Severity calculation tests
- ACK/Resolve workflow tests
- Batch job tests
- Time-to-X metric tests

## Future Enhancements

- **Predictive anomalies:** ML model to predict issues before they occur
- **Root cause analysis:** Auto-suggest likely causes
- **Auto-remediation:** For low-severity, known issues
- **Slack/email notifications:** Real-time alerts
- **Anomaly clustering:** Group related anomalies

