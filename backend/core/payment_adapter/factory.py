"""
支付适配器工厂

根据环境变量自动选择合适的支付提供商
"""

import os
from typing import Optional
from .adapter import PaymentAdapter, PaymentProvider


# 单例实例
_adapter_instance: Optional[PaymentAdapter] = None


def get_payment_adapter() -> PaymentAdapter:
    """
    获取支付适配器实例（单例模式）
    
    检测顺序：
    1. PAYMENT_PROVIDER 环境变量（显式指定）
    2. CLOUD_PROVIDER 环境变量（云服务商）
    3. 检测具体API密钥
    4. 默认使用本地Mock（开发环境）
    
    Returns:
        PaymentAdapter: 支付适配器实例
    """
    global _adapter_instance
    
    if _adapter_instance is not None:
        return _adapter_instance
    
    provider = _detect_provider()
    _adapter_instance = _create_adapter(provider)
    
    return _adapter_instance


def _detect_provider() -> PaymentProvider:
    """
    自动检测支付提供商
    
    Returns:
        PaymentProvider: 检测到的提供商
    """
    # 1. 显式指定
    payment_provider = os.getenv("PAYMENT_PROVIDER", "").lower()
    if payment_provider:
        if payment_provider == "stripe":
            return PaymentProvider.STRIPE
        elif payment_provider in ["alipay", "ali"]:
            return PaymentProvider.ALIPAY
        elif payment_provider in ["wechat", "weixin", "wxpay"]:
            return PaymentProvider.WECHAT
        elif payment_provider in ["local", "mock", "local_mock"]:
            return PaymentProvider.LOCAL_MOCK
    
    # 2. 根据云服务商
    cloud_provider = os.getenv("CLOUD_PROVIDER", "").lower()
    if cloud_provider in ["aliyun", "ali", "alibaba"]:
        return PaymentProvider.ALIPAY
    elif cloud_provider in ["tencent", "tc", "qcloud"]:
        return PaymentProvider.WECHAT
    elif cloud_provider == "local":
        return PaymentProvider.LOCAL_MOCK
    
    # 3. 检测API密钥
    if os.getenv("STRIPE_SECRET_KEY"):
        return PaymentProvider.STRIPE
    
    if os.getenv("ALIPAY_APP_ID") and os.getenv("ALIPAY_PRIVATE_KEY"):
        return PaymentProvider.ALIPAY
    
    if os.getenv("WECHAT_MCHID") and os.getenv("WECHAT_SERIAL_NO"):
        return PaymentProvider.WECHAT
    
    # 4. 默认本地Mock
    return PaymentProvider.LOCAL_MOCK


def _create_adapter(provider: PaymentProvider) -> PaymentAdapter:
    """
    创建适配器实例
    
    Args:
        provider: 提供商类型
        
    Returns:
        PaymentAdapter: 适配器实例
    """
    if provider == PaymentProvider.STRIPE:
        from .adapters.stripe_adapter import StripePaymentAdapter
        return StripePaymentAdapter()
    
    elif provider == PaymentProvider.ALIPAY:
        from .adapters.alipay_adapter import AlipayAdapter
        return AlipayAdapter()
    
    elif provider == PaymentProvider.WECHAT:
        from .adapters.wechat_adapter import WechatPayAdapter
        return WechatPayAdapter()
    
    elif provider == PaymentProvider.LOCAL_MOCK:
        from .adapters.local_mock_adapter import LocalMockPaymentAdapter
        return LocalMockPaymentAdapter()
    
    else:
        raise ValueError(f"Unsupported payment provider: {provider}")


def reset_adapter():
    """重置单例实例（用于测试）"""
    global _adapter_instance
    _adapter_instance = None
