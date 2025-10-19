"""
Feature Flags for Sprint WMS Phase 2
Enable gradual rollout of new features
"""
from enum import Enum
from typing import Dict
import os

class FeatureFlag(str, Enum):
    """Feature flags for WMS features"""
    FF_RECEIVING = "FF_RECEIVING"  # Receiving (Prijem) workflow
    FF_UOM_PACK = "FF_UOM_PACK"    # UoM / Case-Pack conversion
    FF_RBAC_UI = "FF_RBAC_UI"      # RBAC UI administration
    FF_CATALOG_SYNC_V2 = "FF_CATALOG_SYNC_V2"  # Hardened catalog sync


class FeatureFlagService:
    """
    Feature flag service with environment variable override
    
    Usage:
        if FeatureFlagService.is_enabled(FeatureFlag.FF_RECEIVING):
            # Show receiving features
    
    Environment variables:
        FF_RECEIVING=true
        FF_UOM_PACK=false
        FF_RBAC_UI=true
    """
    
    # Default flag states
    _flags: Dict[FeatureFlag, bool] = {
        FeatureFlag.FF_RECEIVING: True,      # Phase 2: Enabled by default
        FeatureFlag.FF_UOM_PACK: True,       # Phase 2: Enabled by default
        FeatureFlag.FF_RBAC_UI: True,        # Phase 2: Enabled by default
        FeatureFlag.FF_CATALOG_SYNC_V2: True,  # Phase 2: Enabled by default
    }
    
    @classmethod
    def is_enabled(cls, flag: FeatureFlag) -> bool:
        """
        Check if feature flag is enabled
        
        Priority:
        1. Environment variable (FF_FEATURE_NAME=true/false)
        2. Default value from _flags
        """
        # Check environment variable first
        env_var = os.getenv(flag.value)
        if env_var is not None:
            return env_var.lower() in ('true', '1', 'yes', 'on')
        
        # Fall back to default
        return cls._flags.get(flag, False)
    
    @classmethod
    def set_flag(cls, flag: FeatureFlag, enabled: bool) -> None:
        """
        Set feature flag value (runtime override)
        
        Note: This does not persist across restarts
        Use environment variables for persistent configuration
        """
        cls._flags[flag] = enabled
    
    @classmethod
    def get_all_flags(cls) -> Dict[str, bool]:
        """Get all feature flags and their current status"""
        return {
            flag.value: cls.is_enabled(flag)
            for flag in FeatureFlag
        }
    
    @classmethod
    def require_flag(cls, flag: FeatureFlag):
        """
        Decorator to require feature flag
        
        Usage:
            @router.get("/receiving")
            @FeatureFlagService.require_flag(FeatureFlag.FF_RECEIVING)
            async def list_receiving(...):
                pass
        """
        from functools import wraps
        from fastapi import HTTPException, status
        
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                if not cls.is_enabled(flag):
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Feature '{flag.value}' is not enabled"
                    )
                return await func(*args, **kwargs)
            return wrapper
        return decorator


# Convenience functions
def is_receiving_enabled() -> bool:
    """Check if receiving feature is enabled"""
    return FeatureFlagService.is_enabled(FeatureFlag.FF_RECEIVING)


def is_uom_pack_enabled() -> bool:
    """Check if UoM/Case-Pack feature is enabled"""
    return FeatureFlagService.is_enabled(FeatureFlag.FF_UOM_PACK)


def is_rbac_ui_enabled() -> bool:
    """Check if RBAC UI is enabled"""
    return FeatureFlagService.is_enabled(FeatureFlag.FF_RBAC_UI)


def is_catalog_sync_v2_enabled() -> bool:
    """Check if hardened catalog sync is enabled"""
    return FeatureFlagService.is_enabled(FeatureFlag.FF_CATALOG_SYNC_V2)

