import uvicorn
import logging
import os
from datetime import datetime
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
from contextlib import asynccontextmanager
from dotenv import load_dotenv

from sqlalchemy import select
from fastapi.staticfiles import StaticFiles

from app.db.database import init_db, AsyncSessionLocal
from app.db.models import Schedule
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
    user_id: Optional[int] = 1


class ScheduleUpdateRequest(BaseModel):
    title: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None


class ScheduleCreateRequest(BaseModel):
    title: str
    start_time: str
    end_time: str
    location: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    user_id: Optional[int] = 1


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 确保 data 目录存在
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
    """主要对话接口"""
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


@app.get("/schedules")
async def get_schedules(start: str = None, end: str = None, user_id: int = None):
    """获取日程列表，支持按时间范围过滤"""
    async with AsyncSessionLocal() as session:
        stmt = select(Schedule).order_by(Schedule.start_time.asc())
        if user_id is not None:
            stmt = stmt.where(Schedule.user_id == user_id)
        if start:
            try:
                dt_start = datetime.strptime(start, "%Y-%m-%d %H:%M:%S")
                stmt = stmt.where(Schedule.start_time >= dt_start)
            except ValueError:
                try:
                    dt_start = datetime.strptime(start, "%Y-%m-%d")
                    stmt = stmt.where(Schedule.start_time >= dt_start)
                except ValueError:
                    raise HTTPException(status_code=400, detail="start 格式应为 YYYY-MM-DD 或 YYYY-MM-DD HH:MM:SS")
        if end:
            try:
                dt_end = datetime.strptime(end, "%Y-%m-%d %H:%M:%S")
                stmt = stmt.where(Schedule.end_time <= dt_end)
            except ValueError:
                try:
                    dt_end = datetime.strptime(end, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
                    stmt = stmt.where(Schedule.end_time <= dt_end)
                except ValueError:
                    raise HTTPException(status_code=400, detail="end 格式应为 YYYY-MM-DD 或 YYYY-MM-DD HH:MM:SS")

        result = await session.execute(stmt)
        schedules = result.scalars().all()
        return [
            {
                "id": s.id,
                "title": s.title,
                "start_time": s.start_time.strftime("%Y-%m-%d %H:%M:%S"),
                "end_time": s.end_time.strftime("%Y-%m-%d %H:%M:%S"),
                "location": s.location_ref,
                "description": s.description,
                "category": s.category,
                "status": s.status,
                "user_id": s.user_id
            }
            for s in schedules
        ]


@app.get("/schedules/{event_id}")
async def get_schedule(event_id: int):
    """获取单个日程"""
    async with AsyncSessionLocal() as session:
        stmt = select(Schedule).where(Schedule.id == event_id)
        result = await session.execute(stmt)
        s = result.scalar_one_or_none()
        if not s:
            raise HTTPException(status_code=404, detail=f"未找到ID为 {event_id} 的日程")
        return {
            "id": s.id,
            "title": s.title,
            "start_time": s.start_time.strftime("%Y-%m-%d %H:%M:%S"),
            "end_time": s.end_time.strftime("%Y-%m-%d %H:%M:%S"),
            "location": s.location_ref,
            "description": s.description,
            "category": s.category,
            "status": s.status
        }


@app.put("/schedules/{event_id}")
async def update_schedule(event_id: int, req: ScheduleUpdateRequest):
    """更新日程（供前端直接调用）"""
    async with AsyncSessionLocal() as session:
        stmt = select(Schedule).where(Schedule.id == event_id)
        result = await session.execute(stmt)
        event = result.scalar_one_or_none()
        if not event:
            raise HTTPException(status_code=404, detail=f"未找到ID为 {event_id} 的日程")

        try:
            time_changed = False
            if req.title is not None:
                event.title = req.title
            if req.start_time is not None:
                event.start_time = datetime.strptime(req.start_time, "%Y-%m-%d %H:%M:%S")
                time_changed = True
            if req.end_time is not None:
                event.end_time = datetime.strptime(req.end_time, "%Y-%m-%d %H:%M:%S")
                time_changed = True
            if req.location is not None:
                event.location_ref = req.location
                time_changed = True
            if req.description is not None:
                event.description = req.description
            if req.category is not None:
                event.category = req.category

            await session.commit()

            return {
                "id": event.id,
                "title": event.title,
                "start_time": event.start_time.strftime("%Y-%m-%d %H:%M:%S"),
                "end_time": event.end_time.strftime("%Y-%m-%d %H:%M:%S"),
                "location": event.location_ref,
                "description": event.description,
                "category": event.category,
                "status": event.status
            }
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"时间格式不正确: {str(e)}")


@app.post("/schedules")
async def create_schedule(req: ScheduleCreateRequest):
    """创建日程（直接创建，不经过 LLM）"""
    async with AsyncSessionLocal() as session:
        try:
            event = Schedule(
                user_id=req.user_id or 1,
                title=req.title,
                start_time=datetime.strptime(req.start_time, "%Y-%m-%d %H:%M:%S"),
                end_time=datetime.strptime(req.end_time, "%Y-%m-%d %H:%M:%S"),
                location_ref=req.location or None,
                description=req.description or None,
                category=req.category or None,
                status="confirmed"
            )
            session.add(event)
            await session.commit()
            await session.refresh(event)
            return {
                "id": event.id,
                "title": event.title,
                "start_time": event.start_time.strftime("%Y-%m-%d %H:%M:%S"),
                "end_time": event.end_time.strftime("%Y-%m-%d %H:%M:%S"),
                "status": event.status
            }
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"时间格式不正确: {str(e)}")


@app.delete("/schedules/{event_id}")
async def delete_schedule(event_id: int):
    """删除日程（供前端直接调用）"""
    async with AsyncSessionLocal() as session:
        stmt = select(Schedule).where(Schedule.id == event_id)
        result = await session.execute(stmt)
        event = result.scalar_one_or_none()
        if not event:
            raise HTTPException(status_code=404, detail=f"未找到ID为 {event_id} 的日程")

        await session.delete(event)
        await session.commit()
        return {"status": "success", "message": f"已删除日程: {event.title}"}


# 挂载前端静态文件（优先使用 Vite 构建产物）
dist_path = "frontend/dist"
if os.path.exists(dist_path):
    app.mount("/", StaticFiles(directory=dist_path, html=True), name="frontend")
elif os.path.exists("frontend"):
    app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
