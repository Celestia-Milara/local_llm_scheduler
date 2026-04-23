import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy import select, and_, or_
from app.db.database import AsyncSessionLocal
from app.db.models import Schedule
from app.services.location_service import get_travel_time

logger = logging.getLogger(__name__)

# 定义返回状态码
CODE_OK = "OK"
CODE_WARN = "WARN"
CODE_ERROR = "ERROR"

async def check_conflict(start_time: str, end_time: str, location: str) -> str:
    """
    检查指定时间段的日程是否存在物理或时间上的冲突。
    
    Args:
        start_time (str): 计划开始时间，格式 ISO (例如 "2026-04-23 14:00:00")
        end_time (str): 计划结束时间，格式 ISO (例如 "2026-04-23 15:00:00")
        location (str): 计划地点
        
    Returns:
        str: 包含 status 和冲突详情的 JSON 字符串。
    """
    try:
        dt_start = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
        dt_end = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")
    except ValueError as e:
        return json.dumps({
            "status": CODE_ERROR,
            "message": f"时间格式错误: {str(e)}"
        }, ensure_ascii=False)

    async with AsyncSessionLocal() as session:
        # 1. 查询在此时间段之前和之后的紧邻行程，用于计算通勤冲突
        # 查询上一个行程
        stmt_prev = select(Schedule).where(
            Schedule.end_time <= dt_start
        ).order_by(Schedule.end_time.desc()).limit(1)
        
        # 查询下一个行程
        stmt_next = select(Schedule).where(
            Schedule.start_time >= dt_end
        ).order_by(Schedule.start_time.asc()).limit(1)
        
        result_prev = await session.execute(stmt_prev)
        prev_event = result_prev.scalar_one_or_none()
        
        result_next = await session.execute(stmt_next)
        next_event = result_next.scalar_one_or_none()

        conflicts = []

        # 2. 检查通勤冲突 (与前一个行程)
        if prev_event and prev_event.location_ref:
            travel_min = await get_travel_time(prev_event.location_ref, location)
            required_arrival_time = prev_event.end_time + timedelta(minutes=travel_min)
            if required_arrival_time > dt_start:
                conflicts.append({
                    "type": "TRAVEL_CONFLICT",
                    "reason": f"距离上一日程 '{prev_event.title}' 仅有 {(dt_start - prev_event.end_time).seconds // 60} 分钟，但通勤需要 {travel_min} 分钟"
                })

        # 3. 检查硬性时间重叠 (Overlap)
        stmt_overlap = select(Schedule).where(
            or_(
                and_(Schedule.start_time < dt_end, Schedule.end_time > dt_start)
            )
        )
        result_overlap = await session.execute(stmt_overlap)
        overlapping_events = result_overlap.scalars().all()
        
        for event in overlapping_events:
            conflicts.append({
                "type": "TIME_OVERLAP",
                "reason": f"与现有日程 '{event.title}' ({event.start_time.strftime('%H:%M')}-{event.end_time.strftime('%H:%M')}) 存在重叠"
            })

        if not conflicts:
            return json.dumps({"status": CODE_OK, "message": "没有发现冲突"}, ensure_ascii=False)
        else:
            return json.dumps({
                "status": CODE_WARN,
                "conflicts": conflicts,
                "message": f"发现 {len(conflicts)} 处冲突，请确认是否仍要保存"
            }, ensure_ascii=False)

async def add_event(title: str, start_time: str, end_time: str, location: str, status: str = "confirmed") -> str:
    """
    将新日程写入数据库。
    
    Args:
        title (str): 日程标题
        start_time (str): 开始时间 (YYYY-MM-DD HH:MM:SS)
        end_time (str): 结束时间 (YYYY-MM-DD HH:MM:SS)
        location (str): 地点
        status (str): 日程状态，默认为 'confirmed'。如果用户已知冲突仍要保存，应传入 'conflicted'。
        
    Returns:
        str: 操作结果的 JSON 字符串。
    """
    try:
        dt_start = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
        dt_end = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return json.dumps({"status": CODE_ERROR, "message": "时间格式不正确"}, ensure_ascii=False)

    async with AsyncSessionLocal() as session:
        try:
            new_event = Schedule(
                title=title,
                start_time=dt_start,
                end_time=dt_end,
                location_ref=location,
                status=status
            )
            session.add(new_event)
            await session.commit()
            return json.dumps({
                "status": CODE_OK,
                "message": f"成功保存日程: {title}",
                "event_id": new_event.id
            }, ensure_ascii=False)
        except Exception as e:
            await session.rollback()
            logger.error(f"Error adding event: {e}")
            return json.dumps({"status": CODE_ERROR, "message": f"保存失败: {str(e)}"}, ensure_ascii=False)
