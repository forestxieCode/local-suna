"""
Supabase database adapter implementation.

Wraps existing Supabase client to conform to DatabaseAdapter interface.
Maintains backward compatibility with existing codebase.
"""

from typing import Optional, Dict, Any, List, AsyncIterator, Callable
from sqlalchemy.ext.asyncio import AsyncSession
import os

from ..adapter import DatabaseAdapter, RealtimeEvent
from core.services.db import get_session, get_read_session, execute_query
from core.services.supabase import get_supabase_client
from core.utils.logger import logger


class SupabaseAdapter(DatabaseAdapter):
    """
    Adapter for Supabase (existing implementation).
    
    Wraps existing Supabase services to provide unified interface.
    """
    
    def __init__(self):
        self._client = None
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize Supabase connection."""
        if self._initialized:
            return
            
        try:
            # Use existing Supabase client
            self._client = await get_supabase_client()
            self._initialized = True
            logger.info("Supabase adapter initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase adapter: {e}")
            raise
    
    async def close(self) -> None:
        """Close Supabase connections."""
        if self._client:
            # Supabase client cleanup is handled by existing code
            self._initialized = False
            self._client = None
            logger.info("Supabase adapter closed")
    
    async def health_check(self) -> Dict[str, Any]:
        """Check Supabase health."""
        try:
            async with get_session() as session:
                result = await session.execute("SELECT 1")
                return {
                    "status": "healthy",
                    "provider": "supabase",
                    "url": os.getenv("SUPABASE_URL", ""),
                    "initialized": self._initialized
                }
        except Exception as e:
            return {
                "status": "unhealthy",
                "provider": "supabase",
                "error": str(e)
            }
    
    async def get_session(self) -> AsyncSession:
        """Get a database session."""
        return get_session()
    
    async def get_read_session(self) -> AsyncSession:
        """Get a read-only session."""
        return get_read_session()
    
    async def execute_query(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None,
        use_read_replica: bool = False
    ) -> List[Dict[str, Any]]:
        """Execute a query using existing infrastructure."""
        return await execute_query(query, params, use_read_replica=use_read_replica)
    
    async def execute_mutation(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None
    ) -> int:
        """Execute a mutation query."""
        async with get_session() as session:
            result = await session.execute(query, params or {})
            await session.commit()
            return result.rowcount
    
    async def insert(
        self,
        table: str,
        data: Dict[str, Any],
        returning: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        """Insert using Supabase client."""
        if not self._client:
            raise RuntimeError("Supabase adapter not initialized")
        
        result = await self._client.table(table).insert(data).execute()
        if returning and result.data:
            return result.data[0]
        return None
    
    async def update(
        self,
        table: str,
        data: Dict[str, Any],
        where: Dict[str, Any],
        returning: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        """Update using Supabase client."""
        if not self._client:
            raise RuntimeError("Supabase adapter not initialized")
        
        query = self._client.table(table).update(data)
        for key, value in where.items():
            query = query.eq(key, value)
        
        result = await query.execute()
        if returning and result.data:
            return result.data[0]
        return None
    
    async def delete(
        self,
        table: str,
        where: Dict[str, Any],
        returning: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        """Delete using Supabase client."""
        if not self._client:
            raise RuntimeError("Supabase adapter not initialized")
        
        query = self._client.table(table).delete()
        for key, value in where.items():
            query = query.eq(key, value)
        
        result = await query.execute()
        if returning and result.data:
            return result.data[0]
        return None
    
    async def select(
        self,
        table: str,
        columns: Optional[List[str]] = None,
        where: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        use_read_replica: bool = True
    ) -> List[Dict[str, Any]]:
        """Select using Supabase client."""
        if not self._client:
            raise RuntimeError("Supabase adapter not initialized")
        
        cols = ",".join(columns) if columns else "*"
        query = self._client.table(table).select(cols)
        
        if where:
            for key, value in where.items():
                query = query.eq(key, value)
        
        if order_by:
            query = query.order(order_by)
        
        if limit:
            query = query.limit(limit)
        
        if offset:
            query = query.offset(offset)
        
        result = await query.execute()
        return result.data or []
    
    async def subscribe(
        self,
        table: str,
        event: RealtimeEvent,
        callback: Callable[[Dict[str, Any]], None],
        where: Optional[Dict[str, Any]] = None
    ) -> str:
        """Subscribe to real-time changes (Supabase native)."""
        # TODO: Implement Supabase realtime subscriptions
        # This requires integrating with Supabase's realtime API
        raise NotImplementedError("Realtime subscriptions not yet implemented for Supabase adapter")
    
    async def unsubscribe(self, subscription_id: str) -> None:
        """Unsubscribe from real-time changes."""
        raise NotImplementedError("Realtime subscriptions not yet implemented for Supabase adapter")
    
    async def begin_transaction(self) -> Any:
        """Begin a transaction."""
        # Use existing session context manager
        return get_session()
    
    async def table_exists(self, table: str) -> bool:
        """Check if table exists."""
        query = """
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = :table_name
        )
        """
        result = await self.execute_query(query, {"table_name": table})
        return result[0]["exists"] if result else False
    
    async def get_table_schema(self, table: str) -> List[Dict[str, Any]]:
        """Get table schema."""
        query = """
        SELECT 
            column_name,
            data_type,
            is_nullable,
            column_default
        FROM information_schema.columns
        WHERE table_name = :table_name
        ORDER BY ordinal_position
        """
        return await self.execute_query(query, {"table_name": table})
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get connection statistics."""
        # Use existing stats from db.py
        from core.services.db import _stats
        return {
            "provider": "supabase",
            "primary_reads": _stats.get("primary_reads", 0),
            "replica_reads": _stats.get("replica_reads", 0),
            "initialized": self._initialized
        }
