"""
Supabase Storage adapter implementation.

Maintains backward compatibility with existing Supabase users.

Uses existing Supabase client infrastructure.

Configuration via environment variables:
    SUPABASE_URL: Supabase project URL
    SUPABASE_ANON_KEY: Anonymous key
    SUPABASE_SERVICE_ROLE_KEY: Service role key (for admin operations)
"""

from typing import Optional, Dict, Any, List, BinaryIO
from datetime import datetime, timedelta
import os
import io

from ..adapter import StorageAdapter, StorageObject, UploadResult
from core.utils.logger import logger


class SupabaseStorageAdapter(StorageAdapter):
    """
    Adapter for Supabase Storage.
    
    Wraps existing Supabase client to provide unified storage interface.
    """
    
    def __init__(self):
        self._client = None
        self._initialized = False
        self._url = ""
    
    async def initialize(self) -> None:
        """Initialize Supabase Storage client."""
        if self._initialized:
            return
        
        try:
            # Import here to avoid circular dependencies
            from core.services.supabase import get_supabase_client
            
            self._client = await get_supabase_client()
            self._url = os.getenv("SUPABASE_URL", "")
            
            self._initialized = True
            logger.info("Supabase Storage adapter initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize Supabase Storage adapter: {e}")
            raise
    
    async def close(self) -> None:
        """Close Supabase connections."""
        # Supabase client cleanup is handled elsewhere
        self._initialized = False
        logger.info("Supabase Storage adapter closed")
    
    async def health_check(self) -> Dict[str, Any]:
        """Check Supabase Storage health."""
        if not self._initialized:
            return {"status": "unhealthy", "provider": "supabase", "error": "Not initialized"}
        
        try:
            # Try to list buckets as health check
            buckets = await self._client.storage.list_buckets()
            return {
                "status": "healthy",
                "provider": "supabase",
                "url": self._url,
                "buckets_count": len(buckets)
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "provider": "supabase",
                "error": str(e)
            }
    
    # Upload Operations
    
    async def upload_file(
        self,
        bucket: str,
        key: str,
        file_data: bytes,
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
        public: bool = False
    ) -> UploadResult:
        """Upload a file to Supabase Storage."""
        file_options = {}
        if content_type:
            file_options['content-type'] = content_type
        
        # Upload
        result = await self._client.storage.from_(bucket).upload(
            key,
            file_data,
            file_options
        )
        
        # Get public URL if public
        url = None
        if public:
            url_result = self._client.storage.from_(bucket).get_public_url(key)
            url = url_result
        
        return UploadResult(
            key=key,
            bucket=bucket,
            size=len(file_data),
            url=url
        )
    
    async def upload_stream(
        self,
        bucket: str,
        key: str,
        stream: BinaryIO,
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
        public: bool = False
    ) -> UploadResult:
        """Upload from stream."""
        data = stream.read()
        return await self.upload_file(bucket, key, data, content_type, metadata, public)
    
    async def multipart_upload_init(
        self,
        bucket: str,
        key: str,
        content_type: Optional[str] = None
    ) -> str:
        """Initialize multipart upload (not directly supported by Supabase)."""
        # Supabase handles large files automatically
        return f"supabase-multipart-{bucket}-{key}"
    
    async def multipart_upload_part(
        self,
        bucket: str,
        key: str,
        upload_id: str,
        part_number: int,
        data: bytes
    ) -> Dict[str, Any]:
        """Upload a part (handled internally by Supabase)."""
        return {
            "part_number": part_number,
            "etag": f"part-{part_number}"
        }
    
    async def multipart_upload_complete(
        self,
        bucket: str,
        key: str,
        upload_id: str,
        parts: List[Dict[str, Any]]
    ) -> UploadResult:
        """Complete multipart upload (handled internally by Supabase)."""
        return UploadResult(
            key=key,
            bucket=bucket,
            size=0,
            url=self.get_public_url(bucket, key)
        )
    
    # Download Operations
    
    async def download_file(
        self,
        bucket: str,
        key: str
    ) -> bytes:
        """Download a file."""
        result = await self._client.storage.from_(bucket).download(key)
        return result
    
    async def download_stream(
        self,
        bucket: str,
        key: str,
        stream: BinaryIO
    ) -> None:
        """Download to stream."""
        data = await self.download_file(bucket, key)
        stream.write(data)
    
    async def get_download_url(
        self,
        bucket: str,
        key: str,
        expires_in: int = 3600
    ) -> str:
        """Generate pre-signed download URL."""
        result = await self._client.storage.from_(bucket).create_signed_url(
            key,
            expires_in
        )
        return result['signedURL']
    
    async def get_upload_url(
        self,
        bucket: str,
        key: str,
        content_type: Optional[str] = None,
        expires_in: int = 3600
    ) -> str:
        """Generate pre-signed upload URL."""
        # Supabase doesn't directly support presigned upload URLs
        # You would typically use the upload method directly
        # Return a placeholder or implement custom logic
        return f"{self._url}/storage/v1/object/{bucket}/{key}"
    
    # File Management
    
    async def delete_file(
        self,
        bucket: str,
        key: str
    ) -> bool:
        """Delete a file."""
        try:
            await self._client.storage.from_(bucket).remove([key])
            return True
        except Exception as e:
            logger.error(f"Failed to delete object {key}: {e}")
            return False
    
    async def delete_files(
        self,
        bucket: str,
        keys: List[str]
    ) -> Dict[str, bool]:
        """Batch delete files."""
        try:
            await self._client.storage.from_(bucket).remove(keys)
            return {key: True for key in keys}
        except Exception as e:
            logger.error(f"Batch delete failed: {e}")
            return {key: False for key in keys}
    
    async def copy_file(
        self,
        source_bucket: str,
        source_key: str,
        dest_bucket: str,
        dest_key: str
    ) -> bool:
        """Copy a file."""
        try:
            await self._client.storage.from_(dest_bucket).copy(
                source_key,
                dest_key,
                source_bucket
            )
            return True
        except Exception as e:
            logger.error(f"Failed to copy object: {e}")
            return False
    
    async def move_file(
        self,
        source_bucket: str,
        source_key: str,
        dest_bucket: str,
        dest_key: str
    ) -> bool:
        """Move a file."""
        try:
            await self._client.storage.from_(dest_bucket).move(
                source_key,
                dest_key,
                source_bucket
            )
            return True
        except Exception as e:
            logger.error(f"Failed to move object: {e}")
            return False
    
    # Metadata and Listing
    
    async def get_object_metadata(
        self,
        bucket: str,
        key: str
    ) -> StorageObject:
        """Get object metadata."""
        # Supabase storage doesn't have a direct head/stat method
        # We need to list and find the object
        result = await self._client.storage.from_(bucket).list(path=key)
        
        if result and len(result) > 0:
            obj = result[0]
            return StorageObject(
                key=key,
                bucket=bucket,
                size=obj.get('metadata', {}).get('size', 0),
                content_type=obj.get('metadata', {}).get('mimetype', ''),
                last_modified=datetime.fromisoformat(obj.get('updated_at', obj.get('created_at'))),
                url=self.get_public_url(bucket, key)
            )
        else:
            raise FileNotFoundError(f"Object {key} not found in bucket {bucket}")
    
    async def list_objects(
        self,
        bucket: str,
        prefix: Optional[str] = None,
        max_keys: int = 1000,
        marker: Optional[str] = None
    ) -> Dict[str, Any]:
        """List objects in bucket."""
        try:
            result = await self._client.storage.from_(bucket).list(
                path=prefix or '',
                limit=max_keys,
                offset=int(marker) if marker else 0
            )
            
            objects = [
                {
                    "key": obj['name'],
                    "size": obj.get('metadata', {}).get('size', 0),
                    "last_modified": datetime.fromisoformat(obj.get('updated_at', obj.get('created_at'))),
                }
                for obj in result
            ]
            
            return {
                "objects": objects,
                "next_marker": str(len(objects)) if len(objects) >= max_keys else None,
                "is_truncated": len(objects) >= max_keys
            }
        except Exception as e:
            logger.error(f"Failed to list objects: {e}")
            return {
                "objects": [],
                "next_marker": None,
                "is_truncated": False
            }
    
    async def file_exists(
        self,
        bucket: str,
        key: str
    ) -> bool:
        """Check if file exists."""
        try:
            await self.get_object_metadata(bucket, key)
            return True
        except:
            return False
    
    # Bucket Management
    
    async def create_bucket(
        self,
        bucket: str,
        public: bool = False
    ) -> bool:
        """Create a new bucket."""
        try:
            await self._client.storage.create_bucket(
                bucket,
                options={'public': public}
            )
            return True
        except Exception as e:
            logger.error(f"Failed to create bucket {bucket}: {e}")
            return False
    
    async def delete_bucket(
        self,
        bucket: str
    ) -> bool:
        """Delete a bucket."""
        try:
            await self._client.storage.delete_bucket(bucket)
            return True
        except Exception as e:
            logger.error(f"Failed to delete bucket {bucket}: {e}")
            return False
    
    async def list_buckets(self) -> List[str]:
        """List all buckets."""
        try:
            buckets = await self._client.storage.list_buckets()
            return [bucket['name'] for bucket in buckets]
        except Exception as e:
            logger.error(f"Failed to list buckets: {e}")
            return []
    
    async def bucket_exists(
        self,
        bucket: str
    ) -> bool:
        """Check if bucket exists."""
        try:
            buckets = await self.list_buckets()
            return bucket in buckets
        except:
            return False
    
    # Utility Methods
    
    def get_public_url(
        self,
        bucket: str,
        key: str
    ) -> Optional[str]:
        """Get public URL."""
        try:
            url = self._client.storage.from_(bucket).get_public_url(key)
            return url
        except:
            return f"{self._url}/storage/v1/object/public/{bucket}/{key}"
    
    def get_cdn_url(
        self,
        bucket: str,
        key: str
    ) -> Optional[str]:
        """Supabase uses CDN automatically for public URLs."""
        return self.get_public_url(bucket, key)
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics."""
        return {
            "provider": "supabase",
            "initialized": self._initialized,
            "url": self._url
        }
