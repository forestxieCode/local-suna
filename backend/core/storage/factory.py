"""
Storage adapter factory - creates the appropriate adapter based on configuration.

Supports:
- Supabase Storage (default for international users)
- Aliyun OSS (China)
- Tencent Cloud COS (China)
- MinIO (self-hosted, S3-compatible)
- AWS S3 (optional)
"""

from typing import Optional
from enum import Enum
import os

from core.utils.logger import logger
from .adapter import StorageAdapter


class StorageProvider(str, Enum):
    """Supported storage providers."""
    SUPABASE = "supabase"
    ALIYUN_OSS = "aliyun_oss"
    TENCENT_COS = "tencent_cos"
    MINIO = "minio"
    AWS_S3 = "aws_s3"


_adapter_instance: Optional[StorageAdapter] = None


def get_storage_provider() -> StorageProvider:
    """
    Determine which storage provider to use based on environment variables.
    
    Priority:
    1. STORAGE_PROVIDER env var
    2. CLOUD_PROVIDER env var (aliyun, tencent, local)
    3. Auto-detect based on available credentials
    4. Default to Supabase
    """
    storage_provider = os.getenv("STORAGE_PROVIDER", "").lower()
    cloud_provider = os.getenv("CLOUD_PROVIDER", "").lower()
    
    # Check explicit storage provider
    if storage_provider:
        try:
            return StorageProvider(storage_provider)
        except ValueError:
            logger.warning(f"Invalid STORAGE_PROVIDER: {storage_provider}")
    
    # Map cloud provider to storage provider
    if cloud_provider in ["aliyun", "alibaba"]:
        return StorageProvider.ALIYUN_OSS
    elif cloud_provider == "tencent":
        return StorageProvider.TENCENT_COS
    elif cloud_provider == "local":
        return StorageProvider.MINIO
    elif cloud_provider == "supabase":
        return StorageProvider.SUPABASE
    
    # Auto-detect based on credentials
    if os.getenv("ALIYUN_OSS_BUCKET") or os.getenv("ALIYUN_ACCESS_KEY_ID"):
        return StorageProvider.ALIYUN_OSS
    elif os.getenv("TENCENT_COS_BUCKET") or os.getenv("TENCENT_SECRET_ID"):
        return StorageProvider.TENCENT_COS
    elif os.getenv("MINIO_ENDPOINT"):
        return StorageProvider.MINIO
    elif os.getenv("AWS_S3_BUCKET"):
        return StorageProvider.AWS_S3
    elif os.getenv("SUPABASE_URL"):
        return StorageProvider.SUPABASE
    
    # Default to Supabase
    logger.info("No storage provider specified, defaulting to Supabase Storage")
    return StorageProvider.SUPABASE


def get_storage_adapter(force_new: bool = False) -> StorageAdapter:
    """
    Get the storage adapter instance (singleton).
    
    Args:
        force_new: Force creation of a new adapter instance
        
    Returns:
        StorageAdapter instance for the configured provider
    """
    global _adapter_instance
    
    if _adapter_instance is not None and not force_new:
        return _adapter_instance
    
    provider = get_storage_provider()
    logger.info(f"Initializing storage adapter for provider: {provider.value}")
    
    if provider == StorageProvider.SUPABASE:
        from .adapters.supabase_storage import SupabaseStorageAdapter
        _adapter_instance = SupabaseStorageAdapter()
    elif provider == StorageProvider.ALIYUN_OSS:
        from .adapters.aliyun_oss import AliyunOSSAdapter
        _adapter_instance = AliyunOSSAdapter()
    elif provider == StorageProvider.TENCENT_COS:
        from .adapters.tencent_cos import TencentCOSAdapter
        _adapter_instance = TencentCOSAdapter()
    elif provider == StorageProvider.MINIO:
        from .adapters.minio_adapter import MinIOAdapter
        _adapter_instance = MinIOAdapter()
    elif provider == StorageProvider.AWS_S3:
        from .adapters.aws_s3 import AWSS3Adapter
        _adapter_instance = AWSS3Adapter()
    else:
        raise ValueError(f"Unsupported storage provider: {provider}")
    
    return _adapter_instance


async def initialize_storage() -> StorageAdapter:
    """
    Initialize the storage adapter.
    
    Should be called during application startup.
    """
    adapter = get_storage_adapter()
    await adapter.initialize()
    logger.info(f"Storage adapter initialized: {type(adapter).__name__}")
    return adapter


async def close_storage() -> None:
    """
    Close the storage adapter.
    
    Should be called during application shutdown.
    """
    global _adapter_instance
    if _adapter_instance:
        await _adapter_instance.close()
        _adapter_instance = None
        logger.info("Storage adapter closed")
