"""
Authentication adapter factory.

Supports:
- Supabase Auth (existing)
- Self-hosted JWT Auth (for China deployments)
"""

from typing import Optional
from enum import Enum
import os

from core.utils.logger import logger
from .adapter import AuthAdapter


class AuthProvider(str, Enum):
    """Supported auth providers."""
    SUPABASE = "supabase"
    JWT = "jwt"  # Self-hosted JWT auth


_adapter_instance: Optional[AuthAdapter] = None


def get_auth_provider() -> AuthProvider:
    """
    Determine which auth provider to use.
    
    Priority:
    1. AUTH_PROVIDER env var
    2. CLOUD_PROVIDER env var
    3. Auto-detect based on credentials
    4. Default to Supabase
    """
    auth_provider = os.getenv("AUTH_PROVIDER", "").lower()
    cloud_provider = os.getenv("CLOUD_PROVIDER", "").lower()
    
    # Check explicit auth provider
    if auth_provider:
        try:
            return AuthProvider(auth_provider)
        except ValueError:
            logger.warning(f"Invalid AUTH_PROVIDER: {auth_provider}")
    
    # Map cloud provider to auth provider
    if cloud_provider in ["aliyun", "tencent", "local"]:
        return AuthProvider.JWT
    elif cloud_provider == "supabase":
        return AuthProvider.SUPABASE
    
    # Auto-detect
    if os.getenv("SUPABASE_URL"):
        return AuthProvider.SUPABASE
    elif os.getenv("JWT_SECRET"):
        return AuthProvider.JWT
    
    # Default
    logger.info("No auth provider specified, defaulting to Supabase Auth")
    return AuthProvider.SUPABASE


def get_auth_adapter(force_new: bool = False) -> AuthAdapter:
    """Get the auth adapter instance (singleton)."""
    global _adapter_instance
    
    if _adapter_instance is not None and not force_new:
        return _adapter_instance
    
    provider = get_auth_provider()
    logger.info(f"Initializing auth adapter for provider: {provider.value}")
    
    if provider == AuthProvider.SUPABASE:
        from .adapters.supabase_auth import SupabaseAuthAdapter
        _adapter_instance = SupabaseAuthAdapter()
    elif provider == AuthProvider.JWT:
        from .adapters.jwt_auth import JWTAuthAdapter
        _adapter_instance = JWTAuthAdapter()
    else:
        raise ValueError(f"Unsupported auth provider: {provider}")
    
    return _adapter_instance


async def initialize_auth() -> AuthAdapter:
    """Initialize the auth adapter."""
    adapter = get_auth_adapter()
    await adapter.initialize()
    logger.info(f"Auth adapter initialized: {type(adapter).__name__}")
    return adapter


async def close_auth() -> None:
    """Close the auth adapter."""
    global _adapter_instance
    if _adapter_instance:
        await _adapter_instance.close()
        _adapter_instance = None
        logger.info("Auth adapter closed")
