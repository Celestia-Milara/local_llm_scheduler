import uvicorn
import logging
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from contextlib import asynccontextmanager
from dotenv import load_dotenv

from app.db.database import init_db
from app.core.agent_engine import run_chat

# 加载环境变量
load_dotenv()

# 从环境变量获取日志级别
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

# 配置日志
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 全局内存 Session 存储
sessions: Dict[str, List[Dict[str, str]]] = {}

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = "default_user"

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 确保 data 目录存在
    import os
    if not os.path.exists("data"):
        os.makedirs("data")
    
    # Startup: 初始化数据库
    logger.info("Initializing database...")
    await init_db()
    yield
    # Shutdown
    logger.info("Shutting down...")

app = FastAPI(title="Privacy Schedule Agent API", lifespan=lifespan)

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """
    主要对话接口
    """
    session_id = request.session_id
    user_input = request.message

    # 获取或初始化历史记录
    if session_id not in sessions:
        sessions[session_id] = []
    
    history = sessions[session_id]

    try:
        # 调用 Agent 引擎
        response_text = await run_chat(user_input, history)
        
        # 更新历史记录
        history.append({"role": "user", "content": user_input})
        history.append({"role": "assistant", "content": response_text})
        
        # 限制历史记录长度
        if len(history) > 20:
            sessions[session_id] = history[-20:]
            
        return {
            "status": "success",
            "response": response_text,
            "session_id": session_id
        }
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

from sqlalchemy import select
from fastapi.staticfiles import StaticFiles
from app.db.models import Schedule
from app.db.database import AsyncSessionLocal, init_db

# ... (之前的内容保持不变)

@app.get("/schedules")
async def get_schedules():
    """
    获取所有日程列表
    """
    async with AsyncSessionLocal() as session:
        stmt = select(Schedule).order_by(Schedule.start_time.asc())
        result = await session.execute(stmt)
        schedules = result.scalars().all()
        return [
            {
                "id": s.id,
                "title": s.title,
                "start_time": s.start_time.strftime("%Y-%m-%d %H:%M:%S"),
                "end_time": s.end_time.strftime("%Y-%m-%d %H:%M:%S"),
                "location": s.location_ref,
                "status": s.status
            }
            for s in schedules
        ]

# 挂载前端静态文件 (假设前端代码在 frontend 目录下)
if os.path.exists("frontend"):
    app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
