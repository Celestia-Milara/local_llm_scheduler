import json
import uuid
import hashlib
import secrets
import uvicorn
import logging
import os
from datetime import datetime
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import Response, JSONResponse, StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Optional, AsyncGenerator
from contextlib import asynccontextmanager
from dotenv import load_dotenv

from sqlalchemy import select
from fastapi.staticfiles import StaticFiles

from app.db.database import init_db, AsyncSessionLocal
from app.db.models import Schedule, ChatSession, ChatMessage, User
from app.core.agent_engine import run_chat, run_chat_stream
from app.core.crypto import encrypt_dict, decrypt_dict
from app.auth.jwt import create_token, verify_token, get_user_id_from_request
from app.auth.middleware import auth_condition_middleware
from app.skill.skills.schedule_management.scripts.conflict import check_conflict, CODE_WARN

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

# 全局内存 Session 存储（上限 100 会话，超限时淘汰最旧）
sessions: Dict[str, List[Dict[str, str]]] = {}
MAX_SESSIONS = 100


# ── 密码工具 ──────────────────────────────────────────────
def _hash_password(password: str) -> str:
    """PBKDF2 密码哈希"""
    salt = secrets.token_hex(16)
    hsh = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100000)
    return f"{salt}${hsh.hex()}"


def _verify_password(password: str, stored: str) -> bool:
    """验证密码"""
    try:
        salt, hsh = stored.split("$", 1)
        return hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100000).hex() == hsh
    except Exception:
        return False


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = "default_user"
    user_id: Optional[int] = 1


class ChatStreamRequest(BaseModel):
    message: str
    session_id: Optional[str] = None  # None = auto-create new session
    user_id: Optional[int] = 1


class AuthRegisterRequest(BaseModel):
    username: str
    password: str


class AuthLoginRequest(BaseModel):
    username: str
    password: str


class ScheduleUpdateRequest(BaseModel):
    title: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    recurrence_rule: Optional[str] = None
    recurrence_end: Optional[str] = None
    confirm_conflict: Optional[bool] = False


class ScheduleCreateRequest(BaseModel):
    title: str
    start_time: str
    end_time: str
    location: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    user_id: Optional[int] = 1
    recurrence_rule: Optional[str] = None
    recurrence_end: Optional[str] = None
    confirm_conflict: Optional[bool] = False


def _parse_conflict_result(conflict_json: str):
    try:
        parsed = json.loads(conflict_json)
    except json.JSONDecodeError:
        return None, [], "冲突检查结果异常"
    return parsed.get("status"), parsed.get("conflicts", []), parsed.get("message", "")


async def _get_or_create_session(session_id: Optional[str], user_id: int) -> str:
    """获取或创建 ChatSession，返回 session_id"""
    async with AsyncSessionLocal() as db:
        if session_id:
            stmt = select(ChatSession).where(ChatSession.id == session_id)
            result = await db.execute(stmt)
            existing = result.scalar_one_or_none()
            if existing:
                return session_id

        # 创建新会话
        new_id = session_id or str(uuid.uuid4())
        db.add(ChatSession(id=new_id, user_id=user_id))
        await db.commit()
        return new_id


async def _save_chat_messages(session_id: str, messages: List[Dict[str, str]]):
    """将对话消息持久化到数据库（仅保存 user 和 assistant 角色）"""
    async with AsyncSessionLocal() as db:
        for msg in messages:
            role = msg.get("role", "")
            if role not in ("user", "assistant"):
                continue
            db.add(ChatMessage(
                session_id=session_id,
                role=role,
                content=msg.get("content", ""),
            ))
        await db.commit()


async def _load_chat_history(session_id: str, max_messages: int = 20) -> List[Dict[str, str]]:
    """从数据库加载最近 N 条对话历史"""
    async with AsyncSessionLocal() as db:
        stmt = (
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.asc())
            .limit(max_messages)
        )
        result = await db.execute(stmt)
        return [
            {"role": msg.role, "content": msg.content or ""}
            for msg in result.scalars().all()
        ]


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 确保 data 目录存在
    if not os.path.exists("data"):
        os.makedirs("data")

    # Startup: 初始化数据库
    logger.info("Initializing database...")
    await init_db()
    logger.info(f"DEPLOY_MODE={os.getenv('DEPLOY_MODE', 'local')}")
    yield
    # Shutdown
    logger.info("Shutting down...")


app = FastAPI(title="Privacy Schedule Agent API", lifespan=lifespan)

# 条件注册认证中间件（cloud 模式启用）
if os.getenv("DEPLOY_MODE", "local") == "cloud":
    from app.auth.middleware import AuthMiddleware
    app.add_middleware(AuthMiddleware)
    logger.info("Auth middleware enabled (cloud mode)")


@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """主要对话接口"""
    session_id = request.session_id
    user_input = request.message

    # 获取或初始化历史记录
    if session_id not in sessions:
        if len(sessions) >= MAX_SESSIONS:
            oldest_key = next(iter(sessions))
            del sessions[oldest_key]
            logger.info(f"Evicted oldest session '{oldest_key}'")
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
        raise HTTPException(status_code=500, detail="内部处理出错，请稍后重试")


async def _sse_generator(gen: AsyncGenerator[dict, None]) -> AsyncGenerator[bytes, None]:
    """将 run_chat_stream 的事件字典包装为 SSE bytes 流"""
    async for event in gen:
        event_type = event.get("type", "")
        data = json.dumps(event.get("data", {}), ensure_ascii=False)
        yield f"event: {event_type}\ndata: {data}\n\n".encode("utf-8")


@app.post("/chat/stream")
async def chat_stream_endpoint(req: ChatStreamRequest):
    """SSE 流式对话接口"""
    session_id = await _get_or_create_session(req.session_id, req.user_id)
    history = await _load_chat_history(session_id)

    async def event_stream():
        # 收集最终消息用于持久化
        final_messages: List[Dict[str, str]] = []
        final_content = ""

        async for event in _sse_generator(run_chat_stream(req.message, history)):
            if event:
                yield event
                data = json.loads(event.decode("utf-8").split("data: ", 1)[-1].strip())
                if event.startswith(b"event: token"):
                    final_content += data.get("text", "")

        # 持久化 user 和 assistant 消息
        final_messages.append({"role": "user", "content": req.message})
        final_messages.append({"role": "assistant", "content": final_content})
        await _save_chat_messages(session_id, final_messages)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


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
                "user_id": s.user_id,
                "recurrence_rule": s.recurrence_rule,
                "recurrence_end": s.recurrence_end.strftime("%Y-%m-%d %H:%M:%S") if s.recurrence_end else None
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
            "status": s.status,
            "recurrence_rule": s.recurrence_rule,
            "recurrence_end": s.recurrence_end.strftime("%Y-%m-%d %H:%M:%S") if s.recurrence_end else None
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
            new_start = event.start_time
            new_end = event.end_time
            new_location = event.location_ref
            time_or_location_changed = False

            if req.start_time is not None:
                new_start = datetime.strptime(req.start_time, "%Y-%m-%d %H:%M:%S")
                time_or_location_changed = True
            if req.end_time is not None:
                new_end = datetime.strptime(req.end_time, "%Y-%m-%d %H:%M:%S")
                time_or_location_changed = True
            if req.location is not None:
                new_location = req.location
                time_or_location_changed = True
            if new_end <= new_start:
                raise HTTPException(status_code=400, detail="结束时间必须晚于开始时间")

            conflicts = []
            if time_or_location_changed:
                conflict_raw = await check_conflict(
                    start_time=new_start.strftime("%Y-%m-%d %H:%M:%S"),
                    end_time=new_end.strftime("%Y-%m-%d %H:%M:%S"),
                    location=(new_location or ""),
                    exclude_event_id=event_id,
                )
                conflict_status, conflicts, conflict_message = _parse_conflict_result(conflict_raw)
                if conflict_status == CODE_WARN and not req.confirm_conflict:
                    return JSONResponse(
                        status_code=409,
                        content={
                            "status": "conflict_requires_confirmation",
                            "message": conflict_message or "检测到冲突，需要显式确认后保存",
                            "conflicts": conflicts,
                        },
                    )

            event.start_time = new_start
            event.end_time = new_end
            event.location_ref = new_location
            if req.description is not None:
                event.description = req.description
            if req.category is not None:
                event.category = req.category
            if req.recurrence_rule is not None:
                event.recurrence_rule = req.recurrence_rule if req.recurrence_rule else None
            if req.recurrence_end is not None:
                event.recurrence_end = datetime.strptime(req.recurrence_end, "%Y-%m-%d %H:%M:%S") if req.recurrence_end else None
            if time_or_location_changed:
                event.status = "conflicted" if conflicts else "confirmed"

            await session.commit()

            return {
                "id": event.id,
                "title": event.title,
                "start_time": event.start_time.strftime("%Y-%m-%d %H:%M:%S"),
                "end_time": event.end_time.strftime("%Y-%m-%d %H:%M:%S"),
                "location": event.location_ref,
                "description": event.description,
                "category": event.category,
                "status": event.status,
                "conflicts": conflicts if event.status == "conflicted" else []
            }
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"时间格式不正确: {str(e)}")


@app.post("/schedules")
async def create_schedule(req: ScheduleCreateRequest):
    """创建日程（直接创建，不经过 LLM）"""
    async with AsyncSessionLocal() as session:
        try:
            dt_start = datetime.strptime(req.start_time, "%Y-%m-%d %H:%M:%S")
            dt_end = datetime.strptime(req.end_time, "%Y-%m-%d %H:%M:%S")
            if dt_end <= dt_start:
                raise HTTPException(status_code=400, detail="结束时间必须晚于开始时间")

            conflict_raw = await check_conflict(
                start_time=dt_start.strftime("%Y-%m-%d %H:%M:%S"),
                end_time=dt_end.strftime("%Y-%m-%d %H:%M:%S"),
                location=(req.location or ""),
            )
            conflict_status, conflicts, conflict_message = _parse_conflict_result(conflict_raw)
            if conflict_status == CODE_WARN and not req.confirm_conflict:
                return JSONResponse(
                    status_code=409,
                    content={
                        "status": "conflict_requires_confirmation",
                        "message": conflict_message or "检测到冲突，需要显式确认后保存",
                        "conflicts": conflicts,
                    },
                )

            event = Schedule(
                user_id=req.user_id or 1,
                title=req.title,
                start_time=dt_start,
                end_time=dt_end,
                location_ref=req.location or None,
                description=req.description or None,
                category=req.category or None,
                status="conflicted" if conflict_status == CODE_WARN else "confirmed",
                recurrence_rule=req.recurrence_rule or None,
                recurrence_end=datetime.strptime(req.recurrence_end, "%Y-%m-%d %H:%M:%S") if req.recurrence_end else None
            )
            session.add(event)
            await session.commit()
            await session.refresh(event)
            return {
                "id": event.id,
                "title": event.title,
                "start_time": event.start_time.strftime("%Y-%m-%d %H:%M:%S"),
                "end_time": event.end_time.strftime("%Y-%m-%d %H:%M:%S"),
                "status": event.status,
                "conflicts": conflicts if event.status == "conflicted" else []
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


@app.get("/schedules/export/json")
async def export_schedules_json(user_id: int = None):
    """导出全部日程为 JSON 文件"""
    async with AsyncSessionLocal() as session:
        stmt = select(Schedule).order_by(Schedule.start_time.asc())
        if user_id is not None:
            stmt = stmt.where(Schedule.user_id == user_id)
        result = await session.execute(stmt)
        schedules = result.scalars().all()
        data = [
            {
                "id": s.id,
                "title": s.title,
                "start_time": s.start_time.strftime("%Y-%m-%d %H:%M:%S"),
                "end_time": s.end_time.strftime("%Y-%m-%d %H:%M:%S"),
                "location": s.location_ref,
                "description": s.description,
                "category": s.category,
                "status": s.status,
                "privacy_level": s.privacy_level,
                "user_id": s.user_id,
                "recurrence_rule": s.recurrence_rule,
                "recurrence_end": s.recurrence_end.strftime("%Y-%m-%d %H:%M:%S") if s.recurrence_end else None
            }
            for s in schedules
        ]
    json_str = json.dumps(data, ensure_ascii=False, indent=2)
    now_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    return Response(
        content=json_str,
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="schedules_export_{now_str}.json"'}
    )


from collections import Counter, defaultdict


class StatsQuery(BaseModel):
    start: str  # YYYY-MM-DD
    end: str    # YYYY-MM-DD
    user_id: Optional[int] = 1


@app.post("/api/statistics/summary")
async def statistics_summary(req: StatsQuery):
    """智能日程统计：分类统计、每日分布、空闲模式"""
    from datetime import timedelta

    async with AsyncSessionLocal() as session:
        try:
            dt_start = datetime.strptime(req.start, "%Y-%m-%d")
            dt_end = datetime.strptime(req.end, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
        except ValueError:
            raise HTTPException(status_code=400, detail="日期格式应为 YYYY-MM-DD")

        stmt = (
            select(Schedule)
            .where(Schedule.user_id == req.user_id)
            .where(Schedule.start_time >= dt_start)
            .where(Schedule.start_time <= dt_end)
            .order_by(Schedule.start_time.asc())
        )
        result = await session.execute(stmt)
        events = result.scalars().all()

        total = len(events)
        if total == 0:
            return {
                "total_events": 0,
                "category_distribution": {},
                "daily_distribution": [],
                "avg_duration_minutes": 0,
                "busiest_day": None,
                "summary": "该时间段内没有日程安排。"
            }

        # 分类统计
        categories = Counter(e.category or "未分类" for e in events)

        # 每日分布
        days: Dict[str, int] = defaultdict(int)
        for e in events:
            day_key = e.start_time.strftime("%Y-%m-%d")
            days[day_key] += 1

        daily_dist = sorted(
            [{"date": d, "count": c} for d, c in days.items()],
            key=lambda x: x["date"]
        )

        # 平均时长（分钟）
        durations = []
        for e in events:
            delta = e.end_time - e.start_time
            durations.append(delta.total_seconds() / 60)
        avg_duration = round(sum(durations) / len(durations)) if durations else 0

        # 最忙的一天
        busiest_day = max(days, key=days.get) if days else None

        # 空闲模式：每天 8:00-20:00 中未被占用的时段
        free_patterns = []
        for date_key in sorted(days.keys())[:7]:  # 最多分析 7 天
            day_start = datetime.strptime(date_key, "%Y-%m-%d")
            day_end = day_start.replace(hour=23, minute=59, second=59)

            day_events = [
                e for e in events
                if day_start <= e.start_time <= day_end
            ]
            day_events.sort(key=lambda e: e.start_time)

            if not day_events:
                free_patterns.append({"date": date_key, "free_slots": [{"start": "08:00", "end": "20:00"}]})
                continue

            slots = []
            cursor = day_start.replace(hour=8, minute=0)
            work_end = day_start.replace(hour=20, minute=0)

            for evt in day_events:
                evt_start = max(evt.start_time, cursor)
                if evt_start > cursor and cursor < work_end:
                    slot_end = min(evt.start_time, work_end)
                    if slot_end > cursor:
                        slots.append({
                            "start": cursor.strftime("%H:%M"),
                            "end": slot_end.strftime("%H:%M"),
                        })
                cursor = max(cursor, evt.end_time)

            if cursor < work_end:
                slots.append({
                    "start": cursor.strftime("%H:%M"),
                    "end": work_end.strftime("%H:%M"),
                })

            free_patterns.append({"date": date_key, "free_slots": slots})

        category_dist = dict(categories.most_common())

        # 生成文字总结
        summary_parts = [
            f"在 {req.start} 至 {req.end} 期间，共 {total} 个日程安排。",
            f"平均每个日程约 {avg_duration} 分钟。",
        ]
        if busiest_day:
            summary_parts.append(f"最忙碌的一天是 {busiest_day}，有 {days[busiest_day]} 个日程。")
        if category_dist:
            top_cat = list(category_dist.keys())[0]
            summary_parts.append(f"最常见的分类是「{top_cat}」，共 {category_dist[top_cat]} 项。")

        return {
            "total_events": total,
            "category_distribution": category_dist,
            "daily_distribution": daily_dist,
            "avg_duration_minutes": avg_duration,
            "busiest_day": busiest_day,
            "free_patterns": free_patterns,
            "summary": " ".join(summary_parts),
        }


# ── 认证端点 ──────────────────────────────────────────────
@app.post("/api/auth/register")
async def auth_register(req: AuthRegisterRequest):
    """用户注册（仅 cloud 模式可用）"""
    async with AsyncSessionLocal() as session:
        stmt = select(User).where(User.username == req.username)
        result = await session.execute(stmt)
        if result.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="用户名已存在")

        user = User(
            username=req.username,
            password_hash=_hash_password(req.password),
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)

        token = create_token(user.id, user.username)
        return {"token": token, "user": {"id": user.id, "username": user.username}}


@app.post("/api/auth/login")
async def auth_login(req: AuthLoginRequest):
    """用户登录"""
    async with AsyncSessionLocal() as session:
        stmt = select(User).where(User.username == req.username)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        if not user or not _verify_password(req.password, user.password_hash):
            raise HTTPException(status_code=401, detail="用户名或密码错误")

        token = create_token(user.id, user.username)
        return {"token": token, "user": {"id": user.id, "username": user.username}}


@app.get("/api/auth/me")
async def auth_me(request: Request):
    """获取当前用户信息"""
    try:
        user_id = await get_user_id_from_request(request)
    except HTTPException:
        raise HTTPException(status_code=401, detail="未认证")

    async with AsyncSessionLocal() as session:
        stmt = select(User).where(User.id == user_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        return {"id": user.id, "username": user.username}


# 挂载前端静态文件（优先使用 Vite 构建产物）
dist_path = "frontend/dist"
if os.path.exists(dist_path):
    app.mount("/", StaticFiles(directory=dist_path, html=True), name="frontend")
elif os.path.exists("frontend"):
    app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
