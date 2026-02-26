"""HealthPulse SQLite → AllergyInsight PostgreSQL 구독자 마이그레이션 스크립트

사용법:
    python scripts/migrate_healthpulse_data.py --db-path /path/to/healthpulse.db

주의:
    - AllergyInsight의 DATABASE_URL 환경변수가 설정되어 있어야 합니다
    - 중복 이메일은 건너뜁니다
"""
import argparse
import sqlite3
import secrets
import sys
import os
from datetime import datetime

# 프로젝트 루트를 path에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.database.connection import SessionLocal
from app.database.subscriber_models import NewsletterSubscriber


def migrate(db_path: str, dry_run: bool = False):
    """HealthPulse SQLite DB에서 구독자 데이터를 마이그레이션"""

    if not os.path.exists(db_path):
        print(f"파일을 찾을 수 없습니다: {db_path}")
        return

    # HealthPulse SQLite 연결
    sqlite_conn = sqlite3.connect(db_path)
    sqlite_conn.row_factory = sqlite3.Row
    cursor = sqlite_conn.cursor()

    # 구독자 테이블 조회 (HealthPulse 스키마에 맞게 조정 필요)
    try:
        cursor.execute("SELECT * FROM subscribers WHERE is_active = 1")
        rows = cursor.fetchall()
    except sqlite3.OperationalError as e:
        print(f"테이블 조회 실패: {e}")
        print("HealthPulse DB 스키마를 확인하세요.")
        sqlite_conn.close()
        return

    print(f"HealthPulse 구독자: {len(rows)}명")

    if dry_run:
        for row in rows:
            print(f"  - {dict(row)}")
        print(f"\n[DRY RUN] {len(rows)}명의 구독자가 마이그레이션 대상입니다.")
        sqlite_conn.close()
        return

    # AllergyInsight DB 세션
    db = SessionLocal()
    migrated = 0
    skipped = 0

    try:
        for row in rows:
            row_dict = dict(row)
            email = row_dict.get("email", "")

            if not email:
                skipped += 1
                continue

            # 이미 존재하는지 확인
            existing = db.query(NewsletterSubscriber).filter(
                NewsletterSubscriber.email == email
            ).first()

            if existing:
                print(f"  건너뜀 (이미 존재): {email}")
                skipped += 1
                continue

            subscriber = NewsletterSubscriber(
                email=email,
                name=row_dict.get("name"),
                subscription_key=secrets.token_hex(32),
                is_verified=True,  # HealthPulse에서 이미 활성인 구독자
                keywords=row_dict.get("keywords", "").split(",") if row_dict.get("keywords") else [],
                group_name="healthpulse_migrated",
                is_active=True,
                subscribed_at=datetime.utcnow(),
                verified_at=datetime.utcnow(),
            )
            db.add(subscriber)
            migrated += 1
            print(f"  마이그레이션: {email}")

        db.commit()
        print(f"\n완료: {migrated}명 마이그레이션, {skipped}명 건너뜀")

    except Exception as e:
        db.rollback()
        print(f"마이그레이션 실패: {e}")
    finally:
        db.close()
        sqlite_conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="HealthPulse → AllergyInsight 구독자 마이그레이션")
    parser.add_argument("--db-path", required=True, help="HealthPulse SQLite DB 파일 경로")
    parser.add_argument("--dry-run", action="store_true", help="실제 마이그레이션 없이 대상 확인만")
    args = parser.parse_args()

    migrate(args.db_path, dry_run=args.dry_run)
