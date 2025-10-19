"""Add AI Intelligence Layer tables and feature flags

Revision ID: 20251019_ai_layer
Revises: 20251019_locations
Create Date: 2025-10-19 18:00:00.000000

Sprint WMS Phase 4 - AI Intelligence Layer
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB, ENUM

# revision identifiers
revision = '20251019_ai_layer'
down_revision = '20251019_locations'
branch_labels = None
depends_on = None


def upgrade():
    # Create anomaly severity enum
    anomaly_severity_enum = ENUM(
        'low',
        'medium',
        'high',
        'critical',
        name='anomaly_severity_enum',
        create_type=True
    )
    anomaly_severity_enum.create(op.get_bind(), checkfirst=True)
    
    # Create anomaly status enum
    anomaly_status_enum = ENUM(
        'new',
        'acknowledged',
        'in_progress',
        'resolved',
        'false_positive',
        name='anomaly_status_enum',
        create_type=True
    )
    anomaly_status_enum.create(op.get_bind(), checkfirst=True)
    
    # Create ai_anomalies table
    op.create_table(
        'ai_anomalies',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('type', sa.String(64), nullable=False, index=True),  # stock_drift, scan_mismatch, task_latency
        sa.Column('severity', anomaly_severity_enum, nullable=False, index=True),
        sa.Column('status', anomaly_status_enum, nullable=False, server_default='new', index=True),
        sa.Column('entity_type', sa.String(64), nullable=True),  # location, article, task, worker
        sa.Column('entity_id', UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('details', JSONB, nullable=False, server_default='{}'),
        sa.Column('confidence', sa.Numeric(3, 2), nullable=False, default=1.0),  # 0.0 to 1.0
        sa.Column('detected_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('acknowledged_by_id', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('acknowledged_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolved_by_id', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolution_note', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
    )
    
    # Create ai_bin_suggestions table
    op.create_table(
        'ai_bin_suggestions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('receiving_item_id', UUID(as_uuid=True), sa.ForeignKey('receiving_item.id'), nullable=False, index=True),
        sa.Column('artikal_id', UUID(as_uuid=True), sa.ForeignKey('artikal.id'), nullable=False),
        sa.Column('suggested_location_id', UUID(as_uuid=True), sa.ForeignKey('locations.id'), nullable=False),
        sa.Column('rank', sa.Integer(), nullable=False),  # 1, 2, 3
        sa.Column('score', sa.Numeric(5, 2), nullable=False),  # 0-100
        sa.Column('confidence', sa.Numeric(3, 2), nullable=False),  # 0.0-1.0
        sa.Column('reason', sa.String(500), nullable=True),
        sa.Column('details', JSONB, nullable=False, server_default='{}'),
        sa.Column('accepted', sa.Boolean(), nullable=True),  # NULL = not acted on, TRUE/FALSE
        sa.Column('accepted_by_id', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('accepted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('rejection_reason', sa.String(500), nullable=True),
        sa.Column('model_version', sa.String(32), nullable=False, default='heuristic_v1'),
        sa.Column('latency_ms', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
    )
    
    # Create ai_restock_suggestions table
    op.create_table(
        'ai_restock_suggestions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('artikal_id', UUID(as_uuid=True), sa.ForeignKey('artikal.id'), nullable=False, index=True),
        sa.Column('magacin_id', UUID(as_uuid=True), sa.ForeignKey('magacin.id'), nullable=False),
        sa.Column('current_stock', sa.Numeric(12, 3), nullable=False),
        sa.Column('suggested_quantity', sa.Numeric(12, 3), nullable=False),
        sa.Column('target_zone', sa.String(32), nullable=True),
        sa.Column('target_location_id', UUID(as_uuid=True), sa.ForeignKey('locations.id'), nullable=True),
        sa.Column('confidence', sa.Numeric(3, 2), nullable=False),
        sa.Column('reason', sa.String(500), nullable=True),
        sa.Column('details', JSONB, nullable=False, server_default='{}'),  # avg_daily_usage, lead_time_days, safety_stock, etc.
        sa.Column('horizon_days', sa.Integer(), nullable=False, default=7),
        sa.Column('deadline', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(32), nullable=False, default='pending', index=True),  # pending, approved, rejected, executed
        sa.Column('approved_by_id', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('rejection_reason', sa.String(500), nullable=True),
        sa.Column('trebovanje_id', UUID(as_uuid=True), sa.ForeignKey('trebovanje.id'), nullable=True),  # Created internal requisition
        sa.Column('model_version', sa.String(32), nullable=False, default='ema_v1'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
    )
    
    # Create ai_model_metadata table (track model versions and performance)
    op.create_table(
        'ai_model_metadata',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('model_name', sa.String(64), nullable=False, index=True),
        sa.Column('model_version', sa.String(32), nullable=False),
        sa.Column('model_type', sa.String(64), nullable=False),  # bin_allocation, restocking, anomaly_detection
        sa.Column('parameters', JSONB, nullable=False, server_default='{}'),
        sa.Column('performance_metrics', JSONB, nullable=False, server_default='{}'),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('activated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deactivated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.UniqueConstraint('model_name', 'model_version', name='uq_model_name_version')
    )
    
    # Create indexes
    op.create_index('idx_ai_anomalies_type_status', 'ai_anomalies', ['type', 'status'])
    op.create_index('idx_ai_anomalies_detected_at', 'ai_anomalies', ['detected_at'])
    op.create_index('idx_ai_bin_suggestions_receiving', 'ai_bin_suggestions', ['receiving_item_id'])
    op.create_index('idx_ai_bin_suggestions_accepted', 'ai_bin_suggestions', ['accepted'])
    op.create_index('idx_ai_restock_status', 'ai_restock_suggestions', ['status'])
    op.create_index('idx_ai_restock_deadline', 'ai_restock_suggestions', ['deadline'])
    
    # Extend audit_log with AI events (if not using enum, just document)
    # AuditAction enum should be extended with:
    # AI_BIN_SUGGESTED, AI_BIN_ACCEPTED, AI_BIN_REJECTED
    # AI_RESTOCK_SUGGESTED, AI_RESTOCK_APPROVED, AI_RESTOCK_REJECTED
    # AI_ANOMALY_DETECTED, AI_ANOMALY_ACK, AI_ANOMALY_RESOLVED


def downgrade():
    # Drop tables in reverse order
    op.drop_table('ai_model_metadata')
    op.drop_table('ai_restock_suggestions')
    op.drop_table('ai_bin_suggestions')
    op.drop_table('ai_anomalies')
    
    # Drop enums
    anomaly_status_enum = ENUM(name='anomaly_status_enum')
    anomaly_status_enum.drop(op.get_bind(), checkfirst=True)
    
    anomaly_severity_enum = ENUM(name='anomaly_severity_enum')
    anomaly_severity_enum.drop(op.get_bind(), checkfirst=True)

