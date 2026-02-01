"""
本地Mock支付适配器

用于开发和测试环境，模拟支付行为
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from ..adapter import (
    PaymentAdapter,
    PaymentProvider,
    PaymentIntent,
    PaymentStatus,
    Subscription,
    SubscriptionStatus,
    Customer,
    Refund,
    Currency
)


class LocalMockPaymentAdapter(PaymentAdapter):
    """
    本地Mock支付适配器
    
    特点：
    - 所有操作立即成功
    - 数据存储在内存中
    - 适用于开发和测试
    """
    
    def __init__(self):
        super().__init__(PaymentProvider.LOCAL_MOCK)
        
        # 内存存储
        self._customers: Dict[str, Customer] = {}
        self._payments: Dict[str, PaymentIntent] = {}
        self._subscriptions: Dict[str, Subscription] = {}
        self._refunds: Dict[str, Refund] = {}
    
    # ========================================================================
    # 客户管理
    # ========================================================================
    
    async def create_customer(
        self,
        email: str,
        name: Optional[str] = None,
        phone: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Customer:
        customer_id = f"cus_mock_{uuid.uuid4().hex[:16]}"
        customer = Customer(
            id=customer_id,
            email=email,
            name=name,
            phone=phone,
            metadata=metadata or {},
            created_at=datetime.utcnow()
        )
        self._customers[customer_id] = customer
        return customer
    
    async def get_customer(self, customer_id: str) -> Optional[Customer]:
        return self._customers.get(customer_id)
    
    async def update_customer(
        self,
        customer_id: str,
        email: Optional[str] = None,
        name: Optional[str] = None,
        phone: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Customer:
        customer = self._customers.get(customer_id)
        if not customer:
            raise ValueError(f"Customer {customer_id} not found")
        
        if email is not None:
            customer.email = email
        if name is not None:
            customer.name = name
        if phone is not None:
            customer.phone = phone
        if metadata is not None:
            customer.metadata = metadata
        
        return customer
    
    async def delete_customer(self, customer_id: str) -> bool:
        if customer_id in self._customers:
            del self._customers[customer_id]
            return True
        return False
    
    # ========================================================================
    # 支付意图
    # ========================================================================
    
    async def create_payment_intent(
        self,
        amount: int,
        currency: Currency,
        customer_id: Optional[str] = None,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> PaymentIntent:
        payment_id = f"pi_mock_{uuid.uuid4().hex[:16]}"
        client_secret = f"{payment_id}_secret_{uuid.uuid4().hex[:8]}"
        
        payment = PaymentIntent(
            id=payment_id,
            amount=amount,
            currency=currency,
            status=PaymentStatus.PENDING,
            customer_id=customer_id,
            description=description,
            metadata=metadata or {},
            created_at=datetime.utcnow(),
            payment_method="mock_method",
            client_secret=client_secret
        )
        self._payments[payment_id] = payment
        return payment
    
    async def get_payment_intent(self, payment_id: str) -> Optional[PaymentIntent]:
        return self._payments.get(payment_id)
    
    async def confirm_payment(self, payment_id: str) -> PaymentIntent:
        payment = self._payments.get(payment_id)
        if not payment:
            raise ValueError(f"Payment {payment_id} not found")
        
        # Mock: 立即成功
        payment.status = PaymentStatus.SUCCEEDED
        return payment
    
    async def cancel_payment(self, payment_id: str) -> PaymentIntent:
        payment = self._payments.get(payment_id)
        if not payment:
            raise ValueError(f"Payment {payment_id} not found")
        
        payment.status = PaymentStatus.CANCELLED
        return payment
    
    # ========================================================================
    # 订阅管理
    # ========================================================================
    
    async def create_subscription(
        self,
        customer_id: str,
        plan_id: str,
        trial_days: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Subscription:
        subscription_id = f"sub_mock_{uuid.uuid4().hex[:16]}"
        
        now = datetime.utcnow()
        if trial_days:
            trial_end = now + timedelta(days=trial_days)
            status = SubscriptionStatus.TRIALING
        else:
            trial_end = None
            status = SubscriptionStatus.ACTIVE
        
        subscription = Subscription(
            id=subscription_id,
            customer_id=customer_id,
            status=status,
            plan_id=plan_id,
            current_period_start=now,
            current_period_end=now + timedelta(days=30),  # Mock: 30天周期
            trial_end=trial_end,
            metadata=metadata or {}
        )
        self._subscriptions[subscription_id] = subscription
        return subscription
    
    async def get_subscription(self, subscription_id: str) -> Optional[Subscription]:
        return self._subscriptions.get(subscription_id)
    
    async def cancel_subscription(
        self,
        subscription_id: str,
        cancel_at_period_end: bool = True
    ) -> Subscription:
        subscription = self._subscriptions.get(subscription_id)
        if not subscription:
            raise ValueError(f"Subscription {subscription_id} not found")
        
        if cancel_at_period_end:
            subscription.cancel_at_period_end = True
        else:
            subscription.status = SubscriptionStatus.CANCELLED
        
        return subscription
    
    async def update_subscription(
        self,
        subscription_id: str,
        plan_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Subscription:
        subscription = self._subscriptions.get(subscription_id)
        if not subscription:
            raise ValueError(f"Subscription {subscription_id} not found")
        
        if plan_id is not None:
            subscription.plan_id = plan_id
        if metadata is not None:
            subscription.metadata = metadata
        
        return subscription
    
    async def list_customer_subscriptions(
        self,
        customer_id: str
    ) -> List[Subscription]:
        return [
            sub for sub in self._subscriptions.values()
            if sub.customer_id == customer_id
        ]
    
    # ========================================================================
    # 退款
    # ========================================================================
    
    async def create_refund(
        self,
        payment_id: str,
        amount: Optional[int] = None,
        reason: Optional[str] = None
    ) -> Refund:
        payment = self._payments.get(payment_id)
        if not payment:
            raise ValueError(f"Payment {payment_id} not found")
        
        refund_id = f"re_mock_{uuid.uuid4().hex[:16]}"
        refund_amount = amount if amount is not None else payment.amount
        
        refund = Refund(
            id=refund_id,
            payment_id=payment_id,
            amount=refund_amount,
            reason=reason,
            status=PaymentStatus.SUCCEEDED,
            created_at=datetime.utcnow()
        )
        self._refunds[refund_id] = refund
        
        # 更新支付状态
        if refund_amount == payment.amount:
            payment.status = PaymentStatus.REFUNDED
        else:
            payment.status = PaymentStatus.PARTIALLY_REFUNDED
        
        return refund
    
    async def get_refund(self, refund_id: str) -> Optional[Refund]:
        return self._refunds.get(refund_id)
    
    # ========================================================================
    # Webhook处理
    # ========================================================================
    
    async def verify_webhook_signature(
        self,
        payload: bytes,
        signature: str,
        secret: str
    ) -> bool:
        # Mock: 始终通过验证
        return True
    
    async def parse_webhook_event(
        self,
        payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        # Mock: 直接返回payload
        return {
            "type": payload.get("type", "payment.succeeded"),
            "data": payload.get("data", {})
        }
    
    # ========================================================================
    # 工具方法
    # ========================================================================
    
    async def get_provider_dashboard_url(
        self,
        resource_type: str,
        resource_id: str
    ) -> str:
        # Mock: 返回本地路径
        return f"http://localhost:8000/mock-dashboard/{resource_type}/{resource_id}"
