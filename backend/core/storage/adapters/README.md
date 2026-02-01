# Storage Adapters Implementation Guide

## Overview

This directory contains storage adapter implementations for multi-cloud object storage support.

## Implemented Adapters

### ✅ Aliyun OSS Adapter (Reference Implementation)
**File**: `aliyun_oss.py`  
**Status**: Fully implemented  
**Features**:
- Single and multipart uploads
- Download with pre-signed URLs
- Bucket management
- CDN support
- Batch operations

This adapter serves as the reference implementation. Other adapters should follow the same pattern.

## Adapters To Be Implemented

Following adapters need to be implemented using the same pattern as `AliyunOSSAdapter`:

### 🔲 Supabase Storage Adapter
**File**: `supabase_storage.py`  
**Package**: `supabase>=2.17.0` (already installed)  
**Config Env Vars**:
- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`
- `SUPABASE_SERVICE_ROLE_KEY`

**Implementation Notes**:
- Use Supabase Storage API
- Wrap existing Supabase client if available
- Support public/private buckets

### 🔲 Tencent Cloud COS Adapter
**File**: `tencent_cos.py`  
**Package**: `cos-python-sdk-v5>=1.9.0`  
**Config Env Vars**:
- `TENCENT_SECRET_ID`
- `TENCENT_SECRET_KEY`
- `TENCENT_COS_REGION`
- `TENCENT_COS_BUCKET`
- `TENCENT_COS_CDN_DOMAIN` (optional)

**Implementation Notes**:
- Very similar to Aliyun OSS adapter
- COS uses different API but same concepts
- Support CDN acceleration

### 🔲 MinIO Adapter
**File**: `minio_adapter.py`  
**Package**: `minio>=7.2.0`  
**Config Env Vars**:
- `MINIO_ENDPOINT`
- `MINIO_ACCESS_KEY`
- `MINIO_SECRET_KEY`
- `MINIO_BUCKET`
- `MINIO_SECURE` (default: true)

**Implementation Notes**:
- S3-compatible interface
- Ideal for local/self-hosted deployments
- Use in Docker Compose for local development

### 🔲 AWS S3 Adapter (Optional)
**File**: `aws_s3.py`  
**Package**: `boto3>=1.40.74` (already installed)  
**Config Env Vars**:
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_S3_REGION`
- `AWS_S3_BUCKET`
- `AWS_CLOUDFRONT_DOMAIN` (optional)

## Implementation Pattern

All adapters must follow this pattern (see `aliyun_oss.py` as reference):

### 1. Inherit from `StorageAdapter`
```python
from ..adapter import StorageAdapter, StorageObject, UploadResult

class MyStorageAdapter(StorageAdapter):
    def __init__(self):
        self._client = None
        self._initialized = False
```

### 2. Implement Core Methods

#### Initialization
```python
async def initialize(self) -> None:
    """Initialize client with credentials from env vars"""
    # 1. Get credentials from environment
    # 2. Create client instance
    # 3. Test connection
    # 4. Set self._initialized = True
```

#### Upload Operations
```python
async def upload_file(self, bucket, key, file_data, ...):
    """Upload file using provider's SDK"""
    # Use provider's upload method
    # Handle metadata and ACL
    # Return UploadResult with URLs
```

#### Download Operations
```python
async def download_file(self, bucket, key):
    """Download file content"""
    # Use provider's download method
    # Return bytes
    
async def get_download_url(self, bucket, key, expires_in):
    """Generate pre-signed URL"""
    # Use provider's URL signing method
```

#### File Management
```python
async def delete_file(self, bucket, key):
    """Delete a file"""
    
async def list_objects(self, bucket, prefix, ...):
    """List objects in bucket"""
```

### 3. Handle Provider-Specific Features

- **Metadata**: Map custom metadata to provider's format
- **ACL**: Handle public/private access appropriately
- **CDN**: Support CDN URLs if available
- **Multipart**: Implement for large files (>5MB)

### 4. Error Handling

```python
try:
    # Provider operation
    result = provider.some_method()
    return success
except ProviderException as e:
    logger.error(f"Operation failed: {e}")
    return failure_or_raise
```

### 5. Environment Configuration

Each adapter should document its required env vars:

```python
"""
Configuration via environment variables:
    PROVIDER_ACCESS_KEY: Access key
    PROVIDER_SECRET_KEY: Secret key
    PROVIDER_ENDPOINT: Service endpoint
    PROVIDER_BUCKET: Default bucket
    PROVIDER_CDN_DOMAIN: Optional CDN
"""
```

## Testing

For each new adapter, create tests:

```python
# tests/test_storage_adapters.py

async def test_aliyun_oss_upload():
    adapter = AliyunOSSAdapter()
    await adapter.initialize()
    
    result = await adapter.upload_file(
        bucket="test",
        key="test.txt",
        file_data=b"Hello World"
    )
    
    assert result.key == "test.txt"
    assert result.size == 11
```

## Adding a New Adapter

1. **Create adapter file**: `adapters/my_adapter.py`
2. **Implement all abstract methods** from `StorageAdapter`
3. **Add to factory**: Update `factory.py` with new provider enum
4. **Add to init**: Update `adapters/__init__.py` import
5. **Update dependencies**: Add package to `pyproject.toml`
6. **Document**: Add env vars to `.env.example`
7. **Test**: Create unit tests

## Quick Start Template

```python
"""
My Storage Provider adapter implementation.

Required package:
    my-storage-sdk>=1.0.0

Configuration:
    MY_PROVIDER_KEY: API key
    MY_PROVIDER_BUCKET: Bucket name
"""

from typing import Optional, Dict, Any, List, BinaryIO
from datetime import datetime
import os

try:
    import my_provider_sdk
    SDK_AVAILABLE = True
except ImportError:
    SDK_AVAILABLE = False

from ..adapter import StorageAdapter, StorageObject, UploadResult
from core.utils.logger import logger


class MyProviderAdapter(StorageAdapter):
    def __init__(self):
        if not SDK_AVAILABLE:
            raise ImportError("my-provider-sdk required")
        
        self._client = None
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize client"""
        api_key = os.getenv("MY_PROVIDER_KEY")
        bucket = os.getenv("MY_PROVIDER_BUCKET")
        
        if not api_key:
            raise ValueError("Missing MY_PROVIDER_KEY")
        
        self._client = my_provider_sdk.Client(api_key)
        self._initialized = True
        logger.info("My provider adapter initialized")
    
    # ... implement other methods following aliyun_oss.py pattern
```

## Dependencies

Add to `backend/pyproject.toml`:

```toml
[project]
dependencies = [
    # Existing dependencies...
    
    # Storage providers (China-friendly)
    "oss2>=2.18.0",  # Aliyun OSS ✅ Implemented
    "cos-python-sdk-v5>=1.9.0",  # Tencent COS
    "minio>=7.2.0",  # MinIO (local/self-hosted)
]
```

## Environment Variables Reference

See `.env.aliyun.example`, `.env.tencent.example`, `.env.local.example` in project root for full configuration examples.
