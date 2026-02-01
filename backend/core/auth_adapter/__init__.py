"""
Authentication adapter module for multi-cloud support.

Provides abstraction layer for different authentication backends:
- Supabase Auth (existing)
- Self-hosted JWT Auth
- Aliyun/Tencent OAuth
"""

from .adapter import AuthAdapter
from .factory import get_auth_adapter

__all__ = ["AuthAdapter", "get_auth_adapter"]
