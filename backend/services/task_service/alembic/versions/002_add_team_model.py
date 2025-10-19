"""add team model and shift management

Revision ID: 002_add_team_model
Revises: 001_initial_schema
Create Date: 2025-10-16 08:39:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '002_add_team_model'
down_revision = '001_initial_schema'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create team table
    op.create_table(
        'team',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False, unique=True),
        sa.Column('worker1_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('worker2_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('shift', sa.String(1), nullable=False),
        sa.Column('active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    
    # Add indexes
    op.create_index('ix_team_name', 'team', ['name'])
    op.create_index('ix_team_shift', 'team', ['shift'])
    op.create_index('ix_team_active', 'team', ['active'])
    
    # Add team_id column to zaduznica
    op.add_column('zaduznica', sa.Column('team_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key('fk_zaduznica_team_id', 'zaduznica', 'team', ['team_id'], ['id'])
    op.create_index('ix_zaduznica_team_id', 'zaduznica', ['team_id'])


def downgrade() -> None:
    # Remove team_id from zaduznica
    op.drop_index('ix_zaduznica_team_id', table_name='zaduznica')
    op.drop_constraint('fk_zaduznica_team_id', 'zaduznica', type_='foreignkey')
    op.drop_column('zaduznica', 'team_id')
    
    # Drop indexes from team table
    op.drop_index('ix_team_active', table_name='team')
    op.drop_index('ix_team_shift', table_name='team')
    op.drop_index('ix_team_name', table_name='team')
    
    # Drop team table
    op.drop_table('team')

