"""Add Sprint-12 Marketing & Automation: Partners, AI Support, CRM, Marketing

Revision ID: 20251020_sprint12_marketing
Revises: 20251020_sprint11_commercial
Create Date: 2025-10-20 03:00:00.000000

Sprint WMS Phase 12 (FINAL) - Marketing, Sales & Automation Setup
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB, ENUM

# revision identifiers
revision = '20251020_sprint12_marketing'
down_revision = '20251020_sprint11_commercial'
branch_labels = None
depends_on = None


def upgrade():
    # Create partner status enum
    partner_status_enum = ENUM(
        'active',
        'pending',
        'suspended',
        'terminated',
        name='partner_status_enum',
        create_type=True
    )
    partner_status_enum.create(op.get_bind(), checkfirst=True)
    
    # Create lead status enum
    lead_status_enum = ENUM(
        'new',
        'contacted',
        'qualified',
        'demo_scheduled',
        'trial',
        'negotiation',
        'closed_won',
        'closed_lost',
        name='lead_status_enum',
        create_type=True
    )
    lead_status_enum.create(op.get_bind(), checkfirst=True)
    
    # Create support query type enum
    support_query_type_enum = ENUM(
        'technical',
        'billing',
        'feature_request',
        'onboarding',
        'general',
        name='support_query_type_enum',
        create_type=True
    )
    support_query_type_enum.create(op.get_bind(), checkfirst=True)
    
    # Create partner_accounts table (reseller/integrator program)
    op.create_table(
        'partner_accounts',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('company_name', sa.String(255), nullable=False),
        sa.Column('contact_name', sa.String(128), nullable=False),
        sa.Column('contact_email', sa.String(255), nullable=False, unique=True, index=True),
        sa.Column('contact_phone', sa.String(32), nullable=True),
        sa.Column('status', partner_status_enum, nullable=False, server_default='pending'),
        sa.Column('region', sa.String(64), nullable=True),  # Serbia, Balkans, EU, etc.
        sa.Column('revenue_share_pct', sa.Numeric(5, 2), nullable=False, default=30.0),  # Commission %
        sa.Column('api_key', sa.String(128), unique=True, nullable=False, index=True),
        sa.Column('tenant_count', sa.Integer(), nullable=False, default=0),
        sa.Column('total_revenue_usd', sa.Numeric(12, 2), nullable=False, default=0.0),
        sa.Column('commission_earned_usd', sa.Numeric(12, 2), nullable=False, default=0.0),
        sa.Column('last_activity_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('metadata', JSONB, nullable=False, server_default='{}'),
    )
    
    # Link tenants to partners
    op.add_column('tenants', sa.Column('partner_id', UUID(as_uuid=True), sa.ForeignKey('partner_accounts.id'), nullable=True, index=True))
    
    # Create sales_leads table (CRM integration)
    op.create_table(
        'sales_leads',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('first_name', sa.String(64), nullable=False),
        sa.Column('last_name', sa.String(64), nullable=False),
        sa.Column('email', sa.String(255), nullable=False, index=True),
        sa.Column('phone', sa.String(32), nullable=True),
        sa.Column('company', sa.String(255), nullable=True),
        sa.Column('status', lead_status_enum, nullable=False, server_default='new'),
        sa.Column('lead_score', sa.Numeric(3, 2), nullable=True),  # AI prediction 0.0-1.0
        sa.Column('source', sa.String(64), nullable=True),  # website, referral, partner, etc.
        sa.Column('utm_campaign', sa.String(128), nullable=True),
        sa.Column('utm_source', sa.String(128), nullable=True),
        sa.Column('utm_medium', sa.String(128), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('crm_id', sa.String(128), nullable=True),  # HubSpot/EspoCRM ID
        sa.Column('partner_id', UUID(as_uuid=True), sa.ForeignKey('partner_accounts.id'), nullable=True, index=True),
        sa.Column('tenant_id', UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=True, index=True),  # If converted
        sa.Column('assigned_to', sa.String(128), nullable=True),
        sa.Column('demo_scheduled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('converted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('lost_reason', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('metadata', JSONB, nullable=False, server_default='{}'),
    )
    
    # Create ai_support_queries table (chatbot logs)
    op.create_table(
        'ai_support_queries',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=True, index=True),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True, index=True),
        sa.Column('session_id', sa.String(128), nullable=False, index=True),
        sa.Column('query_text', sa.Text(), nullable=False),
        sa.Column('query_type', support_query_type_enum, nullable=True),
        sa.Column('ai_response', sa.Text(), nullable=True),
        sa.Column('model_used', sa.String(64), nullable=True),  # gpt-4, gpt-3.5-turbo, etc.
        sa.Column('confidence', sa.Numeric(3, 2), nullable=True),
        sa.Column('resolved', sa.Boolean(), nullable=False, default=False),
        sa.Column('escalated_to_ticket', sa.Boolean(), nullable=False, default=False),
        sa.Column('ticket_id', UUID(as_uuid=True), sa.ForeignKey('support_tickets.id'), nullable=True),
        sa.Column('feedback_score', sa.Integer(), nullable=True),  # 1-5 rating
        sa.Column('processing_time_ms', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('metadata', JSONB, nullable=False, server_default='{}'),
    )
    
    # Create marketing_campaigns table
    op.create_table(
        'marketing_campaigns',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('campaign_type', sa.String(64), nullable=False),  # email, ads, content, social
        sa.Column('status', sa.String(32), nullable=False, default='draft'),  # draft, active, paused, completed
        sa.Column('start_date', sa.Date(), nullable=True),
        sa.Column('end_date', sa.Date(), nullable=True),
        sa.Column('budget_usd', sa.Numeric(10, 2), nullable=True),
        sa.Column('spent_usd', sa.Numeric(10, 2), nullable=False, default=0.0),
        sa.Column('impressions', sa.Integer(), nullable=False, default=0),
        sa.Column('clicks', sa.Integer(), nullable=False, default=0),
        sa.Column('conversions', sa.Integer(), nullable=False, default=0),
        sa.Column('ctr_pct', sa.Numeric(5, 2), nullable=True),  # Click-through rate
        sa.Column('conversion_rate_pct', sa.Numeric(5, 2), nullable=True),
        sa.Column('cost_per_lead_usd', sa.Numeric(8, 2), nullable=True),
        sa.Column('ai_optimized', sa.Boolean(), nullable=False, default=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('metadata', JSONB, nullable=False, server_default='{}'),
    )
    
    # Create blog_posts table (AI-generated content)
    op.create_table(
        'blog_posts',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('slug', sa.String(255), unique=True, nullable=False, index=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('excerpt', sa.Text(), nullable=True),
        sa.Column('language', sa.String(5), nullable=False, default='sr'),  # sr, en
        sa.Column('author', sa.String(128), nullable=True),
        sa.Column('ai_generated', sa.Boolean(), nullable=False, default=False),
        sa.Column('published', sa.Boolean(), nullable=False, default=False),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('views', sa.Integer(), nullable=False, default=0),
        sa.Column('seo_title', sa.String(255), nullable=True),
        sa.Column('seo_description', sa.String(512), nullable=True),
        sa.Column('seo_keywords', sa.String(512), nullable=True),
        sa.Column('featured_image_url', sa.String(512), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('metadata', JSONB, nullable=False, server_default='{}'),
    )
    
    # Create newsletter_subscribers table
    op.create_table(
        'newsletter_subscribers',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('email', sa.String(255), unique=True, nullable=False, index=True),
        sa.Column('name', sa.String(128), nullable=True),
        sa.Column('language', sa.String(5), nullable=False, default='sr'),
        sa.Column('subscribed', sa.Boolean(), nullable=False, default=True),
        sa.Column('subscribed_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('unsubscribed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('source', sa.String(64), nullable=True),
        sa.Column('metadata', JSONB, nullable=False, server_default='{}'),
    )
    
    # Create website_analytics table (aggregated daily)
    op.create_table(
        'website_analytics',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('date', sa.Date(), nullable=False, unique=True, index=True),
        sa.Column('page_views', sa.Integer(), nullable=False, default=0),
        sa.Column('unique_visitors', sa.Integer(), nullable=False, default=0),
        sa.Column('signups', sa.Integer(), nullable=False, default=0),
        sa.Column('trial_starts', sa.Integer(), nullable=False, default=0),
        sa.Column('conversions', sa.Integer(), nullable=False, default=0),
        sa.Column('bounce_rate_pct', sa.Numeric(5, 2), nullable=True),
        sa.Column('avg_session_duration_sec', sa.Integer(), nullable=True),
        sa.Column('top_pages', JSONB, nullable=False, server_default='[]'),
        sa.Column('top_sources', JSONB, nullable=False, server_default='[]'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
    )
    
    # Create indexes
    op.create_index('idx_partner_accounts_status', 'partner_accounts', ['status'])
    op.create_index('idx_partner_accounts_api_key', 'partner_accounts', ['api_key'])
    op.create_index('idx_sales_leads_status', 'sales_leads', ['status'])
    op.create_index('idx_sales_leads_email', 'sales_leads', ['email'])
    op.create_index('idx_sales_leads_score', 'sales_leads', ['lead_score'])
    op.create_index('idx_ai_support_session', 'ai_support_queries', ['session_id'])
    op.create_index('idx_ai_support_tenant', 'ai_support_queries', ['tenant_id'])
    op.create_index('idx_blog_posts_slug', 'blog_posts', ['slug'])
    op.create_index('idx_blog_posts_published', 'blog_posts', ['published', 'published_at'])
    op.create_index('idx_newsletter_email', 'newsletter_subscribers', ['email'])
    op.create_index('idx_website_analytics_date', 'website_analytics', ['date'])
    
    # Add partner reference to tenants
    op.create_index('idx_tenants_partner', 'tenants', ['partner_id'])


def downgrade():
    # Drop indexes
    op.drop_index('idx_tenants_partner', 'tenants')
    
    # Drop tables
    op.drop_table('website_analytics')
    op.drop_table('newsletter_subscribers')
    op.drop_table('blog_posts')
    op.drop_table('marketing_campaigns')
    op.drop_table('ai_support_queries')
    op.drop_table('sales_leads')
    
    # Drop partner reference from tenants
    op.drop_column('tenants', 'partner_id')
    
    op.drop_table('partner_accounts')
    
    # Drop enums
    support_query_type_enum = ENUM(name='support_query_type_enum')
    support_query_type_enum.drop(op.get_bind(), checkfirst=True)
    
    lead_status_enum = ENUM(name='lead_status_enum')
    lead_status_enum.drop(op.get_bind(), checkfirst=True)
    
    partner_status_enum = ENUM(name='partner_status_enum')
    partner_status_enum.drop(op.get_bind(), checkfirst=True)

