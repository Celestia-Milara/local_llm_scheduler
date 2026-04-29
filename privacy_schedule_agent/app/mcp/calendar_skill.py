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
        if prev_event and prev_event.location_ref and location:
            travel_min = await get_travel_time(prev_event.location_ref, location)
            required_arrival_time = prev_event.end_time + timedelta(minutes=travel_min)
            if required_arrival_time > dt_start:
                conflicts.append({
                    "type": "TRAVEL_CONFLICT",
                    "reason": f"距离上一日程 '{prev_event.title}' 仅有 {(dt_start - prev_event.end_time).seconds // 60} 分钟，但通勤需要 {travel_min} 分钟"
                })

        # 2b. 检查通勤冲突 (与后一个行程)
        if next_event and next_event.location_ref and location:
            travel_min = await get_travel_time(location, next_event.location_ref)
            required_arrival_time = dt_end + timedelta(minutes=travel_min)
            if required_arrival_time > next_event.start_time:
                conflicts.append({
                    "type": "TRAVEL_CONFLICT",
                    "reason": f"本日程结束后到下一日程 '{next_event.title}' 仅有 {(next_event.start_time - dt_end).seconds // 60} 分钟，但通勤需要 {travel_min} 分钟"
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

async def add_event(title: str, start_time: str, end_time: str, location: str,
                    description: str = None, category: str = None,
                    status: str = "confirmed") -> str:
    """
    将新日程写入数据库。

    Args:
        title (str): 日程标题
        start_time (str): 开始时间 (YYYY-MM-DD HH:MM:SS)
        end_time (str): 结束时间 (YYYY-MM-DD HH:MM:SS)
        location (str): 地点
        description (str): 日程描述/备注
        category (str): 日程分类（工作/学习/生活等）
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
                description=description,
                category=category,
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


async def query_events(start_time: str = None, end_time: str = None,
                       keyword: str = None, category: str = None) -> str:
    """
    查询日程列表。至少需要提供 start_time+end_time 或 keyword 之一。

    Args:
        start_time (str): 查询起始时间 (YYYY-MM-DD HH:MM:SS)
        end_time (str): 查询结束时间 (YYYY-MM-DD HH:MM:SS)
        keyword (str): 按标题模糊搜索的关键词
        category (str): 按分类过滤

    Returns:
        str: 包含日程列表的 JSON 字符串。
    """
    if not start_time and not end_time and not keyword:
        return json.dumps({
            "status": CODE_ERROR,
            "message": "请至少提供时间范围(start_time+end_time)或搜索关键词(keyword)"
        }, ensure_ascii=False)

    async with AsyncSessionLocal() as session:
        stmt = select(Schedule)
        conditions = []

        if start_time:
            try:
                dt_start = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
                conditions.append(Schedule.start_time >= dt_start)
            except ValueError:
                return json.dumps({"status": CODE_ERROR, "message": "start_time 格式不正确"}, ensure_ascii=False)

        if end_time:
            try:
                dt_end = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")
                conditions.append(Schedule.end_time <= dt_end)
            except ValueError:
                return json.dumps({"status": CODE_ERROR, "message": "end_time 格式不正确"}, ensure_ascii=False)

        if keyword:
            conditions.append(Schedule.title.contains(keyword))

        if category:
            conditions.append(Schedule.category == category)

        if conditions:
            stmt = stmt.where(and_(*conditions))

        stmt = stmt.order_by(Schedule.start_time.asc())
        result = await session.execute(stmt)
        events = result.scalars().all()

        if not events:
            return json.dumps({
                "status": CODE_OK,
                "message": "未找到匹配的日程",
                "events": []
            }, ensure_ascii=False)

        return json.dumps({
            "status": CODE_OK,
            "message": f"找到 {len(events)} 条日程",
            "events": [
                {
                    "id": e.id,
                    "title": e.title,
                    "start_time": e.start_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "end_time": e.end_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "location": e.location_ref,
                    "description": e.description,
                    "category": e.category,
                    "status": e.status
                }
                for e in events
            ]
        }, ensure_ascii=False)


async def update_event(event_id: int, title: str = None,
                       start_time: str = None, end_time: str = None,
                       location: str = None, description: str = None,
                       category: str = None) -> str:
    """
    修改已有日程。只更新传入的非 None 字段。
    如果修改了时间或地点，会自动重新检查冲突。

    Args:
        event_id (int): 日程ID
        title (str): 新标题
        start_time (str): 新开始时间 (YYYY-MM-DD HH:MM:SS)
        end_time (str): 新结束时间 (YYYY-MM-DD HH:MM:SS)
        location (str): 新地点
        description (str): 新描述
        category (str): 新分类

    Returns:
        str: 操作结果的 JSON 字符串，可能包含冲突信息。
    """
    async with AsyncSessionLocal() as session:
        try:
            stmt = select(Schedule).where(Schedule.id == event_id)
            result = await session.execute(stmt)
            event = result.scalar_one_or_none()

            if not event:
                return json.dumps({
                    "status": CODE_ERROR,
                    "message": f"未找到ID为 {event_id} 的日程"
                }, ensure_ascii=False)

            time_or_location_changed = False
            new_start = event.start_time
            new_end = event.end_time
            new_location = location or event.location_ref

            if title is not None:
                event.title = title
            if start_time is not None:
                new_start = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
                event.start_time = new_start
                time_or_location_changed = True
            if end_time is not None:
                new_end = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")
                event.end_time = new_end
                time_or_location_changed = True
            if location is not None:
                event.location_ref = location
                time_or_location_changed = True
            if description is not None:
                event.description = description
            if category is not None:
                event.category = category

            conflict_info = None
            if time_or_location_changed:
                conflict_result = await check_conflict(
                    new_start.strftime("%Y-%m-%d %H:%M:%S"),
                    new_end.strftime("%Y-%m-%d %H:%M:%S"),
                    new_location or ""
                )
                conflict_data = json.loads(conflict_result)
                if conflict_data.get("status") == CODE_WARN:
                    conflict_info = conflict_data
                    event.status = "conflicted"
                else:
                    event.status = "confirmed"

            await session.commit()

            result_data = {
                "status": CODE_OK,
                "message": f"日程 '{event.title}' 已更新",
                "event_id": event.id
            }
            if conflict_info:
                result_data["conflict_warning"] = conflict_info

            return json.dumps(result_data, ensure_ascii=False)

        except ValueError as e:
            return json.dumps({"status": CODE_ERROR, "message": f"时间格式不正确: {str(e)}"}, ensure_ascii=False)
        except Exception as e:
            await session.rollback()
            logger.error(f"Error updating event: {e}")
            return json.dumps({"status": CODE_ERROR, "message": f"更新失败: {str(e)}"}, ensure_ascii=False)


async def delete_event(event_id: int) -> str:
    """
    删除指定日程。

    Args:
        event_id (int): 要删除的日程ID

    Returns:
        str: 操作结果的 JSON 字符串。
    """
    async with AsyncSessionLocal() as session:
        try:
            stmt = select(Schedule).where(Schedule.id == event_id)
            result = await session.execute(stmt)
            event = result.scalar_one_or_none()

            if not event:
                return json.dumps({
                    "status": CODE_ERROR,
                    "message": f"未找到ID为 {event_id} 的日程"
                }, ensure_ascii=False)

            title = event.title
            await session.delete(event)
            await session.commit()
            return json.dumps({
                "status": CODE_OK,
                "message": f"已删除日程: {title}",
                "event_id": event_id
            }, ensure_ascii=False)

        except Exception as e:
            await session.rollback()
            logger.error(f"Error deleting event: {e}")
            return json.dumps({"status": CODE_ERROR, "message": f"删除失败: {str(e)}"}, ensure_ascii=False)


async def find_free_slots(date: str, duration_minutes: int = 60,
                          start_hour: int = 8, end_hour: int = 22) -> str:
    """
    查找指定日期内的空闲时段。

    Args:
        date (str): 日期 (YYYY-MM-DD)
        duration_minutes (int): 需要的最小连续空闲时长（分钟），默认60
        start_hour (int): 查找范围起始小时，默认8
        end_hour (int): 查找范围结束小时，默认22

    Returns:
        str: 包含空闲时段列表的 JSON 字符串。
    """
    try:
        target_date = datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        return json.dumps({"status": CODE_ERROR, "message": "日期格式不正确，应为 YYYY-MM-DD"}, ensure_ascii=False)

    day_start = target_date.replace(hour=start_hour, minute=0, second=0)
    day_end = target_date.replace(hour=end_hour, minute=0, second=0)

    async with AsyncSessionLocal() as session:
        stmt = select(Schedule).where(
            and_(
                Schedule.start_time < day_end,
                Schedule.end_time > day_start
            )
        ).order_by(Schedule.start_time.asc())
        result = await session.execute(stmt)
        events = result.scalars().all()

    slots = []
    cursor = day_start
    for event in events:
        if event.start_time > cursor:
            gap_minutes = (event.start_time - cursor).seconds // 60
            if gap_minutes >= duration_minutes:
                slots.append({
                    "start": cursor.strftime("%H:%M"),
                    "end": event.start_time.strftime("%H:%M"),
                    "duration_minutes": gap_minutes
                })
        cursor = max(cursor, event.end_time)

    if cursor < day_end:
        gap_minutes = (day_end - cursor).seconds // 60
        if gap_minutes >= duration_minutes:
            slots.append({
                "start": cursor.strftime("%H:%M"),
                "end": day_end.strftime("%H:%M"),
                "duration_minutes": gap_minutes
            })

    if not slots:
        return json.dumps({
            "status": CODE_OK,
            "message": f"{date} 在 {start_hour}:00-{end_hour}:00 之间没有 {duration_minutes} 分钟以上的空闲时段",
            "free_slots": []
        }, ensure_ascii=False)

    return json.dumps({
        "status": CODE_OK,
        "message": f"找到 {len(slots)} 个空闲时段",
        "free_slots": slots
    }, ensure_ascii=False)
