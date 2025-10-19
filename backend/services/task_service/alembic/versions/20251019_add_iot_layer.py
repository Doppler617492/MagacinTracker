"""Add IoT Layer (RFID, Doors, Camera, Telemetry, Vision)

Revision ID: 20251019_iot_layer
Revises: 20251019_ai_layer
Create Date: 2025-10-19 20:00:00.000000

Sprint WMS Phase 5 - IoT Integration Layer
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB, ENUM

# revision identifiers
revision = '20251019_iot_layer'
down_revision = '20251019_ai_layer'
branch_labels = None
depends_on = None


def upgrade():
    # Create RFID event type enum
    rfid_event_type_enum = ENUM(
        'entry',
        'exit',
        'read',
        'write',
        name='rfid_event_type_enum',
        create_type=True
    )
    rfid_event_type_enum.create(op.get_bind(), checkfirst=True)
    
    # Create door status enum
    door_status_enum = ENUM(
        'open',
        'closed',
        'opening',
        'closing',
        'stopped',
        'error',
        name='door_status_enum',
        create_type=True
    )
    door_status_enum.create(op.get_bind(), checkfirst=True)
    
    # Create telemetry alert severity enum
    telemetry_alert_severity_enum = ENUM(
        'info',
        'warning',
        'critical',
        name='telemetry_alert_severity_enum',
        create_type=True
    )
    telemetry_alert_severity_enum.create(op.get_bind(), checkfirst=True)
    
    # Create rfid_events table
    op.create_table(
        'rfid_events',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('gateway_id', sa.String(64), nullable=False, index=True),
        sa.Column('antenna_id', sa.String(64), nullable=True, index=True),
        sa.Column('tag_id', sa.String(128), nullable=False, index=True),
        sa.Column('event_type', rfid_event_type_enum, nullable=False, default='read'),
        sa.Column('rssi', sa.Integer(), nullable=True),
        sa.Column('zone', sa.String(64), nullable=True, index=True),
        sa.Column('raw_data', JSONB, nullable=False, server_default='{}'),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
    )
    
    # Create rfid_tag_bindings table
    op.create_table(
        'rfid_tag_bindings',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tag_id', sa.String(128), unique=True, nullable=False, index=True),
        sa.Column('entity_type', sa.String(64), nullable=False, index=True),  # prijem, otprema, lokacija
        sa.Column('entity_id', UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('bound_by_id', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('bound_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('unbound_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('metadata', JSONB, nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
    )
    
    # Create doors table
    op.create_table(
        'doors',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('door_id', sa.String(64), unique=True, nullable=False, index=True),
        sa.Column('naziv', sa.String(128), nullable=False),
        sa.Column('location_id', UUID(as_uuid=True), sa.ForeignKey('locations.id'), nullable=True),
        sa.Column('zone', sa.String(64), nullable=True),
        sa.Column('current_status', door_status_enum, nullable=False, default='closed'),
        sa.Column('last_command', sa.String(32), nullable=True),
        sa.Column('last_command_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_command_by_id', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('safety_beam_status', sa.Boolean(), nullable=True),  # True = clear, False = blocked
        sa.Column('radar_detected', sa.Boolean(), nullable=True),
        sa.Column('auto_close_timeout_seconds', sa.Integer(), nullable=False, default=60),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('metadata', JSONB, nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
    )
    
    # Create door_command_log table
    op.create_table(
        'door_command_log',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('door_id', UUID(as_uuid=True), sa.ForeignKey('doors.id'), nullable=False, index=True),
        sa.Column('command', sa.String(32), nullable=False, index=True),  # open, close, stop
        sa.Column('reason', sa.String(255), nullable=True),
        sa.Column('requested_by_id', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('executed_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('success', sa.Boolean(), nullable=True),
        sa.Column('error_message', sa.String(500), nullable=True),
        sa.Column('safety_blocked', sa.Boolean(), nullable=False, default=False),
        sa.Column('latency_ms', sa.Integer(), nullable=True),
        sa.Column('metadata', JSONB, nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
    )
    
    # Create telemetry_data table
    op.create_table(
        'telemetry_data',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('device_id', sa.String(128), nullable=False, index=True),
        sa.Column('device_type', sa.String(64), nullable=True),  # zebra, sensor, gateway
        sa.Column('zone', sa.String(64), nullable=True, index=True),
        sa.Column('temperature', sa.Numeric(5, 2), nullable=True),
        sa.Column('humidity', sa.Numeric(5, 2), nullable=True),
        sa.Column('vibration', sa.Numeric(8, 4), nullable=True),
        sa.Column('battery_percentage', sa.Integer(), nullable=True),
        sa.Column('ping_ms', sa.Integer(), nullable=True),
        sa.Column('metrics', JSONB, nullable=False, server_default='{}'),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
    )
    
    # Create telemetry_alerts table
    op.create_table(
        'telemetry_alerts',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('device_id', sa.String(128), nullable=False, index=True),
        sa.Column('alert_type', sa.String(64), nullable=False, index=True),  # temp_high, battery_low, ping_timeout
        sa.Column('severity', telemetry_alert_severity_enum, nullable=False),
        sa.Column('message', sa.String(255), nullable=False),
        sa.Column('details', JSONB, nullable=False, server_default='{}'),
        sa.Column('threshold_value', sa.Numeric(10, 2), nullable=True),
        sa.Column('actual_value', sa.Numeric(10, 2), nullable=True),
        sa.Column('raised_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('acknowledged_by_id', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('acknowledged_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
    )
    
    # Create vision_count_tasks table
    op.create_table(
        'vision_count_tasks',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('location_id', UUID(as_uuid=True), sa.ForeignKey('locations.id'), nullable=False, index=True),
        sa.Column('artikal_id', UUID(as_uuid=True), sa.ForeignKey('artikal.id'), nullable=True),
        sa.Column('system_quantity', sa.Numeric(12, 3), nullable=True),
        sa.Column('counted_quantity', sa.Numeric(12, 3), nullable=True),
        sa.Column('variance', sa.Numeric(12, 3), nullable=True),
        sa.Column('photo_ids', JSONB, nullable=False, server_default='[]'),  # Array of photo UUIDs
        sa.Column('comment', sa.Text, nullable=True),
        sa.Column('status', sa.String(32), nullable=False, default='pending', index=True),  # pending, submitted, approved, rejected
        sa.Column('assigned_to_id', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('reviewed_by_id', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('review_note', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
    )
    
    # Create photo_attachments table
    op.create_table(
        'photo_attachments',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('entity_type', sa.String(64), nullable=False, index=True),  # receiving_item, vision_count, anomaly, etc.
        sa.Column('entity_id', UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('file_path', sa.String(500), nullable=False),
        sa.Column('file_size_bytes', sa.Integer(), nullable=False),
        sa.Column('mime_type', sa.String(64), nullable=False),
        sa.Column('thumbnail_path', sa.String(500), nullable=True),
        sa.Column('exif_data', JSONB, nullable=False, server_default='{}'),
        sa.Column('uploaded_by_id', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('uploaded_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('comment', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
    )
    
    # Create indexes
    op.create_index('idx_rfid_events_gateway_antenna', 'rfid_events', ['gateway_id', 'antenna_id'])
    op.create_index('idx_rfid_events_timestamp', 'rfid_events', ['timestamp'])
    op.create_index('idx_rfid_tag_bindings_entity', 'rfid_tag_bindings', ['entity_type', 'entity_id'])
    op.create_index('idx_door_command_log_door', 'door_command_log', ['door_id', 'executed_at'])
    op.create_index('idx_telemetry_data_device_timestamp', 'telemetry_data', ['device_id', 'timestamp'])
    op.create_index('idx_telemetry_alerts_active', 'telemetry_alerts', ['is_active', 'severity'])
    op.create_index('idx_vision_count_status', 'vision_count_tasks', ['status'])
    op.create_index('idx_photo_attachments_entity', 'photo_attachments', ['entity_type', 'entity_id'])
    
    # Seed example doors
    op.execute("""
        -- Get first magacin (or use specific ID)
        DO $$
        DECLARE
            v_magacin_id UUID;
            v_dock_location_id UUID;
        BEGIN
            SELECT id INTO v_magacin_id FROM magacin LIMIT 1;
            
            IF v_magacin_id IS NULL THEN
                INSERT INTO magacin (naziv, aktivan) 
                VALUES ('Veleprodajni Magacin', true)
                RETURNING id INTO v_magacin_id;
            END IF;
            
            -- Get or create dock location
            SELECT id INTO v_dock_location_id 
            FROM locations 
            WHERE magacin_id = v_magacin_id AND code = 'DOCK-01' 
            LIMIT 1;
            
            IF v_dock_location_id IS NULL THEN
                INSERT INTO locations (naziv, code, tip, magacin_id, zona, x_coordinate, y_coordinate)
                VALUES ('Dock 01', 'DOCK-01', 'zone', v_magacin_id, 'DOCK', 0, 0)
                RETURNING id INTO v_dock_location_id;
            END IF;
            
            -- Create example doors
            INSERT INTO doors (door_id, naziv, location_id, zone, current_status, auto_close_timeout_seconds)
            VALUES 
                ('D1', 'Vrata D1 (Prijem)', v_dock_location_id, 'DOCK', 'closed', 60),
                ('D2', 'Vrata D2 (Otprema)', v_dock_location_id, 'DOCK', 'closed', 60),
                ('D3', 'Vrata D3 (Hladnjača)', v_dock_location_id, 'COLD', 'closed', 45)
            ON CONFLICT DO NOTHING;
        END $$;
    """)


def downgrade():
    # Drop tables in reverse order
    op.drop_table('photo_attachments')
    op.drop_table('vision_count_tasks')
    op.drop_table('telemetry_alerts')
    op.drop_table('telemetry_data')
    op.drop_table('door_command_log')
    op.drop_table('doors')
    op.drop_table('rfid_tag_bindings')
    op.drop_table('rfid_events')
    
    # Drop enums
    telemetry_alert_severity_enum = ENUM(name='telemetry_alert_severity_enum')
    telemetry_alert_severity_enum.drop(op.get_bind(), checkfirst=True)
    
    door_status_enum = ENUM(name='door_status_enum')
    door_status_enum.drop(op.get_bind(), checkfirst=True)
    
    rfid_event_type_enum = ENUM(name='rfid_event_type_enum')
    rfid_event_type_enum.drop(op.get_bind(), checkfirst=True)

