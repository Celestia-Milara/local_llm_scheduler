"""冲突检测与空闲时段查找工具"""

import json
import logging
from datetime import datetime, timedelta
from sqlalchemy import select, and_
from app.db.database import AsyncSessionLocal
from app.db.models import Schedule
from app.services.location_service import get_travel_time
from app.skill import skill

logger = logging.getLogger(__name__)

CODE_OK = "OK"
CODE_WARN = "WARN"
CODE_ERROR = "ERROR"


@skill(
    name="check_conflict",
    description="检查指定时间段的日程是否存在物理或时间上的冲突",
    parameters={
        "type": "object",
        "properties": {
            "start_time": {"type": "string", "description": "计划开始时间 (YYYY-MM-DD HH:MM:SS)"},
            "end_time": {"type": "string", "description": "计划结束时间 (YYYY-MM-DD HH:MM:SS)"},
            "location": {"type": "string", "description": "计划地点"},
        },
        "required": ["start_time", "end_time", "location"],
    }
)
async def check_conflict(start_time: str, end_time: str, location: str,
                         exclude_event_id: int = None) -> str:
    """检查时间重叠 + 通勤冲突"""
    try:
        dt_start = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
        dt_end = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")
    except ValueError as e:
        return json.dumps({"status": CODE_ERROR, "message": f"时间格式错误: {str(e)}"}, ensure_ascii=False)

    async with AsyncSessionLocal() as session:
        stmt_prev = select(Schedule).where(
            Schedule.end_time <= dt_start
        ).order_by(Schedule.end_time.desc()).limit(1)
        stmt_next = select(Schedule).where(
            Schedule.start_time >= dt_end
        ).order_by(Schedule.start_time.asc()).limit(1)

        result_prev = await session.execute(stmt_prev)
        prev_event = result_prev.scalar_one_or_none()
        result_next = await session.execute(stmt_next)
        next_event = result_next.scalar_one_or_none()

        conflicts = []

        if prev_event and prev_event.location_ref and location:
            travel_min = get_travel_time(prev_event.location_ref, location)
            required_arrival_time = prev_event.end_time + timedelta(minutes=travel_min)
            if required_arrival_time > dt_start:
                conflicts.append({
                    "type": "TRAVEL_CONFLICT",
                    "reason": f"距离上一日程 '{prev_event.title}' 仅有 {(dt_start - prev_event.end_time).total_seconds() // 60} 分钟，但通勤需要 {travel_min} 分钟"
                })

        if next_event and next_event.location_ref and location:
            travel_min = get_travel_time(location, next_event.location_ref)
            required_arrival_time = dt_end + timedelta(minutes=travel_min)
            if required_arrival_time > next_event.start_time:
                conflicts.append({
                    "type": "TRAVEL_CONFLICT",
                    "reason": f"本日程结束后到下一日程 '{next_event.title}' 仅有 {int((next_event.start_time - dt_end).total_seconds() // 60)} 分钟，但通勤需要 {travel_min} 分钟"
                })

        stmt_overlap = select(Schedule).where(
            and_(Schedule.start_time < dt_end, Schedule.end_time > dt_start)
        )
        if exclude_event_id is not None:
            stmt_overlap = stmt_overlap.where(Schedule.id != exclude_event_id)
        result_overlap = await session.execute(stmt_overlap)
        overlapping_events = result_overlap.scalars().all()

        for event in overlapping_events:
            conflicts.append({
                "type": "TIME_OVERLAP",
                "reason": f"与现有日程 '{event.title}' ({event.start_time.strftime('%H:%M')}-{event.end_time.strftime('%H:%M')}) 存在重叠"
            })

        if not conflicts:
            return json.dumps({"status": CODE_OK, "message": "没有发现冲突"}, ensure_ascii=False)
        return json.dumps({
            "status": CODE_WARN,
            "conflicts": conflicts,
            "message": f"发现 {len(conflicts)} 处冲突，请确认是否仍要保存"
        }, ensure_ascii=False)


@skill(
    name="find_free_slots",
    description="查找指定日期的空闲时段。冲突时可用于向用户建议替代时间",
    parameters={
        "type": "object",
        "properties": {
            "date": {"type": "string", "description": "日期 (YYYY-MM-DD)"},
            "duration_minutes": {"type": "integer", "description": "需要的最小时长（分钟），默认60"},
            "start_hour": {"type": "integer", "description": "查找范围起始小时，默认8"},
            "end_hour": {"type": "integer", "description": "查找范围结束小时，默认22"}
        },
        "required": ["date"],
    }
)
async def find_free_slots(date: str, duration_minutes: int = 60,
                          start_hour: int = 8, end_hour: int = 22) -> str:
    """查找空闲时段"""
    try:
        target_date = datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        return json.dumps({"status": CODE_ERROR, "message": "日期格式不正确，应为 YYYY-MM-DD"}, ensure_ascii=False)

    day_start = target_date.replace(hour=start_hour, minute=0, second=0)
    day_end = target_date.replace(hour=end_hour, minute=0, second=0)

    async with AsyncSessionLocal() as session:
        stmt = select(Schedule).where(
            and_(Schedule.start_time < day_end, Schedule.end_time > day_start)
        ).order_by(Schedule.start_time.asc())
        result = await session.execute(stmt)
        events = result.scalars().all()

    slots = []
    cursor = day_start
    for event in events:
        if event.start_time > cursor:
            gap_minutes = int((event.start_time - cursor).total_seconds() // 60)
            if gap_minutes >= duration_minutes:
                slots.append({"start": cursor.strftime("%H:%M"), "end": event.start_time.strftime("%H:%M"), "duration_minutes": gap_minutes})
        cursor = max(cursor, event.end_time)

    if cursor < day_end:
        gap_minutes = int((day_end - cursor).total_seconds() // 60)
        if gap_minutes >= duration_minutes:
            slots.append({"start": cursor.strftime("%H:%M"), "end": day_end.strftime("%H:%M"), "duration_minutes": gap_minutes})

    return json.dumps({
        "status": CODE_OK,
        "message": f"找到 {len(slots)} 个空闲时段" if slots else f"{date} 在 {start_hour}:00-{end_hour}:00 之间没有 {duration_minutes} 分钟以上的空闲时段",
        "free_slots": slots
    }, ensure_ascii=False)
