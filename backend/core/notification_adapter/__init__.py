"""通知适配器模块"""

from .adapter import (
    NotificationAdapter,
    NotificationProvider,
    EmailMessage,
    EmailRecipient,
    EmailResult,
    EmailStatus,
    SMSMessage,
    SMSResult,
    SMSStatus
)
from .factory import get_notification_adapter, reset_adapter

__all__ = [
    "NotificationAdapter",
    "NotificationProvider",
    "EmailMessage",
    "EmailRecipient",
    "EmailResult",
    "EmailStatus",
    "SMSMessage",
    "SMSResult",
    "SMSStatus",
    "get_notification_adapter",
    "reset_adapter",
]
