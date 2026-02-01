"""
Tencent Cloud COS (Cloud Object Storage) adapter implementation.

Required Python package:
    cos-python-sdk-v5>=1.9.0

Configuration via environment variables:
    TENCENT_SECRET_ID: Secret ID
    TENCENT_SECRET_KEY: Secret Key
    TENCENT_COS_REGION: Region (e.g., ap-guangzhou, ap-shanghai)
    TENCENT_COS_BUCKET: Bucket name (format: bucketname-appid)
    TENCENT_COS_APPID: App ID
    TENCENT_COS_CDN_DOMAIN: Optional CDN domain
"""

from typing import Optional, Dict, Any, List, BinaryIO
from datetime import datetime, timedelta
import os
import io

try:
    from qcloud_cos import CosConfig, CosS3Client
    from qcloud_cos.cos_exception import CosException
    COS_AVAILABLE = True
except ImportError:
    COS_AVAILABLE = False
    CosConfig = None
    CosS3Client = None

from ..adapter import StorageAdapter, StorageObject, UploadResult
from core.utils.logger import logger


class TencentCOSAdapter(StorageAdapter):
    """
    Adapter for Tencent Cloud COS (Cloud Object Storage).
    
    Implementation follows the same pattern as AliyunOSSAdapter.
    """
    
    def __init__(self):
        if not COS_AVAILABLE:
            raise ImportError(
                "qcloud_cos package is required for Tencent COS adapter. "
                "Install it with: pip install cos-python-sdk-v5>=1.9.0"
            )
        
        self._client: Optional[CosS3Client] = None
        self._initialized = False
        self._region = ""
        self._bucket = ""
        self._cdn_domain = ""
    
    async def initialize(self) -> None:
        """Initialize Tencent COS client."""
        if self._initialized:
            return
        
        try:
            secret_id = os.getenv("TENCENT_SECRET_ID")
            secret_key = os.getenv("TENCENT_SECRET_KEY")
            region = os.getenv("TENCENT_COS_REGION", "ap-guangzhou")
            bucket = os.getenv("TENCENT_COS_BUCKET")
            cdn_domain = os.getenv("TENCENT_COS_CDN_DOMAIN", "")
            
            if not all([secret_id, secret_key]):
                raise ValueError("Missing required Tencent COS credentials")
            
            # Create config
            config = CosConfig(
                Region=region,
                SecretId=secret_id,
                SecretKey=secret_key,
                Scheme='https'
            )
            
            # Create client
            self._client = CosS3Client(config)
            self._region = region
            self._bucket = bucket
            self._cdn_domain = cdn_domain
            
            # Test connection if bucket specified
            if bucket:
                try:
                    self._client.head_bucket(Bucket=bucket)
                    logger.info(f"Connected to Tencent COS bucket: {bucket}")
                except CosException as e:
                    logger.warning(f"Bucket '{bucket}' check failed: {e}")
            
            self._initialized = True
            logger.info("Tencent COS adapter initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize Tencent COS adapter: {e}")
            raise
    
    async def close(self) -> None:
        """Close COS connections."""
        self._initialized = False
        logger.info("Tencent COS adapter closed")
    
    async def health_check(self) -> Dict[str, Any]:
        """Check COS health."""
        if not self._initialized:
            return {"status": "unhealthy", "provider": "tencent_cos", "error": "Not initialized"}
        
        try:
            if self._bucket:
                response = self._client.head_bucket(Bucket=self._bucket)
                return {
                    "status": "healthy",
                    "provider": "tencent_cos",
                    "region": self._region,
                    "bucket": self._bucket
                }
            else:
                return {
                    "status": "healthy",
                    "provider": "tencent_cos",
                    "region": self._region,
                    "note": "No default bucket configured"
                }
        except Exception as e:
            return {
                "status": "unhealthy",
                "provider": "tencent_cos",
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
        """Upload a file to COS."""
        headers = {}
        if content_type:
            headers['Content-Type'] = content_type
        
        # COS metadata
        if metadata:
            for k, v in metadata.items():
                headers[f'x-cos-meta-{k}'] = v
        
        # Upload
        response = self._client.put_object(
            Bucket=bucket,
            Key=key,
            Body=file_data,
            **headers
        )
        
        # Set ACL if public
        if public:
            self._client.put_object_acl(
                Bucket=bucket,
                Key=key,
                ACL='public-read'
            )
        
        return UploadResult(
            key=key,
            bucket=bucket,
            size=len(file_data),
            etag=response.get('ETag', '').strip('"'),
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
        headers = {}
        if content_type:
            headers['Content-Type'] = content_type
        
        response = self._client.create_multipart_upload(
            Bucket=bucket,
            Key=key,
            **headers
        )
        return response['UploadId']
    
    async def multipart_upload_part(
        self,
        bucket: str,
        key: str,
        upload_id: str,
        part_number: int,
        data: bytes
    ) -> Dict[str, Any]:
        """Upload a part."""
        response = self._client.upload_part(
            Bucket=bucket,
            Key=key,
            UploadId=upload_id,
            PartNumber=part_number,
            Body=data
        )
        
        return {
            "part_number": part_number,
            "etag": response['ETag'].strip('"')
        }
    
    async def multipart_upload_complete(
        self,
        bucket: str,
        key: str,
        upload_id: str,
        parts: List[Dict[str, Any]]
    ) -> UploadResult:
        """Complete multipart upload."""
        multipart = {
            'Part': [
                {'PartNumber': p['part_number'], 'ETag': p['etag']}
                for p in parts
            ]
        }
        
        response = self._client.complete_multipart_upload(
            Bucket=bucket,
            Key=key,
            UploadId=upload_id,
            MultipartUpload=multipart
        )
        
        # Get object size
        head = self._client.head_object(Bucket=bucket, Key=key)
        
        return UploadResult(
            key=key,
            bucket=bucket,
            size=int(head.get('Content-Length', 0)),
            etag=response.get('ETag', '').strip('"'),
            url=self.get_public_url(bucket, key)
        )
    
    # Download Operations
    
    async def download_file(
        self,
        bucket: str,
        key: str
    ) -> bytes:
        """Download a file."""
        response = self._client.get_object(Bucket=bucket, Key=key)
        return response['Body'].read()
    
    async def download_stream(
        self,
        bucket: str,
        key: str,
        stream: BinaryIO
    ) -> None:
        """Download to stream."""
        response = self._client.get_object(Bucket=bucket, Key=key)
        for chunk in response['Body'].iter_chunks():
            stream.write(chunk)
    
    async def get_download_url(
        self,
        bucket: str,
        key: str,
        expires_in: int = 3600
    ) -> str:
        """Generate pre-signed download URL."""
        url = self._client.get_presigned_url(
            Method='GET',
            Bucket=bucket,
            Key=key,
            Expired=expires_in
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
        headers = {}
        if content_type:
            headers['Content-Type'] = content_type
        
        url = self._client.get_presigned_url(
            Method='PUT',
            Bucket=bucket,
            Key=key,
            Expired=expires_in,
            Headers=headers
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
            self._client.delete_object(Bucket=bucket, Key=key)
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
        objects = [{'Key': key} for key in keys]
        result = {}
        
        try:
            response = self._client.delete_objects(
                Bucket=bucket,
                Delete={'Object': objects}
            )
            
            # Mark deleted as success
            for deleted in response.get('Deleted', []):
                result[deleted['Key']] = True
            
            # Mark errors as failure
            for error in response.get('Error', []):
                result[error['Key']] = False
                
            # Mark remaining as success
            for key in keys:
                if key not in result:
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
            copy_source = {'Bucket': source_bucket, 'Key': source_key, 'Region': self._region}
            self._client.copy_object(
                Bucket=dest_bucket,
                Key=dest_key,
                CopySource=copy_source
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
        head = self._client.head_object(Bucket=bucket, Key=key)
        
        return StorageObject(
            key=key,
            bucket=bucket,
            size=int(head.get('Content-Length', 0)),
            content_type=head.get('Content-Type', ''),
            last_modified=datetime.strptime(head['Last-Modified'], '%a, %d %b %Y %H:%M:%S %Z'),
            etag=head.get('ETag', '').strip('"'),
            metadata=head,
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
        params = {
            'Bucket': bucket,
            'MaxKeys': max_keys
        }
        
        if prefix:
            params['Prefix'] = prefix
        if marker:
            params['Marker'] = marker
        
        response = self._client.list_objects(**params)
        
        objects = [
            {
                "key": obj['Key'],
                "size": obj['Size'],
                "last_modified": datetime.strptime(obj['LastModified'], '%Y-%m-%dT%H:%M:%S.%fZ'),
                "etag": obj['ETag'].strip('"')
            }
            for obj in response.get('Contents', [])
        ]
        
        return {
            "objects": objects,
            "next_marker": response.get('NextMarker'),
            "is_truncated": response.get('IsTruncated', False)
        }
    
    async def file_exists(
        self,
        bucket: str,
        key: str
    ) -> bool:
        """Check if file exists."""
        try:
            self._client.head_object(Bucket=bucket, Key=key)
            return True
        except CosException:
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
            self._client.create_bucket(Bucket=bucket)
            
            if public:
                self._client.put_bucket_acl(Bucket=bucket, ACL='public-read')
            
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
            self._client.delete_bucket(Bucket=bucket)
            return True
        except Exception as e:
            logger.error(f"Failed to delete bucket {bucket}: {e}")
            return False
    
    async def list_buckets(self) -> List[str]:
        """List all buckets."""
        response = self._client.list_buckets()
        return [bucket['Name'] for bucket in response.get('Buckets', [])]
    
    async def bucket_exists(
        self,
        bucket: str
    ) -> bool:
        """Check if bucket exists."""
        try:
            self._client.head_bucket(Bucket=bucket)
            return True
        except CosException:
            return False
        except Exception:
            return False
    
    # Utility Methods
    
    def get_public_url(
        self,
        bucket: str,
        key: str
    ) -> Optional[str]:
        """Get public URL."""
        # Format: https://{bucket}.cos.{region}.myqcloud.com/{key}
        return f"https://{bucket}.cos.{self._region}.myqcloud.com/{key}"
    
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
            "provider": "tencent_cos",
            "initialized": self._initialized,
            "region": self._region,
            "cdn_enabled": bool(self._cdn_domain),
            "default_bucket": self._bucket
        }
