"""
Database adapter factory - creates the appropriate adapter based on configuration.

Supports:
- Supabase (default for international users)
- Aliyun RDS/PolarDB (China)
- Tencent Cloud TDSQL-C (China)
- Local PostgreSQL (self-hosted)
"""

from typing import Optional
from enum import Enum
import os

from core.utils.logger import logger
from .adapter import DatabaseAdapter


class DatabaseProvider(str, Enum):
    """Supported database providers."""
    SUPABASE = "supabase"
    ALIYUN = "aliyun"
    TENCENT = "tencent"
    LOCAL = "local"


_adapter_instance: Optional[DatabaseAdapter] = None


def get_database_provider() -> DatabaseProvider:
    """
    Determine which database provider to use based on environment variables.
    
    Priority:
    1. CLOUD_PROVIDER env var (aliyun, tencent, local, supabase)
    2. DATABASE_PROVIDER env var (backward compatibility)
    3. Default to Supabase if SUPABASE_URL is set
    4. Default to local if DATABASE_URL is set
    """
    cloud_provider = os.getenv("CLOUD_PROVIDER", "").lower()
    db_provider = os.getenv("DATABASE_PROVIDER", "").lower()
    
    # Check explicit cloud provider setting
    if cloud_provider in ["aliyun", "alibaba"]:
        return DatabaseProvider.ALIYUN
    elif cloud_provider == "tencent":
        return DatabaseProvider.TENCENT
    elif cloud_provider == "local":
        return DatabaseProvider.LOCAL
    elif cloud_provider == "supabase":
        return DatabaseProvider.SUPABASE
    
    # Check database provider setting
    if db_provider:
        try:
            return DatabaseProvider(db_provider)
        except ValueError:
            logger.warning(f"Invalid DATABASE_PROVIDER: {db_provider}, defaulting to supabase")
    
    # Auto-detect based on available environment variables
    if os.getenv("SUPABASE_URL"):
        return DatabaseProvider.SUPABASE
    elif os.getenv("ALIYUN_RDS_HOST") or os.getenv("ALIYUN_ACCESS_KEY_ID"):
        return DatabaseProvider.ALIYUN
    elif os.getenv("TENCENT_RDS_HOST") or os.getenv("TENCENT_SECRET_ID"):
        return DatabaseProvider.TENCENT
    elif os.getenv("DATABASE_URL"):
        return DatabaseProvider.LOCAL
    
    # Default to Supabase
    logger.info("No database provider specified, defaulting to Supabase")
    return DatabaseProvider.SUPABASE


def get_database_adapter(force_new: bool = False) -> DatabaseAdapter:
    """
    Get the database adapter instance (singleton).
    
    Args:
        force_new: Force creation of a new adapter instance
        
    Returns:
        DatabaseAdapter instance for the configured provider
    """
    global _adapter_instance
    
    if _adapter_instance is not None and not force_new:
        return _adapter_instance
    
    provider = get_database_provider()
    logger.info(f"Initializing database adapter for provider: {provider.value}")
    
    if provider == DatabaseProvider.SUPABASE:
        from .adapters.supabase_adapter import SupabaseAdapter
        _adapter_instance = SupabaseAdapter()
    elif provider == DatabaseProvider.ALIYUN:
        from .adapters.aliyun_adapter import AliyunAdapter
        _adapter_instance = AliyunAdapter()
    elif provider == DatabaseProvider.TENCENT:
        from .adapters.tencent_adapter import TencentAdapter
        _adapter_instance = TencentAdapter()
    elif provider == DatabaseProvider.LOCAL:
        from .adapters.local_adapter import LocalAdapter
        _adapter_instance = LocalAdapter()
    else:
        raise ValueError(f"Unsupported database provider: {provider}")
    
    return _adapter_instance


async def initialize_database() -> DatabaseAdapter:
    """
    Initialize the database adapter.
    
    Should be called during application startup.
    """
    adapter = get_database_adapter()
    await adapter.initialize()
    logger.info(f"Database adapter initialized: {type(adapter).__name__}")
    return adapter


async def close_database() -> None:
    """
    Close the database adapter.
    
    Should be called during application shutdown.
    """
    global _adapter_instance
    if _adapter_instance:
        await _adapter_instance.close()
        _adapter_instance = None
        logger.info("Database adapter closed")
