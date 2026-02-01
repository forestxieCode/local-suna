"""
Aliyun OSS (Object Storage Service) adapter implementation.

This is a complete reference implementation that other adapters can follow.

Required Python package:
    oss2>=2.18.0

Configuration via environment variables:
    ALIYUN_ACCESS_KEY_ID: Access key ID
    ALIYUN_ACCESS_KEY_SECRET: Access key secret
    ALIYUN_OSS_ENDPOINT: OSS endpoint (e.g., oss-cn-hangzhou.aliyuncs.com)
    ALIYUN_OSS_BUCKET: Default bucket name
    ALIYUN_OSS_REGION: Region (default: cn-hangzhou)
    ALIYUN_OSS_CDN_DOMAIN: Optional CDN domain for faster access
"""

from typing import Optional, Dict, Any, List, BinaryIO
from datetime import datetime, timedelta
import os
import io

try:
    import oss2
    from oss2 import Auth, Bucket
    from oss2.models import SimplifiedObjectInfo
    OSS2_AVAILABLE = True
except ImportError:
    OSS2_AVAILABLE = False
    oss2 = None

from ..adapter import StorageAdapter, StorageObject, UploadResult
from core.utils.logger import logger


class AliyunOSSAdapter(StorageAdapter):
    """
    Adapter for Aliyun OSS (Object Storage Service).
    
    Complete implementation with all features:
    - Single and multipart uploads
    - Download with pre-signed URLs
    - Bucket management
    - CDN support
    """
    
    def __init__(self):
        if not OSS2_AVAILABLE:
            raise ImportError(
                "oss2 package is required for Aliyun OSS adapter. "
                "Install it with: pip install oss2>=2.18.0"
            )
        
        self._auth: Optional[Auth] = None
        self._default_bucket: Optional[Bucket] = None
        self._buckets: Dict[str, Bucket] = {}
        self._initialized = False
        self._endpoint = ""
        self._cdn_domain = ""
    
    async def initialize(self) -> None:
        """Initialize Aliyun OSS client."""
        if self._initialized:
            return
        
        try:
            # Get credentials from environment
            access_key_id = os.getenv("ALIYUN_ACCESS_KEY_ID")
            access_key_secret = os.getenv("ALIYUN_ACCESS_KEY_SECRET")
            endpoint = os.getenv("ALIYUN_OSS_ENDPOINT", "oss-cn-hangzhou.aliyuncs.com")
            default_bucket_name = os.getenv("ALIYUN_OSS_BUCKET")
            cdn_domain = os.getenv("ALIYUN_OSS_CDN_DOMAIN", "")
            
            if not all([access_key_id, access_key_secret]):
                raise ValueError("Missing required Aliyun OSS credentials")
            
            # Create auth
            self._auth = oss2.Auth(access_key_id, access_key_secret)
            self._endpoint = endpoint
            self._cdn_domain = cdn_domain
            
            # Create default bucket if specified
            if default_bucket_name:
                self._default_bucket = oss2.Bucket(
                    self._auth,
                    endpoint,
                    default_bucket_name
                )
                self._buckets[default_bucket_name] = self._default_bucket
                
                # Test connection
                try:
                    self._default_bucket.get_bucket_info()
                    logger.info(f"Connected to Aliyun OSS bucket: {default_bucket_name}")
                except oss2.exceptions.NoSuchBucket:
                    logger.warning(f"Default bucket '{default_bucket_name}' does not exist")
            
            self._initialized = True
            logger.info("Aliyun OSS adapter initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize Aliyun OSS adapter: {e}")
            raise
    
    async def close(self) -> None:
        """Close OSS connections."""
        # OSS2 doesn't require explicit connection closing
        self._initialized = False
        self._buckets.clear()
        logger.info("Aliyun OSS adapter closed")
    
    async def health_check(self) -> Dict[str, Any]:
        """Check OSS health."""
        if not self._initialized:
            return {"status": "unhealthy", "provider": "aliyun_oss", "error": "Not initialized"}
        
        try:
            if self._default_bucket:
                info = self._default_bucket.get_bucket_info()
                return {
                    "status": "healthy",
                    "provider": "aliyun_oss",
                    "endpoint": self._endpoint,
                    "bucket": self._default_bucket.bucket_name,
                    "creation_date": info.creation_date,
                    "storage_class": info.storage_class
                }
            else:
                return {
                    "status": "healthy",
                    "provider": "aliyun_oss",
                    "endpoint": self._endpoint,
                    "note": "No default bucket configured"
                }
        except Exception as e:
            return {
                "status": "unhealthy",
                "provider": "aliyun_oss",
                "error": str(e)
            }
    
    def _get_bucket(self, bucket: str) -> Bucket:
        """Get or create bucket instance."""
        if bucket not in self._buckets:
            self._buckets[bucket] = oss2.Bucket(
                self._auth,
                self._endpoint,
                bucket
            )
        return self._buckets[bucket]
    
    # ==================== Upload Operations ====================
    
    async def upload_file(
        self,
        bucket: str,
        key: str,
        file_data: bytes,
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
        public: bool = False
    ) -> UploadResult:
        """Upload a file to OSS."""
        bucket_obj = self._get_bucket(bucket)
        
        headers = {}
        if content_type:
            headers['Content-Type'] = content_type
        
        if metadata:
            # OSS uses x-oss-meta- prefix for custom metadata
            for key_meta, value in metadata.items():
                headers[f'x-oss-meta-{key_meta}'] = value
        
        # Upload
        result = bucket_obj.put_object(key, file_data, headers=headers)
        
        # Set ACL if public
        if public:
            bucket_obj.put_object_acl(key, oss2.OBJECT_ACL_PUBLIC_READ)
        
        return UploadResult(
            key=key,
            bucket=bucket,
            size=len(file_data),
            etag=result.etag,
            url=self.get_public_url(bucket, key) if public else None,
            cdn_url=self.get_cdn_url(bucket, key) if self._cdn_domain else None
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
        """Initialize multipart upload."""
        bucket_obj = self._get_bucket(bucket)
        
        headers = {}
        if content_type:
            headers['Content-Type'] = content_type
        
        upload_id = bucket_obj.init_multipart_upload(key, headers=headers).upload_id
        return upload_id
    
    async def multipart_upload_part(
        self,
        bucket: str,
        key: str,
        upload_id: str,
        part_number: int,
        data: bytes
    ) -> Dict[str, Any]:
        """Upload a part."""
        bucket_obj = self._get_bucket(bucket)
        result = bucket_obj.upload_part(key, upload_id, part_number, data)
        
        return {
            "part_number": part_number,
            "etag": result.etag
        }
    
    async def multipart_upload_complete(
        self,
        bucket: str,
        key: str,
        upload_id: str,
        parts: List[Dict[str, Any]]
    ) -> UploadResult:
        """Complete multipart upload."""
        bucket_obj = self._get_bucket(bucket)
        
        # Convert parts to OSS format
        part_info_list = [
            oss2.models.PartInfo(part["part_number"], part["etag"])
            for part in parts
        ]
        
        result = bucket_obj.complete_multipart_upload(key, upload_id, part_info_list)
        
        # Get object size
        head = bucket_obj.head_object(key)
        
        return UploadResult(
            key=key,
            bucket=bucket,
            size=head.content_length,
            etag=result.etag,
            url=self.get_public_url(bucket, key)
        )
    
    # ==================== Download Operations ====================
    
    async def download_file(
        self,
        bucket: str,
        key: str
    ) -> bytes:
        """Download a file."""
        bucket_obj = self._get_bucket(bucket)
        result = bucket_obj.get_object(key)
        return result.read()
    
    async def download_stream(
        self,
        bucket: str,
        key: str,
        stream: BinaryIO
    ) -> None:
        """Download to stream."""
        bucket_obj = self._get_bucket(bucket)
        result = bucket_obj.get_object(key)
        
        # Stream download in chunks
        for chunk in result:
            stream.write(chunk)
    
    async def get_download_url(
        self,
        bucket: str,
        key: str,
        expires_in: int = 3600
    ) -> str:
        """Generate pre-signed download URL."""
        bucket_obj = self._get_bucket(bucket)
        url = bucket_obj.sign_url('GET', key, expires_in)
        return url
    
    async def get_upload_url(
        self,
        bucket: str,
        key: str,
        content_type: Optional[str] = None,
        expires_in: int = 3600
    ) -> str:
        """Generate pre-signed upload URL."""
        bucket_obj = self._get_bucket(bucket)
        
        headers = {}
        if content_type:
            headers['Content-Type'] = content_type
        
        url = bucket_obj.sign_url('PUT', key, expires_in, headers=headers)
        return url
    
    # ==================== File Management ====================
    
    async def delete_file(
        self,
        bucket: str,
        key: str
    ) -> bool:
        """Delete a file."""
        try:
            bucket_obj = self._get_bucket(bucket)
            bucket_obj.delete_object(key)
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
        bucket_obj = self._get_bucket(bucket)
        result = {}
        
        try:
            delete_result = bucket_obj.batch_delete_objects(keys)
            # All deleted successfully
            for key in keys:
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
            dest_bucket_obj = self._get_bucket(dest_bucket)
            dest_bucket_obj.copy_object(source_bucket, source_key, dest_key)
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
        # Copy then delete
        if await self.copy_file(source_bucket, source_key, dest_bucket, dest_key):
            return await self.delete_file(source_bucket, source_key)
        return False
    
    # ==================== Metadata and Listing ====================
    
    async def get_object_metadata(
        self,
        bucket: str,
        key: str
    ) -> StorageObject:
        """Get object metadata."""
        bucket_obj = self._get_bucket(bucket)
        head = bucket_obj.head_object(key)
        
        return StorageObject(
            key=key,
            bucket=bucket,
            size=head.content_length,
            content_type=head.content_type,
            last_modified=datetime.fromtimestamp(head.last_modified),
            etag=head.etag,
            metadata=head.headers,
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
        bucket_obj = self._get_bucket(bucket)
        
        result = bucket_obj.list_objects(
            prefix=prefix or '',
            marker=marker or '',
            max_keys=max_keys
        )
        
        objects = [
            {
                "key": obj.key,
                "size": obj.size,
                "last_modified": datetime.fromtimestamp(obj.last_modified),
                "etag": obj.etag
            }
            for obj in result.object_list
        ]
        
        return {
            "objects": objects,
            "next_marker": result.next_marker if result.is_truncated else None,
            "is_truncated": result.is_truncated
        }
    
    async def file_exists(
        self,
        bucket: str,
        key: str
    ) -> bool:
        """Check if file exists."""
        try:
            bucket_obj = self._get_bucket(bucket)
            bucket_obj.head_object(key)
            return True
        except oss2.exceptions.NoSuchKey:
            return False
        except Exception:
            return False
    
    # ==================== Bucket Management ====================
    
    async def create_bucket(
        self,
        bucket: str,
        public: bool = False
    ) -> bool:
        """Create a new bucket."""
        try:
            bucket_obj = self._get_bucket(bucket)
            bucket_obj.create_bucket()
            
            if public:
                bucket_obj.put_bucket_acl(oss2.BUCKET_ACL_PUBLIC_READ)
            
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
            bucket_obj = self._get_bucket(bucket)
            bucket_obj.delete_bucket()
            return True
        except Exception as e:
            logger.error(f"Failed to delete bucket {bucket}: {e}")
            return False
    
    async def list_buckets(self) -> List[str]:
        """List all buckets."""
        service = oss2.Service(self._auth, self._endpoint)
        result = service.list_buckets()
        return [bucket.name for bucket in result.buckets]
    
    async def bucket_exists(
        self,
        bucket: str
    ) -> bool:
        """Check if bucket exists."""
        try:
            bucket_obj = self._get_bucket(bucket)
            bucket_obj.get_bucket_info()
            return True
        except oss2.exceptions.NoSuchBucket:
            return False
        except Exception:
            return False
    
    # ==================== Utility Methods ====================
    
    def get_public_url(
        self,
        bucket: str,
        key: str
    ) -> Optional[str]:
        """Get public URL."""
        # Format: https://{bucket}.{endpoint}/{key}
        return f"https://{bucket}.{self._endpoint}/{key}"
    
    def get_cdn_url(
        self,
        bucket: str,
        key: str
    ) -> Optional[str]:
        """Get CDN URL if configured."""
        if self._cdn_domain:
            return f"https://{self._cdn_domain}/{key}"
        return None
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics."""
        return {
            "provider": "aliyun_oss",
            "initialized": self._initialized,
            "endpoint": self._endpoint,
            "cdn_enabled": bool(self._cdn_domain),
            "default_bucket": self._default_bucket.bucket_name if self._default_bucket else None,
            "cached_buckets": len(self._buckets)
        }
