"""Add Vision AI and Robotics Integration

Revision ID: 20251019_vision_robotics
Revises: 20251019_rfid_locations
Create Date: 2025-10-19 23:00:00.000000

Sprint WMS Phase 7 - Vision AI + Robotics
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB, ENUM

# revision identifiers
revision = '20251019_vision_robotics'
down_revision = '20251019_rfid_locations'
branch_labels = None
depends_on = None


def upgrade():
    # Create indicator type enum
    indicator_type_enum = ENUM(
        'pick',
        'put',
        'alert',
        'guidance',
        name='indicator_type_enum',
        create_type=True
    )
    indicator_type_enum.create(op.get_bind(), checkfirst=True)
    
    # Create indicator status enum
    indicator_status_enum = ENUM(
        'off',
        'on',
        'blink',
        'error',
        name='indicator_status_enum',
        create_type=True
    )
    indicator_status_enum.create(op.get_bind(), checkfirst=True)
    
    # Create AMR task type enum
    amr_task_type_enum = ENUM(
        'pick',
        'putaway',
        'move',
        'transport',
        name='amr_task_type_enum',
        create_type=True
    )
    amr_task_type_enum.create(op.get_bind(), checkfirst=True)
    
    # Create AMR task status enum
    amr_task_status_enum = ENUM(
        'pending',
        'assigned',
        'in_progress',
        'completed',
        'error',
        'cancelled',
        name='amr_task_status_enum',
        create_type=True
    )
    amr_task_status_enum.create(op.get_bind(), checkfirst=True)
    
    # Create vision_audit table
    op.create_table(
        'vision_audit',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('task_item_id', UUID(as_uuid=True), sa.ForeignKey('zaduznica_stavka.id'), nullable=True, index=True),
        sa.Column('location_id', UUID(as_uuid=True), sa.ForeignKey('location_v2.id'), nullable=True),
        sa.Column('article_id', UUID(as_uuid=True), sa.ForeignKey('artikal.id'), nullable=True),
        sa.Column('image_path', sa.String(500), nullable=False),
        sa.Column('detected_qty', sa.Numeric(12, 3), nullable=True),
        sa.Column('confidence', sa.Numeric(3, 2), nullable=False),  # 0.0-1.0
        sa.Column('damaged_flag', sa.Boolean(), nullable=False, default=False),
        sa.Column('model_version', sa.String(32), nullable=False),
        sa.Column('processing_time_ms', sa.Integer(), nullable=True),
        sa.Column('details', JSONB, nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
    )
    
    # Create location_indicator table (Pick-to-Light / Put-to-Light)
    op.create_table(
        'location_indicator',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('location_id', UUID(as_uuid=True), sa.ForeignKey('location_v2.id'), nullable=False, index=True),
        sa.Column('indicator_type', indicator_type_enum, nullable=False),
        sa.Column('status', indicator_status_enum, nullable=False, default='off'),
        sa.Column('color', sa.String(16), nullable=True),  # red, green, blue, white
        sa.Column('device_addr', sa.String(128), nullable=True),  # GPIO / Modbus / MQTT address
        sa.Column('last_command', sa.String(32), nullable=True),
        sa.Column('last_update', sa.DateTime(timezone=True), nullable=True),
        sa.Column('metadata', JSONB, nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.UniqueConstraint('location_id', 'indicator_type', name='uq_location_indicator')
    )
    
    # Create amr_task table (Autonomous Mobile Robot tasks)
    op.create_table(
        'amr_task',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('amr_id', sa.String(64), nullable=True, index=True),
        sa.Column('task_type', amr_task_type_enum, nullable=False),
        sa.Column('from_location_id', UUID(as_uuid=True), sa.ForeignKey('location_v2.id'), nullable=True),
        sa.Column('to_location_id', UUID(as_uuid=True), sa.ForeignKey('location_v2.id'), nullable=True),
        sa.Column('handling_unit_id', UUID(as_uuid=True), sa.ForeignKey('handling_unit.id'), nullable=True),
        sa.Column('status', amr_task_status_enum, nullable=False, default='pending', index=True),
        sa.Column('priority', sa.Integer(), nullable=False, default=5),
        sa.Column('assigned_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_message', sa.String(500), nullable=True),
        sa.Column('metadata', JSONB, nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
    )
    
    # Create indexes
    op.create_index('idx_vision_audit_task_item', 'vision_audit', ['task_item_id'])
    op.create_index('idx_vision_audit_location', 'vision_audit', ['location_id'])
    op.create_index('idx_location_indicator_location', 'location_indicator', ['location_id'])
    op.create_index('idx_amr_task_status', 'amr_task', ['status', 'priority'])
    op.create_index('idx_amr_task_amr_id', 'amr_task', ['amr_id'])


def downgrade():
    # Drop tables
    op.drop_table('amr_task')
    op.drop_table('location_indicator')
    op.drop_table('vision_audit')
    
    # Drop enums
    amr_task_status_enum = ENUM(name='amr_task_status_enum')
    amr_task_status_enum.drop(op.get_bind(), checkfirst=True)
    
    amr_task_type_enum = ENUM(name='amr_task_type_enum')
    amr_task_type_enum.drop(op.get_bind(), checkfirst=True)
    
    indicator_status_enum = ENUM(name='indicator_status_enum')
    indicator_status_enum.drop(op.get_bind(), checkfirst=True)
    
    indicator_type_enum = ENUM(name='indicator_type_enum')
    indicator_type_enum.drop(op.get_bind(), checkfirst=True)

