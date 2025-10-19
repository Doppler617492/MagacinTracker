"""add pantheon erp integration models

Revision ID: 2025101701
Revises: 003_add_shortage_tracking
Create Date: 2025-10-17 06:00:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '2025101701'
down_revision = '003_add_shortage_tracking'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # =========================================================================
    # 1. ENHANCE ARTIKAL TABLE WITH PANTHEON FIELDS
    # =========================================================================
    op.add_column('artikal', sa.Column('supplier', sa.String(255), nullable=True))
    op.add_column('artikal', sa.Column('article_class', sa.String(64), nullable=True))
    op.add_column('artikal', sa.Column('description', sa.Text(), nullable=True))
    op.add_column('artikal', sa.Column('time_chg_ts', sa.DateTime(), nullable=True))
    op.add_column('artikal', sa.Column('last_synced_at', sa.DateTime(), nullable=True))
    op.add_column('artikal', sa.Column('source', sa.String(32), nullable=False, server_default='PANTHEON'))
    
    # Create index on time_chg_ts for efficient delta sync
    op.create_index('ix_artikal_time_chg_ts', 'artikal', ['time_chg_ts'])
    
    # =========================================================================
    # 2. CREATE SUBJECTS TABLE
    # =========================================================================
    op.create_table(
        'subjects',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('code', sa.String(64), unique=True, nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('type', sa.String(32), nullable=False),  # supplier, customer, warehouse
        sa.Column('pib', sa.String(32), nullable=True),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('city', sa.String(128), nullable=True),
        sa.Column('postal_code', sa.String(16), nullable=True),
        sa.Column('country', sa.String(64), nullable=True),
        sa.Column('phone', sa.String(32), nullable=True),
        sa.Column('email', sa.String(128), nullable=True),
        sa.Column('aktivan', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('time_chg_ts', sa.DateTime(), nullable=True),
        sa.Column('last_synced_at', sa.DateTime(), nullable=True),
        sa.Column('source', sa.String(32), nullable=False, server_default='PANTHEON'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()'))
    )
    
    op.create_index('ix_subjects_code', 'subjects', ['code'])
    op.create_index('ix_subjects_type', 'subjects', ['type'])
    op.create_index('ix_subjects_time_chg_ts', 'subjects', ['time_chg_ts'])
    
    # =========================================================================
    # 3. CREATE DOC_TYPES TABLE
    # =========================================================================
    op.create_table(
        'doc_types',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('code', sa.String(64), unique=True, nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('direction', sa.String(32), nullable=False),  # inbound, outbound
        sa.Column('aktivan', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()'))
    )
    
    op.create_index('ix_doc_types_code', 'doc_types', ['code'])
    op.create_index('ix_doc_types_direction', 'doc_types', ['direction'])
    
    # =========================================================================
    # 4. CREATE RECEIPTS TABLE (Inbound Documents)
    # =========================================================================
    op.create_table(
        'receipts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('doc_no', sa.String(64), nullable=False),
        sa.Column('doc_type_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('doc_types.id'), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('supplier_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('subjects.id'), nullable=True),
        sa.Column('store_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('subjects.id'), nullable=True),
        sa.Column('responsible_person', sa.String(128), nullable=True),
        sa.Column('header_ref', sa.String(64), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('last_synced_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()'))
    )
    
    op.create_index('ix_receipts_doc_no', 'receipts', ['doc_no'])
    op.create_index('ix_receipts_date', 'receipts', ['date'])
    op.create_unique_constraint('uq_receipts_doc_no_type_date', 'receipts', ['doc_no', 'doc_type_id', 'date'])
    
    # =========================================================================
    # 5. CREATE RECEIPT_ITEMS TABLE
    # =========================================================================
    op.create_table(
        'receipt_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('receipt_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('receipts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('article_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('artikal.id'), nullable=True),
        sa.Column('code', sa.String(64), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('unit', sa.String(32), nullable=False),
        sa.Column('barcode', sa.String(64), nullable=True),
        sa.Column('qty_requested', sa.Numeric(12, 3), nullable=False, server_default='0'),
        sa.Column('qty_completed', sa.Numeric(12, 3), nullable=False, server_default='0'),
        sa.Column('status', sa.String(32), nullable=False, server_default='new'),  # new, partial, done
        sa.Column('reason_missing', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()'))
    )
    
    op.create_index('ix_receipt_items_receipt_id', 'receipt_items', ['receipt_id'])
    op.create_index('ix_receipt_items_article_id', 'receipt_items', ['article_id'])
    op.create_index('ix_receipt_items_code', 'receipt_items', ['code'])
    
    # =========================================================================
    # 6. CREATE DISPATCHES TABLE (Outbound Documents)
    # =========================================================================
    op.create_table(
        'dispatches',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('doc_no', sa.String(64), nullable=False),
        sa.Column('doc_type_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('doc_types.id'), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('warehouse_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('subjects.id'), nullable=True),
        sa.Column('issuer', sa.String(128), nullable=True),
        sa.Column('receiver', sa.String(128), nullable=True),
        sa.Column('responsible_person', sa.String(128), nullable=True),
        sa.Column('header_ref', sa.String(64), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('last_synced_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()'))
    )
    
    op.create_index('ix_dispatches_doc_no', 'dispatches', ['doc_no'])
    op.create_index('ix_dispatches_date', 'dispatches', ['date'])
    op.create_unique_constraint('uq_dispatches_doc_no_type_date', 'dispatches', ['doc_no', 'doc_type_id', 'date'])
    
    # =========================================================================
    # 7. CREATE DISPATCH_ITEMS TABLE
    # =========================================================================
    op.create_table(
        'dispatch_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('dispatch_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('dispatches.id', ondelete='CASCADE'), nullable=False),
        sa.Column('article_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('artikal.id'), nullable=True),
        sa.Column('code', sa.String(64), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('unit', sa.String(32), nullable=False),
        sa.Column('barcode', sa.String(64), nullable=True),
        sa.Column('qty_requested', sa.Numeric(12, 3), nullable=False, server_default='0'),
        sa.Column('qty_completed', sa.Numeric(12, 3), nullable=False, server_default='0'),
        sa.Column('exists_in_wms', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('wms_flag', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('warehouse_code', sa.String(64), nullable=True),
        sa.Column('status', sa.String(32), nullable=False, server_default='new'),  # new, partial, done
        sa.Column('reason_missing', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()'))
    )
    
    op.create_index('ix_dispatch_items_dispatch_id', 'dispatch_items', ['dispatch_id'])
    op.create_index('ix_dispatch_items_article_id', 'dispatch_items', ['article_id'])
    op.create_index('ix_dispatch_items_code', 'dispatch_items', ['code'])
    op.create_index('ix_dispatch_items_exists_in_wms', 'dispatch_items', ['exists_in_wms'])
    op.create_index('ix_dispatch_items_warehouse_code', 'dispatch_items', ['warehouse_code'])


def downgrade() -> None:
    # Drop dispatch tables
    op.drop_table('dispatch_items')
    op.drop_table('dispatches')
    
    # Drop receipt tables
    op.drop_table('receipt_items')
    op.drop_table('receipts')
    
    # Drop doc_types
    op.drop_table('doc_types')
    
    # Drop subjects
    op.drop_table('subjects')
    
    # Remove artikal enhancements
    op.drop_index('ix_artikal_time_chg_ts', 'artikal')
    op.drop_column('artikal', 'source')
    op.drop_column('artikal', 'last_synced_at')
    op.drop_column('artikal', 'time_chg_ts')
    op.drop_column('artikal', 'description')
    op.drop_column('artikal', 'article_class')
    op.drop_column('artikal', 'supplier')

