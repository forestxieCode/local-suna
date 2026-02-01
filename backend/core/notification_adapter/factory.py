"""
通知适配器工厂

根据环境变量自动选择合适的通知提供商
"""

import os
from typing import Optional
from .adapter import NotificationAdapter, NotificationProvider


# 单例实例
_adapter_instance: Optional[NotificationAdapter] = None


def get_notification_adapter() -> NotificationAdapter:
    """
    获取通知适配器实例（单例模式）
    
    检测顺序：
    1. NOTIFICATION_PROVIDER 环境变量（显式指定）
    2. CLOUD_PROVIDER 环境变量（云服务商）
    3. 检测具体API密钥
    4. 默认使用本地SMTP
    
    Returns:
        NotificationAdapter: 通知适配器实例
    """
    global _adapter_instance
    
    if _adapter_instance is not None:
        return _adapter_instance
    
    provider = _detect_provider()
    _adapter_instance = _create_adapter(provider)
    
    return _adapter_instance


def _detect_provider() -> NotificationProvider:
    """
    自动检测通知提供商
    
    Returns:
        NotificationProvider: 检测到的提供商
    """
    # 1. 显式指定
    notification_provider = os.getenv("NOTIFICATION_PROVIDER", "").lower()
    if notification_provider:
        if notification_provider in ["aliyun", "ali", "alibaba"]:
            return NotificationProvider.ALIYUN
        elif notification_provider in ["tencent", "tc", "qcloud"]:
            return NotificationProvider.TENCENT
        elif notification_provider in ["local", "smtp", "local_smtp"]:
            return NotificationProvider.LOCAL_SMTP
        elif notification_provider == "mailtrap":
            return NotificationProvider.MAILTRAP
    
    # 2. 根据云服务商
    cloud_provider = os.getenv("CLOUD_PROVIDER", "").lower()
    if cloud_provider in ["aliyun", "ali", "alibaba"]:
        return NotificationProvider.ALIYUN
    elif cloud_provider in ["tencent", "tc", "qcloud"]:
        return NotificationProvider.TENCENT
    elif cloud_provider == "local":
        return NotificationProvider.LOCAL_SMTP
    
    # 3. 检测API密钥
    if os.getenv("ALIYUN_ACCESS_KEY_ID") and os.getenv("ALIYUN_ACCESS_KEY_SECRET"):
        return NotificationProvider.ALIYUN
    
    if os.getenv("TENCENT_SECRET_ID") and os.getenv("TENCENT_SECRET_KEY"):
        return NotificationProvider.TENCENT
    
    if os.getenv("MAILTRAP_API_TOKEN"):
        return NotificationProvider.MAILTRAP
    
    # 4. 默认本地SMTP
    return NotificationProvider.LOCAL_SMTP


def _create_adapter(provider: NotificationProvider) -> NotificationAdapter:
    """
    创建适配器实例
    
    Args:
        provider: 提供商类型
        
    Returns:
        NotificationAdapter: 适配器实例
    """
    if provider == NotificationProvider.ALIYUN:
        from .adapters.aliyun_adapter import AliyunNotificationAdapter
        return AliyunNotificationAdapter()
    
    elif provider == NotificationProvider.TENCENT:
        from .adapters.tencent_adapter import TencentNotificationAdapter
        return TencentNotificationAdapter()
    
    elif provider == NotificationProvider.LOCAL_SMTP:
        from .adapters.local_smtp_adapter import LocalSMTPAdapter
        return LocalSMTPAdapter()
    
    elif provider == NotificationProvider.MAILTRAP:
        from .adapters.mailtrap_adapter import MailtrapAdapter
        return MailtrapAdapter()
    
    else:
        raise ValueError(f"Unsupported notification provider: {provider}")


def reset_adapter():
    """重置单例实例（用于测试）"""
    global _adapter_instance
    _adapter_instance = None
