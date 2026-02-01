"""
MinIO adapter implementation for local/self-hosted S3-compatible storage.

MinIO is ideal for:
- Local development
- Self-hosted deployments
- Docker Compose environments

Required Python package:
    minio>=7.2.0

Configuration via environment variables:
    MINIO_ENDPOINT: MinIO server endpoint (e.g., localhost:9000)
    MINIO_ACCESS_KEY: Access key
    MINIO_SECRET_KEY: Secret key
    MINIO_BUCKET: Default bucket name
    MINIO_SECURE: Use HTTPS (default: true)
"""

from typing import Optional, Dict, Any, List, BinaryIO
from datetime import datetime, timedelta
import os
import io

try:
    from minio import Minio
    from minio.error import S3Error
    MINIO_AVAILABLE = True
except ImportError:
    MINIO_AVAILABLE = False
    Minio = None

from ..adapter import StorageAdapter, StorageObject, UploadResult
from core.utils.logger import logger


class MinIOAdapter(StorageAdapter):
    """
    Adapter for MinIO (S3-compatible local storage).
    
    Perfect for local development and self-hosted deployments.
    """
    
    def __init__(self):
        if not MINIO_AVAILABLE:
            raise ImportError(
                "minio package is required for MinIO adapter. "
                "Install it with: pip install minio>=7.2.0"
            )
        
        self._client: Optional[Minio] = None
        self._initialized = False
        self._endpoint = ""
        self._bucket = ""
        self._secure = True
    
    async def initialize(self) -> None:
        """Initialize MinIO client."""
        if self._initialized:
            return
        
        try:
            endpoint = os.getenv("MINIO_ENDPOINT", "localhost:9000")
            access_key = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
            secret_key = os.getenv("MINIO_SECRET_KEY", "minioadmin")
            bucket = os.getenv("MINIO_BUCKET")
            secure = os.getenv("MINIO_SECURE", "true").lower() == "true"
            
            # Create client
            self._client = Minio(
                endpoint,
                access_key=access_key,
                secret_key=secret_key,
                secure=secure
            )
            
            self._endpoint = endpoint
            self._bucket = bucket
            self._secure = secure
            
            # Create default bucket if specified and doesn't exist
            if bucket:
                if not self._client.bucket_exists(bucket):
                    self._client.make_bucket(bucket)
                    logger.info(f"Created MinIO bucket: {bucket}")
                else:
                    logger.info(f"Connected to MinIO bucket: {bucket}")
            
            self._initialized = True
            logger.info("MinIO adapter initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize MinIO adapter: {e}")
            raise
    
    async def close(self) -> None:
        """Close MinIO connections."""
        # MinIO client doesn't require explicit closing
        self._initialized = False
        logger.info("MinIO adapter closed")
    
    async def health_check(self) -> Dict[str, Any]:
        """Check MinIO health."""
        if not self._initialized:
            return {"status": "unhealthy", "provider": "minio", "error": "Not initialized"}
        
        try:
            # Try to list buckets as health check
            list(self._client.list_buckets())
            return {
                "status": "healthy",
                "provider": "minio",
                "endpoint": self._endpoint,
                "secure": self._secure,
                "default_bucket": self._bucket
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "provider": "minio",
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
        """Upload a file to MinIO."""
        # Ensure bucket exists
        if not self._client.bucket_exists(bucket):
            self._client.make_bucket(bucket)
        
        # Upload
        result = self._client.put_object(
            bucket,
            key,
            io.BytesIO(file_data),
            len(file_data),
            content_type=content_type,
            metadata=metadata
        )
        
        # MinIO doesn't have ACL in the same way, but we can set bucket policy
        if public:
            # Set bucket policy to allow public read
            policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {"AWS": "*"},
                        "Action": ["s3:GetObject"],
                        "Resource": [f"arn:aws:s3:::{bucket}/{key}"]
                    }
                ]
            }
            import json
            self._client.set_bucket_policy(bucket, json.dumps(policy))
        
        return UploadResult(
            key=key,
            bucket=bucket,
            size=len(file_data),
            etag=result.etag,
            url=self.get_public_url(bucket, key) if public else None
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
        # For streams, we need to know the size or read the whole thing
        data = stream.read()
        return await self.upload_file(bucket, key, data, content_type, metadata, public)
    
    async def multipart_upload_init(
        self,
        bucket: str,
        key: str,
        content_type: Optional[str] = None
    ) -> str:
        """Initialize multipart upload."""
        # MinIO handles multipart uploads automatically based on size
        # We return a placeholder upload ID
        return f"multipart-{bucket}-{key}"
    
    async def multipart_upload_part(
        self,
        bucket: str,
        key: str,
        upload_id: str,
        part_number: int,
        data: bytes
    ) -> Dict[str, Any]:
        """Upload a part."""
        # MinIO handles this internally, just store the part info
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
        """Complete multipart upload."""
        # For MinIO, we can just do a regular upload with all parts combined
        # In practice, you would collect all parts and upload
        # This is a simplified implementation
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
        response = self._client.get_object(bucket, key)
        try:
            return response.read()
        finally:
            response.close()
            response.release_conn()
    
    async def download_stream(
        self,
        bucket: str,
        key: str,
        stream: BinaryIO
    ) -> None:
        """Download to stream."""
        response = self._client.get_object(bucket, key)
        try:
            for chunk in response.stream(32*1024):
                stream.write(chunk)
        finally:
            response.close()
            response.release_conn()
    
    async def get_download_url(
        self,
        bucket: str,
        key: str,
        expires_in: int = 3600
    ) -> str:
        """Generate pre-signed download URL."""
        url = self._client.presigned_get_object(
            bucket,
            key,
            expires=timedelta(seconds=expires_in)
        )
        return url
    
    async def get_upload_url(
        self,
        bucket: str,
        key: str,
        content_type: Optional[str] = None,
        expires_in: int = 3600
    ) -> str:
        """Generate pre-signed upload URL."""
        url = self._client.presigned_put_object(
            bucket,
            key,
            expires=timedelta(seconds=expires_in)
        )
        return url
    
    # File Management
    
    async def delete_file(
        self,
        bucket: str,
        key: str
    ) -> bool:
        """Delete a file."""
        try:
            self._client.remove_object(bucket, key)
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
        from minio.deleteobjects import DeleteObject
        
        delete_objects = [DeleteObject(key) for key in keys]
        result = {}
        
        try:
            errors = self._client.remove_objects(bucket, delete_objects)
            
            # Collect errors
            error_keys = set()
            for error in errors:
                error_keys.add(error.name)
                result[error.name] = False
            
            # Mark non-errors as success
            for key in keys:
                if key not in error_keys:
                    result[key] = True
                    
        except Exception as e:
            logger.error(f"Batch delete failed: {e}")
            for key in keys:
                result[key] = False
        
        return result
    
    async def copy_file(
        self,
        source_bucket: str,
        source_key: str,
        dest_bucket: str,
        dest_key: str
    ) -> bool:
        """Copy a file."""
        try:
            from minio.commonconfig import CopySource
            
            self._client.copy_object(
                dest_bucket,
                dest_key,
                CopySource(source_bucket, source_key)
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
        if await self.copy_file(source_bucket, source_key, dest_bucket, dest_key):
            return await self.delete_file(source_bucket, source_key)
        return False
    
    # Metadata and Listing
    
    async def get_object_metadata(
        self,
        bucket: str,
        key: str
    ) -> StorageObject:
        """Get object metadata."""
        stat = self._client.stat_object(bucket, key)
        
        return StorageObject(
            key=key,
            bucket=bucket,
            size=stat.size,
            content_type=stat.content_type,
            last_modified=stat.last_modified,
            etag=stat.etag,
            metadata=stat.metadata,
            url=self.get_public_url(bucket, key)
        )
    
    async def list_objects(
        self,
        bucket: str,
        prefix: Optional[str] = None,
        max_keys: int = 1000,
        marker: Optional[str] = None
    ) -> Dict[str, Any]:
        """List objects in bucket."""
        objects = []
        
        try:
            items = self._client.list_objects(
                bucket,
                prefix=prefix or '',
                start_after=marker or '',
            )
            
            count = 0
            last_key = None
            
            for obj in items:
                if count >= max_keys:
                    break
                
                objects.append({
                    "key": obj.object_name,
                    "size": obj.size,
                    "last_modified": obj.last_modified,
                    "etag": obj.etag
                })
                last_key = obj.object_name
                count += 1
            
            return {
                "objects": objects,
                "next_marker": last_key if count >= max_keys else None,
                "is_truncated": count >= max_keys
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
            self._client.stat_object(bucket, key)
            return True
        except S3Error:
            return False
        except Exception:
            return False
    
    # Bucket Management
    
    async def create_bucket(
        self,
        bucket: str,
        public: bool = False
    ) -> bool:
        """Create a new bucket."""
        try:
            if not self._client.bucket_exists(bucket):
                self._client.make_bucket(bucket)
            
            if public:
                # Set public read policy
                import json
                policy = {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Principal": {"AWS": "*"},
                            "Action": ["s3:GetBucketLocation", "s3:ListBucket"],
                            "Resource": [f"arn:aws:s3:::{bucket}"]
                        },
                        {
                            "Effect": "Allow",
                            "Principal": {"AWS": "*"},
                            "Action": ["s3:GetObject"],
                            "Resource": [f"arn:aws:s3:::{bucket}/*"]
                        }
                    ]
                }
                self._client.set_bucket_policy(bucket, json.dumps(policy))
            
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
            self._client.remove_bucket(bucket)
            return True
        except Exception as e:
            logger.error(f"Failed to delete bucket {bucket}: {e}")
            return False
    
    async def list_buckets(self) -> List[str]:
        """List all buckets."""
        buckets = self._client.list_buckets()
        return [bucket.name for bucket in buckets]
    
    async def bucket_exists(
        self,
        bucket: str
    ) -> bool:
        """Check if bucket exists."""
        try:
            return self._client.bucket_exists(bucket)
        except Exception:
            return False
    
    # Utility Methods
    
    def get_public_url(
        self,
        bucket: str,
        key: str
    ) -> Optional[str]:
        """Get public URL."""
        protocol = "https" if self._secure else "http"
        return f"{protocol}://{self._endpoint}/{bucket}/{key}"
    
    def get_cdn_url(
        self,
        bucket: str,
        key: str
    ) -> Optional[str]:
        """MinIO doesn't have built-in CDN, return None."""
        return None
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics."""
        return {
            "provider": "minio",
            "initialized": self._initialized,
            "endpoint": self._endpoint,
            "secure": self._secure,
            "default_bucket": self._bucket
        }
