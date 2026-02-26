"""구독 관리 서비스

구독 신청, 인증, 해지 등의 구독 흐름을 관리합니다.
"""
import os
import secrets
import random
import string
import logging
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from .email_service import get_email_service
from .report_generator import NewsReportGenerator
from ..database.subscriber_models import NewsletterSubscriber, EmailVerification

logger = logging.getLogger(__name__)


class SubscriptionService:
    """구독 관리 서비스"""

    def __init__(self):
        self.email_service = get_email_service()
        self.report_generator = NewsReportGenerator()
        self.verification_expire_minutes = 30

    def subscribe(self, db: Session, email: str, name: Optional[str] = None,
                  keywords: Optional[list[str]] = None) -> dict:
        """구독 신청

        이미 구독 중인 경우 인증 코드를 재발송합니다.

        Returns:
            {"status": "created"|"exists"|"reactivated", "message": str}
        """
        existing = db.query(NewsletterSubscriber).filter(
            NewsletterSubscriber.email == email
        ).first()

        if existing:
            if existing.is_verified and existing.is_active:
                return {
                    "status": "exists",
                    "message": "이미 활성 구독 중입니다.",
                }
            elif not existing.is_active:
                # 재활성화
                existing.is_active = True
                existing.unsubscribed_at = None
                if name:
                    existing.name = name
                if keywords:
                    existing.keywords = keywords
                db.commit()

                self._send_verification(db, email)
                return {
                    "status": "reactivated",
                    "message": "구독이 재활성화되었습니다. 인증 이메일을 확인하세요.",
                }
            else:
                # 미인증 상태 → 인증 코드 재발송
                self._send_verification(db, email)
                return {
                    "status": "exists",
                    "message": "인증 이메일이 재발송되었습니다.",
                }

        # 새 구독자 생성
        subscription_key = secrets.token_hex(32)
        subscriber = NewsletterSubscriber(
            email=email,
            name=name,
            subscription_key=subscription_key,
            keywords=keywords or [],
            is_verified=False,
            is_active=True,
        )
        db.add(subscriber)
        db.commit()

        # 인증 코드 발송
        self._send_verification(db, email)

        return {
            "status": "created",
            "message": "구독 신청이 완료되었습니다. 인증 이메일을 확인하세요.",
        }

    def _send_verification(self, db: Session, email: str):
        """인증 코드 생성 및 발송"""
        # 기존 미사용 코드 만료 처리
        db.query(EmailVerification).filter(
            EmailVerification.email == email,
            EmailVerification.is_used == False,
        ).update({"is_used": True})

        # 새 코드 생성
        code = "".join(random.choices(string.digits, k=6))
        verification = EmailVerification(
            email=email,
            code=code,
            expires_at=datetime.utcnow() + timedelta(minutes=self.verification_expire_minutes),
        )
        db.add(verification)
        db.commit()

        # 이메일 발송
        html = self.report_generator.generate_subscription_key_email(
            verification_code=code,
            expires_minutes=self.verification_expire_minutes,
        )
        self.email_service.send(
            to=email,
            subject="[AllergyInsight] 구독 인증 코드",
            html_body=html,
        )
        logger.info(f"인증 코드 발송: {email}")

    def send_verification_email(self, db: Session, email: str) -> dict:
        """인증 코드 재발송"""
        subscriber = db.query(NewsletterSubscriber).filter(
            NewsletterSubscriber.email == email
        ).first()

        if not subscriber:
            return {"success": False, "message": "구독 신청 내역이 없습니다."}

        if subscriber.is_verified:
            return {"success": False, "message": "이미 인증된 이메일입니다."}

        self._send_verification(db, email)
        return {"success": True, "message": "인증 코드가 재발송되었습니다."}

    def verify(self, db: Session, email: str, code: str) -> dict:
        """인증 코드 확인"""
        verification = db.query(EmailVerification).filter(
            EmailVerification.email == email,
            EmailVerification.code == code,
            EmailVerification.is_used == False,
        ).first()

        if not verification:
            return {"success": False, "message": "유효하지 않은 인증 코드입니다."}

        if verification.expires_at < datetime.utcnow():
            return {"success": False, "message": "인증 코드가 만료되었습니다."}

        if verification.attempts >= verification.max_attempts:
            return {"success": False, "message": "인증 시도 횟수를 초과했습니다."}

        verification.attempts += 1

        # 코드 검증 성공
        verification.is_used = True

        subscriber = db.query(NewsletterSubscriber).filter(
            NewsletterSubscriber.email == email
        ).first()

        if subscriber:
            subscriber.is_verified = True
            subscriber.verified_at = datetime.utcnow()

        db.commit()

        return {
            "success": True,
            "message": "인증이 완료되었습니다.",
            "subscription_key": subscriber.subscription_key if subscriber else None,
        }

    def unsubscribe(self, db: Session, email: str, subscription_key: str) -> dict:
        """구독 해지"""
        subscriber = db.query(NewsletterSubscriber).filter(
            NewsletterSubscriber.email == email,
            NewsletterSubscriber.subscription_key == subscription_key,
        ).first()

        if not subscriber:
            return {"success": False, "message": "구독 정보를 찾을 수 없습니다."}

        if not subscriber.is_active:
            return {"success": False, "message": "이미 해지된 구독입니다."}

        subscriber.is_active = False
        subscriber.unsubscribed_at = datetime.utcnow()
        db.commit()

        return {"success": True, "message": "구독이 해지되었습니다."}

    def get_verified_subscribers(self, db: Session) -> list[NewsletterSubscriber]:
        """인증된 활성 구독자 목록"""
        return db.query(NewsletterSubscriber).filter(
            NewsletterSubscriber.is_verified == True,
            NewsletterSubscriber.is_active == True,
        ).all()

    def get_all_subscribers(
        self, db: Session,
        page: int = 1,
        page_size: int = 20,
        is_verified: Optional[bool] = None,
        is_active: Optional[bool] = None,
    ) -> dict:
        """전체 구독자 목록 (Admin용)"""
        query = db.query(NewsletterSubscriber)

        if is_verified is not None:
            query = query.filter(NewsletterSubscriber.is_verified == is_verified)
        if is_active is not None:
            query = query.filter(NewsletterSubscriber.is_active == is_active)

        total = query.count()
        offset = (page - 1) * page_size
        subscribers = query.order_by(
            NewsletterSubscriber.subscribed_at.desc()
        ).offset(offset).limit(page_size).all()

        return {
            "items": [
                {
                    "id": s.id,
                    "email": s.email,
                    "name": s.name,
                    "is_verified": s.is_verified,
                    "is_active": s.is_active,
                    "keywords": s.keywords or [],
                    "group_name": s.group_name,
                    "subscribed_at": s.subscribed_at.isoformat() if s.subscribed_at else None,
                    "verified_at": s.verified_at.isoformat() if s.verified_at else None,
                }
                for s in subscribers
            ],
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    def update_keywords(self, db: Session, email: str, subscription_key: str,
                        keywords: list[str]) -> dict:
        """구독 키워드 수정"""
        subscriber = db.query(NewsletterSubscriber).filter(
            NewsletterSubscriber.email == email,
            NewsletterSubscriber.subscription_key == subscription_key,
        ).first()

        if not subscriber:
            return {"success": False, "message": "구독 정보를 찾을 수 없습니다."}

        subscriber.keywords = keywords
        db.commit()

        return {"success": True, "message": "키워드가 수정되었습니다."}

    def get_subscription_status(self, db: Session, email: str) -> dict:
        """구독 상태 조회"""
        subscriber = db.query(NewsletterSubscriber).filter(
            NewsletterSubscriber.email == email
        ).first()

        if not subscriber:
            return {"subscribed": False}

        return {
            "subscribed": True,
            "is_verified": subscriber.is_verified,
            "is_active": subscriber.is_active,
            "keywords": subscriber.keywords or [],
            "subscribed_at": subscriber.subscribed_at.isoformat() if subscriber.subscribed_at else None,
        }
