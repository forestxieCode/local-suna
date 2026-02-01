# Authentication Adapters Implementation Guide

## Overview

This directory contains authentication adapter implementations for multi-cloud support.

## Status

### ✅ Interface Defined
- `adapter.py` - Complete authentication interface
- `factory.py` - Provider selection and factory

### 🔲 To Be Implemented

#### Supabase Auth Adapter
**File**: `supabase_auth.py`  
**Priority**: High (for backward compatibility)

Wraps existing Supabase Auth to conform to the AuthAdapter interface.

#### JWT Auth Adapter  
**File**: `jwt_auth.py`  
**Priority**: High (for China deployments)

Self-hosted authentication using:
- FastAPI + JWT
- Redis for session storage
- Aliyun/Tencent SMS for phone verification
- Email service for verification

**Features needed**:
- User registration/login
- JWT token generation and validation
- Password hashing (bcrypt)
- Phone OTP via Aliyun SMS
- Email verification
- OAuth integration (WeChat, Alipay)

## Implementation Notes

The authentication layer is **partially complete**:
1. Interface is fully defined
2. Factory pattern is in place
3. Actual adapter implementations need integration with existing `backend/auth/` module

**Recommendation**: 
- For MVP, continue using existing Supabase Auth
- Implement JWT adapter when migrating away from Supabase
- The interface is ready - just needs concrete implementations

## Integration Points

Existing auth code is in:
- `backend/auth/auth.py` - Current auth logic
- Can be wrapped or refactored to use adapters

## Quick Implementation

For JWT adapter:
```python
class JWTAuthAdapter(AuthAdapter):
    def __init__(self):
        self._secret = os.getenv("JWT_SECRET")
        self._redis_client = None
        
    async def sign_in_with_email(self, email, password):
        # 1. Look up user in database
        # 2. Verify password with bcrypt
        # 3. Generate JWT token
        # 4. Store session in Redis
        # 5. Return Session object
        pass
```

See `storage/adapters/aliyun_oss.py` for implementation pattern reference.
