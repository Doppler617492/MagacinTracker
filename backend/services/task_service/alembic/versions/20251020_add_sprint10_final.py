"""Add Sprint-10 Final Features: AR Collaboration, Multi-Tenancy, Route Optimization

Revision ID: 20251020_sprint10_final
Revises: 20251019_ar_restock
Create Date: 2025-10-20 01:00:00.000000

Sprint WMS Phase 10 (FINAL) - Complete Autonomous WMS Ecosystem
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB, ENUM

# revision identifiers
revision = '20251020_sprint10_final'
down_revision = '20251019_ar_restock'
branch_labels = None
depends_on = None


def upgrade():
    # Create tenant status enum
    tenant_status_enum = ENUM(
        'active',
        'suspended',
        'trial',
        'cancelled',
        name='tenant_status_enum',
        create_type=True
    )
    tenant_status_enum.create(op.get_bind(), checkfirst=True)
    
    # Create route optimization algorithm enum
    route_algorithm_enum = ENUM(
        'dijkstra',
        'genetic',
        'hybrid',
        'nearest_neighbor',
        name='route_algorithm_enum',
        create_type=True
    )
    route_algorithm_enum.create(op.get_bind(), checkfirst=True)
    
    # Create tenants table (SaaS multi-tenancy)
    op.create_table(
        'tenants',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(128), nullable=False),
        sa.Column('domain', sa.String(255), unique=True, nullable=False, index=True),
        sa.Column('db_schema', sa.String(64), unique=True, nullable=False),
        sa.Column('status', tenant_status_enum, nullable=False, default='trial'),
        sa.Column('max_warehouses', sa.Integer(), nullable=False, default=1),
        sa.Column('max_users', sa.Integer(), nullable=False, default=10),
        sa.Column('features', JSONB, nullable=False, server_default='{}'),  # Enabled features per tenant
        sa.Column('metadata', JSONB, nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
    )
    
    # Create ar_collab_sessions table (AR collaboration)
    op.create_table(
        'ar_collab_sessions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('task_id', UUID(as_uuid=True), sa.ForeignKey('zaduznica.id'), nullable=False, index=True),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False, index=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('ended_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('active_flag', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('last_action_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('metadata', JSONB, nullable=False, server_default='{}'),
    )
    
    # Create optimized_routes table (AI route & energy optimization)
    op.create_table(
        'optimized_routes',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('task_id', UUID(as_uuid=True), sa.ForeignKey('zaduznica.id'), nullable=False, index=True),
        sa.Column('algorithm_used', route_algorithm_enum, nullable=False),
        sa.Column('route_json', JSONB, nullable=False),  # Ordered waypoints
        sa.Column('original_distance_m', sa.Numeric(10, 2), nullable=True),
        sa.Column('optimized_distance_m', sa.Numeric(10, 2), nullable=True),
        sa.Column('distance_reduction_pct', sa.Numeric(5, 2), nullable=True),
        sa.Column('energy_saving_pct', sa.Numeric(5, 2), nullable=True),
        sa.Column('battery_usage_projected', sa.Numeric(5, 2), nullable=True),
        sa.Column('generated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('accepted', sa.Boolean(), nullable=True),
        sa.Column('metadata', JSONB, nullable=False, server_default='{}'),
    )
    
    # Create vision_quality_audit table (smart camera auditing)
    op.create_table(
        'vision_quality_audit',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('task_item_id', UUID(as_uuid=True), sa.ForeignKey('zaduznica_stavka.id'), nullable=True, index=True),
        sa.Column('photo_id', UUID(as_uuid=True), sa.ForeignKey('photo_attachments.id'), nullable=False),
        sa.Column('status', sa.String(32), nullable=False),  # ok, damaged, wrong_item, packaging_issue
        sa.Column('confidence', sa.Numeric(3, 2), nullable=False),
        sa.Column('flagged_issues', JSONB, nullable=False, server_default='[]'),  # Array of detected issues
        sa.Column('model_version', sa.String(32), nullable=False),
        sa.Column('processing_time_ms', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
    )
    
    # Add tenant_id to core tables (for multi-tenancy)
    op.add_column('magacin', sa.Column('tenant_id', UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=True, index=True))
    op.add_column('users', sa.Column('tenant_id', UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=True, index=True))
    
    # Create indexes
    op.create_index('idx_tenants_domain', 'tenants', ['domain'])
    op.create_index('idx_tenants_status', 'tenants', ['status'])
    op.create_index('idx_ar_collab_task_active', 'ar_collab_sessions', ['task_id', 'active_flag'])
    op.create_index('idx_optimized_routes_task', 'optimized_routes', ['task_id'])
    op.create_index('idx_vision_quality_task', 'vision_quality_audit', ['task_item_id'])
    op.create_index('idx_magacin_tenant', 'magacin', ['tenant_id'])
    op.create_index('idx_users_tenant', 'users', ['tenant_id'])
    
    # Create default tenant (for existing data)
    op.execute("""
        INSERT INTO tenants (name, domain, db_schema, status, max_warehouses, max_users)
        VALUES ('Cungu WMS', 'localhost', 'public', 'active', 100, 1000)
        ON CONFLICT DO NOTHING;
    """)


def downgrade():
    # Drop tenant references
    op.drop_column('users', 'tenant_id')
    op.drop_column('magacin', 'tenant_id')
    
    # Drop tables
    op.drop_table('vision_quality_audit')
    op.drop_table('optimized_routes')
    op.drop_table('ar_collab_sessions')
    op.drop_table('tenants')
    
    # Drop enums
    route_algorithm_enum = ENUM(name='route_algorithm_enum')
    route_algorithm_enum.drop(op.get_bind(), checkfirst=True)
    
    tenant_status_enum = ENUM(name='tenant_status_enum')
    tenant_status_enum.drop(op.get_bind(), checkfirst=True)

