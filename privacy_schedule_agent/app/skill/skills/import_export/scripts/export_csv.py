"""CSV 导出工具"""

import json
import csv
import io
from app.skill import skill
from sqlalchemy import select
from app.db.database import AsyncSessionLocal
from app.db.models import Schedule


@skill(
    name="export_csv",
    description="将日程导出为 CSV 格式",
    parameters={
        "type": "object",
        "properties": {
            "start_time": {"type": "string", "description": "起始时间 (YYYY-MM-DD HH:MM:SS)"},
            "end_time": {"type": "string", "description": "结束时间 (YYYY-MM-DD HH:MM:SS)"}
        },
        "required": [],
    }
)
async def export_csv(start_time: str = None, end_time: str = None) -> str:
    """导出日程为 CSV 字符串"""
    async with AsyncSessionLocal() as session:
        stmt = select(Schedule).order_by(Schedule.start_time.asc())
        if start_time:
            from datetime import datetime
            stmt = stmt.where(Schedule.start_time >= datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S"))
        if end_time:
            from datetime import datetime
            stmt = stmt.where(Schedule.end_time <= datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S"))
        result = await session.execute(stmt)
        events = result.scalars().all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["标题", "开始时间", "结束时间", "地点", "分类", "描述", "状态"])
    for e in events:
        writer.writerow([
            e.title,
            e.start_time.strftime("%Y-%m-%d %H:%M:%S"),
            e.end_time.strftime("%Y-%m-%d %H:%M:%S"),
            e.location_ref or "",
            e.category or "",
            e.description or "",
            e.status
        ])

    csv_content = output.getvalue()
    return json.dumps({"status": "OK", "csv": csv_content, "count": len(events)}, ensure_ascii=False)
