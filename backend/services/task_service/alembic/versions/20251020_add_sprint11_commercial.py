"""Add Sprint-11 Commercial SaaS Features: Billing, Subscriptions, White-Label

Revision ID: 20251020_sprint11_commercial
Revises: 20251020_sprint10_final
Create Date: 2025-10-20 02:00:00.000000

Sprint WMS Phase 11 - Commercial Launch & SaaS Rollout
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB, ENUM

# revision identifiers
revision = '20251020_sprint11_commercial'
down_revision = '20251020_sprint10_final'
branch_labels = None
depends_on = None


def upgrade():
    # Create subscription plan enum
    plan_enum = ENUM(
        'free_trial',
        'standard',
        'professional',
        'enterprise',
        name='subscription_plan_enum',
        create_type=True
    )
    plan_enum.create(op.get_bind(), checkfirst=True)
    
    # Create payment method enum
    payment_method_enum = ENUM(
        'credit_card',
        'invoice',
        'wire_transfer',
        'none',
        name='payment_method_enum',
        create_type=True
    )
    payment_method_enum.create(op.get_bind(), checkfirst=True)
    
    # Create billing status enum
    billing_status_enum = ENUM(
        'active',
        'payment_due',
        'suspended',
        'cancelled',
        name='billing_status_enum',
        create_type=True
    )
    billing_status_enum.create(op.get_bind(), checkfirst=True)
    
    # Create support ticket status enum
    ticket_status_enum = ENUM(
        'open',
        'in_progress',
        'waiting_customer',
        'resolved',
        'closed',
        name='ticket_status_enum',
        create_type=True
    )
    ticket_status_enum.create(op.get_bind(), checkfirst=True)
    
    # Extend tenants table with commercial fields
    op.add_column('tenants', sa.Column('subscription_plan', plan_enum, nullable=False, server_default='free_trial'))
    op.add_column('tenants', sa.Column('billing_email', sa.String(255), nullable=True))
    op.add_column('tenants', sa.Column('company_pib', sa.String(32), nullable=True))
    op.add_column('tenants', sa.Column('contact_person', sa.String(128), nullable=True))
    op.add_column('tenants', sa.Column('contact_phone', sa.String(32), nullable=True))
    op.add_column('tenants', sa.Column('subdomain', sa.String(64), unique=True, nullable=True, index=True))
    op.add_column('tenants', sa.Column('trial_ends_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('tenants', sa.Column('activated_at', sa.DateTime(timezone=True), nullable=True))
    
    # Create subscriptions table (billing history)
    op.create_table(
        'subscriptions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False, index=True),
        sa.Column('plan', plan_enum, nullable=False),
        sa.Column('billing_status', billing_status_enum, nullable=False, server_default='active'),
        sa.Column('payment_method', payment_method_enum, nullable=False, server_default='none'),
        sa.Column('monthly_price_usd', sa.Numeric(10, 2), nullable=True),
        sa.Column('stripe_customer_id', sa.String(128), nullable=True),
        sa.Column('stripe_subscription_id', sa.String(128), nullable=True),
        sa.Column('current_period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('current_period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('next_billing_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('auto_renew', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('metadata', JSONB, nullable=False, server_default='{}'),
    )
    
    # Create usage_metrics table (track tenant usage for billing)
    op.create_table(
        'usage_metrics',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False, index=True),
        sa.Column('metric_date', sa.Date(), nullable=False, index=True),
        sa.Column('active_users', sa.Integer(), nullable=False, default=0),
        sa.Column('tasks_completed', sa.Integer(), nullable=False, default=0),
        sa.Column('devices_connected', sa.Integer(), nullable=False, default=0),
        sa.Column('api_calls', sa.Integer(), nullable=False, default=0),
        sa.Column('storage_gb', sa.Numeric(10, 2), nullable=False, default=0.0),
        sa.Column('ai_operations', sa.Integer(), nullable=False, default=0),
        sa.Column('vision_audits', sa.Integer(), nullable=False, default=0),
        sa.Column('ar_sessions', sa.Integer(), nullable=False, default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
    )
    
    # Create white_label_settings table (custom branding per tenant)
    op.create_table(
        'white_label_settings',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', UUID(as_uuid=True), sa.ForeignKey('tenants.id'), unique=True, nullable=False, index=True),
        sa.Column('logo_url', sa.String(512), nullable=True),
        sa.Column('primary_color', sa.String(7), nullable=True),  # Hex color
        sa.Column('secondary_color', sa.String(7), nullable=True),
        sa.Column('company_name_override', sa.String(128), nullable=True),
        sa.Column('custom_domain', sa.String(255), nullable=True),
        sa.Column('favicon_url', sa.String(512), nullable=True),
        sa.Column('welcome_message', sa.Text(), nullable=True),
        sa.Column('support_email', sa.String(255), nullable=True),
        sa.Column('support_phone', sa.String(32), nullable=True),
        sa.Column('metadata', JSONB, nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
    )
    
    # Create support_tickets table
    op.create_table(
        'support_tickets',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False, index=True),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True, index=True),
        sa.Column('ticket_number', sa.String(32), unique=True, nullable=False, index=True),
        sa.Column('subject', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('status', ticket_status_enum, nullable=False, server_default='open'),
        sa.Column('priority', sa.String(16), nullable=False, server_default='medium'),  # low, medium, high, urgent
        sa.Column('category', sa.String(64), nullable=True),  # technical, billing, feature_request
        sa.Column('zammad_ticket_id', sa.String(128), nullable=True),
        sa.Column('assigned_to', sa.String(128), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('metadata', JSONB, nullable=False, server_default='{}'),
    )
    
    # Create invoices table (billing records)
    op.create_table(
        'invoices',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False, index=True),
        sa.Column('subscription_id', UUID(as_uuid=True), sa.ForeignKey('subscriptions.id'), nullable=True),
        sa.Column('invoice_number', sa.String(32), unique=True, nullable=False, index=True),
        sa.Column('amount_usd', sa.Numeric(10, 2), nullable=False),
        sa.Column('tax_amount_usd', sa.Numeric(10, 2), nullable=False, default=0.0),
        sa.Column('total_usd', sa.Numeric(10, 2), nullable=False),
        sa.Column('currency', sa.String(3), nullable=False, default='USD'),
        sa.Column('status', sa.String(32), nullable=False, default='pending'),  # pending, paid, overdue, cancelled
        sa.Column('due_date', sa.Date(), nullable=False),
        sa.Column('paid_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('stripe_invoice_id', sa.String(128), nullable=True),
        sa.Column('pdf_url', sa.String(512), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('metadata', JSONB, nullable=False, server_default='{}'),
    )
    
    # Create onboarding_progress table (track tenant setup)
    op.create_table(
        'onboarding_progress',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', UUID(as_uuid=True), sa.ForeignKey('tenants.id'), unique=True, nullable=False, index=True),
        sa.Column('step_signup', sa.Boolean(), nullable=False, default=False),
        sa.Column('step_warehouse_setup', sa.Boolean(), nullable=False, default=False),
        sa.Column('step_users_invited', sa.Boolean(), nullable=False, default=False),
        sa.Column('step_devices_registered', sa.Boolean(), nullable=False, default=False),
        sa.Column('step_first_task', sa.Boolean(), nullable=False, default=False),
        sa.Column('step_payment_method', sa.Boolean(), nullable=False, default=False),
        sa.Column('completed', sa.Boolean(), nullable=False, default=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
    )
    
    # Create indexes
    op.create_index('idx_subscriptions_tenant', 'subscriptions', ['tenant_id'])
    op.create_index('idx_subscriptions_stripe_customer', 'subscriptions', ['stripe_customer_id'])
    op.create_index('idx_usage_metrics_tenant_date', 'usage_metrics', ['tenant_id', 'metric_date'])
    op.create_index('idx_support_tickets_tenant', 'support_tickets', ['tenant_id'])
    op.create_index('idx_support_tickets_status', 'support_tickets', ['status'])
    op.create_index('idx_invoices_tenant', 'invoices', ['tenant_id'])
    op.create_index('idx_invoices_status', 'invoices', ['status'])
    
    # Update default tenant with commercial fields
    op.execute("""
        UPDATE tenants 
        SET subscription_plan = 'enterprise',
            subdomain = 'demo',
            billing_email = 'admin@cunguwms.com',
            contact_person = 'System Administrator',
            activated_at = NOW()
        WHERE domain = 'localhost';
    """)


def downgrade():
    # Drop tables
    op.drop_table('onboarding_progress')
    op.drop_table('invoices')
    op.drop_table('support_tickets')
    op.drop_table('white_label_settings')
    op.drop_table('usage_metrics')
    op.drop_table('subscriptions')
    
    # Drop tenant columns
    op.drop_column('tenants', 'activated_at')
    op.drop_column('tenants', 'trial_ends_at')
    op.drop_column('tenants', 'subdomain')
    op.drop_column('tenants', 'contact_phone')
    op.drop_column('tenants', 'contact_person')
    op.drop_column('tenants', 'company_pib')
    op.drop_column('tenants', 'billing_email')
    op.drop_column('tenants', 'subscription_plan')
    
    # Drop enums
    ticket_status_enum = ENUM(name='ticket_status_enum')
    ticket_status_enum.drop(op.get_bind(), checkfirst=True)
    
    billing_status_enum = ENUM(name='billing_status_enum')
    billing_status_enum.drop(op.get_bind(), checkfirst=True)
    
    payment_method_enum = ENUM(name='payment_method_enum')
    payment_method_enum.drop(op.get_bind(), checkfirst=True)
    
    plan_enum = ENUM(name='subscription_plan_enum')
    plan_enum.drop(op.get_bind(), checkfirst=True)

