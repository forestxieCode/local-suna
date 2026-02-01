"""
Abstract storage adapter interface for multi-cloud object storage.

This adapter provides a unified interface for object storage operations:
- File upload/download
- Pre-signed URLs for secure access
- Bucket/folder management
- File metadata and listing

Supports multiple providers:
- Supabase Storage
- Aliyun OSS
- Tencent Cloud COS
- MinIO (local S3-compatible)
- AWS S3
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List, BinaryIO
from datetime import datetime, timedelta
from dataclasses import dataclass


@dataclass
class StorageObject:
    """Represents a stored object/file."""
    key: str  # Object key/path
    bucket: str  # Bucket/container name
    size: int  # Size in bytes
    content_type: str  # MIME type
    last_modified: datetime
    etag: Optional[str] = None
    metadata: Optional[Dict[str, str]] = None
    url: Optional[str] = None  # Public URL if available


@dataclass
class UploadResult:
    """Result of an upload operation."""
    key: str
    bucket: str
    size: int
    etag: Optional[str] = None
    url: Optional[str] = None
    cdn_url: Optional[str] = None


class StorageAdapter(ABC):
    """
    Abstract base class for object storage adapters.
    
    All storage providers must implement this interface to ensure
    consistent behavior across different cloud providers.
    """
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize storage client and verify connection."""
        pass
    
    @abstractmethod
    async def close(self) -> None:
        """Close storage connections and cleanup resources."""
        pass
    
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """
        Check storage service health and connection status.
        
        Returns:
            Dict with health status, bucket info, etc.
        """
        pass
    
    # ==================== Upload Operations ====================
    
    @abstractmethod
    async def upload_file(
        self,
        bucket: str,
        key: str,
        file_data: bytes,
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
        public: bool = False
    ) -> UploadResult:
        """
        Upload a file to storage.
        
        Args:
            bucket: Bucket/container name
            key: Object key/path
            file_data: File content as bytes
            content_type: MIME type
            metadata: Custom metadata key-value pairs
            public: Make file publicly accessible
            
        Returns:
            UploadResult with upload details
        """
        pass
    
    @abstractmethod
    async def upload_stream(
        self,
        bucket: str,
        key: str,
        stream: BinaryIO,
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
        public: bool = False
    ) -> UploadResult:
        """
        Upload a file from a stream.
        
        Useful for large files to avoid loading entire file into memory.
        """
        pass
    
    @abstractmethod
    async def multipart_upload_init(
        self,
        bucket: str,
        key: str,
        content_type: Optional[str] = None
    ) -> str:
        """
        Initialize a multipart upload for large files.
        
        Returns:
            Upload ID for subsequent operations
        """
        pass
    
    @abstractmethod
    async def multipart_upload_part(
        self,
        bucket: str,
        key: str,
        upload_id: str,
        part_number: int,
        data: bytes
    ) -> Dict[str, Any]:
        """Upload a part in a multipart upload."""
        pass
    
    @abstractmethod
    async def multipart_upload_complete(
        self,
        bucket: str,
        key: str,
        upload_id: str,
        parts: List[Dict[str, Any]]
    ) -> UploadResult:
        """Complete a multipart upload."""
        pass
    
    # ==================== Download Operations ====================
    
    @abstractmethod
    async def download_file(
        self,
        bucket: str,
        key: str
    ) -> bytes:
        """
        Download a file from storage.
        
        Args:
            bucket: Bucket name
            key: Object key
            
        Returns:
            File content as bytes
        """
        pass
    
    @abstractmethod
    async def download_stream(
        self,
        bucket: str,
        key: str,
        stream: BinaryIO
    ) -> None:
        """Download a file to a stream (for large files)."""
        pass
    
    @abstractmethod
    async def get_download_url(
        self,
        bucket: str,
        key: str,
        expires_in: int = 3600
    ) -> str:
        """
        Generate a pre-signed download URL.
        
        Args:
            bucket: Bucket name
            key: Object key
            expires_in: URL expiration time in seconds
            
        Returns:
            Pre-signed URL
        """
        pass
    
    @abstractmethod
    async def get_upload_url(
        self,
        bucket: str,
        key: str,
        content_type: Optional[str] = None,
        expires_in: int = 3600
    ) -> str:
        """
        Generate a pre-signed upload URL for direct client uploads.
        
        Args:
            bucket: Bucket name
            key: Object key
            content_type: Expected MIME type
            expires_in: URL expiration time in seconds
            
        Returns:
            Pre-signed URL
        """
        pass
    
    # ==================== File Management ====================
    
    @abstractmethod
    async def delete_file(
        self,
        bucket: str,
        key: str
    ) -> bool:
        """
        Delete a file from storage.
        
        Args:
            bucket: Bucket name
            key: Object key
            
        Returns:
            True if deleted successfully
        """
        pass
    
    @abstractmethod
    async def delete_files(
        self,
        bucket: str,
        keys: List[str]
    ) -> Dict[str, bool]:
        """
        Delete multiple files (batch operation).
        
        Returns:
            Dict mapping key -> success status
        """
        pass
    
    @abstractmethod
    async def copy_file(
        self,
        source_bucket: str,
        source_key: str,
        dest_bucket: str,
        dest_key: str
    ) -> bool:
        """Copy a file to a new location."""
        pass
    
    @abstractmethod
    async def move_file(
        self,
        source_bucket: str,
        source_key: str,
        dest_bucket: str,
        dest_key: str
    ) -> bool:
        """Move a file to a new location."""
        pass
    
    # ==================== Metadata and Listing ====================
    
    @abstractmethod
    async def get_object_metadata(
        self,
        bucket: str,
        key: str
    ) -> StorageObject:
        """
        Get metadata for an object without downloading it.
        
        Returns:
            StorageObject with metadata
        """
        pass
    
    @abstractmethod
    async def list_objects(
        self,
        bucket: str,
        prefix: Optional[str] = None,
        max_keys: int = 1000,
        marker: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List objects in a bucket.
        
        Args:
            bucket: Bucket name
            prefix: Filter by key prefix
            max_keys: Maximum objects to return
            marker: Pagination marker
            
        Returns:
            Dict with 'objects' list and 'next_marker' for pagination
        """
        pass
    
    @abstractmethod
    async def file_exists(
        self,
        bucket: str,
        key: str
    ) -> bool:
        """Check if a file exists in storage."""
        pass
    
    # ==================== Bucket Management ====================
    
    @abstractmethod
    async def create_bucket(
        self,
        bucket: str,
        public: bool = False
    ) -> bool:
        """
        Create a new bucket/container.
        
        Args:
            bucket: Bucket name
            public: Make bucket publicly accessible
            
        Returns:
            True if created successfully
        """
        pass
    
    @abstractmethod
    async def delete_bucket(
        self,
        bucket: str
    ) -> bool:
        """Delete a bucket (must be empty)."""
        pass
    
    @abstractmethod
    async def list_buckets(self) -> List[str]:
        """List all available buckets."""
        pass
    
    @abstractmethod
    async def bucket_exists(
        self,
        bucket: str
    ) -> bool:
        """Check if a bucket exists."""
        pass
    
    # ==================== Utility Methods ====================
    
    @abstractmethod
    def get_public_url(
        self,
        bucket: str,
        key: str
    ) -> Optional[str]:
        """
        Get the public URL for an object (if publicly accessible).
        
        Returns:
            Public URL or None if not public
        """
        pass
    
    @abstractmethod
    def get_cdn_url(
        self,
        bucket: str,
        key: str
    ) -> Optional[str]:
        """
        Get the CDN URL for an object (if CDN is configured).
        
        Returns:
            CDN URL or None if not configured
        """
        pass
    
    @abstractmethod
    def get_storage_stats(self) -> Dict[str, Any]:
        """
        Get storage usage statistics.
        
        Returns:
            Dict with storage usage, object count, etc.
        """
        pass
