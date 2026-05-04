"""주가/지수 일별 시세 수집기 (pykrx 기반)

대상 종목:
  - 수젠텍       : KOSDAQ 253840
  - 녹십자엠에스 : KOSDAQ 142280
  - 바디텍메드   : KOSDAQ 206640

벤치마크 지수 (시장 abnormal return 계산용):
  - KOSDAQ 종합지수 : 2001 → ticker 'KOSDAQ'

Strategic Intel 모듈 전용. 외부 사용자 노출 금지.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date, datetime
from typing import Iterable

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from ...database.strategic_intel_models import DailyPrice

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 추적 종목 / 지수 정의
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TrackedTicker:
    code: str            # pykrx 호출용 종목/지수 코드
    label: str           # daily_prices.ticker (저장 라벨)
    market: str          # 'KOSDAQ' | 'INDEX'
    company_code: str | None = None  # competitor_companies.code
    is_index: bool = False


TRACKED_TICKERS: list[TrackedTicker] = [
    TrackedTicker(code="253840", label="253840", market="KOSDAQ", company_code="sugentech"),
    TrackedTicker(code="142280", label="142280", market="KOSDAQ", company_code="greencross"),
    TrackedTicker(code="206640", label="206640", market="KOSDAQ", company_code="bodytech"),
    # NOTE: KOSDAQ 종합지수("2001")는 환경에서 KRX API fetch 차단되어 비활성화.
    # 벤치마크 미보유 시 검증기는 종목 자체 수익률(raw return) 기준으로 hit 판정.
    # 추후 별도 데이터 소스 (FinanceDataReader 등) 도입 시 재활성화.
]


COMPANY_TICKER_MAP = {t.company_code: t.label for t in TRACKED_TICKERS if t.company_code}


# ---------------------------------------------------------------------------
# 백필 / 갱신
# ---------------------------------------------------------------------------


def _yyyymmdd(d: date) -> str:
    return d.strftime("%Y%m%d")


def fetch_ticker_ohlcv(ticker: TrackedTicker, start: date, end: date):
    """pykrx에서 일별 OHLCV DataFrame 가져오기 (지수/종목 모두 지원)

    Returns: pandas DataFrame (index=date, columns=시가/고가/저가/종가/거래량/거래대금)
    """
    from pykrx import stock  # lazy import — 테스트 환경에서 import 비용 회피

    if ticker.is_index:
        df = stock.get_index_ohlcv(_yyyymmdd(start), _yyyymmdd(end), ticker.code)
    else:
        df = stock.get_market_ohlcv(_yyyymmdd(start), _yyyymmdd(end), ticker.code)
    return df


def upsert_daily_prices(db: Session, rows: Iterable[dict]) -> int:
    """daily_prices 테이블 upsert (PostgreSQL ON CONFLICT)

    rows: list of dicts with keys ticker, market, trade_date, ... (DailyPrice 모델 컬럼)
    """
    rows = list(rows)
    if not rows:
        return 0

    if db.bind.dialect.name == "postgresql":
        stmt = pg_insert(DailyPrice).values(rows)
        stmt = stmt.on_conflict_do_update(
            index_elements=["ticker", "trade_date"],
            set_={
                "open_price": stmt.excluded.open_price,
                "high_price": stmt.excluded.high_price,
                "low_price": stmt.excluded.low_price,
                "close_price": stmt.excluded.close_price,
                "volume": stmt.excluded.volume,
                "market_cap": stmt.excluded.market_cap,
                "source": stmt.excluded.source,
            },
        )
        db.execute(stmt)
    else:
        # SQLite 등 — fallback (테스트 환경)
        for row in rows:
            existing = (
                db.query(DailyPrice)
                .filter(
                    DailyPrice.ticker == row["ticker"],
                    DailyPrice.trade_date == row["trade_date"],
                )
                .first()
            )
            if existing:
                for k, v in row.items():
                    setattr(existing, k, v)
            else:
                db.add(DailyPrice(**row))
    db.commit()
    return len(rows)


def collect_ticker(
    db: Session,
    ticker: TrackedTicker,
    start: date,
    end: date,
) -> int:
    """단일 종목/지수 수집 → daily_prices 적재

    Returns: upsert된 행 수
    """
    df = fetch_ticker_ohlcv(ticker, start, end)
    if df is None or df.empty:
        logger.warning("pykrx returned empty for %s (%s ~ %s)", ticker.label, start, end)
        return 0

    rows = []
    for ts, row in df.iterrows():
        # pykrx index는 Timestamp — date로 변환
        trade_date = ts.date() if hasattr(ts, "date") else ts
        rows.append(
            {
                "ticker": ticker.label,
                "market": ticker.market,
                "trade_date": trade_date,
                "open_price": _safe_num(row.get("시가")),
                "high_price": _safe_num(row.get("고가")),
                "low_price": _safe_num(row.get("저가")),
                "close_price": _safe_num(row.get("종가")),
                "volume": _safe_int(row.get("거래량")),
                "market_cap": None,  # 시가총액은 별도 API 필요 — v1.1에서 추가
                "source": "pykrx",
                "collected_at": datetime.utcnow(),
            }
        )

    n = upsert_daily_prices(db, rows)
    logger.info("collected %d rows for %s (%s ~ %s)", n, ticker.label, start, end)
    return n


def collect_all(
    db: Session,
    start: date,
    end: date,
    tickers: list[TrackedTicker] | None = None,
) -> dict[str, int]:
    """모든 추적 종목 + 지수 일괄 수집"""
    targets = tickers or TRACKED_TICKERS
    result: dict[str, int] = {}
    for t in targets:
        try:
            result[t.label] = collect_ticker(db, t, start, end)
        except Exception as e:
            logger.exception("collect_ticker failed for %s: %s", t.label, e)
            result[t.label] = -1
    return result


# ---------------------------------------------------------------------------
# 조회 헬퍼 (가설 검증에서 사용)
# ---------------------------------------------------------------------------


def get_close_price(db: Session, ticker: str, trade_date: date) -> float | None:
    """특정일자 종가. 거래일 아니면 None (호출자가 다음 영업일 처리)."""
    row = (
        db.query(DailyPrice.close_price)
        .filter(DailyPrice.ticker == ticker, DailyPrice.trade_date == trade_date)
        .first()
    )
    return float(row[0]) if row and row[0] is not None else None


def next_trading_day_close(
    db: Session, ticker: str, on_or_after: date, max_lookahead_days: int = 7
) -> tuple[date, float] | None:
    """on_or_after 이후 첫 거래일의 종가 (휴장/주말 처리)

    Returns: (실제 거래일, 종가) 또는 None (조회 실패)
    """
    row = (
        db.query(DailyPrice.trade_date, DailyPrice.close_price)
        .filter(DailyPrice.ticker == ticker, DailyPrice.trade_date >= on_or_after)
        .order_by(DailyPrice.trade_date.asc())
        .first()
    )
    if not row:
        return None
    actual_date, close = row
    if (actual_date - on_or_after).days > max_lookahead_days:
        return None
    return actual_date, float(close)


def trading_day_offset_close(
    db: Session, ticker: str, anchor_date: date, offset_days: int
) -> tuple[date, float] | None:
    """anchor_date에서 offset_days만큼 *영업일* 뒤의 종가 (T+1d, T+5d 등)

    영업일 기준이므로 daily_prices에 적재된 거래일만 카운트.
    offset_days = 0 → anchor_date 당일 (또는 다음 거래일)
    offset_days = 5 → anchor 이후 5번째 거래일
    """
    rows = (
        db.query(DailyPrice.trade_date, DailyPrice.close_price)
        .filter(DailyPrice.ticker == ticker, DailyPrice.trade_date >= anchor_date)
        .order_by(DailyPrice.trade_date.asc())
        .limit(offset_days + 2)  # 여유분
        .all()
    )
    if len(rows) <= offset_days:
        return None
    target = rows[offset_days]
    return target[0], float(target[1])


# ---------------------------------------------------------------------------
# 내부 유틸
# ---------------------------------------------------------------------------


def _safe_num(v) -> float | None:
    if v is None:
        return None
    try:
        f = float(v)
        if f != f:  # NaN
            return None
        return f
    except (TypeError, ValueError):
        return None


def _safe_int(v) -> int | None:
    f = _safe_num(v)
    if f is None:
        return None
    return int(f)
