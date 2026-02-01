# 支付适配器实现指南

本目录包含中国化支付服务的适配器实现。

## 📋 支持的提供商

| 提供商 | 状态 | 适用场景 | 实现文件 |
|--------|------|---------|---------|
| **LocalMock** | ✅ 完成 | 开发测试 | `local_mock_adapter.py` |
| **Stripe** | ⚠️ 待重构 | 国际支付（需VPN） | `stripe_adapter.py` (待创建) |
| **支付宝** | ⏳ 待实现 | 中国支付 | `alipay_adapter.py` (待创建) |
| **微信支付** | ⏳ 待实现 | 中国支付 | `wechat_adapter.py` (待创建) |

---

## 🚀 快速开始

### 使用Mock适配器（开发）

```python
# .env
PAYMENT_PROVIDER=local_mock

# 代码中使用
from core.payment_adapter.factory import get_payment_adapter

adapter = get_payment_adapter()

# 创建客户
customer = await adapter.create_customer(
    email="user@example.com",
    name="张三"
)

# 创建支付
payment = await adapter.create_payment_intent(
    amount=9900,  # ¥99.00（单位：分）
    currency=Currency.CNY,
    customer_id=customer.id,
    description="高级会员月费"
)

# 确认支付
confirmed = await adapter.confirm_payment(payment.id)
```

---

## 📝 实现新适配器

### 步骤1: 创建适配器文件

在 `adapters/` 目录下创建新文件，例如 `alipay_adapter.py`

### 步骤2: 继承基类并实现所有方法

```python
from typing import Optional, Dict, Any, List
from ..adapter import (
    PaymentAdapter,
    PaymentProvider,
    PaymentIntent,
    Customer,
    Subscription,
    Refund,
    Currency
)


class AlipayAdapter(PaymentAdapter):
    """支付宝适配器"""
    
    def __init__(self):
        super().__init__(PaymentProvider.ALIPAY)
        
        # 初始化支付宝SDK
        from alipay.aop.api.AlipayClient import AlipayClient
        
        app_id = os.getenv("ALIPAY_APP_ID")
        private_key = os.getenv("ALIPAY_PRIVATE_KEY")
        alipay_public_key = os.getenv("ALIPAY_PUBLIC_KEY")
        
        self.client = AlipayClient(
            appid=app_id,
            app_private_key=private_key,
            alipay_public_key=alipay_public_key
        )
    
    async def create_customer(self, email: str, name: Optional[str] = None, ...):
        # 支付宝不需要预创建客户，直接返回虚拟客户对象
        customer_id = f"alipay_virtual_{hash(email)}"
        return Customer(
            id=customer_id,
            email=email,
            name=name,
            ...
        )
    
    async def create_payment_intent(self, amount: int, currency: Currency, ...):
        # 调用支付宝统一下单API
        from alipay.aop.api.domain.AlipayTradePagePayModel import AlipayTradePagePayModel
        from alipay.aop.api.request.AlipayTradePagePayRequest import AlipayTradePagePayRequest
        
        model = AlipayTradePagePayModel()
        model.out_trade_no = f"order_{uuid.uuid4().hex}"
        model.total_amount = amount / 100  # 转换为元
        model.subject = description
        
        request = AlipayTradePagePayRequest(biz_model=model)
        response = self.client.page_execute(request)
        
        return PaymentIntent(
            id=model.out_trade_no,
            amount=amount,
            currency=currency,
            status=PaymentStatus.PENDING,
            client_secret=response,  # 返回的是HTML表单或URL
            ...
        )
    
    # ... 实现其他必需方法
```

### 步骤3: 在工厂中注册

编辑 `factory.py`，添加检测逻辑和创建逻辑：

```python
# factory.py

def _detect_provider() -> PaymentProvider:
    # 添加检测逻辑
    if os.getenv("ALIPAY_APP_ID"):
        return PaymentProvider.ALIPAY
    ...

def _create_adapter(provider: PaymentProvider) -> PaymentAdapter:
    # 添加创建逻辑
    elif provider == PaymentProvider.ALIPAY:
        from .adapters.alipay_adapter import AlipayAdapter
        return AlipayAdapter()
    ...
```

### 步骤4: 添加环境变量配置

更新 `.env.aliyun.example` 或 `.env.local.example`：

```bash
# 支付配置 - 支付宝
PAYMENT_PROVIDER=alipay
ALIPAY_APP_ID=2021xxxxxxxxxxxxx
ALIPAY_PRIVATE_KEY=MIIEpAIBAAKCA...（你的私钥）
ALIPAY_PUBLIC_KEY=MIIBIjANBg...（支付宝公钥）
ALIPAY_NOTIFY_URL=https://yourdomain.com/api/webhooks/alipay
```

---

## 🔌 适配器API参考

### 必须实现的方法

所有适配器必须实现 `PaymentAdapter` 基类的所有抽象方法：

#### 客户管理
- `create_customer()` - 创建客户
- `get_customer()` - 获取客户
- `update_customer()` - 更新客户
- `delete_customer()` - 删除客户

#### 支付处理
- `create_payment_intent()` - 创建支付意图
- `get_payment_intent()` - 获取支付状态
- `confirm_payment()` - 确认支付
- `cancel_payment()` - 取消支付

#### 订阅管理
- `create_subscription()` - 创建订阅
- `get_subscription()` - 获取订阅
- `cancel_subscription()` - 取消订阅
- `update_subscription()` - 更新订阅
- `list_customer_subscriptions()` - 列出客户订阅

#### 退款
- `create_refund()` - 创建退款
- `get_refund()` - 获取退款

#### Webhook
- `verify_webhook_signature()` - 验证签名
- `parse_webhook_event()` - 解析事件

#### 工具
- `get_provider_dashboard_url()` - 获取控制台URL

---

## 📚 SDK文档

### 支付宝

**官方文档**: https://opendocs.alipay.com/

**Python SDK**:
```bash
pip install alipay-sdk-python
```

**关键API**:
- 统一下单: `AlipayTradePagePayRequest`
- 查询订单: `AlipayTradeQueryRequest`
- 退款: `AlipayTradeRefundRequest`
- 订阅: 需要签约周期扣款产品

### 微信支付

**官方文档**: https://pay.weixin.qq.com/wiki/doc/api/

**Python SDK**:
```bash
pip install wechatpayv3
```

**关键API**:
- Native支付: `/v3/pay/transactions/native`
- H5支付: `/v3/pay/transactions/h5`
- 查询订单: `/v3/pay/transactions/`
- 退款: `/v3/refund/domestic/refunds`

### Stripe

**官方文档**: https://stripe.com/docs/api

**Python SDK**: 已安装 `stripe`

**关键API**:
- PaymentIntent: `stripe.PaymentIntent`
- Customer: `stripe.Customer`
- Subscription: `stripe.Subscription`
- Webhook: `stripe.Webhook.construct_event()`

---

## ⚠️ 重要注意事项

### 1. 金额单位

**统一使用"分"作为单位**：

```python
# ✅ 正确 - ¥99.00 = 9900分
amount = 9900

# ❌ 错误 - 不要使用浮点数
amount = 99.00
```

**转换示例**：
```python
# 分 → 元
yuan = amount / 100

# 元 → 分
fen = int(yuan * 100)
```

### 2. 幂等性

支付操作必须是幂等的，使用唯一标识防止重复支付：

```python
# 支付宝使用 out_trade_no
out_trade_no = f"order_{user_id}_{timestamp}_{uuid}"

# Stripe使用 idempotency_key
idempotency_key = f"sub_{user_id}_{plan_id}"
```

### 3. Webhook安全

**必须验证签名**，防止伪造请求：

```python
async def verify_webhook_signature(self, payload: bytes, signature: str, secret: str):
    # 使用提供商SDK验证
    # 支付宝: 使用公钥验证
    # 微信: 使用HMAC-SHA256
    # Stripe: 使用stripe.Webhook.construct_event()
    ...
```

### 4. 错误处理

捕获并标准化错误：

```python
try:
    response = self.client.execute(request)
except AlipayApiException as e:
    # 转换为统一的异常
    raise PaymentError(f"Alipay error: {e.code} - {e.message}")
```

### 5. 测试环境

**始终使用沙箱环境进行测试**：

```python
# 支付宝沙箱
ALIPAY_GATEWAY = "https://openapi.alipaydev.com/gateway.do"  # 测试
ALIPAY_GATEWAY = "https://openapi.alipay.com/gateway.do"      # 生产

# 微信支付没有独立沙箱，需要申请测试商户号
```

---

## 🧪 测试

### 单元测试示例

```python
import pytest
from core.payment_adapter.factory import get_payment_adapter

@pytest.mark.asyncio
async def test_create_payment():
    adapter = get_payment_adapter()
    
    # 创建客户
    customer = await adapter.create_customer(
        email="test@example.com",
        name="测试用户"
    )
    assert customer.id is not None
    
    # 创建支付
    payment = await adapter.create_payment_intent(
        amount=9900,
        currency=Currency.CNY,
        customer_id=customer.id,
        description="测试支付"
    )
    assert payment.status == PaymentStatus.PENDING
    
    # 确认支付（Mock会立即成功）
    confirmed = await adapter.confirm_payment(payment.id)
    assert confirmed.status == PaymentStatus.SUCCEEDED
```

---

## 📖 参考实现

参考 `local_mock_adapter.py` 查看完整的实现示例。

该Mock适配器展示了：
- ✅ 完整的方法实现
- ✅ 数据模型使用
- ✅ 错误处理
- ✅ 代码注释

---

## 🆘 需要帮助？

1. 查看 `adapter.py` 了解完整的接口定义
2. 参考 `local_mock_adapter.py` 的实现
3. 查看各提供商的官方文档
4. 查看现有的 Stripe 实现（`backend/core/billing/external/stripe/`）

---

**祝开发顺利！** 🚀
