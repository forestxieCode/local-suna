"""
Database adapter module for multi-cloud support.

Provides abstraction layer for different database backends:
- Supabase (PostgreSQL + Auth + Storage + Realtime)
- Aliyun RDS/PolarDB
- Tencent Cloud TDSQL-C
- Local PostgreSQL
"""

from .adapter import DatabaseAdapter
from .factory import get_database_adapter

__all__ = ["DatabaseAdapter", "get_database_adapter"]
