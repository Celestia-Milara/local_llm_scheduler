from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
import os
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# 获取数据库 URL
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./data/schedule.db")

# 创建异步引擎
# 注意: check_same_thread=False 仅适用于 SQLite，切换数据库时需移除
engine = create_async_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

# 创建异步会话工厂
AsyncSessionLocal = async_sessionmaker(
    bind=engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

# 声明基类
class Base(DeclarativeBase):
    pass

async def _migrate_schedule_columns(conn):
    """v2.0/v3.0 迁移：为已有 schedules 表补充新字段"""
    from sqlalchemy import inspect as sa_inspect

    def _do_inspect(sync_conn):
        insp = sa_inspect(sync_conn)
        return [col['name'] for col in insp.get_columns('schedules')]

    existing_columns = await conn.run_sync(_do_inspect)

    new_columns = {
        'description': 'TEXT',
        'category': 'VARCHAR(30)',
    }
    for col_name, col_type in new_columns.items():
        if col_name not in existing_columns:
            await conn.execute(
                text(f"ALTER TABLE schedules ADD COLUMN {col_name} {col_type}")
            )
            logger.info(f"Migration: added column '{col_name}' to schedules table")

    # v3.0: user_id
    if 'user_id' not in existing_columns:
        await conn.execute(
            text("ALTER TABLE schedules ADD COLUMN user_id INTEGER DEFAULT 1")
        )
        logger.info("Migration: added column 'user_id' to schedules table")

    # v3.0+: recurrence_rule
    if 'recurrence_rule' not in existing_columns:
        await conn.execute(
            text("ALTER TABLE schedules ADD COLUMN recurrence_rule VARCHAR(20)")
        )
        await conn.execute(
            text("ALTER TABLE schedules ADD COLUMN recurrence_end DATETIME")
        )
        logger.info("Migration: added recurrence columns to schedules table")

    # Phase 3: is_archived
    if 'is_archived' not in existing_columns:
        await conn.execute(
            text("ALTER TABLE schedules ADD COLUMN is_archived INTEGER DEFAULT 0")
        )
        logger.info("Migration: added column 'is_archived' to schedules table")


# 数据库初始化函数
async def init_db():
    async with engine.begin() as conn:
        from app.db.models import Schedule, Summary, ChatSession, ChatMessage, User  # 确保模型被加载
        await conn.run_sync(Base.metadata.create_all)
        await _migrate_schedule_columns(conn)