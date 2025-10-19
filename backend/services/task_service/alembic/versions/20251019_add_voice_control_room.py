"""Add Voice Picking, Global Control Room, Device Health, Predictive Maintenance

Revision ID: 20251019_voice_control
Revises: 20251019_vision_robotics
Create Date: 2025-10-19 23:30:00.000000

Sprint WMS Phase 8 - Voice + Global Control Room (Real Data Only)
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB, ENUM

# revision identifiers
revision = '20251019_voice_control'
down_revision = '20251019_vision_robotics'
branch_labels = None
depends_on = None


def upgrade():
    # Create device type enum
    device_type_enum = ENUM(
        'scanner',
        'camera',
        'door_controller',
        'edge_gateway',
        'indicator',
        'amr',
        name='device_type_enum',
        create_type=True
    )
    device_type_enum.create(op.get_bind(), checkfirst=True)
    
    # Create predictive alert status enum
    predictive_alert_status_enum = ENUM(
        'new',
        'acknowledged',
        'resolved',
        'false_positive',
        name='predictive_alert_status_enum',
        create_type=True
    )
    predictive_alert_status_enum.create(op.get_bind(), checkfirst=True)
    
    # Create device_health table (real telemetry from MQTT/Kafka)
    op.create_table(
        'device_health',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('device_id', sa.String(128), nullable=False, unique=True, index=True),
        sa.Column('device_type', device_type_enum, nullable=False),
        sa.Column('warehouse_id', UUID(as_uuid=True), sa.ForeignKey('magacin.id'), nullable=True, index=True),
        sa.Column('last_seen_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('cpu_pct', sa.Numeric(5, 2), nullable=True),
        sa.Column('mem_pct', sa.Numeric(5, 2), nullable=True),
        sa.Column('temp_c', sa.Numeric(5, 2), nullable=True),
        sa.Column('battery_pct', sa.Integer(), nullable=True),
        sa.Column('uptime_s', sa.Integer(), nullable=True),
        sa.Column('firmware_ver', sa.String(64), nullable=True),
        sa.Column('ip_address', sa.String(64), nullable=True),
        sa.Column('metadata', JSONB, nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
    )
    
    # Create predictive_alerts table (maintenance forecasting)
    op.create_table(
        'predictive_alerts',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('device_id', sa.String(128), nullable=False, index=True),
        sa.Column('alert_type', sa.String(64), nullable=False, index=True),  # rising_temp, frequent_disconnect, battery_degradation
        sa.Column('severity', sa.String(32), nullable=False),  # warning, critical
        sa.Column('confidence', sa.Numeric(3, 2), nullable=False),  # 0.0-1.0
        sa.Column('first_seen', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('last_seen', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('details', JSONB, nullable=False, server_default='{}'),
        sa.Column('suggested_action', sa.String(500), nullable=True),
        sa.Column('status', predictive_alert_status_enum, nullable=False, default='new', index=True),
        sa.Column('ack_by_id', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('ack_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
    )
    
    # Create voice_command_log table (voice picking audit)
    op.create_table(
        'voice_command_log',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False, index=True),
        sa.Column('task_item_id', UUID(as_uuid=True), sa.ForeignKey('zaduznica_stavka.id'), nullable=True, index=True),
        sa.Column('command_text', sa.String(255), nullable=False),
        sa.Column('recognized_intent', sa.String(64), nullable=True),  # confirm, next, repeat, stop, quantity
        sa.Column('extracted_value', sa.String(128), nullable=True),
        sa.Column('confidence', sa.Numeric(3, 2), nullable=True),
        sa.Column('success', sa.Boolean(), nullable=False),
        sa.Column('error_message', sa.String(500), nullable=True),
        sa.Column('processing_time_ms', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
    )
    
    # Create indexes
    op.create_index('idx_device_health_warehouse', 'device_health', ['warehouse_id', 'device_type'])
    op.create_index('idx_device_health_last_seen', 'device_health', ['last_seen_at'])
    op.create_index('idx_predictive_alerts_status', 'predictive_alerts', ['status', 'severity'])
    op.create_index('idx_predictive_alerts_device', 'predictive_alerts', ['device_id'])
    op.create_index('idx_voice_command_user', 'voice_command_log', ['user_id', 'created_at'])


def downgrade():
    # Drop tables
    op.drop_table('voice_command_log')
    op.drop_table('predictive_alerts')
    op.drop_table('device_health')
    
    # Drop enums
    predictive_alert_status_enum = ENUM(name='predictive_alert_status_enum')
    predictive_alert_status_enum.drop(op.get_bind(), checkfirst=True)
    
    device_type_enum = ENUM(name='device_type_enum')
    device_type_enum.drop(op.get_bind(), checkfirst=True)

