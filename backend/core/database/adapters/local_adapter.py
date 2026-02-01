"""
Local PostgreSQL database adapter implementation.

Supports:
- Self-hosted PostgreSQL
- Docker PostgreSQL container
- Development/testing environments

This adapter is similar to cloud adapters but optimized for local deployment.
"""

from typing import Optional, Dict, Any, List, Callable
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker, AsyncEngine
from sqlalchemy.pool import AsyncAdaptedQueuePool
from contextlib import asynccontextmanager
import os
import uuid

from ..adapter import DatabaseAdapter, RealtimeEvent
from core.utils.logger import logger


class LocalAdapter(DatabaseAdapter):
    """
    Adapter for local PostgreSQL deployment.
    
    Configuration via environment variables:
    - DATABASE_URL: Full PostgreSQL connection URL
      OR individual components:
    - POSTGRES_HOST: Database host (default: localhost)
    - POSTGRES_PORT: Database port (default: 5432)
    - POSTGRES_DATABASE: Database name (default: kortix)
    - POSTGRES_USER: Database username
    - POSTGRES_PASSWORD: Database password
    """
    
    def __init__(self):
        self._engine: Optional[AsyncEngine] = None
        self._session_factory: Optional[async_sessionmaker] = None
        self._initialized = False
        self._subscriptions: Dict[str, Dict[str, Any]] = {}
    
    def _get_database_url(self) -> str:
        """Build database connection URL."""
        # Check for full DATABASE_URL first
        if url := os.getenv("DATABASE_URL"):
            # Convert to async URL if needed
            if url.startswith("postgresql://"):
                url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
            elif url.startswith("postgres://"):
                url = url.replace("postgres://", "postgresql+asyncpg://", 1)
            return url
        
        # Build from components
        host = os.getenv("POSTGRES_HOST", "localhost")
        port = os.getenv("POSTGRES_PORT", "5432")
        database = os.getenv("POSTGRES_DATABASE", "kortix")
        username = os.getenv("POSTGRES_USER", "postgres")
        password = os.getenv("POSTGRES_PASSWORD", "")
        
        if not password:
            logger.warning("POSTGRES_PASSWORD not set, using empty password")
        
        return f"postgresql+asyncpg://{username}:{password}@{host}:{port}/{database}"
    
    async def initialize(self) -> None:
        """Initialize local PostgreSQL connection."""
        if self._initialized:
            return
        
        try:
            db_url = self._get_database_url()
            
            # Use larger pool for local development
            self._engine = create_async_engine(
                db_url,
                poolclass=AsyncAdaptedQueuePool,
                pool_size=10,
                max_overflow=20,
                pool_timeout=30,
                pool_recycle=3600,
                echo=os.getenv("POSTGRES_ECHO", "false").lower() == "true"
            )
            
            self._session_factory = async_sessionmaker(
                self._engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            # Test connection
            async with self._engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            
            self._initialized = True
            logger.info("Local PostgreSQL adapter initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize local adapter: {e}")
            raise
    
    async def close(self) -> None:
        """Close connections."""
        if self._engine:
            await self._engine.dispose()
        
        self._initialized = False
        logger.info("Local PostgreSQL adapter closed")
    
    async def health_check(self) -> Dict[str, Any]:
        """Check health."""
        if not self._initialized:
            return {"status": "unhealthy", "provider": "local", "error": "Not initialized"}
        
        try:
            async with self._engine.connect() as conn:
                result = await conn.execute(text("SELECT version()"))
                version = result.scalar()
                return {
                    "status": "healthy",
                    "provider": "local",
                    "host": os.getenv("POSTGRES_HOST", "localhost"),
                    "database": os.getenv("POSTGRES_DATABASE", "kortix"),
                    "version": version
                }
        except Exception as e:
            return {
                "status": "unhealthy",
                "provider": "local",
                "error": str(e)
            }
    
    @asynccontextmanager
    async def get_session(self) -> AsyncSession:
        """Get a database session."""
        if not self._session_factory:
            raise RuntimeError("Local adapter not initialized")
        
        async with self._session_factory() as session:
            yield session
    
    @asynccontextmanager
    async def get_read_session(self) -> AsyncSession:
        """Get a read-only session (same as write for local)."""
        if not self._session_factory:
            raise RuntimeError("Local adapter not initialized")
        
        async with self._session_factory() as session:
            yield session
    
    async def execute_query(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None,
        use_read_replica: bool = False
    ) -> List[Dict[str, Any]]:
        """Execute a query."""
        if not self._session_factory:
            raise RuntimeError("Local adapter not initialized")
        
        async with self._session_factory() as session:
            result = await session.execute(text(query), params or {})
            return [dict(row._mapping) for row in result]
    
    async def execute_mutation(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None
    ) -> int:
        """Execute a mutation query."""
        if not self._session_factory:
            raise RuntimeError("Local adapter not initialized")
        
        async with self._session_factory() as session:
            result = await session.execute(text(query), params or {})
            await session.commit()
            return result.rowcount
    
    async def insert(
        self,
        table: str,
        data: Dict[str, Any],
        returning: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        """Insert a row."""
        columns = ", ".join(data.keys())
        placeholders = ", ".join(f":{key}" for key in data.keys())
        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        
        if returning:
            query += f" RETURNING {', '.join(returning)}"
            result = await self.execute_query(query, data)
            return result[0] if result else None
        else:
            await self.execute_mutation(query, data)
            return None
    
    async def update(
        self,
        table: str,
        data: Dict[str, Any],
        where: Dict[str, Any],
        returning: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        """Update rows."""
        set_clause = ", ".join(f"{key} = :data_{key}" for key in data.keys())
        where_clause = " AND ".join(f"{key} = :where_{key}" for key in where.keys())
        
        params = {f"data_{k}": v for k, v in data.items()}
        params.update({f"where_{k}": v for k, v in where.items()})
        
        query = f"UPDATE {table} SET {set_clause} WHERE {where_clause}"
        
        if returning:
            query += f" RETURNING {', '.join(returning)}"
            result = await self.execute_query(query, params)
            return result[0] if result else None
        else:
            await self.execute_mutation(query, params)
            return None
    
    async def delete(
        self,
        table: str,
        where: Dict[str, Any],
        returning: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        """Delete rows."""
        where_clause = " AND ".join(f"{key} = :{key}" for key in where.keys())
        query = f"DELETE FROM {table} WHERE {where_clause}"
        
        if returning:
            query += f" RETURNING {', '.join(returning)}"
            result = await self.execute_query(query, where)
            return result[0] if result else None
        else:
            await self.execute_mutation(query, where)
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
        """Select rows."""
        cols = ", ".join(columns) if columns else "*"
        query = f"SELECT {cols} FROM {table}"
        params = {}
        
        if where:
            where_clause = " AND ".join(f"{key} = :{key}" for key in where.keys())
            query += f" WHERE {where_clause}"
            params = where
        
        if order_by:
            query += f" ORDER BY {order_by}"
        
        if limit:
            query += f" LIMIT {limit}"
        
        if offset:
            query += f" OFFSET {offset}"
        
        return await self.execute_query(query, params, use_read_replica=use_read_replica)
    
    async def subscribe(
        self,
        table: str,
        event: RealtimeEvent,
        callback: Callable[[Dict[str, Any]], None],
        where: Optional[Dict[str, Any]] = None
    ) -> str:
        """Subscribe to real-time changes."""
        subscription_id = str(uuid.uuid4())
        logger.warning("Real-time subscriptions require PostgreSQL triggers and LISTEN/NOTIFY to be configured")
        return subscription_id
    
    async def unsubscribe(self, subscription_id: str) -> None:
        """Unsubscribe from real-time changes."""
        if subscription_id in self._subscriptions:
            del self._subscriptions[subscription_id]
    
    async def begin_transaction(self) -> Any:
        """Begin a transaction."""
        return self.get_session()
    
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
        stats = {
            "provider": "local",
            "initialized": self._initialized
        }
        
        if self._engine:
            pool = self._engine.pool
            stats["pool"] = {
                "size": pool.size(),
                "checked_in": pool.checkedin(),
                "overflow": pool.overflow(),
                "checked_out": pool.checkedout()
            }
        
        return stats
