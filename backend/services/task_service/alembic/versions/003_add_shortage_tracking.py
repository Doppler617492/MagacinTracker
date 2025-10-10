"""add shortage tracking fields

Revision ID: 2025101001
Revises: 2024120101
Create Date: 2025-10-10 09:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '2025101001'
down_revision = '2024120101'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create discrepancy_status enum
    discrepancy_status_enum = postgresql.ENUM(
        'none', 'short_pick', 'not_found', 'damaged', 'wrong_barcode',
        name='discrepancy_status_enum',
        create_type=False
    )
    discrepancy_status_enum.create(op.get_bind(), checkfirst=True)
    
    # Add new columns to trebovanje_stavka
    op.add_column('trebovanje_stavka', 
        sa.Column('picked_qty', sa.Numeric(12, 3), nullable=False, server_default='0'))
    op.add_column('trebovanje_stavka', 
        sa.Column('missing_qty', sa.Numeric(12, 3), nullable=False, server_default='0'))
    op.add_column('trebovanje_stavka', 
        sa.Column('discrepancy_status', discrepancy_status_enum, nullable=False, server_default='none'))
    op.add_column('trebovanje_stavka', 
        sa.Column('discrepancy_reason', sa.Text(), nullable=True))
    op.add_column('trebovanje_stavka', 
        sa.Column('last_scanned_code', sa.String(64), nullable=True))
    
    # Add new columns to trebovanje
    op.add_column('trebovanje', 
        sa.Column('allow_incomplete_close', sa.Boolean(), nullable=False, server_default='true'))
    op.add_column('trebovanje', 
        sa.Column('closed_by', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('trebovanje', 
        sa.Column('closed_at', sa.DateTime(timezone=True), nullable=True))
    
    # Add foreign key for closed_by
    op.create_foreign_key(
        'trebovanje_closed_by_fkey',
        'trebovanje', 'users',
        ['closed_by'], ['id']
    )


def downgrade() -> None:
    # Remove foreign key
    op.drop_constraint('trebovanje_closed_by_fkey', 'trebovanje', type_='foreignkey')
    
    # Remove columns from trebovanje
    op.drop_column('trebovanje', 'closed_at')
    op.drop_column('trebovanje', 'closed_by')
    op.drop_column('trebovanje', 'allow_incomplete_close')
    
    # Remove columns from trebovanje_stavka
    op.drop_column('trebovanje_stavka', 'last_scanned_code')
    op.drop_column('trebovanje_stavka', 'discrepancy_reason')
    op.drop_column('trebovanje_stavka', 'discrepancy_status')
    op.drop_column('trebovanje_stavka', 'missing_qty')
    op.drop_column('trebovanje_stavka', 'picked_qty')
    
    # Drop enum
    sa.Enum(name='discrepancy_status_enum').drop(op.get_bind(), checkfirst=True)

