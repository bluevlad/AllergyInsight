"""주가/지수 일별 시세 수집기 (pykrx + FinanceDataReader 멀티소스)

대상 종목 (pykrx 우선):
  - 수젠텍       : KOSDAQ 253840
  - 녹십자엠에스 : KOSDAQ 142280
  - 바디텍메드   : KOSDAQ 206640

벤치마크 지수 (FinanceDataReader 우선 — pykrx KRX 메타 차단 환경 우회):
  - KOSDAQ 종합지수 : FDR 'KQ11' → ticker 라벨 'KOSDAQ'

각 종목/지수는 primary_source 로 우선 시도하고, 실패 시 fallback 소스로 재시도.
실제 사용된 소스는 daily_prices.source 컬럼에 기록 ('pykrx' | 'fdr').

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
    fdr_symbol: str | None = None    # FinanceDataReader 심볼 (보조/우선 소스)
    primary_source: str = "pykrx"    # 'pykrx' | 'fdr' — 우선 시도할 소스


TRACKED_TICKERS: list[TrackedTicker] = [
    TrackedTicker(code="253840", label="253840", market="KOSDAQ", company_code="sugentech",
                  fdr_symbol="253840"),
    TrackedTicker(code="142280", label="142280", market="KOSDAQ", company_code="greencross",
                  fdr_symbol="142280"),
    TrackedTicker(code="206640", label="206640", market="KOSDAQ", company_code="bodytech",
                  fdr_symbol="206640"),
    # KOSDAQ 종합지수: pykrx KRX 메타 fetch 차단 환경 → FinanceDataReader 우선
    TrackedTicker(code="2001", label="KOSDAQ", market="INDEX", is_index=True,
                  fdr_symbol="KQ11", primary_source="fdr"),
]


COMPANY_TICKER_MAP = {t.company_code: t.label for t in TRACKED_TICKERS if t.company_code}


# ---------------------------------------------------------------------------
# 백필 / 갱신
# ---------------------------------------------------------------------------


def _yyyymmdd(d: date) -> str:
    return d.strftime("%Y%m%d")


def _fetch_pykrx(ticker: TrackedTicker, start: date, end: date):
    """pykrx에서 OHLCV — 한국어 컬럼(시가/고가/저가/종가/거래량) 반환"""
    from pykrx import stock  # lazy import

    if ticker.is_index:
        df = stock.get_index_ohlcv(_yyyymmdd(start), _yyyymmdd(end), ticker.code)
    else:
        df = stock.get_market_ohlcv(_yyyymmdd(start), _yyyymmdd(end), ticker.code)
    return df


def _fetch_pykrx_market_cap(ticker: TrackedTicker, start: date, end: date):
    """pykrx 일별 시가총액 — 종목 전용 (지수는 N/A).

    Returns: dict {date: market_cap_int}, 실패 시 빈 dict.
    """
    if ticker.is_index:
        return {}
    try:
        from pykrx import stock
        df = stock.get_market_cap_by_date(_yyyymmdd(start), _yyyymmdd(end), ticker.code)
        if df is None or df.empty:
            return {}
        # pykrx 컬럼: 시가총액 / 거래량 / 거래대금 / 상장주식수
        out: dict = {}
        for ts, row in df.iterrows():
            d = ts.date() if hasattr(ts, "date") else ts
            cap = _safe_int(row.get("시가총액"))
            if cap is not None:
                out[d] = cap
        return out
    except Exception as e:
        logger.warning("market_cap fetch failed for %s: %s", ticker.label, e)
        return {}


def _fetch_fdr(symbol: str, start: date, end: date):
    """FinanceDataReader에서 OHLCV — 영문 컬럼(Open/High/Low/Close/Volume) 반환"""
    import FinanceDataReader as fdr  # lazy import
    return fdr.DataReader(symbol, start, end)


def _normalize_ohlcv_row(row, source: str) -> dict:
    """소스별 컬럼명 차이를 흡수하여 OHLCV 표준 dict 반환"""
    if source == "pykrx":
        return {
            "open_price": _safe_num(row.get("시가")),
            "high_price": _safe_num(row.get("고가")),
            "low_price": _safe_num(row.get("저가")),
            "close_price": _safe_num(row.get("종가")),
            "volume": _safe_int(row.get("거래량")),
        }
    if source == "fdr":
        return {
            "open_price": _safe_num(row.get("Open")),
            "high_price": _safe_num(row.get("High")),
            "low_price": _safe_num(row.get("Low")),
            "close_price": _safe_num(row.get("Close")),
            "volume": _safe_int(row.get("Volume")),
        }
    raise ValueError(f"unknown source: {source}")


def fetch_ticker_ohlcv(ticker: TrackedTicker, start: date, end: date) -> tuple:
    """primary_source 우선, 실패 시 fallback 소스로 재시도.

    Returns: (DataFrame, used_source) — 모두 실패 시 (None, None)
    """
    # 시도 순서 결정: primary 우선, fdr_symbol 있으면 fallback 추가
    order: list[str] = [ticker.primary_source]
    if ticker.primary_source == "pykrx" and ticker.fdr_symbol:
        order.append("fdr")
    elif ticker.primary_source == "fdr":
        order.append("pykrx")

    last_error: Exception | None = None
    for source in order:
        try:
            if source == "pykrx":
                df = _fetch_pykrx(ticker, start, end)
            elif source == "fdr":
                if not ticker.fdr_symbol:
                    continue
                df = _fetch_fdr(ticker.fdr_symbol, start, end)
            else:
                continue
            if df is None or df.empty:
                logger.info("source %s returned empty for %s", source, ticker.label)
                continue
            return df, source
        except Exception as e:
            last_error = e
            logger.warning("source %s failed for %s: %s", source, ticker.label, e)

    if last_error:
        logger.error("all sources failed for %s: %s", ticker.label, last_error)
    return None, None


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
    """단일 종목/지수 수집 → daily_prices 적재 (멀티소스 fallback 적용)

    Returns: upsert된 행 수
    """
    df, used_source = fetch_ticker_ohlcv(ticker, start, end)
    if df is None or df.empty or used_source is None:
        logger.warning("all sources returned empty for %s (%s ~ %s)", ticker.label, start, end)
        return 0

    # 시가총액 보조 fetch — pykrx 사용 시 종목만 (지수 N/A)
    cap_by_date: dict = {}
    if used_source == "pykrx" and not ticker.is_index:
        cap_by_date = _fetch_pykrx_market_cap(ticker, start, end)

    rows = []
    for ts, row in df.iterrows():
        # pandas Timestamp → date 변환 (pykrx/fdr 모두 동일)
        trade_date = ts.date() if hasattr(ts, "date") else ts
        ohlcv = _normalize_ohlcv_row(row, used_source)
        if ohlcv["close_price"] is None:
            continue  # 종가 결측 row skip
        rows.append(
            {
                "ticker": ticker.label,
                "market": ticker.market,
                "trade_date": trade_date,
                **ohlcv,
                "market_cap": cap_by_date.get(trade_date),
                "source": used_source,
                "collected_at": datetime.utcnow(),
            }
        )

    n = upsert_daily_prices(db, rows)
    logger.info("collected %d rows for %s (source=%s, %s ~ %s)",
                n, ticker.label, used_source, start, end)
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


def trailing_volume_zscore(
    db: Session,
    ticker: str,
    anchor_date: date,
    *,
    lookback_days: int = 60,
    min_n: int = 20,
) -> float | None:
    """anchor_date 거래량의 직전 lookback_days 영업일 분포 대비 z-score.

    표본 < min_n 또는 표준편차 0 이면 None.
    """
    import statistics

    past = (
        db.query(DailyPrice.volume)
        .filter(
            DailyPrice.ticker == ticker,
            DailyPrice.trade_date < anchor_date,
            DailyPrice.volume.isnot(None),
        )
        .order_by(DailyPrice.trade_date.desc())
        .limit(lookback_days)
        .all()
    )
    if len(past) < min_n:
        return None
    volumes = [float(r[0]) for r in past]
    mu = statistics.mean(volumes)
    try:
        sigma = statistics.stdev(volumes)
    except statistics.StatisticsError:
        return None
    if sigma == 0:
        return None
    anchor_row = (
        db.query(DailyPrice.volume)
        .filter(DailyPrice.ticker == ticker, DailyPrice.trade_date == anchor_date)
        .first()
    )
    if not anchor_row or anchor_row[0] is None:
        return None
    return (float(anchor_row[0]) - mu) / sigma


def market_cap_change_ratio(
    db: Session, ticker: str, anchor_date: date, target_date: date
) -> float | None:
    """anchor → target 시가총액 변화율 ((target - anchor) / anchor).

    둘 중 하나라도 cap=NULL 또는 anchor=0 시 None.
    """
    rows = (
        db.query(DailyPrice.trade_date, DailyPrice.market_cap)
        .filter(
            DailyPrice.ticker == ticker,
            DailyPrice.trade_date.in_([anchor_date, target_date]),
            DailyPrice.market_cap.isnot(None),
        )
        .all()
    )
    by_date = {r[0]: float(r[1]) for r in rows}
    cap_anchor = by_date.get(anchor_date)
    cap_target = by_date.get(target_date)
    if cap_anchor is None or cap_target is None or cap_anchor == 0:
        return None
    return (cap_target - cap_anchor) / cap_anchor


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
