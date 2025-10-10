# Reports and Analytics Documentation

## Overview

The Magacin Track system provides comprehensive analytics and reporting capabilities through the Admin KPI Dashboard and CSV export functionality.

## KPI Dashboard

### Features

The Analytics page (`/analytics`) provides:

- **Real-time KPI metrics** with automatic refresh
- **Interactive charts** (line, bar, pie) using Ant Design Charts
- **Advanced filtering** by radnja, period, date range, and worker
- **CSV export** functionality with Pantheon MP format
- **Responsive design** for desktop and mobile

### Available Charts

#### 1. Daily Trend (Line Chart)
- **API**: `GET /api/kpi/daily-stats`
- **Data**: Daily completion trends over time
- **Metrics**: Total items, completed tasks, manual vs scanned
- **Colors**: Blue (total), Green (completed), Yellow (manual)

#### 2. Top 5 Workers (Bar Chart)
- **API**: `GET /api/kpi/top-workers`
- **Data**: Most productive workers by completed tasks
- **Metrics**: Worker name, completed tasks count
- **Color**: Blue gradient

#### 3. Manual vs Scanning (Pie Chart)
- **API**: `GET /api/kpi/manual-completion`
- **Data**: Distribution of manual confirmations vs barcode scanning
- **Metrics**: Manual items, scanned items
- **Colors**: Blue (scanned), Green (manual)

### KPI Cards

The dashboard displays key metrics in card format:

- **Ukupno stavki**: Total items processed
- **Manual %**: Percentage of manual confirmations
- **Prosječno vrijeme**: Average time per task (minutes)
- **Aktivni radnici**: Number of active workers

### Filters

#### Available Filter Options

1. **Radnja (Store)**
   - `pantheon` - Pantheon store
   - `maxi` - Maxi store
   - `idea` - Idea store
   - `null` - All stores

2. **Period**
   - `1d` - Last 1 day
   - `7d` - Last 7 days
   - `30d` - Last 30 days
   - `90d` - Last 90 days

3. **Date Range**
   - Custom date range picker
   - Format: DD.MM.YYYY
   - Overrides period filter when selected

4. **Radnik (Worker)**
   - `marko.sef@example.com` - Marko Šef
   - `ana.radnik@example.com` - Ana Radnik
   - `petar.worker@example.com` - Petar Worker
   - `null` - All workers

## CSV Export

### Functionality

The CSV export feature generates reports in Pantheon MP calculation format:

- **API**: `GET /api/reports/export`
- **Format**: UTF-8 encoded CSV with semicolon delimiter
- **Compatibility**: Excel-compatible
- **Audit**: `REPORT_EXPORTED` event + `report_export_duration_ms` metric

### CSV Structure

#### Header Section
```csv
Broj dokumenta;Radnja;Odgovorna osoba;Datum
DOC-2024-001;Pantheon;Marko Šef;15.01.2024
```

#### Articles Table
```csv
Šifra;Naziv;Količina;Cijena;Ukupno
ART-001;Artikl 1;10;25.50;255.00
ART-002;Artikl 2;5;15.75;78.75
ART-003;Artikl 3;20;8.25;165.00
```

#### Footer Section
```csv
;;;;
UKUPNO;;;498.75
;;;;
Potpis odgovorne osobe:;________________
Datum potvrde:;15.01.2024
```

### Export Parameters

The CSV export accepts the same filter parameters as the KPI dashboard:

- `radnja` - Filter by store
- `period` - Filter by time period
- `radnik` - Filter by worker
- `date_range` - Custom date range

### Example API Call

```bash
curl -H "Authorization: Bearer <token>" \
  "http://localhost:8123/api/reports/export?radnja=pantheon&period=7d" \
  -o magacin-report-2024-01-15.csv
```

## API Endpoints

### KPI Endpoints

#### GET /api/kpi/daily-stats
Returns daily statistics for trend analysis.

**Parameters:**
- `radnja` (optional): Store filter
- `period` (optional): Time period (1d, 7d, 30d, 90d)
- `radnik` (optional): Worker filter

**Response:**
```json
{
  "data": [
    {
      "date": "2024-01-15",
      "value": 150,
      "type": "total_items"
    }
  ],
  "summary": {
    "total_items": 1050,
    "manual_percentage": 23.5,
    "avg_time_per_task": 4.2,
    "total_tasks": 45,
    "completed_tasks": 42
  }
}
```

#### GET /api/kpi/top-workers
Returns top performing workers.

**Parameters:**
- `radnja` (optional): Store filter
- `period` (optional): Time period

**Response:**
```json
{
  "data": [
    {
      "worker_name": "Marko Šef",
      "completed_tasks": 25
    }
  ],
  "summary": {
    "active_workers": 8
  }
}
```

#### GET /api/kpi/manual-completion
Returns manual vs scanning completion statistics.

**Parameters:**
- `radnja` (optional): Store filter
- `period` (optional): Time period

**Response:**
```json
{
  "data": [
    {
      "type": "scanned",
      "value": 850
    },
    {
      "type": "manual",
      "value": 200
    }
  ],
  "summary": {
    "scanned_items": 850,
    "manual_items": 200
  }
}
```

### Export Endpoint

#### GET /api/reports/export
Generates and downloads CSV report.

**Parameters:**
- `radnja` (optional): Store filter
- `period` (optional): Time period
- `radnik` (optional): Worker filter

**Response:**
- Content-Type: `text/csv; charset=utf-8`
- Content-Disposition: `attachment; filename="magacin-report-YYYY-MM-DD.csv"`
- Body: CSV content with Pantheon MP format

## Performance Considerations

### Caching
- KPI data is cached for 5 minutes
- Manual refresh available via "Osveži" button
- Real-time updates via WebSocket (future enhancement)

### Data Volume
- Daily stats: Optimized for up to 90 days
- Top workers: Limited to top 5 performers
- CSV export: Paginated for large datasets

### Browser Compatibility
- Modern browsers with ES6+ support
- Chrome 80+, Firefox 75+, Safari 13+
- Mobile responsive design

## Security

### Authentication
- JWT token required for all endpoints
- Admin role required for analytics access
- Audit logging for all export operations

### Data Privacy
- Worker names anonymized in public reports
- Sensitive data filtered based on user permissions
- GDPR compliance for data export

## Troubleshooting

### Common Issues

1. **Charts not loading**
   - Check API connectivity
   - Verify authentication token
   - Check browser console for errors

2. **CSV export fails**
   - Ensure sufficient permissions
   - Check file size limits
   - Verify date range validity

3. **Filter not working**
   - Clear browser cache
   - Check API parameter format
   - Verify filter values exist in database

### Debug Mode

Enable debug logging by setting:
```javascript
localStorage.setItem('debug', 'true');
```

This will log all API calls and responses to the browser console.