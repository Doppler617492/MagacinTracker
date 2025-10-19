"""
AI Anomaly Detection Service
Manhattan Active WMS - Phase 4
"""
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import and_, select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.ai_models import AIAnomaly
from ..models.locations import Location, ArticleLocation
from ..models.zaduznica import ZaduznicaStavka
from ..models.enums import AnomalySeverity, AnomalyStatus, AuditAction


class AIAnomalyDetectionService:
    """
    Anomaly detection for:
    1. Stock drift - bin stock frequently mismatches after operations
    2. Scan mismatch spikes - high error rate in barcode scanning
    3. Task latency spikes - P95 execution time increased significantly
    """
    
    # Thresholds
    STOCK_DRIFT_THRESHOLD = 0.20  # 20% error rate in 7 days
    SCAN_MISMATCH_THRESHOLD = 0.15  # 15% mismatch rate in shift
    TASK_LATENCY_SPIKE_THRESHOLD = 0.30  # 30% increase in P95 time
    
    @staticmethod
    async def detect_stock_drift_anomalies(
        db: AsyncSession,
        magacin_id: Optional[uuid.UUID] = None
    ) -> List[AIAnomaly]:
        """
        Detect bins with frequent stock discrepancies
        
        Logic:
            - Get bins with cycle counts in last 7 days
            - Calculate error rate (variance / system quantity)
            - Flag if error rate > 20%
        """
        since_date = datetime.now(timezone.utc) - timedelta(days=7)
        
        # Query cycle count items with variances
        from ..models.locations import CycleCountItem
        query = select(
            CycleCountItem.location_id,
            func.count(CycleCountItem.id).label('count_total'),
            func.sum(
                func.abs(CycleCountItem.variance)
            ).label('total_variance'),
            func.sum(CycleCountItem.system_quantity).label('total_system')
        ).where(
            and_(
                CycleCountItem.counted_at >= since_date,
                CycleCountItem.variance.isnot(None)
            )
        ).group_by(CycleCountItem.location_id)
        
        result = await db.execute(query)
        location_stats = result.all()
        
        anomalies = []
        
        for stat in location_stats:
            if stat.total_system == 0:
                continue
            
            error_rate = float(stat.total_variance) / float(stat.total_system)
            
            if error_rate > AIAnomalyDetectionService.STOCK_DRIFT_THRESHOLD:
                # Get location details
                location = await db.get(Location, stat.location_id)
                if not location:
                    continue
                
                # Determine severity
                if error_rate > 0.5:
                    severity = AnomalySeverity.CRITICAL
                elif error_rate > 0.35:
                    severity = AnomalySeverity.HIGH
                elif error_rate > 0.25:
                    severity = AnomalySeverity.MEDIUM
                else:
                    severity = AnomalySeverity.LOW
                
                # Create anomaly
                anomaly = AIAnomaly(
                    type='stock_drift',
                    severity=severity,
                    status=AnomalyStatus.NEW,
                    entity_type='location',
                    entity_id=location.id,
                    title=f'Odstupanje zaliha u {location.code}',
                    description=f'Lokacija {location.code} ima {error_rate*100:.1f}% greške u poslednjih 7 dana.',
                    details={
                        'location_code': location.code,
                        'error_rate': error_rate,
                        'count_total': stat.count_total,
                        'total_variance': float(stat.total_variance),
                        'period_days': 7
                    },
                    confidence=Decimal('0.85')
                )
                db.add(anomaly)
                anomalies.append(anomaly)
        
        if anomalies:
            await db.commit()
            
            # Audit log
            from ..models.audit import AuditLog
            audit = AuditLog(
                user_id=None,  # System
                action=AuditAction.AI_ANOMALY_DETECTED,
                entity_type='ai_anomaly',
                entity_id=None,
                details={
                    'type': 'stock_drift',
                    'count': len(anomalies)
                }
            )
            db.add(audit)
            await db.commit()
        
        return anomalies
    
    @staticmethod
    async def detect_scan_mismatch_anomalies(
        db: AsyncSession,
        hours_window: int = 4
    ) -> List[AIAnomaly]:
        """
        Detect scan mismatch spikes in recent shifts
        
        Logic:
            - Get scan audit logs from last 4 hours
            - Calculate mismatch rate
            - Flag if rate > 15%
        """
        since_time = datetime.now(timezone.utc) - timedelta(hours=hours_window)
        
        # Query audit logs for scan events
        from ..models.audit import AuditLog
        query = select(
            func.count(AuditLog.id).label('total_scans'),
            func.sum(
                func.case(
                    (AuditLog.action == 'SCAN_MISMATCH', 1),
                    else_=0
                )
            ).label('mismatch_count')
        ).where(
            and_(
                AuditLog.created_at >= since_time,
                AuditLog.action.in_(['SCAN_OK', 'SCAN_MISMATCH'])
            )
        )
        
        result = await db.execute(query)
        stats = result.one()
        
        anomalies = []
        
        if stats.total_scans > 0:
            mismatch_rate = float(stats.mismatch_count) / float(stats.total_scans)
            
            if mismatch_rate > AIAnomalyDetectionService.SCAN_MISMATCH_THRESHOLD:
                # Determine severity
                if mismatch_rate > 0.3:
                    severity = AnomalySeverity.CRITICAL
                elif mismatch_rate > 0.25:
                    severity = AnomalySeverity.HIGH
                elif mismatch_rate > 0.2:
                    severity = AnomalySeverity.MEDIUM
                else:
                    severity = AnomalySeverity.LOW
                
                anomaly = AIAnomaly(
                    type='scan_mismatch',
                    severity=severity,
                    status=AnomalyStatus.NEW,
                    entity_type='system',
                    entity_id=None,
                    title=f'Povećan broj grešaka skeniranja',
                    description=f'Stopa grešaka skeniranja: {mismatch_rate*100:.1f}% u poslednjih {hours_window}h.',
                    details={
                        'mismatch_rate': mismatch_rate,
                        'total_scans': stats.total_scans,
                        'mismatch_count': stats.mismatch_count,
                        'hours_window': hours_window
                    },
                    confidence=Decimal('0.90')
                )
                db.add(anomaly)
                anomalies.append(anomaly)
        
        if anomalies:
            await db.commit()
            
            # Audit log
            from ..models.audit import AuditLog
            audit = AuditLog(
                user_id=None,
                action=AuditAction.AI_ANOMALY_DETECTED,
                entity_type='ai_anomaly',
                entity_id=None,
                details={
                    'type': 'scan_mismatch',
                    'count': len(anomalies)
                }
            )
            db.add(audit)
            await db.commit()
        
        return anomalies
    
    @staticmethod
    async def detect_task_latency_anomalies(
        db: AsyncSession,
        shift_id: Optional[uuid.UUID] = None
    ) -> List[AIAnomaly]:
        """
        Detect task latency spikes (P95 increased > 30%)
        
        Logic:
            - Compare current shift P95 to 7-day average
            - Flag if increase > 30%
        """
        # Get P95 for current shift (last 4 hours)
        current_window = datetime.now(timezone.utc) - timedelta(hours=4)
        
        query = select(
            func.percentile_cont(0.95).within_group(
                ZaduznicaStavka.duration_seconds
            ).label('p95_current')
        ).where(
            and_(
                ZaduznicaStavka.completed_at >= current_window,
                ZaduznicaStavka.duration_seconds.isnot(None),
                ZaduznicaStavka.status == 'done'
            )
        )
        result = await db.execute(query)
        p95_current = result.scalar()
        
        if not p95_current:
            return []  # No data
        
        # Get P95 for last 7 days (baseline)
        baseline_window = datetime.now(timezone.utc) - timedelta(days=7)
        
        query = select(
            func.percentile_cont(0.95).within_group(
                ZaduznicaStavka.duration_seconds
            ).label('p95_baseline')
        ).where(
            and_(
                ZaduznicaStavka.completed_at >= baseline_window,
                ZaduznicaStavka.completed_at < current_window,
                ZaduznicaStavka.duration_seconds.isnot(None),
                ZaduznicaStavka.status == 'done'
            )
        )
        result = await db.execute(query)
        p95_baseline = result.scalar()
        
        if not p95_baseline or p95_baseline == 0:
            return []
        
        # Calculate increase
        increase_pct = (float(p95_current) - float(p95_baseline)) / float(p95_baseline)
        
        anomalies = []
        
        if increase_pct > AIAnomalyDetectionService.TASK_LATENCY_SPIKE_THRESHOLD:
            # Determine severity
            if increase_pct > 0.7:
                severity = AnomalySeverity.CRITICAL
            elif increase_pct > 0.5:
                severity = AnomalySeverity.HIGH
            elif increase_pct > 0.4:
                severity = AnomalySeverity.MEDIUM
            else:
                severity = AnomalySeverity.LOW
            
            anomaly = AIAnomaly(
                type='task_latency',
                severity=severity,
                status=AnomalyStatus.NEW,
                entity_type='system',
                entity_id=None,
                title=f'Povećano vreme izvršavanja zadataka',
                description=f'P95 vreme povećano za {increase_pct*100:.1f}% u odnosu na prethodnu nedelju.',
                details={
                    'p95_current': float(p95_current),
                    'p95_baseline': float(p95_baseline),
                    'increase_pct': increase_pct,
                    'hours_window': 4,
                    'baseline_days': 7
                },
                confidence=Decimal('0.80')
            )
            db.add(anomaly)
            anomalies.append(anomaly)
        
        if anomalies:
            await db.commit()
            
            # Audit log
            from ..models.audit import AuditLog
            audit = AuditLog(
                user_id=None,
                action=AuditAction.AI_ANOMALY_DETECTED,
                entity_type='ai_anomaly',
                entity_id=None,
                details={
                    'type': 'task_latency',
                    'count': len(anomalies)
                }
            )
            db.add(audit)
            await db.commit()
        
        return anomalies
    
    @staticmethod
    async def acknowledge_anomaly(
        db: AsyncSession,
        anomaly_id: uuid.UUID,
        user_id: uuid.UUID
    ) -> bool:
        """Mark anomaly as acknowledged"""
        anomaly = await db.get(AIAnomaly, anomaly_id)
        if not anomaly or anomaly.status != AnomalyStatus.NEW:
            return False
        
        anomaly.status = AnomalyStatus.ACKNOWLEDGED
        anomaly.acknowledged_by_id = user_id
        anomaly.acknowledged_at = datetime.now(timezone.utc)
        
        # Audit log
        from ..models.audit import AuditLog
        audit = AuditLog(
            user_id=user_id,
            action=AuditAction.AI_ANOMALY_ACK,
            entity_type='ai_anomaly',
            entity_id=anomaly_id,
            details={
                'type': anomaly.type,
                'severity': anomaly.severity.value
            }
        )
        db.add(audit)
        
        await db.commit()
        return True
    
    @staticmethod
    async def resolve_anomaly(
        db: AsyncSession,
        anomaly_id: uuid.UUID,
        user_id: uuid.UUID,
        resolution_note: str
    ) -> bool:
        """Mark anomaly as resolved"""
        anomaly = await db.get(AIAnomaly, anomaly_id)
        if not anomaly:
            return False
        
        anomaly.status = AnomalyStatus.RESOLVED
        anomaly.resolved_by_id = user_id
        anomaly.resolved_at = datetime.now(timezone.utc)
        anomaly.resolution_note = resolution_note
        
        # Audit log
        from ..models.audit import AuditLog
        audit = AuditLog(
            user_id=user_id,
            action=AuditAction.AI_ANOMALY_RESOLVED,
            entity_type='ai_anomaly',
            entity_id=anomaly_id,
            details={
                'type': anomaly.type,
                'resolution_note': resolution_note
            }
        )
        db.add(audit)
        
        await db.commit()
        return True

