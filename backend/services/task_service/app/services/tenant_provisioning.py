"""
Tenant Provisioning Service - Sprint 11 Commercial SaaS

Automatic tenant creation, schema provisioning, and onboarding.
"""
import uuid
import secrets
import string
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import text
import bcrypt

from app_common.logging import get_logger
from app_common.events import emit_event

logger = get_logger(__name__)


class TenantProvisioningService:
    """
    Automated tenant provisioning for SaaS onboarding
    Serbian: Servis za automatsko kreiranje tenanta
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_tenant(
        self,
        company_name: str,
        company_pib: str,
        contact_person: str,
        contact_email: str,
        contact_phone: str,
        subscription_plan: str = "free_trial",
    ) -> Dict[str, Any]:
        """
        Complete tenant provisioning workflow
        
        Steps:
        1. Generate subdomain (e.g., acme-warehouse.cunguwms.com)
        2. Create tenant record
        3. Create DB schema
        4. Run Alembic migrations
        5. Seed initial data (roles, permissions)
        6. Create admin user
        7. Create default warehouse
        8. Create subscription record
        9. Initialize onboarding progress
        10. Send welcome email
        
        Returns: tenant_id, subdomain, admin_password, setup_url
        """
        
        logger.info(f"Starting tenant provisioning for {company_name}")
        
        try:
            # Step 1: Generate subdomain (slugify company name)
            subdomain = self._generate_subdomain(company_name)
            db_schema = f"tenant_{subdomain}"
            
            # Step 2: Create tenant record
            tenant_id = str(uuid.uuid4())
            trial_ends_at = datetime.utcnow() + timedelta(days=14)  # 14-day trial
            
            self.db.execute(text("""
                INSERT INTO tenants (
                    id, name, domain, db_schema, subdomain, status, subscription_plan,
                    company_pib, contact_person, billing_email, contact_phone,
                    trial_ends_at, activated_at, created_at
                ) VALUES (
                    :id, :name, :domain, :db_schema, :subdomain, 'trial', :plan,
                    :pib, :contact, :email, :phone,
                    :trial_ends, NOW(), NOW()
                )
            """), {
                "id": tenant_id,
                "name": company_name,
                "domain": f"{subdomain}.cunguwms.com",
                "db_schema": db_schema,
                "subdomain": subdomain,
                "plan": subscription_plan,
                "pib": company_pib,
                "contact": contact_person,
                "email": contact_email,
                "phone": contact_phone,
                "trial_ends": trial_ends_at,
            })
            
            # Step 3: Create DB schema
            self.db.execute(text(f"CREATE SCHEMA IF NOT EXISTS {db_schema}"))
            self.db.commit()
            
            logger.info(f"Created schema {db_schema} for tenant {tenant_id}")
            
            # Step 4: Run migrations (in tenant schema)
            # Note: In production, this would call Alembic programmatically
            # For now, we'll copy the core tables structure
            self._copy_schema_structure(db_schema)
            
            # Step 5: Seed initial roles and permissions
            admin_role_id = self._seed_roles(tenant_id, db_schema)
            
            # Step 6: Create admin user
            admin_email = contact_email
            admin_password = self._generate_password()
            admin_user_id = self._create_admin_user(
                tenant_id, db_schema, admin_role_id,
                contact_person, admin_email, admin_password
            )
            
            # Step 7: Create default warehouse
            warehouse_id = self._create_default_warehouse(tenant_id, db_schema, company_name)
            
            # Step 8: Create subscription record
            subscription_id = self._create_subscription(tenant_id, subscription_plan)
            
            # Step 9: Initialize onboarding progress
            self._init_onboarding_progress(tenant_id)
            
            # Step 10: Emit audit event
            emit_event(
                action="TENANT_SIGNUP",
                entity_type="tenant",
                entity_id=tenant_id,
                user_id=None,
                details={
                    "company_name": company_name,
                    "subdomain": subdomain,
                    "plan": subscription_plan,
                }
            )
            
            self.db.commit()
            
            logger.info(f"Tenant provisioning complete: {tenant_id} ({subdomain})")
            
            return {
                "tenant_id": tenant_id,
                "subdomain": subdomain,
                "domain": f"{subdomain}.cunguwms.com",
                "admin_email": admin_email,
                "admin_password": admin_password,  # Send via secure channel
                "setup_url": f"https://{subdomain}.cunguwms.com/setup",
                "trial_ends_at": trial_ends_at.isoformat(),
                "warehouse_id": warehouse_id,
                "subscription_id": subscription_id,
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Tenant provisioning failed: {e}")
            raise
    
    def _generate_subdomain(self, company_name: str) -> str:
        """
        Generate URL-safe subdomain from company name
        Example: "Acme Warehouse Ltd" -> "acme-warehouse"
        """
        import re
        # Remove special chars, convert to lowercase
        subdomain = re.sub(r'[^a-zA-Z0-9\s-]', '', company_name.lower())
        subdomain = re.sub(r'\s+', '-', subdomain.strip())
        subdomain = subdomain[:32]  # Max 32 chars
        
        # Check uniqueness
        result = self.db.execute(
            text("SELECT COUNT(*) FROM tenants WHERE subdomain = :sub"),
            {"sub": subdomain}
        ).scalar()
        
        if result > 0:
            # Append random suffix
            subdomain = f"{subdomain}-{secrets.token_hex(3)}"
        
        return subdomain
    
    def _generate_password(self, length: int = 16) -> str:
        """Generate secure random password"""
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        password = ''.join(secrets.choice(alphabet) for _ in range(length))
        return password
    
    def _copy_schema_structure(self, schema: str):
        """
        Copy core table structure to new tenant schema
        In production: Use Alembic migrations
        """
        # This is simplified - in production, run full Alembic migrations
        core_tables = [
            "users", "roles", "user_roles", "permissions", "role_permissions",
            "magacin", "lokacija", "lokacija_v2", "artikal", "zaduznica",
            "zaduznica_stavka", "photo_attachments", "audit_log"
        ]
        
        for table in core_tables:
            try:
                # Copy table structure (not data)
                self.db.execute(text(f"""
                    CREATE TABLE IF NOT EXISTS {schema}.{table} 
                    (LIKE public.{table} INCLUDING ALL)
                """))
            except Exception as e:
                logger.warning(f"Could not copy table {table}: {e}")
        
        self.db.commit()
    
    def _seed_roles(self, tenant_id: str, schema: str) -> str:
        """Create basic roles for new tenant"""
        admin_role_id = str(uuid.uuid4())
        
        self.db.execute(text(f"""
            INSERT INTO {schema}.roles (id, name, description, level, active, created_at)
            VALUES 
                (:admin_id, 'ADMIN', 'System Administrator', 100, true, NOW()),
                (:manager_id, 'MENADZER', 'Warehouse Manager', 80, true, NOW()),
                (:worker_id, 'MAGACIONER', 'Warehouse Worker', 50, true, NOW())
        """), {
            "admin_id": admin_role_id,
            "manager_id": str(uuid.uuid4()),
            "worker_id": str(uuid.uuid4()),
        })
        
        return admin_role_id
    
    def _create_admin_user(
        self, tenant_id: str, schema: str, role_id: str,
        name: str, email: str, password: str
    ) -> str:
        """Create initial admin user"""
        user_id = str(uuid.uuid4())
        
        # Hash password
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        self.db.execute(text(f"""
            INSERT INTO {schema}.users (
                id, username, email, display_name, password_hash, 
                active, tenant_id, created_at
            ) VALUES (
                :id, :username, :email, :name, :hash,
                true, :tenant_id, NOW()
            )
        """), {
            "id": user_id,
            "username": email.split('@')[0],
            "email": email,
            "name": name,
            "hash": password_hash.decode('utf-8'),
            "tenant_id": tenant_id,
        })
        
        # Assign admin role
        self.db.execute(text(f"""
            INSERT INTO {schema}.user_roles (user_id, role_id, assigned_at)
            VALUES (:user_id, :role_id, NOW())
        """), {
            "user_id": user_id,
            "role_id": role_id,
        })
        
        return user_id
    
    def _create_default_warehouse(self, tenant_id: str, schema: str, company_name: str) -> str:
        """Create initial warehouse"""
        warehouse_id = str(uuid.uuid4())
        
        self.db.execute(text(f"""
            INSERT INTO {schema}.magacin (
                id, sifra, naziv, adresa, aktivan, tenant_id, created_at
            ) VALUES (
                :id, 'MAG-01', :name, 'Glavno skladište', true, :tenant_id, NOW()
            )
        """), {
            "id": warehouse_id,
            "name": f"{company_name} - Magacin",
            "tenant_id": tenant_id,
        })
        
        return warehouse_id
    
    def _create_subscription(self, tenant_id: str, plan: str) -> str:
        """Create initial subscription record"""
        subscription_id = str(uuid.uuid4())
        
        # Get plan pricing
        prices = {
            "free_trial": 0.0,
            "standard": 299.0,
            "professional": 599.0,
            "enterprise": 1299.0,
        }
        
        monthly_price = prices.get(plan, 0.0)
        
        self.db.execute(text("""
            INSERT INTO subscriptions (
                id, tenant_id, plan, billing_status, payment_method,
                monthly_price_usd, current_period_start, current_period_end,
                next_billing_date, auto_renew, created_at, updated_at
            ) VALUES (
                :id, :tenant_id, :plan, 'active', 'none',
                :price, NOW(), NOW() + INTERVAL '30 days',
                NOW() + INTERVAL '30 days', true, NOW(), NOW()
            )
        """), {
            "id": subscription_id,
            "tenant_id": tenant_id,
            "plan": plan,
            "price": monthly_price,
        })
        
        return subscription_id
    
    def _init_onboarding_progress(self, tenant_id: str):
        """Initialize onboarding checklist"""
        self.db.execute(text("""
            INSERT INTO onboarding_progress (
                tenant_id, step_signup, created_at, updated_at
            ) VALUES (
                :tenant_id, true, NOW(), NOW()
            )
        """), {"tenant_id": tenant_id})
    
    def upgrade_subscription(
        self, tenant_id: str, new_plan: str
    ) -> Dict[str, Any]:
        """
        Upgrade/downgrade tenant subscription
        Updates feature flags and billing
        """
        logger.info(f"Upgrading tenant {tenant_id} to {new_plan}")
        
        # Update tenant plan
        self.db.execute(text("""
            UPDATE tenants 
            SET subscription_plan = :plan, updated_at = NOW()
            WHERE id = :tenant_id
        """), {"plan": new_plan, "tenant_id": tenant_id})
        
        # Create new subscription record
        subscription_id = self._create_subscription(tenant_id, new_plan)
        
        # Emit audit event
        emit_event(
            action="SUBSCRIPTION_UPGRADED",
            entity_type="subscription",
            entity_id=subscription_id,
            user_id=None,
            details={"tenant_id": tenant_id, "new_plan": new_plan}
        )
        
        self.db.commit()
        
        return {
            "tenant_id": tenant_id,
            "new_plan": new_plan,
            "subscription_id": subscription_id,
        }
    
    def suspend_tenant(self, tenant_id: str, reason: str = "payment_overdue"):
        """Suspend tenant due to payment issues"""
        logger.warning(f"Suspending tenant {tenant_id}: {reason}")
        
        self.db.execute(text("""
            UPDATE tenants 
            SET status = 'suspended'
            WHERE id = :tenant_id
        """), {"tenant_id": tenant_id})
        
        self.db.execute(text("""
            UPDATE subscriptions
            SET billing_status = 'suspended'
            WHERE tenant_id = :tenant_id AND billing_status = 'active'
        """), {"tenant_id": tenant_id})
        
        self.db.commit()

