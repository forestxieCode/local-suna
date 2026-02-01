"""
Object storage adapter module for multi-cloud support.

Provides abstraction layer for different storage backends:
- Supabase Storage
- Aliyun OSS (Object Storage Service)
- Tencent Cloud COS (Cloud Object Storage)
- Local MinIO (S3-compatible)
- AWS S3 (optional)
"""

from .adapter import StorageAdapter
from .factory import get_storage_adapter

__all__ = ["StorageAdapter", "get_storage_adapter"]
