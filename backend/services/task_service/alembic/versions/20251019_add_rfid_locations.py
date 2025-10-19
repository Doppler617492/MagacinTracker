"""Add RFID location tracking and inventory-by-location

Revision ID: 20251019_rfid_locations
Revises: 20251019_iot_layer
Create Date: 2025-10-19 22:00:00.000000

Sprint WMS Phase 6 - RFID Locations & Live Map
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB, ENUM

# revision identifiers
revision = '20251019_rfid_locations'
down_revision = '20251019_iot_layer'
branch_labels = None
depends_on = None


def upgrade():
    # Create warehouse zone type enum
    zone_type_enum = ENUM(
        'dock',
        'chill',
        'aisle',
        'quarantine',
        'staging',
        name='zone_type_enum',
        create_type=True
    )
    zone_type_enum.create(op.get_bind(), checkfirst=True)
    
    # Create location type enum (more granular)
    location_type_v2_enum = ENUM(
        'bin',
        'pallet',
        'flowrack',
        'shelf',
        name='location_type_v2_enum',
        create_type=True
    )
    location_type_v2_enum.create(op.get_bind(), checkfirst=True)
    
    # Create tag type enum
    tag_type_enum = ENUM(
        'rfid',
        'qr',
        'barcode',
        name='tag_type_enum',
        create_type=True
    )
    tag_type_enum.create(op.get_bind(), checkfirst=True)
    
    # Create handling unit type enum
    hu_type_enum = ENUM(
        'pallet',
        'carton',
        'roll',
        'tote',
        name='hu_type_enum',
        create_type=True
    )
    hu_type_enum.create(op.get_bind(), checkfirst=True)
    
    # Create handling unit status enum
    hu_status_enum = ENUM(
        'inbound',
        'staged',
        'stored',
        'picked',
        'outbound',
        name='hu_status_enum',
        create_type=True
    )
    hu_status_enum.create(op.get_bind(), checkfirst=True)
    
    # Create warehouse_zone table
    op.create_table(
        'warehouse_zone',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('magacin_id', UUID(as_uuid=True), sa.ForeignKey('magacin.id'), nullable=False, index=True),
        sa.Column('code', sa.String(32), nullable=False, index=True),
        sa.Column('name', sa.String(128), nullable=False),
        sa.Column('zone_type', zone_type_enum, nullable=False),
        sa.Column('temp_range_min', sa.Numeric(5, 2), nullable=True),
        sa.Column('temp_range_max', sa.Numeric(5, 2), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('metadata', JSONB, nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.UniqueConstraint('magacin_id', 'code', name='uq_warehouse_zone_code')
    )
    
    # Create location_v2 table (granular bin/slot level)
    op.create_table(
        'location_v2',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('zone_id', UUID(as_uuid=True), sa.ForeignKey('warehouse_zone.id'), nullable=False, index=True),
        sa.Column('code', sa.String(64), nullable=False, index=True),
        sa.Column('name', sa.String(128), nullable=False),
        sa.Column('location_type', location_type_v2_enum, nullable=False),
        sa.Column('capacity_uom', sa.String(32), nullable=True),
        sa.Column('max_capacity', sa.Numeric(12, 3), nullable=True),
        sa.Column('is_pick_face', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('x_coordinate', sa.Numeric(8, 2), nullable=True),
        sa.Column('y_coordinate', sa.Numeric(8, 2), nullable=True),
        sa.Column('metadata', JSONB, nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.UniqueConstraint('zone_id', 'code', name='uq_location_v2_code')
    )
    
    # Create location_tag table (RFID/QR tags for locations)
    op.create_table(
        'location_tag',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('location_id', UUID(as_uuid=True), sa.ForeignKey('location_v2.id'), nullable=False, index=True),
        sa.Column('tag_type', tag_type_enum, nullable=False),
        sa.Column('tag_value', sa.String(128), nullable=False, index=True),
        sa.Column('is_primary', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.UniqueConstraint('tag_type', 'tag_value', name='uq_location_tag_value')
    )
    
    # Create inventory_by_location table
    op.create_table(
        'inventory_by_location',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('location_id', UUID(as_uuid=True), sa.ForeignKey('location_v2.id'), nullable=False, index=True),
        sa.Column('article_id', UUID(as_uuid=True), sa.ForeignKey('artikal.id'), nullable=False, index=True),
        sa.Column('uom', sa.String(32), nullable=False, server_default='PCS'),
        sa.Column('qty', sa.Numeric(12, 3), nullable=False, server_default='0'),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.UniqueConstraint('location_id', 'article_id', 'uom', name='uq_inv_by_location')
    )
    
    # Create handling_unit table (pallets, cartons, roll-containers)
    op.create_table(
        'handling_unit',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('hu_type', hu_type_enum, nullable=False),
        sa.Column('epc_tag', sa.String(128), unique=True, nullable=True, index=True),
        sa.Column('gross_weight', sa.Numeric(10, 3), nullable=True),
        sa.Column('status', hu_status_enum, nullable=False, server_default='inbound'),
        sa.Column('current_location_id', UUID(as_uuid=True), sa.ForeignKey('location_v2.id'), nullable=True, index=True),
        sa.Column('metadata', JSONB, nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
    )
    
    # Extend task_item (zaduznica_stavka) with location tracking
    op.add_column('zaduznica_stavka', sa.Column('from_location_id', UUID(as_uuid=True), sa.ForeignKey('location_v2.id'), nullable=True))
    op.add_column('zaduznica_stavka', sa.Column('to_location_id', UUID(as_uuid=True), sa.ForeignKey('location_v2.id'), nullable=True))
    op.add_column('zaduznica_stavka', sa.Column('confirm_mode', sa.String(32), nullable=True))  # 'rfid', 'manual', 'barcode'
    op.add_column('zaduznica_stavka', sa.Column('confirmed_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('zaduznica_stavka', sa.Column('confirmed_by_id', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True))
    
    # Create indexes
    op.create_index('idx_warehouse_zone_code', 'warehouse_zone', ['code'])
    op.create_index('idx_location_v2_code', 'location_v2', ['code'])
    op.create_index('idx_location_v2_zone', 'location_v2', ['zone_id', 'is_active'])
    op.create_index('idx_location_tag_value', 'location_tag', ['tag_value'])
    op.create_index('idx_inv_by_loc_location', 'inventory_by_location', ['location_id', 'article_id'])
    op.create_index('idx_handling_unit_epc', 'handling_unit', ['epc_tag'])
    op.create_index('idx_handling_unit_location', 'handling_unit', ['current_location_id'])
    
    # Seed example data (1 warehouse, 3 zones, 30 locations)
    op.execute("""
        DO $$
        DECLARE
            v_magacin_id UUID;
            v_zone_dock UUID;
            v_zone_aisle_a UUID;
            v_zone_chill UUID;
            v_loc_id UUID;
            v_article_id UUID;
        BEGIN
            -- Get or create warehouse
            SELECT id INTO v_magacin_id FROM magacin LIMIT 1;
            IF v_magacin_id IS NULL THEN
                INSERT INTO magacin (naziv, aktivan) VALUES ('Veleprodajni Magacin', true)
                RETURNING id INTO v_magacin_id;
            END IF;
            
            -- Create zones
            INSERT INTO warehouse_zone (magacin_id, code, name, zone_type, is_active)
            VALUES (v_magacin_id, 'DOK', 'Dok D1 (Prijem)', 'dock', true)
            RETURNING id INTO v_zone_dock;
            
            INSERT INTO warehouse_zone (magacin_id, code, name, zone_type, is_active)
            VALUES (v_magacin_id, 'A', 'Aisle A (Brza prodaja)', 'aisle', true)
            RETURNING id INTO v_zone_aisle_a;
            
            INSERT INTO warehouse_zone (magacin_id, code, name, zone_type, temp_range_min, temp_range_max, is_active)
            VALUES (v_magacin_id, 'HLD', 'Hladnjača', 'chill', 2, 8, true)
            RETURNING id INTO v_zone_chill;
            
            -- Create locations in Aisle A (10 bins)
            FOR i IN 1..10 LOOP
                INSERT INTO location_v2 (zone_id, code, name, location_type, max_capacity, is_pick_face, x_coordinate, y_coordinate)
                VALUES (
                    v_zone_aisle_a,
                    'A01-R01-P01-B' || LPAD(i::text, 2, '0'),
                    'Bin A01-R01-P01-' || LPAD(i::text, 2, '0'),
                    'bin',
                    100,
                    CASE WHEN i <= 5 THEN true ELSE false END,
                    10 + (i * 2),
                    10
                )
                RETURNING id INTO v_loc_id;
                
                -- Add QR tag
                INSERT INTO location_tag (location_id, tag_type, tag_value, is_primary)
                VALUES (v_loc_id, 'qr', 'QR-A01-R01-P01-B' || LPAD(i::text, 2, '0'), true);
                
                -- Add RFID tag (if i <= 5, pick face bins)
                IF i <= 5 THEN
                    INSERT INTO location_tag (location_id, tag_type, tag_value, is_primary)
                    VALUES (v_loc_id, 'rfid', 'RFID-A01-R01-P01-B' || LPAD(i::text, 2, '0'), false);
                END IF;
            END LOOP;
            
            -- Create locations in Dock (10 staging locations)
            FOR i IN 1..10 LOOP
                INSERT INTO location_v2 (zone_id, code, name, location_type, max_capacity, x_coordinate, y_coordinate)
                VALUES (
                    v_zone_dock,
                    'DOK-STAGE-' || LPAD(i::text, 2, '0'),
                    'Staging ' || LPAD(i::text, 2, '0'),
                    'pallet',
                    500,
                    5 + (i * 3),
                    5
                )
                RETURNING id INTO v_loc_id;
                
                -- Add QR tag
                INSERT INTO location_tag (location_id, tag_type, tag_value, is_primary)
                VALUES (v_loc_id, 'qr', 'QR-DOK-STAGE-' || LPAD(i::text, 2, '0'), true);
            END LOOP;
            
            -- Create locations in Chill (10 bins)
            FOR i IN 1..10 LOOP
                INSERT INTO location_v2 (zone_id, code, name, location_type, max_capacity, x_coordinate, y_coordinate)
                VALUES (
                    v_zone_chill,
                    'HLD-R01-P01-B' || LPAD(i::text, 2, '0'),
                    'Hladnjača Bin ' || LPAD(i::text, 2, '0'),
                    'bin',
                    50,
                    20 + (i * 2),
                    20
                )
                RETURNING id INTO v_loc_id;
                
                -- Add QR tag
                INSERT INTO location_tag (location_id, tag_type, tag_value, is_primary)
                VALUES (v_loc_id, 'qr', 'QR-HLD-R01-P01-B' || LPAD(i::text, 2, '0'), true);
            END LOOP;
            
            -- Seed some inventory (if articles exist)
            SELECT id INTO v_article_id FROM artikal WHERE aktivan = true LIMIT 1;
            IF v_article_id IS NOT NULL THEN
                -- Add inventory to first 5 Aisle A bins
                FOR i IN 1..5 LOOP
                    SELECT id INTO v_loc_id FROM location_v2 
                    WHERE code = 'A01-R01-P01-B' || LPAD(i::text, 2, '0') LIMIT 1;
                    
                    IF v_loc_id IS NOT NULL THEN
                        INSERT INTO inventory_by_location (location_id, article_id, uom, qty)
                        VALUES (v_loc_id, v_article_id, 'PCS', 50 + (i * 10));
                    END IF;
                END LOOP;
            END IF;
            
        END $$;
    """)


def downgrade():
    # Drop extensions to existing tables
    op.drop_column('zaduznica_stavka', 'confirmed_by_id')
    op.drop_column('zaduznica_stavka', 'confirmed_at')
    op.drop_column('zaduznica_stavka', 'confirm_mode')
    op.drop_column('zaduznica_stavka', 'to_location_id')
    op.drop_column('zaduznica_stavka', 'from_location_id')
    
    # Drop tables in reverse order
    op.drop_table('handling_unit')
    op.drop_table('inventory_by_location')
    op.drop_table('location_tag')
    op.drop_table('location_v2')
    op.drop_table('warehouse_zone')
    
    # Drop enums
    hu_status_enum = ENUM(name='hu_status_enum')
    hu_status_enum.drop(op.get_bind(), checkfirst=True)
    
    hu_type_enum = ENUM(name='hu_type_enum')
    hu_type_enum.drop(op.get_bind(), checkfirst=True)
    
    tag_type_enum = ENUM(name='tag_type_enum')
    tag_type_enum.drop(op.get_bind(), checkfirst=True)
    
    location_type_v2_enum = ENUM(name='location_type_v2_enum')
    location_type_v2_enum.drop(op.get_bind(), checkfirst=True)
    
    zone_type_enum = ENUM(name='zone_type_enum')
    zone_type_enum.drop(op.get_bind(), checkfirst=True)

