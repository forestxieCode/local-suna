"""
Abstract authentication adapter interface for multi-cloud support.

This adapter provides a unified interface for authentication operations:
- User registration and login
- JWT token generation and validation
- OAuth integration (WeChat, Alipay, etc.)
- Session management
- Password reset and email verification
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum


class AuthProvider(str, Enum):
    """Authentication providers."""
    EMAIL = "email"
    PHONE = "phone"
    WECHAT = "wechat"
    ALIPAY = "alipay"
    GOOGLE = "google"
    GITHUB = "github"


@dataclass
class User:
    """User object."""
    id: str
    email: Optional[str] = None
    phone: Optional[str] = None
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    email_verified: bool = False
    phone_verified: bool = False
    created_at: Optional[datetime] = None
    last_sign_in_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class Session:
    """Authentication session."""
    access_token: str
    refresh_token: Optional[str] = None
    user: Optional[User] = None
    expires_at: Optional[datetime] = None
    token_type: str = "Bearer"


@dataclass
class OAuthConfig:
    """OAuth provider configuration."""
    provider: str
    client_id: str
    client_secret: str
    redirect_uri: str
    scopes: List[str]


class AuthAdapter(ABC):
    """
    Abstract base class for authentication adapters.
    
    All auth providers must implement this interface.
    """
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize authentication service."""
        pass
    
    @abstractmethod
    async def close(self) -> None:
        """Close authentication connections."""
        pass
    
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """Check authentication service health."""
        pass
    
    # ==================== User Registration & Login ====================
    
    @abstractmethod
    async def sign_up_with_email(
        self,
        email: str,
        password: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Session:
        """
        Register a new user with email and password.
        
        Args:
            email: User email
            password: User password (will be hashed)
            metadata: Additional user metadata
            
        Returns:
            Session with access token and user info
        """
        pass
    
    @abstractmethod
    async def sign_up_with_phone(
        self,
        phone: str,
        password: str,
        verification_code: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Session:
        """
        Register a new user with phone number.
        
        Args:
            phone: Phone number (E.164 format)
            password: User password
            verification_code: SMS verification code
            metadata: Additional user metadata
            
        Returns:
            Session with access token and user info
        """
        pass
    
    @abstractmethod
    async def sign_in_with_email(
        self,
        email: str,
        password: str
    ) -> Session:
        """
        Sign in with email and password.
        
        Args:
            email: User email
            password: User password
            
        Returns:
            Session with access token
        """
        pass
    
    @abstractmethod
    async def sign_in_with_phone(
        self,
        phone: str,
        password: str
    ) -> Session:
        """
        Sign in with phone number and password.
        
        Args:
            phone: Phone number
            password: User password
            
        Returns:
            Session with access token
        """
        pass
    
    @abstractmethod
    async def sign_in_with_phone_otp(
        self,
        phone: str,
        otp: str
    ) -> Session:
        """
        Sign in with phone number and OTP (One-Time Password).
        
        Args:
            phone: Phone number
            otp: One-time password from SMS
            
        Returns:
            Session with access token
        """
        pass
    
    # ==================== OAuth ====================
    
    @abstractmethod
    async def get_oauth_url(
        self,
        provider: str,
        redirect_uri: str
    ) -> str:
        """
        Get OAuth authorization URL.
        
        Args:
            provider: OAuth provider (wechat, alipay, google, etc.)
            redirect_uri: Callback URI
            
        Returns:
            Authorization URL to redirect user to
        """
        pass
    
    @abstractmethod
    async def sign_in_with_oauth(
        self,
        provider: str,
        code: str,
        redirect_uri: str
    ) -> Session:
        """
        Sign in with OAuth code.
        
        Args:
            provider: OAuth provider
            code: Authorization code from OAuth callback
            redirect_uri: Original redirect URI
            
        Returns:
            Session with access token
        """
        pass
    
    # ==================== Token Management ====================
    
    @abstractmethod
    async def verify_token(
        self,
        token: str
    ) -> Optional[User]:
        """
        Verify and decode access token.
        
        Args:
            token: Access token to verify
            
        Returns:
            User if token is valid, None otherwise
        """
        pass
    
    @abstractmethod
    async def refresh_session(
        self,
        refresh_token: str
    ) -> Session:
        """
        Refresh access token using refresh token.
        
        Args:
            refresh_token: Refresh token
            
        Returns:
            New session with refreshed access token
        """
        pass
    
    @abstractmethod
    async def sign_out(
        self,
        token: str
    ) -> bool:
        """
        Sign out and invalidate token.
        
        Args:
            token: Access token to invalidate
            
        Returns:
            True if successful
        """
        pass
    
    # ==================== User Management ====================
    
    @abstractmethod
    async def get_user(
        self,
        user_id: str
    ) -> Optional[User]:
        """
        Get user by ID.
        
        Args:
            user_id: User ID
            
        Returns:
            User object or None
        """
        pass
    
    @abstractmethod
    async def get_user_by_email(
        self,
        email: str
    ) -> Optional[User]:
        """Get user by email."""
        pass
    
    @abstractmethod
    async def get_user_by_phone(
        self,
        phone: str
    ) -> Optional[User]:
        """Get user by phone number."""
        pass
    
    @abstractmethod
    async def update_user(
        self,
        user_id: str,
        data: Dict[str, Any]
    ) -> User:
        """
        Update user profile.
        
        Args:
            user_id: User ID
            data: Fields to update
            
        Returns:
            Updated user object
        """
        pass
    
    @abstractmethod
    async def delete_user(
        self,
        user_id: str
    ) -> bool:
        """Delete user account."""
        pass
    
    # ==================== Password Management ====================
    
    @abstractmethod
    async def update_password(
        self,
        user_id: str,
        old_password: str,
        new_password: str
    ) -> bool:
        """
        Update user password.
        
        Args:
            user_id: User ID
            old_password: Current password
            new_password: New password
            
        Returns:
            True if successful
        """
        pass
    
    @abstractmethod
    async def reset_password_request(
        self,
        email: str
    ) -> bool:
        """
        Send password reset email.
        
        Args:
            email: User email
            
        Returns:
            True if email sent
        """
        pass
    
    @abstractmethod
    async def reset_password_confirm(
        self,
        token: str,
        new_password: str
    ) -> bool:
        """
        Confirm password reset with token.
        
        Args:
            token: Reset token from email
            new_password: New password
            
        Returns:
            True if successful
        """
        pass
    
    # ==================== Verification ====================
    
    @abstractmethod
    async def send_email_verification(
        self,
        user_id: str
    ) -> bool:
        """Send email verification link."""
        pass
    
    @abstractmethod
    async def verify_email(
        self,
        token: str
    ) -> bool:
        """Verify email with token."""
        pass
    
    @abstractmethod
    async def send_phone_otp(
        self,
        phone: str
    ) -> bool:
        """
        Send OTP to phone number.
        
        Args:
            phone: Phone number
            
        Returns:
            True if SMS sent
        """
        pass
    
    @abstractmethod
    async def verify_phone(
        self,
        phone: str,
        otp: str
    ) -> bool:
        """
        Verify phone number with OTP.
        
        Args:
            phone: Phone number
            otp: One-time password
            
        Returns:
            True if verified
        """
        pass
    
    # ==================== Utility ====================
    
    @abstractmethod
    def hash_password(
        self,
        password: str
    ) -> str:
        """Hash a password for storage."""
        pass
    
    @abstractmethod
    def verify_password(
        self,
        password: str,
        hashed: str
    ) -> bool:
        """Verify password against hash."""
        pass
    
    @abstractmethod
    def generate_token(
        self,
        user_id: str,
        expires_in: int = 3600
    ) -> str:
        """Generate JWT access token."""
        pass
