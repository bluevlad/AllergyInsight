"""스케줄러 실행 로그 모델"""
from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, Float, Text
from sqlalchemy.dialects.postgresql import JSONB

from .connection import Base


class SchedulerExecutionLog(Base):
    """스케줄러 Job 실행 이력"""
    __tablename__ = "scheduler_execution_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(String(100), nullable=False, index=True)
    status = Column(String(20), nullable=False, index=True)  # 'running', 'success', 'failed'
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Float, nullable=True)
    result_summary = Column(JSONB, nullable=True)
    error_message = Column(Text, nullable=True)
    trigger_type = Column(String(20), nullable=False, default="scheduled")  # 'scheduled', 'manual'
