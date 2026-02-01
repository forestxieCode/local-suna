"""
Abstract database adapter interface for multi-cloud support.

This adapter provides a unified interface for database operations across different providers:
- Supabase (existing)
- Aliyun RDS/PolarDB
- Tencent Cloud TDSQL-C
- Local PostgreSQL

Key features abstracted:
1. CRUD operations
2. Real-time subscriptions (via WebSocket or LISTEN/NOTIFY)
3. Row-level security (RLS) - implemented at application layer when needed
4. Connection pooling
5. Transaction management
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List, AsyncIterator, Callable
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from enum import Enum


class RealtimeEvent(str, Enum):
    """Database realtime event types."""
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    ALL = "*"


class DatabaseAdapter(ABC):
    """
    Abstract base class for database adapters.
    
    All database providers must implement this interface to ensure
    consistent behavior across different cloud providers.
    """
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize database connection and pools."""
        pass
    
    @abstractmethod
    async def close(self) -> None:
        """Close database connections and cleanup resources."""
        pass
    
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """
        Check database health and connection status.
        
        Returns:
            Dict with health status, latency, pool stats, etc.
        """
        pass
    
    # ==================== Session Management ====================
    
    @abstractmethod
    async def get_session(self) -> AsyncSession:
        """
        Get a database session for executing queries.
        
        Usage:
            async with adapter.get_session() as session:
                result = await session.execute(query)
        """
        pass
    
    @abstractmethod
    async def get_read_session(self) -> AsyncSession:
        """
        Get a read-only session (may use read replica if available).
        
        For read-heavy workloads, this can improve performance by
        distributing load to read replicas.
        """
        pass
    
    # ==================== CRUD Operations ====================
    
    @abstractmethod
    async def execute_query(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None,
        use_read_replica: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Execute a raw SQL query and return results.
        
        Args:
            query: SQL query string
            params: Query parameters (for parameterized queries)
            use_read_replica: Use read replica if available
            
        Returns:
            List of rows as dictionaries
        """
        pass
    
    @abstractmethod
    async def execute_mutation(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Execute a mutation query (INSERT, UPDATE, DELETE).
        
        Args:
            query: SQL mutation query
            params: Query parameters
            
        Returns:
            Number of affected rows
        """
        pass
    
    @abstractmethod
    async def insert(
        self,
        table: str,
        data: Dict[str, Any],
        returning: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Insert a row into a table.
        
        Args:
            table: Table name
            data: Column-value pairs to insert
            returning: Columns to return after insert
            
        Returns:
            Inserted row data if returning is specified
        """
        pass
    
    @abstractmethod
    async def update(
        self,
        table: str,
        data: Dict[str, Any],
        where: Dict[str, Any],
        returning: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Update rows in a table.
        
        Args:
            table: Table name
            data: Column-value pairs to update
            where: WHERE clause conditions
            returning: Columns to return after update
            
        Returns:
            Updated row data if returning is specified
        """
        pass
    
    @abstractmethod
    async def delete(
        self,
        table: str,
        where: Dict[str, Any],
        returning: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Delete rows from a table.
        
        Args:
            table: Table name
            where: WHERE clause conditions
            returning: Columns to return after delete
            
        Returns:
            Deleted row data if returning is specified
        """
        pass
    
    @abstractmethod
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
        """
        Select rows from a table.
        
        Args:
            table: Table name
            columns: Columns to select (None = all)
            where: WHERE clause conditions
            order_by: ORDER BY clause
            limit: LIMIT clause
            offset: OFFSET clause
            use_read_replica: Use read replica if available
            
        Returns:
            List of matching rows
        """
        pass
    
    # ==================== Real-time Subscriptions ====================
    
    @abstractmethod
    async def subscribe(
        self,
        table: str,
        event: RealtimeEvent,
        callback: Callable[[Dict[str, Any]], None],
        where: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Subscribe to real-time changes on a table.
        
        Implementation varies by provider:
        - Supabase: Native realtime API
        - Others: PostgreSQL LISTEN/NOTIFY + WebSocket
        
        Args:
            table: Table to watch
            event: Event type to listen for
            callback: Function to call on events
            where: Optional filter conditions
            
        Returns:
            Subscription ID for later unsubscribe
        """
        pass
    
    @abstractmethod
    async def unsubscribe(self, subscription_id: str) -> None:
        """
        Unsubscribe from a real-time subscription.
        
        Args:
            subscription_id: ID returned from subscribe()
        """
        pass
    
    # ==================== Transaction Management ====================
    
    @abstractmethod
    async def begin_transaction(self) -> Any:
        """
        Begin a database transaction.
        
        Usage:
            async with adapter.begin_transaction() as tx:
                await tx.execute(query1)
                await tx.execute(query2)
                # Auto-commits on success, rolls back on exception
        """
        pass
    
    # ==================== Utility Methods ====================
    
    @abstractmethod
    async def table_exists(self, table: str) -> bool:
        """Check if a table exists in the database."""
        pass
    
    @abstractmethod
    async def get_table_schema(self, table: str) -> List[Dict[str, Any]]:
        """
        Get schema information for a table.
        
        Returns:
            List of column definitions with name, type, nullable, etc.
        """
        pass
    
    @abstractmethod
    def get_connection_stats(self) -> Dict[str, Any]:
        """
        Get connection pool statistics.
        
        Returns:
            Dict with pool size, active connections, wait times, etc.
        """
        pass
