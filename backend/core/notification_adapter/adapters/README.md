# 通知适配器实现指南

本目录包含中国化通知服务（邮件+短信）的适配器实现。

## 📋 支持的提供商

| 提供商 | 状态 | 适用场景 | 实现文件 |
|--------|------|---------|---------|
| **LocalSMTP** | ✅ 完成 | 开发测试 | `local_smtp_adapter.py` |
| **Mailtrap** | ⏳ 待重构 | 开发测试 | `mailtrap_adapter.py` (待创建) |
| **阿里云** | ⏳ 待实现 | 中国生产环境 | `aliyun_adapter.py` (待创建) |
| **腾讯云** | ⏳ 待实现 | 中国生产环境 | `tencent_adapter.py` (待创建) |

---

## 🚀 快速开始

### 使用本地SMTP（开发）

```python
# .env
NOTIFICATION_PROVIDER=local_smtp
SMTP_HOST=localhost
SMTP_PORT=1025  # Mailpit默认端口
SMTP_FROM_EMAIL=noreply@localhost

# 代码中使用
from core.notification_adapter.factory import get_notification_adapter

adapter = get_notification_adapter()

# 发送邮件
result = await adapter.send_simple_email(
    to_email="user@example.com",
    to_name="张三",
    subject="欢迎使用Kortix",
    html_content="<h1>欢迎!</h1><p>感谢注册。</p>",
    text_content="欢迎! 感谢注册。"
)

# 发送验证码短信（Mock）
sms_result = await adapter.send_verification_code(
    phone="13800138000",
    code="123456",
    expire_minutes=5
)
```

---

## 📝 实现新适配器

### 步骤1: 创建适配器文件

在 `adapters/` 目录下创建新文件，例如 `aliyun_adapter.py`

### 步骤2: 继承基类并实现所有方法

```python
from typing import Optional, Dict, Any
from ..adapter import (
    NotificationAdapter,
    NotificationProvider,
    EmailMessage,
    EmailResult,
    EmailStatus,
    SMSMessage,
    SMSResult,
    SMSStatus
)


class AliyunNotificationAdapter(NotificationAdapter):
    """阿里云通知适配器（邮件推送 + 短信）"""
    
    def __init__(self):
        super().__init__(NotificationProvider.ALIYUN)
        
        # 初始化阿里云SDK
        import os
        from alibabacloud_dm20151123.client import Client as DmClient
        from alibabacloud_dysmsapi20170525.client import Client as SmsClient
        from alibabacloud_tea_openapi import models as open_api_models
        
        # 邮件推送客户端
        dm_config = open_api_models.Config(
            access_key_id=os.getenv("ALIYUN_ACCESS_KEY_ID"),
            access_key_secret=os.getenv("ALIYUN_ACCESS_KEY_SECRET"),
            endpoint="dm.aliyuncs.com"
        )
        self.dm_client = DmClient(dm_config)
        
        # 短信客户端
        sms_config = open_api_models.Config(
            access_key_id=os.getenv("ALIYUN_ACCESS_KEY_ID"),
            access_key_secret=os.getenv("ALIYUN_ACCESS_KEY_SECRET"),
            endpoint="dysmsapi.aliyuncs.com"
        )
        self.sms_client = SmsClient(sms_config)
    
    async def send_email(self, message: EmailMessage) -> EmailResult:
        """发送邮件"""
        from alibabacloud_dm20151123 import models as dm_models
        
        request = dm_models.SingleSendMailRequest(
            account_name=message.from_email,
            address_type=1,  # 1=随机账号
            reply_to_address=True if message.reply_to else False,
            to_address=message.to[0].email,
            subject=message.subject,
            html_body=message.html_content,
            text_body=message.text_content
        )
        
        response = self.dm_client.single_send_mail(request)
        
        return EmailResult(
            message_id=response.body.env_id,
            status=EmailStatus.SENT,
            sent_at=datetime.utcnow()
        )
    
    async def send_sms(self, message: SMSMessage) -> SMSResult:
        """发送短信"""
        from alibabacloud_dysmsapi20170525 import models as sms_models
        import json
        
        request = sms_models.SendSmsRequest(
            phone_numbers=message.phone,
            sign_name=message.sign_name,
            template_code=message.template_code,
            template_param=json.dumps(message.template_params) if message.template_params else None
        )
        
        response = self.sms_client.send_sms(request)
        
        return SMSResult(
            message_id=response.body.biz_id,
            status=SMSStatus.SENT if response.body.code == 'OK' else SMSStatus.FAILED,
            sent_at=datetime.utcnow(),
            error=response.body.message if response.body.code != 'OK' else None
        )
    
    # ... 实现其他必需方法
```

### 步骤3: 在工厂中注册

编辑 `factory.py`，添加检测和创建逻辑（已完成）

### 步骤4: 添加环境变量配置

更新 `.env.aliyun.example`:

```bash
# 通知服务 - 阿里云
NOTIFICATION_PROVIDER=aliyun

# 邮件推送
ALIYUN_DM_FROM_EMAIL=noreply@yourdomain.com
ALIYUN_DM_FROM_NAME=Kortix

# 短信服务
ALIYUN_SMS_SIGN_NAME=Kortix
ALIYUN_SMS_VERIFICATION_TEMPLATE=SMS_123456789  # 验证码模板CODE
```

---

## 🔌 适配器API参考

### 必须实现的方法

#### 邮件服务
- `send_email()` - 发送邮件
- `send_template_email()` - 发送模板邮件
- `get_email_status()` - 查询邮件状态

#### 短信服务
- `send_sms()` - 发送短信
- `send_template_sms()` - 发送模板短信
- `get_sms_status()` - 查询短信状态

#### 便捷方法（基类已实现）
- `send_simple_email()` - 发送简单邮件
- `send_verification_code()` - 发送验证码
- `send_bulk_emails()` - 批量发送邮件
- `send_bulk_sms()` - 批量发送短信

---

## 📚 SDK文档

### 阿里云邮件推送

**官方文档**: https://help.aliyun.com/product/29412.html

**Python SDK**:
```bash
pip install alibabacloud-dm20151123
```

**关键API**:
- 单一发信: `SingleSendMailRequest`
- 批量发信: `BatchSendMailRequest`
- 模板发信: `SingleSendMailRequest` (设置template_name)

### 阿里云短信

**官方文档**: https://help.aliyun.com/product/44282.html

**Python SDK**:
```bash
pip install alibabacloud-dysmsapi20170525
```

**关键API**:
- 发送短信: `SendSmsRequest`
- 批量发送: `SendBatchSmsRequest`
- 查询详情: `QuerySendDetailsRequest`

### 腾讯云邮件推送

**官方文档**: https://cloud.tencent.com/document/product/1288

**Python SDK**:
```bash
pip install tencentcloud-sdk-python
```

### 腾讯云短信

**官方文档**: https://cloud.tencent.com/document/product/382

**Python SDK**: 已包含在 `tencentcloud-sdk-python`

---

## ⚠️ 重要注意事项

### 1. 邮件发送限制

**阿里云邮件推送**:
- 需要域名验证和备案
- 每日发送量有限额
- 必须配置发信地址

**本地SMTP**:
- 适合开发测试
- 推荐使用Mailpit（http://localhost:8025查看）

### 2. 短信签名和模板

**必须先申请签名和模板**：

```python
# 阿里云短信模板示例
# 模板CODE: SMS_123456789
# 模板内容: 您的验证码是${code}，${expire}分钟内有效。

# 使用
await adapter.send_template_sms(
    phone="13800138000",
    template_code="SMS_123456789",
    template_params={
        "code": "123456",
        "expire": "5"
    },
    sign_name="Kortix"
)
```

### 3. 手机号格式

**统一使用11位手机号**：

```python
# 使用工具方法标准化
phone = adapter.normalize_phone("+86 138 0013 8000")
# 结果: "13800138000"

# 验证格式
is_valid = adapter.validate_phone(phone)
```

### 4. 错误处理

```python
try:
    result = await adapter.send_sms(message)
    if result.status == SMSStatus.FAILED:
        print(f"发送失败: {result.error}")
except Exception as e:
    print(f"异常: {e}")
```

### 5. 频率限制

**阿里云短信限制**:
- 同一手机号1分钟最多1条
- 同一手机号1小时最多5条
- 同一手机号1天最多10条

**建议**: 在应用层实现频率控制

---

## 🧪 测试

### 单元测试示例

```python
import pytest
from core.notification_adapter.factory import get_notification_adapter

@pytest.mark.asyncio
async def test_send_email():
    adapter = get_notification_adapter()
    
    result = await adapter.send_simple_email(
        to_email="test@example.com",
        to_name="测试用户",
        subject="测试邮件",
        html_content="<h1>测试</h1>",
        text_content="测试"
    )
    
    assert result.status == EmailStatus.SENT
    assert result.message_id is not None

@pytest.mark.asyncio
async def test_send_verification_code():
    adapter = get_notification_adapter()
    
    result = await adapter.send_verification_code(
        phone="13800138000",
        code="123456"
    )
    
    assert result.status == SMSStatus.SENT
    assert result.message_id is not None
```

### 本地测试（使用Mailpit）

```bash
# 1. 启动Mailpit（Docker Compose已包含）
docker compose -f docker-compose.local.yaml up mailpit -d

# 2. 配置
SMTP_HOST=localhost
SMTP_PORT=1025

# 3. 发送测试邮件
python -c "
from core.notification_adapter import get_notification_adapter
import asyncio

async def test():
    adapter = get_notification_adapter()
    result = await adapter.send_simple_email(
        to_email='test@example.com',
        to_name='测试',
        subject='测试邮件',
        html_content='<h1>测试</h1>'
    )
    print(result)

asyncio.run(test())
"

# 4. 查看邮件: http://localhost:8025
```

---

## 📖 参考实现

参考 `local_smtp_adapter.py` 查看完整的实现示例。

该适配器展示了：
- ✅ SMTP邮件发送
- ✅ Mock短信发送
- ✅ 完整的错误处理
- ✅ 测试工具方法

---

## 🆘 需要帮助？

1. 查看 `adapter.py` 了解完整的接口定义
2. 参考 `local_smtp_adapter.py` 的实现
3. 查看各提供商的官方文档
4. 查看现有的邮件服务（`backend/core/services/email.py`）

---

**祝开发顺利！** 📧📱
