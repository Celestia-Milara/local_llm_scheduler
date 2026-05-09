"""日程 CRUD 工具"""

import json
import logging
from datetime import datetime
from sqlalchemy import select, and_
from app.db.database import AsyncSessionLocal
from app.db.models import Schedule
from app.skill import skill
from app.skill.skills.schedule_management.scripts.conflict import check_conflict, CODE_OK, CODE_WARN

logger = logging.getLogger(__name__)
CODE_ERROR = "ERROR"


@skill(
    name="add_event",
    description="将新日程写入数据库",
    parameters={
        "type": "object",
        "properties": {
            "title": {"type": "string", "description": "日程标题"},
            "start_time": {"type": "string", "description": "开始时间 (YYYY-MM-DD HH:MM:SS)"},
            "end_time": {"type": "string", "description": "结束时间 (YYYY-MM-DD HH:MM:SS)"},
            "location": {"type": "string", "description": "地点"},
            "description": {"type": "string", "description": "日程描述或备注"},
            "category": {"type": "string", "description": "日程分类（如：工作、学习、生活）"},
            "status": {"type": "string", "description": "日程状态，默认为 'confirmed'。强行保存冲突日程时设为 'conflicted'"}
        },
        "required": ["title", "start_time", "end_time", "location"],
    }
)
async def add_event(title: str, start_time: str, end_time: str, location: str,
                    description: str = None, category: str = None,
                    status: str = "confirmed", user_id: int = 1) -> str:
    try:
        dt_start = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
        dt_end = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return json.dumps({"status": CODE_ERROR, "message": "时间格式不正确"}, ensure_ascii=False)

    async with AsyncSessionLocal() as session:
        try:
            new_event = Schedule(
                user_id=user_id, title=title,
                start_time=dt_start, end_time=dt_end,
                location_ref=location, description=description,
                category=category, status=status
            )
            session.add(new_event)
            await session.commit()
            return json.dumps({"status": CODE_OK, "message": f"成功保存日程: {title}", "event_id": new_event.id}, ensure_ascii=False)
        except Exception as e:
            await session.rollback()
            return json.dumps({"status": CODE_ERROR, "message": f"保存失败: {str(e)}"}, ensure_ascii=False)


@skill(
    name="query_events",
    description="查询日程列表。可按时间范围、关键词或分类查询，至少需要时间范围或关键词",
    parameters={
        "type": "object",
        "properties": {
            "start_time": {"type": "string", "description": "查询起始时间 (YYYY-MM-DD HH:MM:SS)"},
            "end_time": {"type": "string", "description": "查询结束时间 (YYYY-MM-DD HH:MM:SS)"},
            "keyword": {"type": "string", "description": "按标题模糊搜索的关键词"},
            "category": {"type": "string", "description": "按分类过滤"}
        },
        "required": [],
    }
)
async def query_events(start_time: str = None, end_time: str = None,
                       keyword: str = None, category: str = None) -> str:
    if not start_time and not end_time and not keyword:
        return json.dumps({"status": CODE_ERROR, "message": "请至少提供时间范围或关键词"}, ensure_ascii=False)

    async with AsyncSessionLocal() as session:
        stmt = select(Schedule)
        conditions = []
        if start_time:
            try:
                conditions.append(Schedule.start_time >= datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S"))
            except ValueError:
                return json.dumps({"status": CODE_ERROR, "message": "start_time 格式不正确"}, ensure_ascii=False)
        if end_time:
            try:
                conditions.append(Schedule.end_time <= datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S"))
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

        return json.dumps({
            "status": CODE_OK,
            "message": f"找到 {len(events)} 条日程" if events else "未找到匹配的日程",
            "events": [
                {
                    "id": e.id, "title": e.title,
                    "start_time": e.start_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "end_time": e.end_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "location": e.location_ref, "description": e.description,
                    "category": e.category, "status": e.status
                } for e in events
            ]
        }, ensure_ascii=False)


@skill(
    name="update_event",
    description="修改已有日程。只更新传入的字段，修改时间或地点会自动重新检查冲突",
    parameters={
        "type": "object",
        "properties": {
            "event_id": {"type": "integer", "description": "日程ID"},
            "title": {"type": "string", "description": "新标题"},
            "start_time": {"type": "string", "description": "新开始时间 (YYYY-MM-DD HH:MM:SS)"},
            "end_time": {"type": "string", "description": "新结束时间 (YYYY-MM-DD HH:MM:SS)"},
            "location": {"type": "string", "description": "新地点"},
            "description": {"type": "string", "description": "新描述"},
            "category": {"type": "string", "description": "新分类"}
        },
        "required": ["event_id"],
    }
)
async def update_event(event_id: int, title: str = None,
                       start_time: str = None, end_time: str = None,
                       location: str = None, description: str = None,
                       category: str = None) -> str:
    async with AsyncSessionLocal() as session:
        try:
            result = await session.execute(select(Schedule).where(Schedule.id == event_id))
            event = result.scalar_one_or_none()
            if not event:
                return json.dumps({"status": CODE_ERROR, "message": f"未找到ID为 {event_id} 的日程"}, ensure_ascii=False)

            new_start = event.start_time
            new_end = event.end_time
            new_location = location or event.location_ref
            time_or_location_changed = False

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

            if time_or_location_changed:
                conflict_result = await check_conflict(
                    new_start.strftime("%Y-%m-%d %H:%M:%S"),
                    new_end.strftime("%Y-%m-%d %H:%M:%S"),
                    new_location or "",
                    exclude_event_id=event_id
                )
                conflict_data = json.loads(conflict_result)
                if conflict_data.get("status") == CODE_WARN:
                    event.status = "conflicted"
                else:
                    event.status = "confirmed"

            await session.commit()
            result_data = {"status": CODE_OK, "message": f"日程 '{event.title}' 已更新", "event_id": event.id}
            return json.dumps(result_data, ensure_ascii=False)
        except ValueError as e:
            return json.dumps({"status": CODE_ERROR, "message": f"时间格式不正确: {str(e)}"}, ensure_ascii=False)
        except Exception as e:
            await session.rollback()
            return json.dumps({"status": CODE_ERROR, "message": f"更新失败: {str(e)}"}, ensure_ascii=False)


@skill(
    name="delete_event",
    description="删除指定日程",
    parameters={
        "type": "object",
        "properties": {
            "event_id": {"type": "integer", "description": "要删除的日程ID"}
        },
        "required": ["event_id"],
    }
)
async def delete_event(event_id: int) -> str:
    async with AsyncSessionLocal() as session:
        try:
            result = await session.execute(select(Schedule).where(Schedule.id == event_id))
            event = result.scalar_one_or_none()
            if not event:
                return json.dumps({"status": CODE_ERROR, "message": f"未找到ID为 {event_id} 的日程"}, ensure_ascii=False)
            title = event.title
            await session.delete(event)
            await session.commit()
            return json.dumps({"status": CODE_OK, "message": f"已删除日程: {title}", "event_id": event_id}, ensure_ascii=False)
        except Exception as e:
            await session.rollback()
            return json.dumps({"status": CODE_ERROR, "message": f"删除失败: {str(e)}"}, ensure_ascii=False)
