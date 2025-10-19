"""Add partial completion fields for Manhattan-style exception handling

Revision ID: 20251019_partial
Revises: 2025101701_pantheon_erp_integration
Create Date: 2025-10-19 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ENUM

# revision identifiers, used by Alembic.
revision = '20251019_partial'
down_revision = '2025101701_pantheon_erp_integration'
branch_labels = None
depends_on = None


def upgrade():
    # Create partial completion reason enum
    partial_reason_enum = ENUM(
        'nema_na_stanju',
        'osteceno', 
        'nije_pronađeno',
        'krivi_artikal',
        'drugo',
        name='partial_completion_reason_enum',
        create_type=True
    )
    partial_reason_enum.create(op.get_bind(), checkfirst=True)
    
    # Add količina_pronađena to trebovanje_stavka
    op.add_column(
        'trebovanje_stavka',
        sa.Column('kolicina_pronađena', sa.Numeric(12, 3), nullable=True)
    )
    
    # Add razlog (reason) to trebovanje_stavka
    op.add_column(
        'trebovanje_stavka',
        sa.Column('razlog', partial_reason_enum, nullable=True)
    )
    
    # Add razlog_tekst for custom reasons
    op.add_column(
        'trebovanje_stavka',
        sa.Column('razlog_tekst', sa.Text(), nullable=True)
    )
    
    # Add is_partial flag
    op.add_column(
        'trebovanje_stavka',
        sa.Column('is_partial', sa.Boolean(), nullable=False, server_default='false')
    )
    
    # Add completion percentage helper field
    op.add_column(
        'trebovanje_stavka',
        sa.Column('procenat_ispunjenja', sa.Numeric(5, 2), nullable=True)
    )
    
    # Add timestamp for completion tracking
    op.add_column(
        'trebovanje_stavka',
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True)
    )
    
    # Add completed_by user reference
    op.add_column(
        'trebovanje_stavka',
        sa.Column('completed_by_id', sa.UUID(), nullable=True)
    )
    
    # Add foreign key constraint
    op.create_foreign_key(
        'fk_trebovanje_stavka_completed_by',
        'trebovanje_stavka', 
        'users',
        ['completed_by_id'], 
        ['id']
    )
    
    # Add check constraint: količina_pronađena <= kolicina_trazena
    op.create_check_constraint(
        'ck_kolicina_pronađena_le_trazena',
        'trebovanje_stavka',
        'kolicina_pronađena IS NULL OR kolicina_pronađena <= kolicina_trazena'
    )
    
    # Add check constraint: if is_partial, količina_pronađena < kolicina_trazena
    op.create_check_constraint(
        'ck_partial_requires_lower_quantity',
        'trebovanje_stavka',
        'NOT is_partial OR (kolicina_pronađena IS NOT NULL AND kolicina_pronađena < kolicina_trazena)'
    )
    
    # Add check constraint: if is_partial and razlog='drugo', razlog_tekst must exist
    op.create_check_constraint(
        'ck_drugo_requires_text',
        'trebovanje_stavka',
        "NOT (is_partial AND razlog = 'drugo') OR razlog_tekst IS NOT NULL"
    )
    
    # Create index for partial completions
    op.create_index(
        'idx_trebovanje_stavka_is_partial',
        'trebovanje_stavka',
        ['is_partial']
    )
    
    # Create index for completion tracking
    op.create_index(
        'idx_trebovanje_stavka_completed_at',
        'trebovanje_stavka',
        ['completed_at']
    )
    
    # Update existing records: set količina_pronađena = picked_qty for completed items
    op.execute("""
        UPDATE trebovanje_stavka 
        SET kolicina_pronađena = picked_qty,
            procenat_ispunjenja = CASE 
                WHEN kolicina_trazena > 0 THEN (picked_qty / kolicina_trazena * 100)
                ELSE 100
            END,
            is_partial = CASE
                WHEN picked_qty < kolicina_trazena THEN true
                ELSE false
            END
        WHERE status = 'done' AND picked_qty > 0
    """)


def downgrade():
    # Drop indexes
    op.drop_index('idx_trebovanje_stavka_completed_at', 'trebovanje_stavka')
    op.drop_index('idx_trebovanje_stavka_is_partial', 'trebovanje_stavka')
    
    # Drop check constraints
    op.drop_constraint('ck_drugo_requires_text', 'trebovanje_stavka', type_='check')
    op.drop_constraint('ck_partial_requires_lower_quantity', 'trebovanje_stavka', type_='check')
    op.drop_constraint('ck_kolicina_pronađena_le_trazena', 'trebovanje_stavka', type_='check')
    
    # Drop foreign key
    op.drop_constraint('fk_trebovanje_stavka_completed_by', 'trebovanje_stavka', type_='foreignkey')
    
    # Drop columns
    op.drop_column('trebovanje_stavka', 'completed_by_id')
    op.drop_column('trebovanje_stavka', 'completed_at')
    op.drop_column('trebovanje_stavka', 'procenat_ispunjenja')
    op.drop_column('trebovanje_stavka', 'is_partial')
    op.drop_column('trebovanje_stavka', 'razlog_tekst')
    op.drop_column('trebovanje_stavka', 'razlog')
    op.drop_column('trebovanje_stavka', 'kolicina_pronađena')
    
    # Drop enum type
    partial_reason_enum = ENUM(
        'nema_na_stanju',
        'osteceno',
        'nije_pronađeno',
        'krivi_artikal',
        'drugo',
        name='partial_completion_reason_enum'
    )
    partial_reason_enum.drop(op.get_bind(), checkfirst=True)

