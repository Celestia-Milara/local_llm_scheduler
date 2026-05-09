"""iCal 导入工具"""

import json
import re
import logging
from datetime import datetime
from app.skill import skill
from app.db.database import AsyncSessionLocal
from app.db.models import Schedule
from app.skill.skills.schedule_management.scripts.conflict import check_conflict, CODE_WARN, CODE_OK

logger = logging.getLogger(__name__)


def _parse_ical(ics_text: str) -> list:
    """简易 iCal 解析器，提取 VEVENT 块"""
    events = []
    vevent_pattern = re.compile(r"BEGIN:VEVENT(.*?)END:VEVENT", re.DOTALL)
    dtstart_pattern = re.compile(r"DTSTART[^:]*:(\d{4})(\d{2})(\d{2})T(\d{2})(\d{2})(\d{2})")
    dtend_pattern = re.compile(r"DTEND[^:]*:(\d{4})(\d{2})(\d{2})T(\d{2})(\d{2})(\d{2})")
    summary_pattern = re.compile(r"SUMMARY:(.+)")
    location_pattern = re.compile(r"LOCATION:(.+)")
    description_pattern = re.compile(r"DESCRIPTION:(.+)")

    for match in vevent_pattern.finditer(ics_text):
        block = match.group(1)
        def _get(pattern):
            m = pattern.search(block)
            return m.group(1).strip() if m else None

        dt_s = dtstart_pattern.search(block)
        dt_e = dtend_pattern.search(block)
        if not dt_s or not dt_e:
            continue

        def _fmt(d):
            return f"{d.group(1)}-{d.group(2)}-{d.group(3)} {d.group(4)}:{d.group(5)}:{d.group(6)}"

        events.append({
            "title": _get(summary_pattern) or "导入日程",
            "start_time": _fmt(dt_s),
            "end_time": _fmt(dt_e),
            "location": _get(location_pattern) or "",
            "description": _get(description_pattern) or ""
        })

    return events


@skill(
    name="import_ical",
    description="从 iCal (.ics) 文本导入日程，导入前检查冲突",
    parameters={
        "type": "object",
        "properties": {
            "ics_text": {"type": "string", "description": "iCal 格式的日历文本"}
        },
        "required": ["ics_text"],
    }
)
async def import_ical(ics_text: str) -> str:
    """解析 iCal 并导入日程"""
    parsed = _parse_ical(ics_text)
    if not parsed:
        return json.dumps({"status": "ERROR", "message": "未能从输入中解析出有效的 VEVENT 日程"}, ensure_ascii=False)

    results = {"total": len(parsed), "imported": 0, "conflicted": 0, "failed": 0, "details": []}

    for ev in parsed:
        conflict_raw = await check_conflict(ev["start_time"], ev["end_time"], ev["location"])
        conflict_data = json.loads(conflict_raw)
        has_conflict = conflict_data.get("status") == CODE_WARN
        status = "conflicted" if has_conflict else "confirmed"

        try:
            async with AsyncSessionLocal() as session:
                new_event = Schedule(
                    title=ev["title"],
                    start_time=datetime.strptime(ev["start_time"], "%Y-%m-%d %H:%M:%S"),
                    end_time=datetime.strptime(ev["end_time"], "%Y-%m-%d %H:%M:%S"),
                    location_ref=ev["location"] or None,
                    description=ev["description"] or None,
                    status=status
                )
                session.add(new_event)
                await session.commit()

            if has_conflict:
                results["conflicted"] += 1
            else:
                results["imported"] += 1
            results["details"].append({"title": ev["title"], "status": status})
        except Exception as e:
            results["failed"] += 1
            results["details"].append({"title": ev["title"], "status": "failed", "error": str(e)})

    return json.dumps({"status": "OK", **results}, ensure_ascii=False)
