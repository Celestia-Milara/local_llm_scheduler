from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

# 获取数据库 URL
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./data/schedule.db")

# 创建异步引擎
engine = create_async_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False}
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

# 数据库初始化函数
async def init_db():
    async with engine.begin() as conn:
        # 注意：这里调用的是 run_sync 来执行同步方法 create_all
        from app.db.models import Schedule, Summary # 确保模型被加载
        await conn.run_sync(Base.metadata.create_all)