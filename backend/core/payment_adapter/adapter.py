"""
支付服务适配器 - 统一接口

支持的提供商:
- Stripe (国际, 需要VPN)
- 支付宝 (中国)
- 微信支付 (中国)
- 本地模拟 (开发测试)
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
from dataclasses import dataclass


class PaymentProvider(str, Enum):
    """支付提供商枚举"""
    STRIPE = "stripe"          # 国际支付
    ALIPAY = "alipay"          # 支付宝
    WECHAT = "wechat"          # 微信支付
    LOCAL_MOCK = "local_mock"  # 本地模拟（开发测试）


class PaymentStatus(str, Enum):
    """支付状态"""
    PENDING = "pending"              # 待支付
    PROCESSING = "processing"        # 处理中
    SUCCEEDED = "succeeded"          # 成功
    FAILED = "failed"                # 失败
    CANCELLED = "cancelled"          # 已取消
    REFUNDED = "refunded"            # 已退款
    PARTIALLY_REFUNDED = "partially_refunded"  # 部分退款


class SubscriptionStatus(str, Enum):
    """订阅状态"""
    ACTIVE = "active"              # 活跃
    PAST_DUE = "past_due"          # 逾期
    CANCELLED = "cancelled"        # 已取消
    UNPAID = "unpaid"              # 未支付
    TRIALING = "trialing"          # 试用中
    INCOMPLETE = "incomplete"      # 未完成


class Currency(str, Enum):
    """货币类型"""
    USD = "USD"  # 美元
    CNY = "CNY"  # 人民币
    EUR = "EUR"  # 欧元


@dataclass
class PaymentIntent:
    """支付意图"""
    id: str                           # 支付ID
    amount: int                       # 金额（分）
    currency: Currency                # 货币
    status: PaymentStatus             # 状态
    customer_id: Optional[str] = None # 客户ID
    description: Optional[str] = None # 描述
    metadata: Optional[Dict[str, Any]] = None  # 元数据
    created_at: Optional[datetime] = None      # 创建时间
    payment_method: Optional[str] = None       # 支付方式
    client_secret: Optional[str] = None        # 客户端密钥（前端支付用）


@dataclass
class Subscription:
    """订阅信息"""
    id: str                                    # 订阅ID
    customer_id: str                           # 客户ID
    status: SubscriptionStatus                 # 状态
    plan_id: str                              # 计划ID
    current_period_start: datetime            # 当前周期开始
    current_period_end: datetime              # 当前周期结束
    cancel_at_period_end: bool = False        # 周期结束时取消
    trial_end: Optional[datetime] = None      # 试用结束时间
    metadata: Optional[Dict[str, Any]] = None # 元数据


@dataclass
class Customer:
    """客户信息"""
    id: str                                    # 客户ID
    email: str                                 # 邮箱
    name: Optional[str] = None                # 名称
    phone: Optional[str] = None               # 电话
    metadata: Optional[Dict[str, Any]] = None # 元数据
    created_at: Optional[datetime] = None     # 创建时间


@dataclass
class Refund:
    """退款信息"""
    id: str                                    # 退款ID
    payment_id: str                           # 原支付ID
    amount: int                               # 退款金额（分）
    reason: Optional[str] = None              # 退款原因
    status: PaymentStatus                     # 状态
    created_at: Optional[datetime] = None     # 创建时间


class PaymentAdapter(ABC):
    """
    支付服务适配器抽象基类
    
    所有支付提供商必须实现此接口
    """
    
    def __init__(self, provider: PaymentProvider):
        self.provider = provider
    
    # ========================================================================
    # 客户管理
    # ========================================================================
    
    @abstractmethod
    async def create_customer(
        self,
        email: str,
        name: Optional[str] = None,
        phone: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Customer:
        """
        创建客户
        
        Args:
            email: 客户邮箱
            name: 客户姓名
            phone: 客户电话
            metadata: 自定义元数据
            
        Returns:
            Customer: 客户信息
        """
        pass
    
    @abstractmethod
    async def get_customer(self, customer_id: str) -> Optional[Customer]:
        """获取客户信息"""
        pass
    
    @abstractmethod
    async def update_customer(
        self,
        customer_id: str,
        email: Optional[str] = None,
        name: Optional[str] = None,
        phone: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Customer:
        """更新客户信息"""
        pass
    
    @abstractmethod
    async def delete_customer(self, customer_id: str) -> bool:
        """删除客户"""
        pass
    
    # ========================================================================
    # 支付意图
    # ========================================================================
    
    @abstractmethod
    async def create_payment_intent(
        self,
        amount: int,
        currency: Currency,
        customer_id: Optional[str] = None,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> PaymentIntent:
        """
        创建支付意图
        
        Args:
            amount: 金额（分）
            currency: 货币类型
            customer_id: 客户ID
            description: 描述
            metadata: 元数据
            
        Returns:
            PaymentIntent: 支付意图（包含client_secret用于前端支付）
        """
        pass
    
    @abstractmethod
    async def get_payment_intent(self, payment_id: str) -> Optional[PaymentIntent]:
        """获取支付意图"""
        pass
    
    @abstractmethod
    async def confirm_payment(self, payment_id: str) -> PaymentIntent:
        """确认支付（服务端确认）"""
        pass
    
    @abstractmethod
    async def cancel_payment(self, payment_id: str) -> PaymentIntent:
        """取消支付"""
        pass
    
    # ========================================================================
    # 订阅管理
    # ========================================================================
    
    @abstractmethod
    async def create_subscription(
        self,
        customer_id: str,
        plan_id: str,
        trial_days: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Subscription:
        """
        创建订阅
        
        Args:
            customer_id: 客户ID
            plan_id: 计划ID
            trial_days: 试用天数
            metadata: 元数据
            
        Returns:
            Subscription: 订阅信息
        """
        pass
    
    @abstractmethod
    async def get_subscription(self, subscription_id: str) -> Optional[Subscription]:
        """获取订阅信息"""
        pass
    
    @abstractmethod
    async def cancel_subscription(
        self,
        subscription_id: str,
        cancel_at_period_end: bool = True
    ) -> Subscription:
        """
        取消订阅
        
        Args:
            subscription_id: 订阅ID
            cancel_at_period_end: 是否在周期结束时取消（True=周期结束，False=立即）
        """
        pass
    
    @abstractmethod
    async def update_subscription(
        self,
        subscription_id: str,
        plan_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Subscription:
        """更新订阅"""
        pass
    
    @abstractmethod
    async def list_customer_subscriptions(
        self,
        customer_id: str
    ) -> List[Subscription]:
        """列出客户的所有订阅"""
        pass
    
    # ========================================================================
    # 退款
    # ========================================================================
    
    @abstractmethod
    async def create_refund(
        self,
        payment_id: str,
        amount: Optional[int] = None,  # None表示全额退款
        reason: Optional[str] = None
    ) -> Refund:
        """
        创建退款
        
        Args:
            payment_id: 原支付ID
            amount: 退款金额（分），None表示全额退款
            reason: 退款原因
        """
        pass
    
    @abstractmethod
    async def get_refund(self, refund_id: str) -> Optional[Refund]:
        """获取退款信息"""
        pass
    
    # ========================================================================
    # Webhook处理
    # ========================================================================
    
    @abstractmethod
    async def verify_webhook_signature(
        self,
        payload: bytes,
        signature: str,
        secret: str
    ) -> bool:
        """
        验证Webhook签名
        
        Args:
            payload: 原始请求体
            signature: 签名头
            secret: Webhook密钥
            
        Returns:
            bool: 签名是否有效
        """
        pass
    
    @abstractmethod
    async def parse_webhook_event(
        self,
        payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        解析Webhook事件
        
        Args:
            payload: Webhook负载
            
        Returns:
            Dict: 标准化的事件数据
            {
                "type": "payment.succeeded",
                "data": {...}
            }
        """
        pass
    
    # ========================================================================
    # 工具方法
    # ========================================================================
    
    @abstractmethod
    async def get_provider_dashboard_url(
        self,
        resource_type: str,  # "customer", "payment", "subscription"
        resource_id: str
    ) -> str:
        """
        获取提供商控制台URL
        
        Args:
            resource_type: 资源类型
            resource_id: 资源ID
            
        Returns:
            str: 控制台URL
        """
        pass
    
    def format_amount(self, amount: int, currency: Currency) -> str:
        """
        格式化金额显示
        
        Args:
            amount: 金额（分）
            currency: 货币
            
        Returns:
            str: 格式化字符串，如 "¥99.00", "$9.99"
        """
        if currency == Currency.CNY:
            return f"¥{amount / 100:.2f}"
        elif currency == Currency.USD:
            return f"${amount / 100:.2f}"
        elif currency == Currency.EUR:
            return f"€{amount / 100:.2f}"
        return f"{amount / 100:.2f} {currency.value}"
