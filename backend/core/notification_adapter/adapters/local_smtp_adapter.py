"""
本地SMTP + Mock短信适配器

用于本地开发和测试环境
"""

import os
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
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


class LocalSMTPAdapter(NotificationAdapter):
    """
    本地SMTP + Mock短信适配器
    
    特点：
    - 使用本地SMTP服务器发送邮件（如Mailpit）
    - Mock短信发送（仅打印日志）
    - 适用于开发和测试
    """
    
    def __init__(self):
        super().__init__(NotificationProvider.LOCAL_SMTP)
        
        # SMTP配置
        self.smtp_host = os.getenv("SMTP_HOST", "localhost")
        self.smtp_port = int(os.getenv("SMTP_PORT", "1025"))
        self.smtp_user = os.getenv("SMTP_USER", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.smtp_use_tls = os.getenv("SMTP_USE_TLS", "false").lower() == "true"
        
        # 默认发件人
        self.default_from_email = os.getenv("SMTP_FROM_EMAIL", "noreply@localhost")
        self.default_from_name = os.getenv("SMTP_FROM_NAME", "Kortix Local")
        
        # Mock短信存储（开发用）
        self._sms_storage: Dict[str, SMSResult] = {}
    
    # ========================================================================
    # 邮件服务
    # ========================================================================
    
    async def send_email(self, message: EmailMessage) -> EmailResult:
        """发送邮件"""
        try:
            # 创建邮件
            msg = MIMEMultipart('alternative')
            msg['Subject'] = message.subject
            msg['From'] = f"{message.from_name or self.default_from_name} <{message.from_email or self.default_from_email}>"
            msg['To'] = ', '.join([f"{r.name} <{r.email}>" if r.name else r.email for r in message.to])
            
            if message.reply_to:
                msg['Reply-To'] = message.reply_to
            
            if message.cc:
                msg['Cc'] = ', '.join([f"{r.name} <{r.email}>" if r.name else r.email for r in message.cc])
            
            # 添加内容
            if message.text_content:
                msg.attach(MIMEText(message.text_content, 'plain', 'utf-8'))
            
            if message.html_content:
                msg.attach(MIMEText(message.html_content, 'html', 'utf-8'))
            
            # 发送
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.smtp_use_tls:
                    server.starttls()
                
                if self.smtp_user and self.smtp_password:
                    server.login(self.smtp_user, self.smtp_password)
                
                recipients = [r.email for r in message.to]
                if message.cc:
                    recipients.extend([r.email for r in message.cc])
                if message.bcc:
                    recipients.extend([r.email for r in message.bcc])
                
                server.sendmail(
                    message.from_email or self.default_from_email,
                    recipients,
                    msg.as_string()
                )
            
            message_id = f"local_{uuid.uuid4().hex[:16]}"
            
            return EmailResult(
                message_id=message_id,
                status=EmailStatus.SENT,
                sent_at=datetime.utcnow()
            )
            
        except Exception as e:
            return EmailResult(
                message_id="",
                status=EmailStatus.FAILED,
                sent_at=datetime.utcnow(),
                error=str(e)
            )
    
    async def send_template_email(
        self,
        to_email: str,
        to_name: Optional[str],
        template_id: str,
        template_vars: Dict[str, Any]
    ) -> EmailResult:
        """
        发送模板邮件（本地实现简化版）
        
        本地环境不支持云端模板，这里简单渲染
        """
        # 简单的模板渲染（实际应使用Jinja2等模板引擎）
        subject = f"Template: {template_id}"
        html_content = f"<h1>Template: {template_id}</h1><pre>{template_vars}</pre>"
        text_content = f"Template: {template_id}\n{template_vars}"
        
        return await self.send_simple_email(
            to_email=to_email,
            to_name=to_name,
            subject=subject,
            html_content=html_content,
            text_content=text_content
        )
    
    async def get_email_status(self, message_id: str) -> EmailStatus:
        """查询邮件状态（本地Mock）"""
        # 本地环境无法跟踪，默认返回已发送
        return EmailStatus.SENT
    
    # ========================================================================
    # 短信服务（Mock）
    # ========================================================================
    
    async def send_sms(self, message: SMSMessage) -> SMSResult:
        """发送短信（Mock实现）"""
        message_id = f"sms_mock_{uuid.uuid4().hex[:16]}"
        
        # Mock: 打印到日志
        print(f"\n{'='*60}")
        print(f"📱 Mock SMS Sent")
        print(f"{'='*60}")
        print(f"To: {message.phone}")
        print(f"Content: {message.content}")
        if message.sign_name:
            print(f"Sign: {message.sign_name}")
        if message.template_code:
            print(f"Template: {message.template_code}")
            print(f"Params: {message.template_params}")
        print(f"{'='*60}\n")
        
        result = SMSResult(
            message_id=message_id,
            status=SMSStatus.SENT,
            sent_at=datetime.utcnow()
        )
        
        # 存储到内存（方便测试验证）
        self._sms_storage[message_id] = result
        
        return result
    
    async def send_verification_code(
        self,
        phone: str,
        code: str,
        expire_minutes: int = 5
    ) -> SMSResult:
        """发送验证码（Mock）"""
        message = SMSMessage(
            phone=phone,
            content=f"【Kortix】您的验证码是：{code}，{expire_minutes}分钟内有效。",
            sign_name="Kortix"
        )
        return await self.send_sms(message)
    
    async def send_template_sms(
        self,
        phone: str,
        template_code: str,
        template_params: Dict[str, str],
        sign_name: Optional[str] = None
    ) -> SMSResult:
        """发送模板短信（Mock）"""
        # Mock: 简单渲染模板
        content = f"Template {template_code}: {template_params}"
        
        message = SMSMessage(
            phone=phone,
            content=content,
            template_code=template_code,
            template_params=template_params,
            sign_name=sign_name or "Kortix"
        )
        return await self.send_sms(message)
    
    async def get_sms_status(self, message_id: str) -> SMSStatus:
        """查询短信状态（Mock）"""
        result = self._sms_storage.get(message_id)
        if result:
            return result.status
        return SMSStatus.FAILED
    
    # ========================================================================
    # 工具方法
    # ========================================================================
    
    def get_sent_sms_count(self) -> int:
        """获取已发送短信数量（测试用）"""
        return len(self._sms_storage)
    
    def get_last_sms(self) -> Optional[SMSResult]:
        """获取最后发送的短信（测试用）"""
        if self._sms_storage:
            return list(self._sms_storage.values())[-1]
        return None
    
    def clear_sms_storage(self):
        """清空短信存储（测试用）"""
        self._sms_storage.clear()
