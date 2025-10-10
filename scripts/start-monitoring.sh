#!/usr/bin/env bash
set -euo pipefail

# Start monitoring infrastructure for Magacin Track

echo "🚀 Starting Magacin Track Monitoring Infrastructure..."

# Create monitoring network if it doesn't exist
if ! docker network ls | grep -q "magacin-track_monitoring"; then
    echo "📡 Creating monitoring network..."
    docker network create magacin-track_monitoring
fi

# Start monitoring services
echo "📊 Starting Prometheus, Grafana, and Alertmanager..."
docker compose -f docker-compose.monitoring.yml up -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 10

# Check service health
echo "🔍 Checking service health..."

# Prometheus
if curl -s http://localhost:9090/-/healthy > /dev/null; then
    echo "✅ Prometheus is healthy"
else
    echo "❌ Prometheus is not responding"
fi

# Grafana
if curl -s http://localhost:3000/api/health > /dev/null; then
    echo "✅ Grafana is healthy"
else
    echo "❌ Grafana is not responding"
fi

# Alertmanager
if curl -s http://localhost:9093/-/healthy > /dev/null; then
    echo "✅ Alertmanager is healthy"
else
    echo "❌ Alertmanager is not responding"
fi

echo ""
echo "🎉 Monitoring infrastructure is ready!"
echo ""
echo "📊 Access URLs:"
echo "  - Prometheus: http://localhost:9090"
echo "  - Grafana: http://localhost:3000 (admin/admin123)"
echo "  - Alertmanager: http://localhost:9093"
echo ""
echo "🔧 Next steps:"
echo "  1. Start the main application: docker compose up -d"
echo "  2. Configure Grafana dashboards (auto-provisioned)"
echo "  3. Set up Slack webhook in alertmanager.yml"
echo "  4. Configure email SMTP settings in alertmanager.yml"
echo ""
echo "📈 Grafana dashboards will be automatically loaded from:"
echo "  - monitoring/grafana/dashboards/"
echo ""
echo "🚨 Alert rules are configured in:"
echo "  - monitoring/alert_rules.yml"
