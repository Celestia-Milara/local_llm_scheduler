from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column
from .database import Base

class Schedule(Base):
    """日程明细表"""
    __tablename__ = "schedules"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    start_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    location_ref: Mapped[Optional[str]] = mapped_column(String(100))
    
    # 核心状态：confirmed(已确认), conflicted(带冲突保存)
    status: Mapped[str] = mapped_column(String(20), default="confirmed")
    
    # 隐私等级：1-公开, 2-内部, 3-绝密
    privacy_level: Mapped[int] = mapped_column(Integer, default=1)
    
    # 归档关联：指向总结表
    summary_id: Mapped[Optional[int]] = mapped_column(ForeignKey("summaries.id"))

class Summary(Base):
    """数据归档摘要表"""
    __tablename__ = "summaries"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    time_range: Mapped[str] = mapped_column(String(50)) # 例如 "2026-W16"
    content: Mapped[str] = mapped_column(Text) # LLM 生成的总结内容
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)