"""기존 사용자 비밀번호 마이그레이션

기존 simple 인증 사용자에게 기본 비밀번호(dnflskfk)를 설정합니다.
password_hash 컬럼이 없으면 ALTER TABLE로 추가합니다.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import bcrypt
from sqlalchemy import text
from app.database.connection import SessionLocal


DEFAULT_PASSWORD = "dnflskfk"

# 특정 사용자별 비밀번호 설정
SPECIAL_PASSWORDS = {
    "홍길동": "123456",
    "김철수": "123456",
}


def migrate():
    db = SessionLocal()
    try:
        # 1. password_hash 컬럼 추가 (없으면)
        db.execute(text("""
            ALTER TABLE users ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255)
        """))
        db.commit()
        print("[OK] password_hash 컬럼 확인/추가 완료")

        # 2. 특정 사용자 비밀번호 개별 설정
        for name, password in SPECIAL_PASSWORDS.items():
            pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
            result = db.execute(text("""
                UPDATE users SET password_hash = :password_hash
                WHERE name = :name
            """), {"password_hash": pw_hash, "name": name})
            if result.rowcount > 0:
                print(f"[OK] '{name}' 비밀번호 설정 완료")
            else:
                print(f"[SKIP] '{name}' 사용자를 찾을 수 없음")
        db.commit()

        # 3. 나머지 사용자에게 기본 비밀번호 설정
        password_hash = bcrypt.hashpw(
            DEFAULT_PASSWORD.encode(), bcrypt.gensalt()
        ).decode()

        result = db.execute(text("""
            UPDATE users
            SET password_hash = :password_hash
            WHERE password_hash IS NULL
        """), {"password_hash": password_hash})
        db.commit()

        updated = result.rowcount
        print(f"[OK] 나머지 {updated}명 사용자에게 기본 비밀번호 설정 완료")

        # 4. 이메일 없는 사용자 확인
        rows = db.execute(text("""
            SELECT id, name, phone, email FROM users WHERE email IS NULL
        """)).fetchall()

        if rows:
            print(f"\n[WARN] 이메일 미설정 사용자 {len(rows)}명:")
            for row in rows:
                print(f"  - id={row[0]} name={row[1]} phone={row[2]}")
            print("  → 이 사용자들은 이메일 설정 후 로그인 가능합니다.")

        print("\n마이그레이션 완료!")

    except Exception as e:
        db.rollback()
        print(f"[ERROR] 마이그레이션 실패: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    migrate()
