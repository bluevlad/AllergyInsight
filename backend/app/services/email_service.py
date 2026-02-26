"""이메일 발송 서비스

Gmail SMTP를 사용한 이메일 발송을 제공합니다.
"""
import os
import smtplib
import logging
from dataclasses import dataclass
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class SendResult:
    """이메일 발송 결과"""
    success: bool
    recipient: str
    error: Optional[str] = None


class EmailService:
    """Gmail SMTP 이메일 발송 서비스"""

    def __init__(
        self,
        gmail_address: Optional[str] = None,
        gmail_app_password: Optional[str] = None,
    ):
        self.gmail_address = gmail_address or os.getenv("GMAIL_ADDRESS", "")
        self.gmail_app_password = gmail_app_password or os.getenv("GMAIL_APP_PASSWORD", "")
        self.smtp_host = "smtp.gmail.com"
        self.smtp_port = 587

    @property
    def is_configured(self) -> bool:
        """이메일 설정 여부"""
        return bool(self.gmail_address and self.gmail_app_password)

    def send(
        self,
        to: str,
        subject: str,
        html_body: str,
        from_name: str = "AllergyInsight",
    ) -> SendResult:
        """이메일 발송

        Args:
            to: 수신자 이메일
            subject: 제목
            html_body: HTML 본문
            from_name: 발신자 이름

        Returns:
            SendResult: 발송 결과
        """
        if not self.is_configured:
            return SendResult(
                success=False,
                recipient=to,
                error="이메일 설정이 되어있지 않습니다 (GMAIL_ADDRESS, GMAIL_APP_PASSWORD)",
            )

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{from_name} <{self.gmail_address}>"
            msg["To"] = to

            msg.attach(MIMEText(html_body, "html", "utf-8"))

            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.gmail_address, self.gmail_app_password)
                server.send_message(msg)

            logger.info(f"이메일 발송 성공: {to}")
            return SendResult(success=True, recipient=to)

        except Exception as e:
            logger.error(f"이메일 발송 실패 ({to}): {e}")
            return SendResult(success=False, recipient=to, error=str(e))

    def send_batch(
        self,
        recipients: list[str],
        subject: str,
        html_body: str,
        from_name: str = "AllergyInsight",
    ) -> list[SendResult]:
        """다수 수신자에게 이메일 일괄 발송"""
        results = []
        for recipient in recipients:
            result = self.send(recipient, subject, html_body, from_name)
            results.append(result)
        return results


# 싱글톤
_email_service: Optional[EmailService] = None


def get_email_service() -> EmailService:
    """EmailService 싱글톤"""
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service
