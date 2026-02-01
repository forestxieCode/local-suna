"""
通知服务适配器 - 统一接口

支持的功能:
- 邮件发送
- 短信发送
- 模板渲染

支持的提供商:
- 阿里云（邮件推送 + 短信）
- 腾讯云（邮件推送 + 短信）
- 本地SMTP + Mock短信
- Mailtrap（已有，保留兼容）
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
from dataclasses import dataclass


class NotificationProvider(str, Enum):
    """通知提供商枚举"""
    ALIYUN = "aliyun"          # 阿里云
    TENCENT = "tencent"        # 腾讯云
    LOCAL_SMTP = "local_smtp"  # 本地SMTP
    MAILTRAP = "mailtrap"      # Mailtrap（已有）


class EmailStatus(str, Enum):
    """邮件状态"""
    PENDING = "pending"        # 待发送
    SENT = "sent"             # 已发送
    DELIVERED = "delivered"    # 已送达
    FAILED = "failed"         # 失败
    BOUNCED = "bounced"       # 退信


class SMSStatus(str, Enum):
    """短信状态"""
    PENDING = "pending"        # 待发送
    SENT = "sent"             # 已发送
    DELIVERED = "delivered"    # 已送达
    FAILED = "failed"         # 失败


@dataclass
class EmailRecipient:
    """邮件收件人"""
    email: str                          # 邮箱地址
    name: Optional[str] = None         # 收件人姓名


@dataclass
class EmailMessage:
    """邮件消息"""
    to: List[EmailRecipient]           # 收件人列表
    subject: str                        # 主题
    html_content: Optional[str] = None # HTML内容
    text_content: Optional[str] = None # 纯文本内容
    from_email: Optional[str] = None   # 发件人邮箱
    from_name: Optional[str] = None    # 发件人姓名
    reply_to: Optional[str] = None     # 回复地址
    cc: Optional[List[EmailRecipient]] = None    # 抄送
    bcc: Optional[List[EmailRecipient]] = None   # 密送
    attachments: Optional[List[Dict[str, Any]]] = None  # 附件


@dataclass
class EmailResult:
    """邮件发送结果"""
    message_id: str                    # 消息ID
    status: EmailStatus                # 状态
    sent_at: datetime                  # 发送时间
    error: Optional[str] = None        # 错误信息


@dataclass
class SMSMessage:
    """短信消息"""
    phone: str                         # 手机号
    content: str                       # 短信内容
    template_code: Optional[str] = None  # 模板代码
    template_params: Optional[Dict[str, str]] = None  # 模板参数
    sign_name: Optional[str] = None    # 签名


@dataclass
class SMSResult:
    """短信发送结果"""
    message_id: str                    # 消息ID
    status: SMSStatus                  # 状态
    sent_at: datetime                  # 发送时间
    error: Optional[str] = None        # 错误信息


class NotificationAdapter(ABC):
    """
    通知服务适配器抽象基类
    
    所有通知提供商必须实现此接口
    """
    
    def __init__(self, provider: NotificationProvider):
        self.provider = provider
    
    # ========================================================================
    # 邮件服务
    # ========================================================================
    
    @abstractmethod
    async def send_email(self, message: EmailMessage) -> EmailResult:
        """
        发送邮件
        
        Args:
            message: 邮件消息
            
        Returns:
            EmailResult: 发送结果
        """
        pass
    
    async def send_simple_email(
        self,
        to_email: str,
        to_name: Optional[str],
        subject: str,
        html_content: Optional[str] = None,
        text_content: Optional[str] = None
    ) -> EmailResult:
        """
        发送简单邮件（便捷方法）
        
        Args:
            to_email: 收件人邮箱
            to_name: 收件人姓名
            subject: 主题
            html_content: HTML内容
            text_content: 纯文本内容
            
        Returns:
            EmailResult: 发送结果
        """
        message = EmailMessage(
            to=[EmailRecipient(email=to_email, name=to_name)],
            subject=subject,
            html_content=html_content,
            text_content=text_content
        )
        return await self.send_email(message)
    
    @abstractmethod
    async def send_template_email(
        self,
        to_email: str,
        to_name: Optional[str],
        template_id: str,
        template_vars: Dict[str, Any]
    ) -> EmailResult:
        """
        发送模板邮件
        
        Args:
            to_email: 收件人邮箱
            to_name: 收件人姓名
            template_id: 模板ID
            template_vars: 模板变量
            
        Returns:
            EmailResult: 发送结果
        """
        pass
    
    @abstractmethod
    async def get_email_status(self, message_id: str) -> EmailStatus:
        """
        查询邮件状态
        
        Args:
            message_id: 消息ID
            
        Returns:
            EmailStatus: 邮件状态
        """
        pass
    
    # ========================================================================
    # 短信服务
    # ========================================================================
    
    @abstractmethod
    async def send_sms(self, message: SMSMessage) -> SMSResult:
        """
        发送短信
        
        Args:
            message: 短信消息
            
        Returns:
            SMSResult: 发送结果
        """
        pass
    
    async def send_verification_code(
        self,
        phone: str,
        code: str,
        expire_minutes: int = 5
    ) -> SMSResult:
        """
        发送验证码短信（便捷方法）
        
        Args:
            phone: 手机号
            code: 验证码
            expire_minutes: 过期时间（分钟）
            
        Returns:
            SMSResult: 发送结果
        """
        # 子类可以重写以使用特定的验证码模板
        message = SMSMessage(
            phone=phone,
            content=f"您的验证码是：{code}，{expire_minutes}分钟内有效。"
        )
        return await self.send_sms(message)
    
    @abstractmethod
    async def send_template_sms(
        self,
        phone: str,
        template_code: str,
        template_params: Dict[str, str],
        sign_name: Optional[str] = None
    ) -> SMSResult:
        """
        发送模板短信
        
        Args:
            phone: 手机号
            template_code: 模板代码
            template_params: 模板参数
            sign_name: 签名
            
        Returns:
            SMSResult: 发送结果
        """
        pass
    
    @abstractmethod
    async def get_sms_status(self, message_id: str) -> SMSStatus:
        """
        查询短信状态
        
        Args:
            message_id: 消息ID
            
        Returns:
            SMSStatus: 短信状态
        """
        pass
    
    # ========================================================================
    # 批量发送
    # ========================================================================
    
    async def send_bulk_emails(
        self,
        messages: List[EmailMessage]
    ) -> List[EmailResult]:
        """
        批量发送邮件
        
        Args:
            messages: 邮件消息列表
            
        Returns:
            List[EmailResult]: 发送结果列表
        """
        results = []
        for message in messages:
            try:
                result = await self.send_email(message)
                results.append(result)
            except Exception as e:
                # 单个失败不影响其他
                results.append(EmailResult(
                    message_id="",
                    status=EmailStatus.FAILED,
                    sent_at=datetime.utcnow(),
                    error=str(e)
                ))
        return results
    
    async def send_bulk_sms(
        self,
        messages: List[SMSMessage]
    ) -> List[SMSResult]:
        """
        批量发送短信
        
        Args:
            messages: 短信消息列表
            
        Returns:
            List[SMSResult]: 发送结果列表
        """
        results = []
        for message in messages:
            try:
                result = await self.send_sms(message)
                results.append(result)
            except Exception as e:
                results.append(SMSResult(
                    message_id="",
                    status=SMSStatus.FAILED,
                    sent_at=datetime.utcnow(),
                    error=str(e)
                ))
        return results
    
    # ========================================================================
    # 工具方法
    # ========================================================================
    
    def validate_email(self, email: str) -> bool:
        """
        验证邮箱格式
        
        Args:
            email: 邮箱地址
            
        Returns:
            bool: 是否有效
        """
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def validate_phone(self, phone: str) -> bool:
        """
        验证手机号格式（中国大陆）
        
        Args:
            phone: 手机号
            
        Returns:
            bool: 是否有效
        """
        import re
        # 支持+86、86、不带前缀
        pattern = r'^(\+?86)?1[3-9]\d{9}$'
        return re.match(pattern, phone) is not None
    
    def normalize_phone(self, phone: str) -> str:
        """
        标准化手机号（去除+86、86前缀）
        
        Args:
            phone: 原始手机号
            
        Returns:
            str: 标准化手机号（11位）
        """
        # 移除所有非数字字符
        phone = ''.join(filter(str.isdigit, phone))
        # 移除86前缀
        if phone.startswith('86') and len(phone) == 13:
            phone = phone[2:]
        return phone
