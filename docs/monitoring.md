# Monitoring & Alerting Setup

## Overview

Magacin Track uses Prometheus for metrics collection, Grafana for visualization, and Alertmanager for alert handling. The monitoring stack provides comprehensive observability across all services.

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Prometheus    │    │     Grafana     │    │  Alertmanager   │
│   (Metrics)     │    │ (Visualization) │    │   (Alerts)      │
│   Port: 9090    │    │   Port: 3000    │    │   Port: 9093    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
         ┌─────────────────────────────────────────────────────┐
         │                 Application Services                 │
         │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐   │
         │  │ API Gateway │ │Task Service │ │Import Service│   │
         │  │   :8000     │ │   :8001     │ │   :8003     │   │
         │  └─────────────┘ └─────────────┘ └─────────────┘   │
         │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐   │
         │  │Realtime Wkr │ │   Redis     │ │ PostgreSQL  │   │
         │  │   :8004     │ │   :6379     │ │   :5432     │   │
         │  └─────────────┘ └─────────────┘ └─────────────┘   │
         └─────────────────────────────────────────────────────┘
```

## Quick Start

### 1. Start Monitoring Infrastructure

```bash
# Start monitoring services
./scripts/start-monitoring.sh

# Start main application
docker compose up -d
```

### 2. Access Dashboards

- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin123)
- **Alertmanager**: http://localhost:9093

## Metrics Collection

### Service Metrics

All services expose Prometheus metrics at `/metrics` endpoint:

- **API Gateway** (`:8000/metrics`): HTTP requests, response times, WebSocket connections
- **Task Service** (`:8001/metrics`): Database operations, task processing
- **Import Service** (`:8003/metrics`): File processing, import jobs
- **Realtime Worker** (`:8004/metrics`): Message processing, WebSocket events

### System Metrics

- **Node Exporter** (`:9100/metrics`): CPU, memory, disk, network
- **Redis Exporter** (`:9121/metrics`): Redis performance and memory
- **Postgres Exporter** (`:9187/metrics`): Database connections and queries

### Custom Metrics

#### API Gateway
- `http_requests_total`: Total HTTP requests by method, status, endpoint
- `http_request_duration_seconds`: Request duration histograms
- `socketio_connections`: Active WebSocket connections

#### Realtime Worker
- `realtime_messages_processed_total`: Total processed messages
- `websocket_disconnections_total`: WebSocket disconnection count
- `websocket_active_connections`: Current active connections

## Alert Rules

### Critical Alerts

#### High Error Rate
```yaml
- alert: HighErrorRate
  expr: rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) > 0.02
  for: 2m
  labels:
    severity: critical
```

#### Service Down
```yaml
- alert: ServiceDown
  expr: up == 0
  for: 1m
  labels:
    severity: critical
```

#### Database Connection Issues
```yaml
- alert: DatabaseConnectionIssues
  expr: pg_up == 0
  for: 1m
  labels:
    severity: critical
```

### Warning Alerts

#### High P95 Scan Latency
```yaml
- alert: HighScanLatency
  expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket{endpoint="/api/scan"}[5m])) > 0.3
  for: 1m
  labels:
    severity: warning
```

#### WebSocket Disconnect Spike
```yaml
- alert: WebSocketDisconnectSpike
  expr: increase(websocket_disconnections_total[5m]) > 10
  for: 1m
  labels:
    severity: warning
```

#### High Memory Usage
```yaml
- alert: HighMemoryUsage
  expr: (node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes > 0.9
  for: 5m
  labels:
    severity: warning
```

## Alert Configuration

### Email Notifications

Configure SMTP settings in `monitoring/alertmanager.yml`:

```yaml
global:
  smtp_smarthost: 'smtp.gmail.com:587'
  smtp_from: 'alerts@yourcompany.com'
  smtp_auth_username: 'alerts@yourcompany.com'
  smtp_auth_password: 'your-app-password'
```

### Slack Notifications

Add Slack webhook URL in `monitoring/alertmanager.yml`:

```yaml
slack_configs:
  - api_url: 'https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK'
    channel: '#alerts-critical'
    title: '🚨 Critical Alert'
```

### Alert Routing

- **Critical alerts**: Email + Slack #alerts-critical
- **Warning alerts**: Email + Slack #alerts-warning
- **Inhibition rules**: Critical alerts suppress warnings for same service

## Grafana Dashboards

### System Overview Dashboard

**Location**: `monitoring/grafana/dashboards/magacin-overview.json`

**Panels**:
- Request Rate by Service
- Response Time Percentiles (P50, P95)
- Error Rate %
- WebSocket Connections
- Realtime Messages/sec
- WebSocket Disconnects/sec
- CPU Usage %
- Memory Usage %

### Dashboard Features

- **Auto-refresh**: 30 seconds
- **Time range**: Last 1 hour (configurable)
- **Thresholds**: Visual indicators for critical levels
- **Annotations**: Alert events overlaid on graphs

## Troubleshooting

### Common Issues

#### Prometheus Not Scraping Services

1. Check service health:
   ```bash
   curl http://localhost:8000/health
   curl http://localhost:8001/health
   ```

2. Verify metrics endpoint:
   ```bash
   curl http://localhost:8000/metrics
   ```

3. Check Prometheus targets:
   - Go to http://localhost:9090/targets
   - Verify all services show "UP" status

#### Grafana Not Loading Dashboards

1. Check Grafana logs:
   ```bash
   docker logs magacin-grafana
   ```

2. Verify dashboard files:
   ```bash
   ls -la monitoring/grafana/dashboards/
   ```

3. Check provisioning:
   ```bash
   ls -la monitoring/grafana/provisioning/dashboards/
   ```

#### Alerts Not Firing

1. Check Alertmanager configuration:
   ```bash
   curl http://localhost:9093/api/v1/status
   ```

2. Verify alert rules:
   - Go to http://localhost:9090/alerts
   - Check rule evaluation status

3. Test alert routing:
   ```bash
   curl -XPOST http://localhost:9093/api/v1/alerts
   ```

### Performance Tuning

#### Prometheus Retention

Adjust retention in `docker-compose.monitoring.yml`:

```yaml
command:
  - '--storage.tsdb.retention.time=200h'  # 8 days
  - '--storage.tsdb.retention.size=10GB'  # Max storage
```

#### Grafana Performance

- Enable query caching
- Use recording rules for complex queries
- Limit dashboard refresh rates

## Security Considerations

### Access Control

- **Grafana**: Change default admin password
- **Prometheus**: Consider authentication for production
- **Alertmanager**: Secure webhook endpoints

### Network Security

- Use internal networks for service communication
- Expose only necessary ports
- Implement firewall rules

### Data Privacy

- Sanitize log data in metrics
- Avoid exposing sensitive information
- Use environment variables for credentials

## Maintenance

### Regular Tasks

1. **Monitor disk usage**:
   ```bash
   docker system df
   ```

2. **Clean up old data**:
   ```bash
   docker volume prune
   ```

3. **Update dashboards**:
   - Export from Grafana UI
   - Update JSON files in `monitoring/grafana/dashboards/`

4. **Review alert rules**:
   - Adjust thresholds based on historical data
   - Add new alerts for business metrics

### Backup

1. **Grafana dashboards**:
   ```bash
   cp -r monitoring/grafana/dashboards/ backups/
   ```

2. **Prometheus data**:
   ```bash
   docker run --rm -v magacin-track_prometheus_data:/data -v $(pwd):/backup alpine tar czf /backup/prometheus-backup.tar.gz -C /data .
   ```

## Production Deployment

### Scaling Considerations

- **Prometheus**: Use federation for multiple instances
- **Grafana**: Consider clustering for high availability
- **Alertmanager**: Use clustering for reliability

### High Availability

- Deploy multiple Prometheus instances
- Use external storage (S3, GCS) for long-term retention
- Implement service discovery for dynamic environments

### Monitoring the Monitor

- Monitor Prometheus itself
- Set up alerts for monitoring system failures
- Use external monitoring (e.g., Uptime Robot) as backup
