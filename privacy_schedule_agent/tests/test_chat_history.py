"""Phase 2 测试：对话持久化 ORM 层"""

import importlib
import os
import sys
import tempfile
from pathlib import Path

import pytest


@pytest.fixture(scope="module")
def chat_db():
    """用独立的临时 DB + 干净 import 隔离测试"""
    tmp_dir = tempfile.TemporaryDirectory()
    db_file = Path(tmp_dir.name) / "test_chat.db"
    os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{db_file}"

    # 清除已缓存的 app 模块，确保用新的 DATABASE_URL
    for mod in list(sys.modules.keys()):
        if mod.startswith("app.") or mod == "app":
            del sys.modules[mod]

    from app.db.database import init_db, AsyncSessionLocal
    from app.db.models import ChatSession, ChatMessage
    from sqlalchemy import select
    import asyncio

    # 初始化表结构
    asyncio.run(init_db())

    yield {
        "AsyncSessionLocal": AsyncSessionLocal,
        "ChatSession": ChatSession,
        "ChatMessage": ChatMessage,
        "select": select,
    }

    # 清理
    asyncio.run(AsyncSessionLocal().close())
    from app.db.database import engine
    asyncio.run(engine.dispose())
    tmp_dir.cleanup()


@pytest.mark.asyncio
async def test_create_chat_session(chat_db):
    """应能创建 ChatSession 并持久化"""
    Session = chat_db["AsyncSessionLocal"]
    ChatSession = chat_db["ChatSession"]
    select = chat_db["select"]

    async with Session() as session:
        cs = ChatSession(id="test-session-1", user_id=1)
        session.add(cs)
        await session.commit()

    async with Session() as session:
        result = await session.execute(
            select(ChatSession).where(ChatSession.id == "test-session-1")
        )
        loaded = result.scalar_one_or_none()
        assert loaded is not None
        assert loaded.user_id == 1


@pytest.mark.asyncio
async def test_add_chat_messages(chat_db):
    """应能添加 ChatMessage 并关联到 Session"""
    Session = chat_db["AsyncSessionLocal"]
    ChatSession = chat_db["ChatSession"]
    ChatMessage = chat_db["ChatMessage"]
    select = chat_db["select"]

    async with Session() as session:
        session.add(ChatSession(id="session-msg-test", user_id=1))
        await session.commit()

    async with Session() as session:
        session.add(ChatMessage(session_id="session-msg-test", role="user", content="你好"))
        session.add(ChatMessage(session_id="session-msg-test", role="assistant", content="你好！有什么可以帮助你的吗？"))
        await session.commit()

    async with Session() as session:
        result = await session.execute(
            select(ChatMessage)
            .where(ChatMessage.session_id == "session-msg-test")
            .order_by(ChatMessage.created_at)
        )
        msgs = result.scalars().all()
        assert len(msgs) == 2
        assert msgs[0].role == "user"
        assert msgs[0].content == "你好"
        assert msgs[1].role == "assistant"


@pytest.mark.asyncio
async def test_chat_session_timestamps(chat_db):
    """ChatSession 应自动设置 created_at 和 updated_at"""
    Session = chat_db["AsyncSessionLocal"]
    ChatSession = chat_db["ChatSession"]
    select = chat_db["select"]

    async with Session() as session:
        session.add(ChatSession(id="timestamps-test", user_id=1))
        await session.commit()

    async with Session() as session:
        result = await session.execute(
            select(ChatSession).where(ChatSession.id == "timestamps-test")
        )
        loaded = result.scalar_one()
        assert loaded.created_at is not None
        assert loaded.updated_at is not None
