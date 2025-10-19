"""Add receiving (prijem) entities for Manhattan-style inbound workflow

Revision ID: 20251019_receiving
Revises: 20251019_partial
Create Date: 2025-10-19 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB, ENUM

# revision identifiers
revision = '20251019_receiving'
down_revision = '20251019_partial'
branch_labels = None
depends_on = None


def upgrade():
    # Create receiving status enum
    receiving_status_enum = ENUM(
        'novo',
        'u_toku',
        'završeno',
        'završeno_djelimično',
        name='receiving_status_enum',
        create_type=True
    )
    receiving_status_enum.create(op.get_bind(), checkfirst=True)
    
    # Create receiving reason enum (for discrepancies)
    receiving_reason_enum = ENUM(
        'manjak',
        'višak',
        'oštećeno',
        'nije_isporučeno',
        'drugo',
        name='receiving_reason_enum',
        create_type=True
    )
    receiving_reason_enum.create(op.get_bind(), checkfirst=True)
    
    # Create receiving item status enum
    receiving_item_status_enum = ENUM(
        'novo',
        'u_toku',
        'gotovo',
        name='receiving_item_status_enum',
        create_type=True
    )
    receiving_item_status_enum.create(op.get_bind(), checkfirst=True)
    
    # Create receiving_header table
    op.create_table(
        'receiving_header',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('broj_prijema', sa.String(64), nullable=False, unique=True, index=True),
        sa.Column('dobavljac_id', UUID(as_uuid=True), sa.ForeignKey('subjects.id'), nullable=True),
        sa.Column('magacin_id', UUID(as_uuid=True), sa.ForeignKey('magacin.id'), nullable=False),
        sa.Column('datum', sa.Date(), nullable=False, index=True),
        sa.Column('status', receiving_status_enum, nullable=False, server_default='novo', index=True),
        sa.Column('created_by_id', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('started_by_id', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_by_id', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('meta', JSONB, nullable=True, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
    )
    
    # Create indexes for receiving_header
    op.create_index('idx_receiving_header_broj', 'receiving_header', ['broj_prijema'])
    op.create_index('idx_receiving_header_status', 'receiving_header', ['status'])
    op.create_index('idx_receiving_header_datum', 'receiving_header', ['datum'])
    op.create_index('idx_receiving_header_magacin', 'receiving_header', ['magacin_id'])
    op.create_index('idx_receiving_header_dobavljac', 'receiving_header', ['dobavljac_id'])
    
    # Create receiving_item table
    op.create_table(
        'receiving_item',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('header_id', UUID(as_uuid=True), sa.ForeignKey('receiving_header.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('artikal_id', UUID(as_uuid=True), sa.ForeignKey('artikal.id'), nullable=True),
        sa.Column('sifra', sa.String(64), nullable=False, index=True),
        sa.Column('naziv', sa.String(255), nullable=False),
        sa.Column('jedinica_mjere', sa.String(32), nullable=False),
        sa.Column('kolicina_trazena', sa.Numeric(12, 3), nullable=False),
        sa.Column('kolicina_primljena', sa.Numeric(12, 3), nullable=False, server_default='0'),
        sa.Column('razlog', receiving_reason_enum, nullable=True),
        sa.Column('napomena', sa.Text(), nullable=True),
        sa.Column('attachments', JSONB, nullable=False, server_default='[]'),
        sa.Column('status', receiving_item_status_enum, nullable=False, server_default='novo'),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_by_id', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
    )
    
    # Create indexes for receiving_item
    op.create_index('idx_receiving_item_header', 'receiving_item', ['header_id'])
    op.create_index('idx_receiving_item_artikal', 'receiving_item', ['artikal_id'])
    op.create_index('idx_receiving_item_sifra', 'receiving_item', ['sifra'])
    op.create_index('idx_receiving_item_status', 'receiving_item', ['status'])
    
    # Add check constraints
    op.create_check_constraint(
        'ck_receiving_item_trazena_gt_zero',
        'receiving_item',
        'kolicina_trazena > 0'
    )
    
    op.create_check_constraint(
        'ck_receiving_item_primljena_ge_zero',
        'receiving_item',
        'kolicina_primljena >= 0'
    )
    
    # Add UoM fields to artikal table
    op.add_column('artikal', sa.Column('base_uom', sa.String(32), nullable=True, server_default='PCS'))
    op.add_column('artikal', sa.Column('pack_uom', sa.String(32), nullable=True))
    op.add_column('artikal', sa.Column('conversion_factor', sa.Numeric(8, 3), nullable=True))
    op.add_column('artikal', sa.Column('is_primary_pack', sa.Boolean(), nullable=False, server_default='false'))
    
    # Add check constraint for conversion factor
    op.create_check_constraint(
        'ck_conversion_factor_positive',
        'artikal',
        'conversion_factor IS NULL OR conversion_factor > 0'
    )
    
    # Create index on pack_uom
    op.create_index('idx_artikal_pack_uom', 'artikal', ['pack_uom'])
    
    # Update existing artikal records to have base_uom
    op.execute("""
        UPDATE artikal 
        SET base_uom = 'PCS' 
        WHERE base_uom IS NULL
    """)


def downgrade():
    # Drop receiving tables
    op.drop_table('receiving_item')
    op.drop_table('receiving_header')
    
    # Drop UoM columns from artikal
    op.drop_index('idx_artikal_pack_uom', 'artikal')
    op.drop_constraint('ck_conversion_factor_positive', 'artikal', type_='check')
    op.drop_column('artikal', 'is_primary_pack')
    op.drop_column('artikal', 'conversion_factor')
    op.drop_column('artikal', 'pack_uom')
    op.drop_column('artikal', 'base_uom')
    
    # Drop enums
    receiving_item_status_enum = ENUM(name='receiving_item_status_enum')
    receiving_item_status_enum.drop(op.get_bind(), checkfirst=True)
    
    receiving_reason_enum = ENUM(name='receiving_reason_enum')
    receiving_reason_enum.drop(op.get_bind(), checkfirst=True)
    
    receiving_status_enum = ENUM(name='receiving_status_enum')
    receiving_status_enum.drop(op.get_bind(), checkfirst=True)

