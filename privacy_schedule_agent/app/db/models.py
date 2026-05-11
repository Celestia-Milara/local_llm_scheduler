from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, DateTime, ForeignKey, Text, func, JSON
from sqlalchemy.orm import Mapped, mapped_column
from .database import Base

class Schedule(Base):
    """日程明细表"""
    __tablename__ = "schedules"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, default=1, index=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    start_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    location_ref: Mapped[Optional[str]] = mapped_column(String(100))

    description: Mapped[Optional[str]] = mapped_column(Text)
    category: Mapped[Optional[str]] = mapped_column(String(30))

    # 核心状态：confirmed(已确认), conflicted(带冲突保存)
    status: Mapped[str] = mapped_column(String(20), default="confirmed")

    # 隐私等级：1-公开, 2-内部, 3-绝密
    privacy_level: Mapped[int] = mapped_column(Integer, default=1)

    # 重复规则：daily / weekly / monthly / weekdays
    recurrence_rule: Mapped[Optional[str]] = mapped_column(String(20))
    # 重复结束日期（可选，不设则永久重复）
    recurrence_end: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # 归档标记：False=活跃, True=已归档
    is_archived: Mapped[bool] = mapped_column(Integer, default=0)

    # 归档关联：指向总结表
    summary_id: Mapped[Optional[int]] = mapped_column(ForeignKey("summaries.id"))

class Summary(Base):
    """数据归档摘要表"""
    __tablename__ = "summaries"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    time_range: Mapped[str] = mapped_column(String(50)) # 例如 "2026-W16"
    content: Mapped[str] = mapped_column(Text) # LLM 生成的总结内容
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class ChatSession(Base):
    """AI 对话会话表"""
    __tablename__ = "chat_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)  # UUID
    user_id: Mapped[int] = mapped_column(Integer, default=1, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class ChatMessage(Base):
    """AI 对话消息表"""
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String(36), ForeignKey("chat_sessions.id"), index=True)
    role: Mapped[str] = mapped_column(String(20))  # user / assistant / tool
    content: Mapped[Optional[str]] = mapped_column(Text)
    tool_calls: Mapped[Optional[dict]] = mapped_column(JSON)  # tool_call 元数据
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class User(Base):
    """用户表（cloud 模式多用户认证用）"""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(256), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())