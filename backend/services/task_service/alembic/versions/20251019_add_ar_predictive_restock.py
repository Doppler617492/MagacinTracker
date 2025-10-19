"""Add AR Interface and Predictive Re-stocking with Pantheon Integration

Revision ID: 20251019_ar_restock
Revises: 20251019_voice_control
Create Date: 2025-10-20 00:00:00.000000

Sprint WMS Phase 9 - AR + Predictive Re-stocking (Real Data Only)
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB, ENUM

# revision identifiers
revision = '20251019_ar_restock'
down_revision = '20251019_voice_control'
branch_labels = None
depends_on = None


def upgrade():
    # Create AR session status enum
    ar_session_status_enum = ENUM(
        'active',
        'paused',
        'completed',
        'error',
        name='ar_session_status_enum',
        create_type=True
    )
    ar_session_status_enum.create(op.get_bind(), checkfirst=True)
    
    # Create restock suggestion status enum
    restock_status_enum = ENUM(
        'pending',
        'approved',
        'rejected',
        'ordered',
        'received',
        name='restock_status_enum',
        create_type=True
    )
    restock_status_enum.create(op.get_bind(), checkfirst=True)
    
    # Add 3D coordinates to location_v2 (for AR)
    op.add_column('location_v2', sa.Column('z_coordinate', sa.Numeric(8, 2), nullable=True))
    op.add_column('location_v2', sa.Column('height_m', sa.Numeric(5, 2), nullable=True))
    
    # Create ar_sessions table
    op.create_table(
        'ar_sessions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False, index=True),
        sa.Column('task_id', UUID(as_uuid=True), sa.ForeignKey('zaduznica.id'), nullable=True, index=True),
        sa.Column('device_id', sa.String(128), nullable=True),
        sa.Column('status', ar_session_status_enum, nullable=False, default='active'),
        sa.Column('route_data', JSONB, nullable=False, server_default='[]'),  # Ordered waypoints
        sa.Column('current_step', sa.Integer(), nullable=False, default=0),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('metadata', JSONB, nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
    )
    
    # Create restock_suggestions table (AI-driven + Pantheon-integrated)
    op.create_table(
        'restock_suggestions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('article_id', UUID(as_uuid=True), sa.ForeignKey('artikal.id'), nullable=False, index=True),
        sa.Column('warehouse_id', UUID(as_uuid=True), sa.ForeignKey('magacin.id'), nullable=False, index=True),
        sa.Column('current_stock', sa.Numeric(12, 3), nullable=False),
        sa.Column('predicted_need', sa.Numeric(12, 3), nullable=False),
        sa.Column('suggested_quantity', sa.Numeric(12, 3), nullable=False),
        sa.Column('confidence', sa.Numeric(3, 2), nullable=False),  # 0.0-1.0
        sa.Column('due_date', sa.Date(), nullable=False, index=True),
        sa.Column('status', restock_status_enum, nullable=False, default='pending', index=True),
        sa.Column('forecast_data', JSONB, nullable=False, server_default='{}'),  # Historical data, trend
        sa.Column('pantheon_data', JSONB, nullable=False, server_default='{}'),  # Sales data from Pantheon
        sa.Column('approved_by_id', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('rejection_reason', sa.String(500), nullable=True),
        sa.Column('pantheon_order_id', sa.String(128), nullable=True),  # If ordered via Pantheon
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
    )
    
    # Create predictive_model_runs table (track forecasting performance)
    op.create_table(
        'predictive_model_runs',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('run_type', sa.String(64), nullable=False),  # restock_forecast, demand_prediction
        sa.Column('warehouse_id', UUID(as_uuid=True), sa.ForeignKey('magacin.id'), nullable=True),
        sa.Column('articles_analyzed', sa.Integer(), nullable=False),
        sa.Column('suggestions_generated', sa.Integer(), nullable=False),
        sa.Column('model_version', sa.String(32), nullable=False),
        sa.Column('parameters', JSONB, nullable=False, server_default='{}'),
        sa.Column('performance_metrics', JSONB, nullable=False, server_default='{}'),  # Accuracy, MAPE, etc.
        sa.Column('execution_time_ms', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
    )
    
    # Create indexes
    op.create_index('idx_ar_sessions_user_task', 'ar_sessions', ['user_id', 'task_id'])
    op.create_index('idx_ar_sessions_status', 'ar_sessions', ['status'])
    op.create_index('idx_restock_suggestions_status_due', 'restock_suggestions', ['status', 'due_date'])
    op.create_index('idx_restock_suggestions_warehouse', 'restock_suggestions', ['warehouse_id', 'created_at'])
    op.create_index('idx_predictive_model_runs_type', 'predictive_model_runs', ['run_type', 'created_at'])


def downgrade():
    # Drop tables
    op.drop_table('predictive_model_runs')
    op.drop_table('restock_suggestions')
    op.drop_table('ar_sessions')
    
    # Drop columns from location_v2
    op.drop_column('location_v2', 'height_m')
    op.drop_column('location_v2', 'z_coordinate')
    
    # Drop enums
    restock_status_enum = ENUM(name='restock_status_enum')
    restock_status_enum.drop(op.get_bind(), checkfirst=True)
    
    ar_session_status_enum = ENUM(name='ar_session_status_enum')
    ar_session_status_enum.drop(op.get_bind(), checkfirst=True)

