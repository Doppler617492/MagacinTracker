"""
Feature Flags for Sprint WMS Phase 2
Enable gradual rollout of new features
"""
from enum import Enum
from typing import Dict
import os

class FeatureFlag(str, Enum):
    """Feature flags for WMS features"""
    # Phase 2
    FF_RECEIVING = "FF_RECEIVING"  # Receiving (Prijem) workflow
    FF_UOM_PACK = "FF_UOM_PACK"    # UoM / Case-Pack conversion
    FF_RBAC_UI = "FF_RBAC_UI"      # RBAC UI administration
    FF_CATALOG_SYNC_V2 = "FF_CATALOG_SYNC_V2"  # Hardened catalog sync
    
    # Phase 4 - AI Intelligence Layer
    FF_AI_BIN_ALLOCATION = "FF_AI_BIN_ALLOCATION"  # AI-powered bin suggestions
    FF_AI_RESTOCKING = "FF_AI_RESTOCKING"          # Predictive restocking
    FF_AI_ANOMALY = "FF_AI_ANOMALY"                # Anomaly detection
    FF_SMART_KPI = "FF_SMART_KPI"                  # Smart KPI & benchmarking
    
    # Phase 5 - IoT Integration Layer
    FF_IOT_RFID = "FF_IOT_RFID"                    # RFID gateway integration
    FF_IOT_DOORS = "FF_IOT_DOORS"                  # Industrial door control
    FF_IOT_CAMERA = "FF_IOT_CAMERA"                # Camera verification & photos
    FF_IOT_TELEMETRY = "FF_IOT_TELEMETRY"          # Sensor telemetry & alerts
    FF_VISION_COUNT = "FF_VISION_COUNT"            # Vision-based cycle counting
    
    # Phase 6 - RFID Locations & Live Map
    FF_LOCATIONS = "FF_LOCATIONS"                  # Location management
    FF_RFID_ZONES = "FF_RFID_ZONES"                # RFID zone tracking
    FF_LIVE_MAP = "FF_LIVE_MAP"                    # Live map with WebSocket
    FF_PICK_TO_LIGHT = "FF_PICK_TO_LIGHT"          # Pick-to-light indicators
    FF_PALLET_TRACKING = "FF_PALLET_TRACKING"      # Handling unit tracking
    
    # Phase 7 - Vision AI & Robotics
    FF_VISION_AI = "FF_VISION_AI"                  # Vision AI image analysis
    FF_AMR_INTEGRATION = "FF_AMR_INTEGRATION"      # AMR robotics integration
    FF_LIGHT_GUIDANCE = "FF_LIGHT_GUIDANCE"        # LED light guidance


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
        # Phase 2: Enabled by default
        FeatureFlag.FF_RECEIVING: True,
        FeatureFlag.FF_UOM_PACK: True,
        FeatureFlag.FF_RBAC_UI: True,
        FeatureFlag.FF_CATALOG_SYNC_V2: True,
        
        # Phase 4 - AI: Disabled by default for safe rollout
        FeatureFlag.FF_AI_BIN_ALLOCATION: False,
        FeatureFlag.FF_AI_RESTOCKING: False,
        FeatureFlag.FF_AI_ANOMALY: False,
        FeatureFlag.FF_SMART_KPI: False,
        
        # Phase 5 - IoT: Disabled by default for safe rollout
        FeatureFlag.FF_IOT_RFID: False,
        FeatureFlag.FF_IOT_DOORS: False,
        FeatureFlag.FF_IOT_CAMERA: False,
        FeatureFlag.FF_IOT_TELEMETRY: False,
        FeatureFlag.FF_VISION_COUNT: False,
        
        # Phase 6 - RFID Locations: Disabled by default for safe rollout
        FeatureFlag.FF_LOCATIONS: False,
        FeatureFlag.FF_RFID_ZONES: False,
        FeatureFlag.FF_LIVE_MAP: False,
        FeatureFlag.FF_PICK_TO_LIGHT: False,
        FeatureFlag.FF_PALLET_TRACKING: False,
        
        # Phase 7 - Vision AI & Robotics: Disabled by default
        FeatureFlag.FF_VISION_AI: False,
        FeatureFlag.FF_AMR_INTEGRATION: False,
        FeatureFlag.FF_LIGHT_GUIDANCE: False,
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


# Phase 4 - AI Intelligence Layer
def is_ai_bin_allocation_enabled() -> bool:
    """Check if AI bin allocation is enabled"""
    return FeatureFlagService.is_enabled(FeatureFlag.FF_AI_BIN_ALLOCATION)


def is_ai_restocking_enabled() -> bool:
    """Check if AI restocking is enabled"""
    return FeatureFlagService.is_enabled(FeatureFlag.FF_AI_RESTOCKING)


def is_ai_anomaly_enabled() -> bool:
    """Check if AI anomaly detection is enabled"""
    return FeatureFlagService.is_enabled(FeatureFlag.FF_AI_ANOMALY)


def is_smart_kpi_enabled() -> bool:
    """Check if Smart KPI is enabled"""
    return FeatureFlagService.is_enabled(FeatureFlag.FF_SMART_KPI)


# Phase 5 - IoT Integration Layer
def is_iot_rfid_enabled() -> bool:
    """Check if IoT RFID is enabled"""
    return FeatureFlagService.is_enabled(FeatureFlag.FF_IOT_RFID)


def is_iot_doors_enabled() -> bool:
    """Check if IoT Door Control is enabled"""
    return FeatureFlagService.is_enabled(FeatureFlag.FF_IOT_DOORS)


def is_iot_camera_enabled() -> bool:
    """Check if IoT Camera is enabled"""
    return FeatureFlagService.is_enabled(FeatureFlag.FF_IOT_CAMERA)


def is_iot_telemetry_enabled() -> bool:
    """Check if IoT Telemetry is enabled"""
    return FeatureFlagService.is_enabled(FeatureFlag.FF_IOT_TELEMETRY)


def is_vision_count_enabled() -> bool:
    """Check if Vision Count is enabled"""
    return FeatureFlagService.is_enabled(FeatureFlag.FF_VISION_COUNT)


# Phase 6 - RFID Locations & Live Map
def is_locations_enabled() -> bool:
    """Check if Location Management is enabled"""
    return FeatureFlagService.is_enabled(FeatureFlag.FF_LOCATIONS)


def is_rfid_zones_enabled() -> bool:
    """Check if RFID Zone Tracking is enabled"""
    return FeatureFlagService.is_enabled(FeatureFlag.FF_RFID_ZONES)


def is_live_map_enabled() -> bool:
    """Check if Live Map is enabled"""
    return FeatureFlagService.is_enabled(FeatureFlag.FF_LIVE_MAP)


def is_pick_to_light_enabled() -> bool:
    """Check if Pick-to-Light is enabled (reserved)"""
    return FeatureFlagService.is_enabled(FeatureFlag.FF_PICK_TO_LIGHT)


def is_pallet_tracking_enabled() -> bool:
    """Check if Pallet Tracking is enabled"""
    return FeatureFlagService.is_enabled(FeatureFlag.FF_PALLET_TRACKING)


# Phase 7 - Vision AI & Robotics
def is_vision_ai_enabled() -> bool:
    """Check if Vision AI is enabled"""
    return FeatureFlagService.is_enabled(FeatureFlag.FF_VISION_AI)


def is_amr_integration_enabled() -> bool:
    """Check if AMR Integration is enabled"""
    return FeatureFlagService.is_enabled(FeatureFlag.FF_AMR_INTEGRATION)


def is_light_guidance_enabled() -> bool:
    """Check if Light Guidance is enabled"""
    return FeatureFlagService.is_enabled(FeatureFlag.FF_LIGHT_GUIDANCE)

