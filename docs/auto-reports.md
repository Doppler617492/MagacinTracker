# Automated KPI Reports Documentation

## Overview

The Automated KPI Reports system provides scheduled delivery of warehouse performance insights via email and Slack. The system generates comprehensive reports with KPI summaries, visualizations, and CSV data in Pantheon MP format.

## Features

### 📧 Multi-Channel Delivery
- **Email Reports**: HTML format with embedded charts and CSV attachments
- **Slack Notifications**: Rich messages with KPI summaries and CSV data
- **Flexible Scheduling**: Daily, weekly, and monthly frequencies
- **Custom Timing**: Configurable send times (default: 07:00)

### 📊 Comprehensive Content
- **KPI Summary**: Total items, manual percentage, average time, completed tasks
- **Visual Charts**: Daily trends, top workers, manual vs scanning distribution
- **CSV Export**: Pantheon MP format with complete data
- **Filter Support**: By store, period, and worker

### 🔧 Management Interface
- **Schedule Management**: Create, edit, enable/disable schedules
- **Run Now**: Immediate report delivery
- **History Tracking**: Complete audit trail
- **Statistics**: Success/failure metrics

## System Architecture

### Backend Components

#### 1. Reports API (`/api/reports/`)
- **CRUD Operations**: Full schedule management
- **Run Now**: Immediate report execution
- **History**: Report delivery tracking
- **Audit Logging**: Complete event tracking

#### 2. Cron Scheduler
- **Automated Execution**: Checks schedules every minute
- **Timezone Support**: Configurable timezone (default: Europe/Belgrade)
- **Background Processing**: Non-blocking report generation
- **Error Handling**: Graceful failure recovery

#### 3. Email Service
- **SMTP Integration**: Configurable email server
- **HTML Templates**: Professional report formatting
- **CSV Attachments**: Pantheon MP format
- **Chart Embedding**: Visual data representation

#### 4. Slack Service
- **Webhook Integration**: Direct Slack API communication
- **Rich Messages**: Formatted KPI summaries
- **Channel Support**: Multiple channel delivery
- **CSV Data**: Inline or attachment format

### Frontend Components

#### 1. Reports Page (`/reports`)
- **Schedule List**: Table view with all schedules
- **Create/Edit Modal**: Wizard-style schedule creation
- **Statistics Dashboard**: Success metrics and overview
- **Action Buttons**: Run now, edit, delete, enable/disable

#### 2. Integration with Analytics
- **Filter Context**: Passes current dashboard filters
- **AI Assistant**: Can trigger reports from chat
- **Real-time Updates**: Live schedule status

## Configuration

### Environment Variables

#### SMTP Configuration
```env
# Email Server Settings
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASS=your-app-password
SMTP_FROM=noreply@magacin.com
SMTP_TLS=true
```

#### Slack Configuration
```env
# Slack Webhook
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK
SLACK_CHANNEL=#magacin-reports
SLACK_USERNAME=Magacin Bot
SLACK_ICON_EMOJI=:chart_with_upwards_trend:
```

#### Scheduler Configuration
```env
# Cron Scheduler
REPORT_CRON_TZ=Europe/Belgrade
REPORT_DEFAULT_HOUR=7
REPORT_DEFAULT_MINUTE=0
```

### Docker Compose Integration

Add to your `docker-compose.yml`:

```yaml
services:
  api-gateway:
    environment:
      - SMTP_HOST=${SMTP_HOST}
      - SMTP_PORT=${SMTP_PORT}
      - SMTP_USER=${SMTP_USER}
      - SMTP_PASS=${SMTP_PASS}
      - SMTP_FROM=${SMTP_FROM}
      - SLACK_WEBHOOK_URL=${SLACK_WEBHOOK_URL}
      - REPORT_CRON_TZ=${REPORT_CRON_TZ}
```

## API Reference

### Schedule Management

#### POST /api/reports/schedules
Create a new report schedule.

**Request Body:**
```json
{
  "name": "Dnevni KPI izvještaj",
  "description": "Automatski dnevni izvještaj za menadžment",
  "channel": "email",
  "frequency": "daily",
  "recipients": ["manager@magacin.com", "ceo@magacin.com"],
  "filters": {
    "radnja": "pantheon",
    "period": "7d"
  },
  "enabled": true,
  "time_hour": 7,
  "time_minute": 0
}
```

**Response:**
```json
{
  "id": "uuid",
  "name": "Dnevni KPI izvještaj",
  "description": "Automatski dnevni izvještaj za menadžment",
  "channel": "email",
  "frequency": "daily",
  "recipients": ["manager@magacin.com", "ceo@magacin.com"],
  "filters": {
    "radnja": "pantheon",
    "period": "7d"
  },
  "enabled": true,
  "time_hour": 7,
  "time_minute": 0,
  "created_at": "2024-01-15T07:00:00Z",
  "updated_at": "2024-01-15T07:00:00Z",
  "last_sent": null,
  "next_send": "2024-01-16T07:00:00Z",
  "total_sent": 0,
  "total_failed": 0
}
```

#### GET /api/reports/schedules
Get all report schedules.

#### PATCH /api/reports/schedules/{id}
Update a report schedule.

#### DELETE /api/reports/schedules/{id}
Delete a report schedule.

#### POST /api/reports/run-now/{id}
Run a report schedule immediately.

**Request Body:**
```json
{
  "schedule_id": "uuid",
  "recipients": ["custom@magacin.com"],
  "filters": {
    "radnja": "maxi",
    "period": "30d"
  }
}
```

### Report History

#### GET /api/reports/schedules/{id}/history
Get report sending history for a schedule.

**Response:**
```json
{
  "schedule_id": "uuid",
  "history": [
    {
      "sent_at": "2024-01-15T07:00:00Z",
      "recipients": ["manager@magacin.com"],
      "status": "success",
      "processing_time_ms": 1250
    }
  ],
  "total": 1
}
```

## Report Formats

### Email Report Structure

#### HTML Body
- **Header**: Report title and generation timestamp
- **KPI Cards**: Key metrics in visual cards
- **Charts Section**: Embedded visualizations
- **Filters Summary**: Applied filters display
- **Footer**: System information and CSV note

#### CSV Attachment
Pantheon MP format with:
- **Header**: Document number, store, responsible person, date
- **Articles Table**: Worker performance data
- **Footer**: Total sum and signature fields

### Slack Message Structure

#### Message Content
- **Title**: Report name and timestamp
- **KPI Summary**: Key metrics in formatted text
- **Top Workers**: Performance rankings
- **Distribution**: Manual vs scanning breakdown
- **Filters**: Applied filter summary

#### Attachments
- **CSV Data**: Formatted as code block
- **Color Coding**: Visual status indicators
- **Footer**: System branding and timestamp

## Scheduling Logic

### Frequency Calculations

#### Daily Reports
- **Trigger**: Every day at specified time
- **Next Send**: Next day at same time
- **Example**: 07:00 daily → next send tomorrow 07:00

#### Weekly Reports
- **Trigger**: Every Monday at specified time
- **Next Send**: Next Monday at same time
- **Example**: Monday 07:00 → next send next Monday 07:00

#### Monthly Reports
- **Trigger**: First day of month at specified time
- **Next Send**: First day of next month at same time
- **Example**: 1st at 07:00 → next send next month 1st at 07:00

### Timezone Handling
- **Server Timezone**: Configurable via `REPORT_CRON_TZ`
- **Default**: Europe/Belgrade (UTC+1/+2)
- **DST Support**: Automatic daylight saving time handling

## Audit & Monitoring

### Audit Events

#### Schedule Events
- `REPORT_SCHEDULED`: New schedule created
- `REPORT_SCHEDULE_UPDATED`: Schedule modified
- `REPORT_SCHEDULE_DELETED`: Schedule removed
- `REPORT_RUN_NOW`: Manual report trigger

#### Delivery Events
- `REPORT_SENT`: Successful report delivery
- `REPORT_SEND_FAILED`: Failed report delivery
- `EMAIL_REPORT_SENT`: Email delivery success
- `SLACK_REPORT_SENT`: Slack delivery success

#### Scheduler Events
- `REPORT_SCHEDULER_STARTED`: Scheduler service started
- `REPORT_SCHEDULER_STOPPED`: Scheduler service stopped
- `REPORT_SCHEDULED_SEND_START`: Scheduled report execution started
- `REPORT_SCHEDULED_SEND_SUCCESS`: Scheduled report execution completed

### Metrics

#### Prometheus Metrics
- `report_send_duration_ms`: Report generation time
- `report_send_total`: Total reports sent
- `report_send_fail_total`: Failed report deliveries
- `report_schedules_active`: Active schedule count

#### Dashboard Metrics
- **Total Schedules**: Number of configured schedules
- **Active Schedules**: Currently enabled schedules
- **Success Rate**: Percentage of successful deliveries
- **Average Processing Time**: Mean report generation time

## Troubleshooting

### Common Issues

#### 1. Reports Not Sending
**Symptoms**: Schedules active but no reports received
**Solutions**:
- Check SMTP/Slack configuration
- Verify scheduler service is running
- Check timezone settings
- Review error logs for delivery failures

#### 2. Email Delivery Failures
**Symptoms**: Reports created but emails not received
**Solutions**:
- Verify SMTP credentials
- Check spam/junk folders
- Test SMTP connection manually
- Review email server logs

#### 3. Slack Notifications Not Working
**Symptoms**: Reports created but Slack messages not appearing
**Solutions**:
- Verify webhook URL is correct
- Check Slack channel permissions
- Test webhook manually
- Review Slack app configuration

#### 4. Scheduler Not Running
**Symptoms**: No automated reports being sent
**Solutions**:
- Check scheduler service status
- Verify timezone configuration
- Review scheduler logs
- Restart API Gateway service

### Debug Mode

Enable debug logging:
```env
LOG_LEVEL=DEBUG
REPORT_DEBUG=true
```

This will log:
- Schedule evaluation details
- Email/Slack delivery attempts
- Processing time measurements
- Error stack traces

### Manual Testing

#### Test Email Delivery
```bash
curl -X POST http://localhost:8123/api/reports/run-now/{schedule_id} \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{"recipients": ["test@example.com"]}'
```

#### Test Slack Delivery
```bash
curl -X POST http://localhost:8123/api/reports/run-now/{schedule_id} \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{"recipients": ["#test-channel"]}'
```

## Security Considerations

### Access Control
- **Authentication**: JWT token required for all endpoints
- **Authorization**: Admin and manager roles only
- **Audit Trail**: Complete logging of all actions
- **Data Privacy**: No sensitive data in logs

### Email Security
- **TLS Encryption**: Secure SMTP connections
- **Authentication**: SMTP username/password
- **Content Filtering**: No sensitive data in email body
- **Attachment Security**: CSV files contain only aggregated data

### Slack Security
- **Webhook Validation**: Secure webhook URLs
- **Channel Restrictions**: Configurable channel access
- **Message Sanitization**: No sensitive data in messages
- **Rate Limiting**: Prevents spam delivery

## Performance Optimization

### Scheduler Performance
- **Efficient Checking**: 1-minute intervals for schedule evaluation
- **Background Processing**: Non-blocking report generation
- **Memory Management**: Efficient schedule storage
- **Error Recovery**: Graceful handling of failures

### Report Generation
- **Caching**: KPI data caching for faster generation
- **Parallel Processing**: Concurrent email/Slack delivery
- **Resource Management**: Memory-efficient CSV generation
- **Timeout Handling**: Configurable processing timeouts

### Database Optimization
- **Indexed Queries**: Optimized schedule lookups
- **Batch Operations**: Efficient history logging
- **Connection Pooling**: Database connection management
- **Query Optimization**: Minimal database queries

## Future Enhancements

### Planned Features
1. **Advanced Scheduling**: Cron expressions, custom intervals
2. **Report Templates**: Customizable report formats
3. **Multi-language**: Support for multiple languages
4. **PDF Generation**: Professional PDF reports
5. **Interactive Charts**: Clickable chart elements

### Integration Improvements
1. **Microsoft Teams**: Teams webhook integration
2. **Discord**: Discord bot notifications
3. **Webhook Support**: Generic webhook delivery
4. **API Integration**: External system integration
5. **Mobile Notifications**: Push notification support

### Analytics Enhancements
1. **Report Analytics**: Track report open rates
2. **User Preferences**: Personalized report settings
3. **A/B Testing**: Report format optimization
4. **Feedback System**: User feedback collection
5. **Usage Analytics**: Report consumption metrics

## Support & Maintenance

### Monitoring
- **Health Checks**: Scheduler service monitoring
- **Performance Metrics**: Report generation times
- **Error Tracking**: Failed delivery monitoring
- **Usage Statistics**: Schedule utilization metrics

### Maintenance Tasks
- **Log Rotation**: Regular log file cleanup
- **Database Cleanup**: Old history record removal
- **Configuration Updates**: Regular security updates
- **Performance Tuning**: Optimization based on usage

### Support Contacts
- **Technical Issues**: development@magacin.com
- **Configuration Help**: support@magacin.com
- **Feature Requests**: product@magacin.com

---

**Documentation Version**: 1.0  
**Last Updated**: January 15, 2024  
**Maintained by**: Development Team
