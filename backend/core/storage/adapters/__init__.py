"""Storage adapter implementations package."""

__all__ = [
    "AliyunOSSAdapter",
    "TencentCOSAdapter",
    "MinIOAdapter",
    "SupabaseStorageAdapter"
]

# All adapters are now fully implemented
try:
    from .aliyun_oss import AliyunOSSAdapter
except ImportError:
    pass

try:
    from .tencent_cos import TencentCOSAdapter
except ImportError:
    pass

try:
    from .minio_adapter import MinIOAdapter
except ImportError:
    pass

try:
    from .supabase_storage import SupabaseStorageAdapter
except ImportError:
    pass

