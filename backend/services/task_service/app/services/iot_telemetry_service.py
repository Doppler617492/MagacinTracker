"""
Telemetry Service - Sensor monitoring & alert rules
Manhattan Active WMS - Phase 5
"""
import uuid
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import and_, select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.iot_models import TelemetryData, TelemetryAlert
from ..models.enums import TelemetryAlertSeverity, AuditAction


class TelemetryService:
    """
    Telemetry monitoring service:
    - Temperature, humidity, vibration monitoring
    - Zebra battery tracking
    - Ping/latency monitoring
    - Alert rule engine
    """
    
    # Alert thresholds (configurable per warehouse)
    THRESHOLDS = {
        'temperature': {
            'cold_zone_min': 2.0,    # °C
            'cold_zone_max': 8.0,    # °C
            'normal_max': 30.0,      # °C
        },
        'humidity': {
            'max': 80.0,  # %
        },
        'battery': {
            'low': 15,     # %
            'critical': 10, # %
        },
        'ping': {
            'slow': 200,      # ms
            'timeout': 1000,  # ms
        }
    }
    
    @staticmethod
    async def report_telemetry(
        db: AsyncSession,
        device_id: str,
        device_type: Optional[str] = None,
        zone: Optional[str] = None,
        temperature: Optional[float] = None,
        humidity: Optional[float] = None,
        vibration: Optional[float] = None,
        battery_percentage: Optional[int] = None,
        ping_ms: Optional[int] = None,
        extra_metrics: dict = None
    ) -> TelemetryData:
        """
        Record telemetry data and check alert rules
        
        Returns:
            TelemetryData record
        """
        # Create telemetry record
        telemetry = TelemetryData(
            device_id=device_id,
            device_type=device_type,
            zone=zone,
            temperature=Decimal(str(temperature)) if temperature is not None else None,
            humidity=Decimal(str(humidity)) if humidity is not None else None,
            vibration=Decimal(str(vibration)) if vibration is not None else None,
            battery_percentage=battery_percentage,
            ping_ms=ping_ms,
            metrics=extra_metrics or {},
            timestamp=datetime.now(timezone.utc)
        )
        db.add(telemetry)
        
        # Check alert rules
        alerts = []
        
        # Temperature alerts
        if temperature is not None:
            if zone and 'COLD' in zone.upper():
                # Cold zone
                if temperature < TelemetryService.THRESHOLDS['temperature']['cold_zone_min']:
                    alerts.append({
                        'type': 'temp_low',
                        'severity': TelemetryAlertSeverity.CRITICAL,
                        'message': f'Temperatura ispod praga u hladnjači: {temperature}°C',
                        'threshold': TelemetryService.THRESHOLDS['temperature']['cold_zone_min'],
                        'actual': temperature
                    })
                elif temperature > TelemetryService.THRESHOLDS['temperature']['cold_zone_max']:
                    alerts.append({
                        'type': 'temp_high',
                        'severity': TelemetryAlertSeverity.CRITICAL,
                        'message': f'Temperatura iznad praga u hladnjači: {temperature}°C',
                        'threshold': TelemetryService.THRESHOLDS['temperature']['cold_zone_max'],
                        'actual': temperature
                    })
            else:
                # Normal zone
                if temperature > TelemetryService.THRESHOLDS['temperature']['normal_max']:
                    alerts.append({
                        'type': 'temp_high',
                        'severity': TelemetryAlertSeverity.WARNING,
                        'message': f'Temperatura visoka: {temperature}°C',
                        'threshold': TelemetryService.THRESHOLDS['temperature']['normal_max'],
                        'actual': temperature
                    })
        
        # Humidity alerts
        if humidity is not None and humidity > TelemetryService.THRESHOLDS['humidity']['max']:
            alerts.append({
                'type': 'humidity_high',
                'severity': TelemetryAlertSeverity.WARNING,
                'message': f'Vlažnost visoka: {humidity}%',
                'threshold': TelemetryService.THRESHOLDS['humidity']['max'],
                'actual': humidity
            })
        
        # Battery alerts (Zebra devices)
        if battery_percentage is not None:
            if battery_percentage <= TelemetryService.THRESHOLDS['battery']['critical']:
                alerts.append({
                    'type': 'battery_critical',
                    'severity': TelemetryAlertSeverity.CRITICAL,
                    'message': f'Baterija kritično niska: {battery_percentage}%',
                    'threshold': TelemetryService.THRESHOLDS['battery']['critical'],
                    'actual': battery_percentage
                })
            elif battery_percentage <= TelemetryService.THRESHOLDS['battery']['low']:
                alerts.append({
                    'type': 'battery_low',
                    'severity': TelemetryAlertSeverity.WARNING,
                    'message': f'Baterija niska: {battery_percentage}%',
                    'threshold': TelemetryService.THRESHOLDS['battery']['low'],
                    'actual': battery_percentage
                })
        
        # Ping alerts
        if ping_ms is not None:
            if ping_ms >= TelemetryService.THRESHOLDS['ping']['timeout']:
                alerts.append({
                    'type': 'ping_timeout',
                    'severity': TelemetryAlertSeverity.CRITICAL,
                    'message': f'Ping timeout: {ping_ms}ms',
                    'threshold': TelemetryService.THRESHOLDS['ping']['timeout'],
                    'actual': ping_ms
                })
            elif ping_ms >= TelemetryService.THRESHOLDS['ping']['slow']:
                alerts.append({
                    'type': 'ping_slow',
                    'severity': TelemetryAlertSeverity.INFO,
                    'message': f'Ping spor: {ping_ms}ms',
                    'threshold': TelemetryService.THRESHOLDS['ping']['slow'],
                    'actual': ping_ms
                })
        
        # Create alerts
        for alert_data in alerts:
            # Check if similar alert already active
            query = select(TelemetryAlert).where(
                and_(
                    TelemetryAlert.device_id == device_id,
                    TelemetryAlert.alert_type == alert_data['type'],
                    TelemetryAlert.is_active == True
                )
            )
            result = await db.execute(query)
            existing = result.scalar_one_or_none()
            
            if not existing:
                # Create new alert
                alert = TelemetryAlert(
                    device_id=device_id,
                    alert_type=alert_data['type'],
                    severity=alert_data['severity'],
                    message=alert_data['message'],
                    details={'zone': zone, 'device_type': device_type},
                    threshold_value=Decimal(str(alert_data['threshold'])),
                    actual_value=Decimal(str(alert_data['actual'])),
                    raised_at=datetime.now(timezone.utc),
                    is_active=True
                )
                db.add(alert)
                
                # Audit
                from ..models.audit import AuditLog
                audit = AuditLog(
                    user_id=None,
                    action=AuditAction.TELEMETRY_ALERT_RAISED,
                    entity_type='telemetry_alert',
                    entity_id=alert.id,
                    details={
                        'device_id': device_id,
                        'alert_type': alert_data['type'],
                        'severity': alert_data['severity'].value,
                        'message': alert_data['message']
                    }
                )
                db.add(audit)
        
        # Audit telemetry report
        from ..models.audit import AuditLog
        audit = AuditLog(
            user_id=None,
            action=AuditAction.TELEMETRY_REPORTED,
            entity_type='telemetry_data',
            entity_id=telemetry.id,
            details={
                'device_id': device_id,
                'zone': zone,
                'alerts_raised': len(alerts)
            }
        )
        db.add(audit)
        
        await db.commit()
        await db.refresh(telemetry)
        
        return telemetry
    
    @staticmethod
    async def acknowledge_alert(
        db: AsyncSession,
        alert_id: uuid.UUID,
        user_id: uuid.UUID
    ) -> bool:
        """Acknowledge telemetry alert"""
        alert = await db.get(TelemetryAlert, alert_id)
        if not alert or not alert.is_active:
            return False
        
        alert.acknowledged_by_id = user_id
        alert.acknowledged_at = datetime.now(timezone.utc)
        alert.is_active = False
        alert.resolved_at = datetime.now(timezone.utc)
        
        # Audit
        from ..models.audit import AuditLog
        audit = AuditLog(
            user_id=user_id,
            action=AuditAction.TELEMETRY_ALERT_ACKED,
            entity_type='telemetry_alert',
            entity_id=alert_id,
            details={
                'device_id': alert.device_id,
                'alert_type': alert.alert_type
            }
        )
        db.add(audit)
        
        await db.commit()
        return True
    
    @staticmethod
    async def get_latest_telemetry(
        db: AsyncSession,
        device_id: str
    ) -> Optional[TelemetryData]:
        """Get latest telemetry for device"""
        query = select(TelemetryData).where(
            TelemetryData.device_id == device_id
        ).order_by(desc(TelemetryData.timestamp)).limit(1)
        
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_active_alerts(
        db: AsyncSession,
        device_id: Optional[str] = None,
        severity: Optional[TelemetryAlertSeverity] = None
    ) -> List[TelemetryAlert]:
        """Get active alerts"""
        query = select(TelemetryAlert).where(TelemetryAlert.is_active == True)
        
        if device_id:
            query = query.where(TelemetryAlert.device_id == device_id)
        if severity:
            query = query.where(TelemetryAlert.severity == severity)
        
        query = query.order_by(desc(TelemetryAlert.raised_at))
        
        result = await db.execute(query)
        return result.scalars().all()

