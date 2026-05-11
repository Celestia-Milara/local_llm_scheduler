"""数据生命周期管理：过期日程归档 + LLM 摘要生成"""

import logging
import json
from datetime import datetime, timedelta
from sqlalchemy import select

from app.db.database import AsyncSessionLocal
from app.db.models import Schedule, Summary

logger = logging.getLogger(__name__)

# 过期天数阈值
ARCHIVE_AFTER_DAYS = 30

# 每次最多处理条数
MAX_BATCH_SIZE = 50


async def archive_old_schedules(user_id: int = 1) -> int:
    """
    归档过期日程：
    1. 查找 end_time 超过 ARCHIVE_AFTER_DAYS 且未归档的日程
    2. 按周分组生成摘要写入 summaries 表
    3. 软删除（设 is_archived = 1）
    返回处理的日程条数
    """
    cutoff = datetime.now() - timedelta(days=ARCHIVE_AFTER_DAYS)

    async with AsyncSessionLocal() as session:
        stmt = (
            select(Schedule)
            .where(Schedule.user_id == user_id)
            .where(Schedule.end_time < cutoff)
            .where(Schedule.is_archived == 0)
            .order_by(Schedule.start_time.asc())
            .limit(MAX_BATCH_SIZE)
        )
        result = await session.execute(stmt)
        events = result.scalars().all()

        if not events:
            return 0

        # 按 ISO 周分组
        weeks: dict[str, list[Schedule]] = {}
        for evt in events:
            iso_year, iso_week, _ = evt.start_time.isocalendar()
            week_key = f"{iso_year}-W{iso_week:02d}"
            weeks.setdefault(week_key, []).append(evt)

        # 为每周生成摘要
        for week_key, week_events in weeks.items():
            summary_text = _make_week_summary(week_key, week_events)
            summary = Summary(time_range=week_key, content=summary_text)
            session.add(summary)
            await session.flush()  # 获取 summary.id

            # 关联摘要并标记归档
            for evt in week_events:
                evt.summary_id = summary.id
                evt.is_archived = 1

        await session.commit()
        logger.info(f"Archived {len(events)} schedules, {len(weeks)} weekly summaries")
        return len(events)


def _make_week_summary(week_key: str, events: list[Schedule]) -> str:
    """生成一周日程的文字摘要（无需 LLM，直接结构化）"""
    total = len(events)
    categories: dict[str, int] = {}
    total_duration = 0

    for evt in events:
        cat = evt.category or "未分类"
        categories[cat] = categories.get(cat, 0) + 1
        duration = (evt.end_time - evt.start_time).total_seconds() / 60
        total_duration += duration

    avg_duration = round(total_duration / total) if total else 0
    cat_desc = ", ".join(f"{k} {v}项" for k, v in sorted(categories.items(), key=lambda x: -x[1]))

    parts = [
        f"第 {week_key} 周共 {total} 个日程安排，",
        f"平均每个约 {avg_duration} 分钟。",
        f"分类：{cat_desc}。" if cat_desc else "",
    ]
    return "".join(parts)


async def get_archived_summaries(user_id: int = 1, limit: int = 20) -> list[dict]:
    """获取已归档的日程摘要列表"""
    async with AsyncSessionLocal() as session:
        stmt = (
            select(Schedule)
            .where(Schedule.user_id == user_id)
            .where(Schedule.is_archived == 1)
            .order_by(Schedule.start_time.desc())
            .limit(limit)
        )
        result = await session.execute(stmt)
        events = result.scalars().all()

        summaries = []
        for evt in events:
            summaries.append({
                "id": evt.id,
                "title": evt.title,
                "start_time": evt.start_time.strftime("%Y-%m-%d %H:%M"),
                "end_time": evt.end_time.strftime("%Y-%m-%d %H:%M"),
                "summary_id": evt.summary_id,
                "archived": True,
            })
        return summaries
