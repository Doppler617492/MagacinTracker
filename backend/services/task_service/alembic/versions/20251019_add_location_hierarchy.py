"""Add location hierarchy for warehouse management (Zona→Regal→Polica→Bin)

Revision ID: 20251019_locations
Revises: 20251019_receiving
Create Date: 2025-10-19 16:00:00.000000

Manhattan Active WMS - Full location-based warehouse management
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB, ENUM

# revision identifiers
revision = '20251019_locations'
down_revision = '20251019_receiving'
branch_labels = None
depends_on = None


def upgrade():
    # Create location type enum
    location_type_enum = ENUM(
        'zone',     # Zona
        'regal',    # Regal (Rack)
        'polica',   # Polica (Shelf)
        'bin',      # Bin (smallest unit)
        name='location_type_enum',
        create_type=True
    )
    location_type_enum.create(op.get_bind(), checkfirst=True)
    
    # Create cycle count status enum
    cycle_count_status_enum = ENUM(
        'scheduled',
        'in_progress',
        'completed',
        'cancelled',
        name='cycle_count_status_enum',
        create_type=True
    )
    cycle_count_status_enum.create(op.get_bind(), checkfirst=True)
    
    # Create locations table (self-referencing hierarchy)
    op.create_table(
        'locations',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('naziv', sa.String(128), nullable=False),
        sa.Column('code', sa.String(32), unique=True, nullable=False, index=True),
        sa.Column('tip', location_type_enum, nullable=False, index=True),
        sa.Column('parent_id', UUID(as_uuid=True), sa.ForeignKey('locations.id'), nullable=True, index=True),
        sa.Column('magacin_id', UUID(as_uuid=True), sa.ForeignKey('magacin.id'), nullable=False, index=True),
        sa.Column('zona', sa.String(32), nullable=True, index=True),  # Denormalized for fast lookup
        sa.Column('x_coordinate', sa.Numeric(8, 2), nullable=True),
        sa.Column('y_coordinate', sa.Numeric(8, 2), nullable=True),
        sa.Column('capacity_max', sa.Numeric(12, 3), nullable=True),
        sa.Column('capacity_current', sa.Numeric(12, 3), nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('metadata', JSONB, nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
    )
    
    # Create article_locations table (inventory by location)
    op.create_table(
        'article_locations',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('artikal_id', UUID(as_uuid=True), sa.ForeignKey('artikal.id'), nullable=False, index=True),
        sa.Column('location_id', UUID(as_uuid=True), sa.ForeignKey('locations.id'), nullable=False, index=True),
        sa.Column('quantity', sa.Numeric(12, 3), nullable=False, server_default='0'),
        sa.Column('uom', sa.String(32), nullable=False, server_default='PCS'),
        sa.Column('last_counted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_moved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_primary_location', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.UniqueConstraint('artikal_id', 'location_id', name='uq_article_location')
    )
    
    # Create cycle_counts table
    op.create_table(
        'cycle_counts',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('location_id', UUID(as_uuid=True), sa.ForeignKey('locations.id'), nullable=True, index=True),
        sa.Column('scheduled_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('assigned_to_id', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', cycle_count_status_enum, nullable=False, server_default='scheduled', index=True),
        sa.Column('count_type', sa.String(32), nullable=True),  # 'zone', 'regal', 'article', 'random'
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
    )
    
    # Create cycle_count_items table
    op.create_table(
        'cycle_count_items',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('cycle_count_id', UUID(as_uuid=True), sa.ForeignKey('cycle_counts.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('artikal_id', UUID(as_uuid=True), sa.ForeignKey('artikal.id'), nullable=False),
        sa.Column('location_id', UUID(as_uuid=True), sa.ForeignKey('locations.id'), nullable=False),
        sa.Column('system_quantity', sa.Numeric(12, 3), nullable=False),
        sa.Column('counted_quantity', sa.Numeric(12, 3), nullable=True),
        sa.Column('variance', sa.Numeric(12, 3), nullable=True),
        sa.Column('variance_percent', sa.Numeric(5, 2), nullable=True),
        sa.Column('reason', sa.String(255), nullable=True),
        sa.Column('counted_by_id', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('counted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
    )
    
    # Create putaway_tasks table
    op.create_table(
        'putaway_tasks',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('receiving_item_id', UUID(as_uuid=True), sa.ForeignKey('receiving_item.id'), nullable=False, index=True),
        sa.Column('suggested_location_id', UUID(as_uuid=True), sa.ForeignKey('locations.id'), nullable=True),
        sa.Column('actual_location_id', UUID(as_uuid=True), sa.ForeignKey('locations.id'), nullable=True),
        sa.Column('quantity', sa.Numeric(12, 3), nullable=False),
        sa.Column('status', sa.String(32), nullable=False, server_default='pending'),
        sa.Column('assigned_to_id', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('duration_seconds', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
    )
    
    # Create pick_routes table
    op.create_table(
        'pick_routes',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('zaduznica_id', UUID(as_uuid=True), sa.ForeignKey('zaduznica.id'), nullable=False, index=True),
        sa.Column('route_data', JSONB, nullable=False, server_default='[]'),
        sa.Column('total_distance_meters', sa.Numeric(8, 2), nullable=True),
        sa.Column('estimated_time_minutes', sa.Integer(), nullable=True),
        sa.Column('actual_time_minutes', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
    )
    
    # Extend receiving_item for putaway tracking
    op.add_column('receiving_item', sa.Column('suggested_location_id', UUID(as_uuid=True), sa.ForeignKey('locations.id'), nullable=True))
    op.add_column('receiving_item', sa.Column('actual_location_id', UUID(as_uuid=True), sa.ForeignKey('locations.id'), nullable=True))
    op.add_column('receiving_item', sa.Column('putaway_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('receiving_item', sa.Column('putaway_by_id', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True))
    
    # Extend zaduznica_stavka for pick tracking
    op.add_column('zaduznica_stavka', sa.Column('pick_location_id', UUID(as_uuid=True), sa.ForeignKey('locations.id'), nullable=True))
    op.add_column('zaduznica_stavka', sa.Column('pick_sequence', sa.Integer(), nullable=True))
    op.add_column('zaduznica_stavka', sa.Column('picked_at', sa.DateTime(timezone=True), nullable=True))
    
    # Create indexes
    op.create_index('idx_putaway_tasks_receiving_item', 'putaway_tasks', ['receiving_item_id'])
    op.create_index('idx_putaway_tasks_status', 'putaway_tasks', ['status'])
    op.create_index('idx_pick_routes_zaduznica', 'pick_routes', ['zaduznica_id'])
    op.create_index('idx_cycle_counts_status', 'cycle_counts', ['status'])
    op.create_index('idx_cycle_counts_scheduled', 'cycle_counts', ['scheduled_at'])
    
    # Seed example location hierarchy (Veleprodajni Magacin)
    op.execute("""
        -- Get magacin ID (assuming Veleprodajni Magacin exists)
        DO $$
        DECLARE
            v_magacin_id UUID;
            v_zona_a UUID;
            v_zona_b UUID;
            v_regal_a1 UUID;
            v_regal_a2 UUID;
            v_polica_a1_1 UUID;
            v_polica_a1_2 UUID;
        BEGIN
            -- Get first magacin (or create if not exists)
            SELECT id INTO v_magacin_id FROM magacin LIMIT 1;
            
            IF v_magacin_id IS NULL THEN
                INSERT INTO magacin (naziv, aktivan) 
                VALUES ('Veleprodajni Magacin', true)
                RETURNING id INTO v_magacin_id;
            END IF;
            
            -- Create Zona A
            INSERT INTO locations (naziv, code, tip, magacin_id, zona, x_coordinate, y_coordinate, capacity_max)
            VALUES ('Zona A', 'ZA', 'zone', v_magacin_id, 'A', 10, 10, 10000)
            RETURNING id INTO v_zona_a;
            
            -- Create Zona B
            INSERT INTO locations (naziv, code, tip, magacin_id, zona, x_coordinate, y_coordinate, capacity_max)
            VALUES ('Zona B', 'ZB', 'zone', v_magacin_id, 'B', 50, 10, 8000)
            RETURNING id INTO v_zona_b;
            
            -- Create Regal A1 in Zona A
            INSERT INTO locations (naziv, code, tip, parent_id, magacin_id, zona, x_coordinate, y_coordinate, capacity_max)
            VALUES ('Regal A1', 'ZA-R01', 'regal', v_zona_a, v_magacin_id, 'A', 12, 12, 1000)
            RETURNING id INTO v_regal_a1;
            
            -- Create Regal A2 in Zona A
            INSERT INTO locations (naziv, code, tip, parent_id, magacin_id, zona, x_coordinate, y_coordinate, capacity_max)
            VALUES ('Regal A2', 'ZA-R02', 'regal', v_zona_a, v_magacin_id, 'A', 15, 12, 1000)
            RETURNING id INTO v_regal_a2;
            
            -- Create Police (Shelves) in Regal A1
            INSERT INTO locations (naziv, code, tip, parent_id, magacin_id, zona, x_coordinate, y_coordinate, capacity_max)
            VALUES ('Polica A1-1', 'ZA-R01-P01', 'polica', v_regal_a1, v_magacin_id, 'A', 12, 12, 500)
            RETURNING id INTO v_polica_a1_1;
            
            INSERT INTO locations (naziv, code, tip, parent_id, magacin_id, zona, x_coordinate, y_coordinate, capacity_max)
            VALUES ('Polica A1-2', 'ZA-R01-P02', 'polica', v_regal_a1, v_magacin_id, 'A', 12, 13, 500)
            RETURNING id INTO v_polica_a1_2;
            
            -- Create Bins in Polica A1-1
            INSERT INTO locations (naziv, code, tip, parent_id, magacin_id, zona, capacity_max)
            VALUES 
                ('Bin A1-1-01', 'ZA-R01-P01-B01', 'bin', v_polica_a1_1, v_magacin_id, 'A', 100),
                ('Bin A1-1-02', 'ZA-R01-P01-B02', 'bin', v_polica_a1_1, v_magacin_id, 'A', 100),
                ('Bin A1-1-03', 'ZA-R01-P01-B03', 'bin', v_polica_a1_1, v_magacin_id, 'A', 100),
                ('Bin A1-1-04', 'ZA-R01-P01-B04', 'bin', v_polica_a1_1, v_magacin_id, 'A', 100),
                ('Bin A1-1-05', 'ZA-R01-P01-B05', 'bin', v_polica_a1_1, v_magacin_id, 'A', 100);
            
            -- Create Bins in Polica A1-2
            INSERT INTO locations (naziv, code, tip, parent_id, magacin_id, zona, capacity_max)
            VALUES 
                ('Bin A1-2-01', 'ZA-R01-P02-B01', 'bin', v_polica_a1_2, v_magacin_id, 'A', 100),
                ('Bin A1-2-02', 'ZA-R01-P02-B02', 'bin', v_polica_a1_2, v_magacin_id, 'A', 100),
                ('Bin A1-2-03', 'ZA-R01-P02-B03', 'bin', v_polica_a1_2, v_magacin_id, 'A', 100);
        END $$;
    """)


def downgrade():
    # Drop tables in reverse order (due to foreign keys)
    op.drop_table('pick_routes')
    op.drop_table('putaway_tasks')
    op.drop_table('cycle_count_items')
    op.drop_table('cycle_counts')
    op.drop_table('article_locations')
    
    # Drop location columns from existing tables
    op.drop_column('zaduznica_stavka', 'picked_at')
    op.drop_column('zaduznica_stavka', 'pick_sequence')
    op.drop_column('zaduznica_stavka', 'pick_location_id')
    op.drop_column('receiving_item', 'putaway_by_id')
    op.drop_column('receiving_item', 'putaway_at')
    op.drop_column('receiving_item', 'actual_location_id')
    op.drop_column('receiving_item', 'suggested_location_id')
    
    # Drop locations table
    op.drop_table('locations')
    
    # Drop enums
    cycle_count_status_enum = ENUM(name='cycle_count_status_enum')
    cycle_count_status_enum.drop(op.get_bind(), checkfirst=True)
    
    location_type_enum = ENUM(name='location_type_enum')
    location_type_enum.drop(op.get_bind(), checkfirst=True)

