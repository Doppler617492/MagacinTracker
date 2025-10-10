"""User Management & RBAC System

Revision ID: 2024120101
Revises: 2024050601
Create Date: 2024-12-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '2024120101'
down_revision = '2024050601'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create user_role_enum
    user_role_enum = postgresql.ENUM(
        'ADMIN', 'MENADZER', 'SEF', 'KOMERCIJALISTA', 'MAGACIONER',
        name='user_role_enum'
    )
    user_role_enum.create(op.get_bind())
    
    # Create users table
    op.create_table('users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('first_name', sa.String(length=100), nullable=False),
        sa.Column('last_name', sa.String(length=100), nullable=False),
        sa.Column('role', user_role_enum, nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('last_login', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
    )
    
    # Create indexes
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    op.create_index('ix_users_role', 'users', ['role'])
    op.create_index('ix_users_is_active', 'users', ['is_active'])
    
    # Update audit_action_enum to include authentication actions
    op.execute("ALTER TYPE audit_action ADD VALUE 'LOGIN_SUCCESS'")
    op.execute("ALTER TYPE audit_action ADD VALUE 'LOGIN_FAILED'")
    op.execute("ALTER TYPE audit_action ADD VALUE 'LOGOUT'")
    op.execute("ALTER TYPE audit_action ADD VALUE 'PASSWORD_RESET'")
    op.execute("ALTER TYPE audit_action ADD VALUE 'USER_CREATED'")
    op.execute("ALTER TYPE audit_action ADD VALUE 'USER_ROLE_CHANGED'")
    op.execute("ALTER TYPE audit_action ADD VALUE 'USER_DEACTIVATED'")
    
    # Update audit_log table
    op.add_column('audit_log', sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('audit_log', sa.Column('ip_address', sa.String(length=45), nullable=True))
    op.add_column('audit_log', sa.Column('user_agent', sa.String(length=500), nullable=True))
    
    # Add foreign key constraint
    op.create_foreign_key('fk_audit_log_user_id', 'audit_log', 'users', ['user_id'], ['id'])
    
    # Create indexes for audit_log
    op.create_index('ix_audit_log_user_id', 'audit_log', ['user_id'])
    op.create_index('ix_audit_log_action', 'audit_log', ['action'])
    op.create_index('ix_audit_log_created_at', 'audit_log', ['created_at'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_audit_log_created_at', table_name='audit_log')
    op.drop_index('ix_audit_log_action', table_name='audit_log')
    op.drop_index('ix_audit_log_user_id', table_name='audit_log')
    
    # Drop foreign key constraint
    op.drop_constraint('fk_audit_log_user_id', 'audit_log', type_='foreignkey')
    
    # Drop columns from audit_log
    op.drop_column('audit_log', 'user_agent')
    op.drop_column('audit_log', 'ip_address')
    op.drop_column('audit_log', 'user_id')
    
    # Note: Cannot remove enum values in PostgreSQL, so we leave them
    
    # Drop users table
    op.drop_index('ix_users_is_active', table_name='users')
    op.drop_index('ix_users_role', table_name='users')
    op.drop_index('ix_users_email', table_name='users')
    op.drop_table('users')
    
    # Drop user_role_enum
    op.execute("DROP TYPE user_role_enum")
