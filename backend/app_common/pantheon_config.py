"""
Pantheon API Configuration
Enterprise-grade configuration for CunguWMS Pantheon integration
"""
from __future__ import annotations

import os
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class PantheonConfig(BaseSettings):
    """Pantheon API Configuration with enterprise defaults"""
    
    # API Credentials - CORRECTED (HOTFIX 2025-10-17)
    base_url: str = Field(
        default="http://cungu.pantheonmn.net:3003",
        description="Pantheon API base URL"
    )
    username: str = Field(
        default="CunguWMS",
        description="Pantheon API username"
    )
    password: str = Field(
        default="C!g#2W4s5#$M6",
        description="Pantheon API password"
    )
    
    # Rate Limiting & Timeouts
    rate_limit_rps: int = Field(
        default=1,
        description="Rate limit: requests per second (strict Pantheon limit)"
    )
    timeout_ms: int = Field(
        default=10000,
        description="Request timeout in milliseconds"
    )
    retry_max: int = Field(
        default=3,
        description="Maximum number of retries for failed requests"
    )
    
    # Circuit Breaker
    circuit_breaker_threshold: int = Field(
        default=3,
        description="Number of failures before circuit breaker opens"
    )
    circuit_breaker_timeout_s: int = Field(
        default=120,
        description="Circuit breaker timeout in seconds (2 minutes)"
    )
    
    # Delta Sync Configuration
    delta_window_days: int = Field(
        default=1,
        description="Number of days to look back for delta sync"
    )
    page_limit: int = Field(
        default=1000,
        description="Page size for paginated API requests"
    )
    
    # Sync Schedules (Cron Format)
    sync_schedule_catalog: str = Field(
        default="0 2 * * *",
        description="Catalog sync schedule (daily at 02:00)"
    )
    sync_schedule_subjects: str = Field(
        default="30 2 * * *",
        description="Subjects sync schedule (daily at 02:30)"
    )
    sync_schedule_issue: str = Field(
        default="0 */2 * * *",
        description="Issue documents sync schedule (every 2 hours)"
    )
    sync_schedule_receipt: str = Field(
        default="30 */2 * * *",
        description="Receipt documents sync schedule (every 2 hours, offset 30min)"
    )
    
    # Warehouse Configuration
    wms_magacin_code: str = Field(
        default="VELE_TEST",
        description="WMS warehouse code for filtering"
    )
    
    # Timezone
    timezone: str = Field(
        default="Europe/Belgrade",
        description="System timezone"
    )
    
    # Token Management
    token_refresh_buffer_minutes: int = Field(
        default=5,
        description="Refresh token N minutes before expiration"
    )
    
    # Monitoring & Metrics
    metrics_enabled: bool = Field(
        default=True,
        description="Enable Prometheus metrics"
    )
    
    class Config:
        env_prefix = "CUNGUWMS_"
        case_sensitive = False


# Global instance
pantheon_config = PantheonConfig()

