# WMS Dashboard Documentation

## Overview

The WMS Dashboard (`/dashboard`) is a fully functional, enterprise-grade warehouse management dashboard that provides real-time insights into warehouse operations. It replaces the previous static layout with dynamic components that fetch live data from backend APIs.

## Features

### 1. Real-Time KPI Cards

**Location:** Top row of the dashboard
**Data Source:** `/api/tv/snapshot` endpoint
**Refresh Interval:** 30 seconds

#### KPI Cards:
- **Total Tasks Today:** Shows `total_tasks_today` from TV snapshot
- **Completed (%):** Displays `completed_percentage` with animated progress bar
- **Active Workers:** Shows `active_workers` count with color coding (green=active, red=none)
- **Shift Time Remaining:** Dynamic calculation based on current time and shift schedules

#### Shift Calculation:
- **Shift 1:** 08:00–15:00
- **Shift 2:** 12:00–19:00
- Automatically detects active shift and shows countdown
- Updates every minute

### 2. Performance Charts

#### Tasks Completed per Hour (Left Chart)
- **Type:** Line chart using Ant Design Charts
- **Data:** Simulated hourly task completion data (8-hour window)
- **Refresh:** Manual refresh button + auto-refresh every 60 seconds
- **Tooltip:** Shows worker/team and task count

#### Warehouse Load Distribution (Right Chart)
- **Type:** Pie chart showing task distribution by worker
- **Data Source:** `/api/kpi/top-workers` endpoint
- **Features:** Color legend, tooltip with completion rates
- **Refresh:** Manual refresh button + auto-refresh every 2 minutes

### 3. Operational Events Table

**Data Source:** `/api/stream/events/recent` endpoint
**Refresh Interval:** 30 seconds
**Pagination:** 20 entries per page

#### Columns:
- **Time:** Formatted timestamp (HH:MM)
- **Type:** Event type with color coding
  - Critical: Red with exclamation icon
  - Warning: Orange with warning icon
  - Info: Blue with check icon
  - Partial: Yellow with warning icon
- **Worker:** Worker ID (e.g., #24) or "Sistem"
- **Message:** Event description

### 4. AI Insights Panel

**Trigger:** "AI Summary" button in header
**Data Source:** `/api/ai/query` endpoint
**Features:**
- Expandable side drawer (400px width)
- AI-generated insights and recommendations
- Confidence score display
- Manual refresh capability
- Context-aware queries (Serbian language, 1-day scope)

### 5. Alert System

**Location:** Top-right notification bell
**Features:**
- Badge counter (currently shows 0)
- Click to open modal with active alerts
- Links to related documents/workers
- Real-time updates

### 6. User Context

**Location:** Top-right corner
**Features:**
- Currently logged-in user display
- Role badge (ADMIN, ŠEF MAGACINA, KOMERCIJALISTA)
- Dropdown menu with:
  - Profile information
  - Logout option

## API Endpoints Used

### Primary Data Sources:
- `GET /api/tv/snapshot` - KPI data and real-time metrics
- `GET /api/kpi/daily-stats` - Daily statistics
- `GET /api/kpi/top-workers` - Worker performance data
- `GET /api/kpi/manual-completion` - Manual completion statistics
- `GET /api/stream/events/recent` - Recent operational events

### AI Integration:
- `POST /api/ai/query` - AI insights generation

## Data Refresh Logic

### Auto-Refresh Intervals:
- **TV Snapshot:** 30 seconds
- **Daily Stats:** 60 seconds
- **Top Workers:** 2 minutes
- **Manual Completion:** 2 minutes
- **Recent Events:** 30 seconds
- **Global Refresh:** 60 seconds (invalidates all dashboard queries)

### Manual Refresh:
- Individual refresh buttons on each component
- Global "Refresh" button in header
- AI Insights refresh button

## Component Structure

```
DashboardPage
├── Header (Title + Controls)
├── KPI Cards Row (4 cards)
├── Charts Row (Performance + Workload)
├── Events Table
└── AI Insights Drawer
```

## Styling

- **Background:** Light gray (`#f5f5f5`)
- **Cards:** White background with shadows
- **Colors:** 
  - Primary: `#1890ff` (blue)
  - Success: `#52c41a` (green)
  - Warning: `#faad14` (yellow)
  - Error: `#f5222d` (red)
- **Typography:** Ant Design default fonts
- **Responsive:** Mobile-friendly with responsive grid

## Error Handling

- Loading states with spinners
- Graceful fallbacks for missing data
- Console error logging
- User-friendly error messages

## Performance Considerations

- React Query caching (5-minute TTL)
- Background updates
- Optimized re-renders
- Efficient data transformations

## Future Enhancements

### Planned Features:
- Mini warehouse map preview
- Average pick time metrics
- AI forecast for next hour
- Enhanced alert system with notifications
- Real-time WebSocket updates
- Export functionality

### Technical Improvements:
- Code splitting for better performance
- Virtual scrolling for large event tables
- Advanced filtering and search
- Customizable dashboard layouts
- Theme switching

## Troubleshooting

### Common Issues:
1. **Data not loading:** Check API Gateway connectivity
2. **Charts not rendering:** Verify Ant Design Charts installation
3. **AI insights failing:** Check AI service availability
4. **Shift calculation incorrect:** Verify timezone settings

### Debug Information:
- All API calls are logged to console
- React Query DevTools available in development
- Network tab shows all requests/responses

## Security

- JWT token authentication required
- Role-based access control
- Secure API communication
- Input validation and sanitization

---

**Last Updated:** October 17, 2025
**Version:** 1.0.0
**Maintainer:** Development Team
