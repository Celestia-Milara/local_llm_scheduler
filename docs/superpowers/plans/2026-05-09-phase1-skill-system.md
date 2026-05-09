# Phase 1: Skill 系统升级 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将当前硬编码的 6 个工具重构为插件式 Skill 系统——一个目录 = 一个 Skill，内含 .md 指令 + scripts/ 工具脚本

**Architecture:** `app/skill/` 包含注册器（@skill 装饰器）、加载器（目录扫描 + .md 解析）、热加载器。Skill 目录放在 `app/skill/skills/` 下，工具脚本放在各 Skill 的 `scripts/` 子目录中。`agent_engine.py` 改为从注册表动态加载 TOOLS 和系统提示词。

**Tech Stack:** Python 3.10+, FastAPI, pytest, watchfiles

---

### Task 0: 创建目录结构

**Files:**
- Create: `app/skill/` (directory)
- Create: `app/skill/skills/schedule_management/scripts/` (directory)
- Create: `app/skill/skills/weekly_summary/scripts/` (directory)
- Create: `app/skill/skills/import_export/scripts/` (directory)

- [ ] **Step 1: Create directory tree**

```bash
mkdir -p privacy_schedule_agent/app/skill/skills/schedule_management/scripts
mkdir -p privacy_schedule_agent/app/skill/skills/weekly_summary/scripts
mkdir -p privacy_schedule_agent/app/skill/skills/import_export/scripts
```

- [ ] **Step 2: Create `__init__.py` files**

```bash
touch privacy_schedule_agent/app/skill/__init__.py
touch privacy_schedule_agent/app/skill/skills/__init__.py
touch privacy_schedule_agent/app/skill/skills/schedule_management/__init__.py
touch privacy_schedule_agent/app/skill/skills/schedule_management/scripts/__init__.py
touch privacy_schedule_agent/app/skill/skills/weekly_summary/__init__.py
touch privacy_schedule_agent/app/skill/skills/weekly_summary/scripts/__init__.py
touch privacy_schedule_agent/app/skill/skills/import_export/__init__.py
touch privacy_schedule_agent/app/skill/skills/import_export/scripts/__init__.py
```

- [ ] **Step 3: Add `watchfiles` to requirements**

Edit `privacy_schedule_agent/requirements.txt`, add `watchfiles` line:

```
watchfiles
```

- [ ] **Step 4: Commit**

```bash
git add privacy_schedule_agent/app/skill/
git add privacy_schedule_agent/requirements.txt
git commit -m "feat: scaffold skill directory structure"
```

---

### Task 1: @skill 装饰器 + 注册表

**Files:**
- Write: `app/skill/__init__.py`

- [ ] **Step 1: Write the @skill decorator and registry**

Write `privacy_schedule_agent/app/skill/__init__.py`:

```python
"""Skill 注册表：@skill 装饰器 + 动态工具加载"""

from typing import Callable, Dict, Any, List
import json
import logging

logger = logging.getLogger(__name__)

_SKILL_REGISTRY: Dict[str, Dict[str, Any]] = {}

def skill(name: str, description: str, parameters: dict):
    """装饰器：将函数注册为 LLM 可调用的 Tool"""
    def decorator(func: Callable):
        _SKILL_REGISTRY[name] = {
            "function": func,
            "description": description,
            "parameters": parameters,
        }
        logger.debug(f"Registered skill: {name}")
        return func
    return decorator


def get_tools() -> List[dict]:
    """返回 LLM Function Calling 所需的 tools 列表"""
    return [
        {
            "type": "function",
            "function": {
                "name": name,
                "description": meta["description"],
                "parameters": meta["parameters"],
            }
        }
        for name, meta in _SKILL_REGISTRY.items()
    ]


def get_available_functions() -> Dict[str, Callable]:
    """返回 {name: function} 映射表"""
    return {
        name: meta["function"]
        for name, meta in _SKILL_REGISTRY.items()
    }


async def execute_tool(name: str, args: dict) -> str:
    """按名称执行 Skill，返回 JSON 字符串"""
    if name not in _SKILL_REGISTRY:
        return json.dumps({"status": "ERROR", "message": f"未知的工具名称: {name}"})
    func = _SKILL_REGISTRY[name]["function"]
    return await func(**args)


def clear_registry():
    """清空注册表（测试用）"""
    _SKILL_REGISTRY.clear()
```

- [ ] **Step 2: Write unit test**

Write `privacy_schedule_agent/tests/test_skill_registry.py`:

```python
import pytest
from app.skill import skill, get_tools, get_available_functions, execute_tool, clear_registry

@pytest.fixture(autouse=True)
def clean_registry():
    clear_registry()
    yield

@skill("test_func", "A test function", {
    "type": "object",
    "properties": {"x": {"type": "string"}},
    "required": ["x"]
})
async def test_func(x: str) -> str:
    return f"hello {x}"

@pytest.mark.asyncio
async def test_register_and_get_tools():
    tools = get_tools()
    assert len(tools) == 1
    assert tools[0]["function"]["name"] == "test_func"

@pytest.mark.asyncio
async def test_execute_tool():
    result = await execute_tool("test_func", {"x": "world"})
    assert result == "hello world"

@pytest.mark.asyncio
async def test_execute_unknown_tool():
    result = await execute_tool("nonexistent", {})
    assert "ERROR" in result
```

- [ ] **Step 3: Run test to verify it fails initially**

```bash
cd privacy_schedule_agent
pytest tests/test_skill_registry.py -v
```
Expected: ModuleNotFoundError or similar — the registry file doesn't exist yet.

- [ ] **Step 4: Run test to verify it passes**

```bash
cd privacy_schedule_agent
pytest tests/test_skill_registry.py -v
```
Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add privacy_schedule_agent/app/skill/__init__.py
git add privacy_schedule_agent/tests/test_skill_registry.py
git commit -m "feat: add @skill decorator and registry"
```

---

### Task 2: Skill 加载器 (loader.py)

**Files:**
- Create: `app/skill/loader.py`
- Test: `tests/test_skill_loader.py`

- [ ] **Step 1: Write the loader**

Write `privacy_schedule_agent/app/skill/loader.py`:

```python
"""Skill 加载器：扫描 skills/ 目录，加载 .md 指令和 scripts/ 工具"""

import os
import re
import logging
import importlib.util

logger = logging.getLogger(__name__)

SKILLS_DIR = os.path.join(os.path.dirname(__file__), "skills")


def discover_skills():
    """遍历 skills/ 下所有子目录，导入 scripts/ 中的 .py 文件"""
    if not os.path.exists(SKILLS_DIR):
        logger.warning(f"Skills directory not found: {SKILLS_DIR}")
        return

    for skill_name in os.listdir(SKILLS_DIR):
        skill_dir = os.path.join(SKILLS_DIR, skill_name)
        if not os.path.isdir(skill_dir) or skill_name.startswith("_"):
            continue

        scripts_dir = os.path.join(skill_dir, "scripts")
        if not os.path.isdir(scripts_dir):
            continue

        # 导入 scripts/ 下的所有 .py 模块（触发 @skill 装饰器）
        for fname in os.listdir(scripts_dir):
            if fname.endswith(".py") and not fname.startswith("_"):
                module_name = fname[:-3]
                full_path = os.path.join(scripts_dir, fname)
                spec = importlib.util.spec_from_file_location(
                    f"app.skill.skills.{skill_name}.scripts.{module_name}",
                    full_path
                )
                if spec and spec.loader:
                    mod = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(mod)
                    logger.info(f"Loaded skill module: {skill_name}/scripts/{fname}")


def load_skill_prompts() -> str:
    """读取所有 Skill 的 .md 文件，拼接为系统提示词片段"""
    if not os.path.exists(SKILLS_DIR):
        return ""

    parts = []
    for skill_name in sorted(os.listdir(SKILLS_DIR)):
        skill_dir = os.path.join(SKILLS_DIR, skill_name)
        if not os.path.isdir(skill_dir) or skill_name.startswith("_"):
            continue

        # 读取所有 .md 文件
        for fname in sorted(os.listdir(skill_dir)):
            if not fname.endswith(".md"):
                continue
            md_path = os.path.join(skill_dir, fname)
            try:
                with open(md_path, "r", encoding="utf-8") as f:
                    content = f.read()
                # 简单 frontmatter 解析（--- 包裹的 YAML）
                body = content
                if content.startswith("---"):
                    match = re.match(r"^---\s*\n(.*?\n)---\s*\n(.*)", content, re.DOTALL)
                    if match:
                        body = match.group(2).strip()
                parts.append(body)
            except Exception as e:
                logger.error(f"Error reading {md_path}: {e}")

    return "\n\n".join(parts)
```

- [ ] **Step 2: Write unit test**

Write `privacy_schedule_agent/tests/test_skill_loader.py`:

```python
import os
import pytest
from app.skill import clear_registry, get_tools
from app.skill.loader import discover_skills, load_skill_prompts

@pytest.fixture(autouse=True)
def clean():
    clear_registry()
    yield

@pytest.mark.asyncio
async def test_discover_skills_loads_md_prompts():
    """运行 discover_skills 后应该能加载到已注册的 Skill"""
    discover_skills()
    tools = get_tools()
    # 至少有 schedule_management 的 6 个工具
    assert len(tools) >= 6

@pytest.mark.asyncio
async def test_load_skill_prompts_returns_string():
    prompts = load_skill_prompts()
    assert isinstance(prompts, str)
    assert len(prompts) > 0
    # 应该包含日程管理的关键词
    assert "日程" in prompts
```

- [ ] **Step 3: Run tests**

```bash
cd privacy_schedule_agent
pytest tests/test_skill_loader.py -v
```
Expected: 2 passed (after tools are migrated in Task 3)

- [ ] **Step 4: Commit**

```bash
git add privacy_schedule_agent/app/skill/loader.py
git add privacy_schedule_agent/tests/test_skill_loader.py
git commit -m "feat: add skill loader with directory scanning"
```

---

### Task 3: 迁移现有工具 → schedule_management Skill

**Files:**
- Create: `app/skill/skills/schedule_management/scripts/crud.py` (add_event, query_events, update_event, delete_event)
- Create: `app/skill/skills/schedule_management/scripts/conflict.py` (check_conflict, find_free_slots)
- Create: `app/skill/skills/schedule_management/schedule_management.md`
- Remove: `app/mcp/calendar_skill.py`
- Remove: `app/mcp/` directory (if empty)

- [ ] **Step 1: Write conflict.py (check_conflict + find_free_slots)**

Write `privacy_schedule_agent/app/skill/skills/schedule_management/scripts/conflict.py`:

```python
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
```

- [ ] **Step 2: Write crud.py (add_event, query_events, update_event, delete_event)**

Write `privacy_schedule_agent/app/skill/skills/schedule_management/scripts/crud.py`:

```python
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
```

- [ ] **Step 3: Write skill markdown**

Write `privacy_schedule_agent/app/skill/skills/schedule_management/schedule_management.md`:

```markdown
---
name: 日程管理
description: 创建、查询、修改、删除日程
triggers: ["添加日程", "查看安排", "修改会议", "删除日程"]
---

## 创建日程
- 添加前必须先调用 check_conflict 检查冲突
- 冲突时调用 find_free_slots 查找空闲时段，向用户展示替代建议
- 用户明确确认后才调用 add_event
- 时间格式统一为 ISO 8601 (YYYY-MM-DD HH:MM:SS)

## 查询日程
- 使用 query_events 按时间范围查询
- 支持按标题关键词和分类过滤

## 修改日程
- 先用 query_events 找到对应日程获取 event_id
- 修改时间或地点后系统自动重新检查冲突
- 使用 update_event

## 删除日程
- 先用 query_events 找到对应日程获取 event_id
- 使用 delete_event
```

- [ ] **Step 4: Run tests**

```bash
cd privacy_schedule_agent
pytest tests/test_skill_registry.py tests/test_skill_loader.py -v
```
Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add privacy_schedule_agent/app/skill/skills/schedule_management/
git commit -m "feat: migrate calendar tools to schedule_management skill"
```

---

### Task 4: 更新 agent_engine.py 动态加载

**Files:**
- Modify: `app/core/agent_engine.py`
- Modify: `main.py` (update import from calendar_skill)

- [ ] **Step 1: Update agent_engine.py**

Edit `privacy_schedule_agent/app/core/agent_engine.py`:

Replace the import block (lines 1-11):
```python
import json
import logging
import ollama
import os
from datetime import datetime, timezone
from typing import List, Dict, Any
from dotenv import load_dotenv
# Remove: from app.mcp.calendar_skill import ...
# Add:
from app.skill import get_tools, get_available_functions, execute_tool
from app.skill.loader import discover_skills, load_skill_prompts
```

After `client = ollama.AsyncClient(host=OLLAMA_HOST)` (line 22), add:
```python
# 启动时扫描并加载所有 Skill
discover_skills()
```

Replace the SYSTEM_PROMPT_TEMPLATE (lines 25-37) to include skill prompts:
```python
SKILL_PROMPTS = load_skill_prompts()

SYSTEM_PROMPT_TEMPLATE = """
你是一个隐私保护型日程助理。你负责管理用户的日程，并确保时间安排合理且无冲突。

核心规则：
1. 在添加任何日程前，必须先调用 `check_conflict` 工具。
2. 冲突处理：如果工具返回 WARN 状态，向用户展示具体冲突原因，并调用 `find_free_slots` 查找空闲时段，给出替代建议。询问用户选择「接受建议」「手动指定时间」「强行保存」还是「取消」。
3. 强行保存：只有在用户明确表示要强行保存冲突日程时，才调用 `add_event` 并将 status 设置为 'conflicted'。
4. 查询日程：用户询问日程安排时，使用 `query_events` 工具。根据用户描述推断时间范围（如「明天」=明天0:00-23:59，「这周」=本周一到周日）。
5. 修改日程：用户要求修改日程时，先用 `query_events` 找到对应日程获取 event_id，再调用 `update_event`。修改时间或地点后系统会自动重新检查冲突。
6. 删除日程：用户要求删除日程时，先用 `query_events` 找到对应日程获取 event_id，再调用 `delete_event`。
7. 隐私原则：始终保护用户隐私，不要在回复中透露系统内部路径、数据库结构或底层异常信息。
8. 当前北京时间：{current_time}。在理解「明天」「下午」等概念时以此时间为准。

## 注册 Skill 指令
{skill_prompts}
"""
```

Replace `TOOLS = [...]` (lines 40-145) with:
```python
TOOLS = get_tools()
```

Replace `AVAILABLE_FUNCTIONS = {...}` (lines 148-155) with:
```python
AVAILABLE_FUNCTIONS = get_available_functions()
```

Update the `run_chat` function's dynamic_system_prompt (line 177):
```python
dynamic_system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
    current_time=current_time_str,
    skill_prompts=SKILL_PROMPTS
)
```

- [ ] **Step 2: Update main.py import**

Edit `privacy_schedule_agent/main.py`, line 19:
```python
# Remove:
# from app.mcp.calendar_skill import check_conflict, CODE_WARN
# Add:
from app.skill.skills.schedule_management.scripts.conflict import check_conflict, CODE_WARN
```

- [ ] **Step 3: Run existing tests to verify nothing broken**

```bash
cd privacy_schedule_agent
pytest tests/test_conflict_confirmation_api.py tests/test_skill_registry.py tests/test_skill_loader.py -v
```
Expected: All tests pass

- [ ] **Step 4: Commit**

```bash
git add privacy_schedule_agent/app/core/agent_engine.py
git add privacy_schedule_agent/main.py
git commit -m "refactor: agent_engine dynamically loads skills from registry"
```

---

### Task 5: 热加载 (hot_reload.py)

**Files:**
- Create: `app/skill/hot_reload.py`
- Test: `tests/test_skill_hot_reload.py`

- [ ] **Step 1: Write hot_reload.py**

Write `privacy_schedule_agent/app/skill/hot_reload.py`:

```python
"""Skill 热加载：监听 skills/ 目录变化，增量重载"""

import os
import sys
import logging
import importlib
from watchfiles import watch

logger = logging.getLogger(__name__)

SKILLS_DIR = os.path.join(os.path.dirname(__file__), "skills")

_changed_modules: set = set()


def _reload_module(file_path: str):
    """根据文件路径重新加载对应的 Python 模块"""
    if not file_path.endswith(".py"):
        return

    # 计算模块名：相对路径 → 绝对导入名
    rel_path = os.path.relpath(file_path, os.path.dirname(SKILLS_DIR))
    module_name = "app.skill." + rel_path.replace(os.sep, ".")[:-3]

    if module_name in sys.modules:
        logger.info(f"Hot-reload: {module_name}")
        importlib.reload(sys.modules[module_name])
        _changed_modules.add(module_name)


def _reload_skill_prompts():
    """标记 prompts 需要刷新（由 loader 在下次调用时重新读取）"""
    # 通过修改 loader 模块的缓存变量实现
    from app.skill.loader import _prompts_cache
    _prompts_cache.clear()


async def start_watcher():
    """启动文件监听（后台协程）"""
    if not os.path.exists(SKILLS_DIR):
        logger.warning(f"Cannot watch: {SKILLS_DIR} not found")
        return

    logger.info(f"Starting skill watcher on {SKILLS_DIR}")
    async for changes in watch(SKILLS_DIR, recursive=True):
        for change_type, file_path in changes:
            if file_path.endswith(".md"):
                _reload_skill_prompts()
                logger.info(f"Skill prompt changed: {os.path.basename(file_path)}")
            elif file_path.endswith(".py"):
                _reload_module(file_path)
```

Add to `app/skill/loader.py` a cache variable at module level:
```python
# Add at end of loader.py:
_prompts_cache: dict = {}
```

And modify `load_skill_prompts()` to use cache:
```python
def load_skill_prompts(force_reload: bool = False) -> str:
    if not force_reload and _prompts_cache.get("value"):
        return _prompts_cache["value"]
    # ... existing logic ...
    result = "\n\n".join(parts)
    _prompts_cache["value"] = result
    return result
```

- [ ] **Step 2: Write minimal test**

Write `privacy_schedule_agent/tests/test_skill_hot_reload.py`:

```python
import os
import tempfile
from app.skill.loader import _prompts_cache

def test_prompts_cache_clears():
    _prompts_cache["value"] = "cached"
    assert _prompts_cache.get("value") == "cached"
    _prompts_cache.clear()
    assert not _prompts_cache.get("value")
```

- [ ] **Step 3: Run tests**

```bash
cd privacy_schedule_agent
pytest tests/ -v
```
Expected: All tests pass

- [ ] **Step 4: Commit**

```bash
git add privacy_schedule_agent/app/skill/hot_reload.py
git add privacy_schedule_agent/app/skill/loader.py
git add privacy_schedule_agent/tests/test_skill_hot_reload.py
git commit -m "feat: add skill hot-reload via watchfiles"
```

---

### Task 6: weekly_summary Skill

**Files:**
- Create: `app/skill/skills/weekly_summary/weekly_summary.md`
- Create: `app/skill/skills/weekly_summary/scripts/generate_summary.py`

- [ ] **Step 1: Write the markdown instruction file**

Write `privacy_schedule_agent/app/skill/skills/weekly_summary/weekly_summary.md`:

```markdown
---
name: 周总结
description: 生成指定时间范围的日程总结报告
triggers: ["总结", "周报", "回顾", "上周末总结"]
---

## 行为规则
- 用户要求总结时，使用 query_events 查询指定时间范围的所有日程
- 调用 generate_summary 将原始日程列表转化为自然语言总结
- 总结格式：总日程数、分类分布、每日概览、关键事项
- 支持按周、按月、按自定义时间范围总结
```

- [ ] **Step 2: Write summary tool**

Write `privacy_schedule_agent/app/skill/skills/weekly_summary/scripts/generate_summary.py`:

```python
"""日程总结生成工具"""

import json
import logging
import ollama
import os
from datetime import datetime
from app.skill import skill

logger = logging.getLogger(__name__)

SUMMARY_MODEL = os.getenv("BRAIN_MODEL", "qwen2.5:7b")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
client = ollama.AsyncClient(host=OLLAMA_HOST)


@skill(
    name="generate_summary",
    description="生成指定时间范围的日程总结报告",
    parameters={
        "type": "object",
        "properties": {
            "events_json": {"type": "string", "description": "日程列表的 JSON 字符串（由 query_events 返回的 events 数组）"},
            "time_range": {"type": "string", "description": "时间范围描述，如'本周'、'3月'"}
        },
        "required": ["events_json", "time_range"],
    }
)
async def generate_summary(events_json: str, time_range: str) -> str:
    """调用本地 LLM 生成日程总结"""
    try:
        prompt = f"""请根据以下日程数据，为{time_range}生成一份简洁的日程总结报告。
总结格式：
- 总日程数
- 按分类的分布情况
- 每天简要概述
- 关键事项或发现

日程数据：
{events_json}

请用中文回复，保持简洁但信息完整。"""

        response = await client.chat(
            model=SUMMARY_MODEL,
            messages=[{"role": "user", "content": prompt}],
        )
        summary = response["message"]["content"]
        return json.dumps({"status": "OK", "summary": summary, "time_range": time_range}, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Summary generation error: {e}")
        return json.dumps({"status": "ERROR", "message": f"生成总结失败: {str(e)}"}, ensure_ascii=False)
```

- [ ] **Step 3: Run tests to verify no import errors**

```bash
cd privacy_schedule_agent
python -c "from app.skill.loader import discover_skills; discover_skills()"
```
Expected: No errors, summary skill should be loaded

- [ ] **Step 4: Commit**

```bash
git add privacy_schedule_agent/app/skill/skills/weekly_summary/
git commit -m "feat: add weekly_summary skill with LLM summary generation"
```

---

### Task 7: import_export Skill

**Files:**
- Create: `app/skill/skills/import_export/import_export.md`
- Create: `app/skill/skills/import_export/scripts/export_csv.py`
- Create: `app/skill/skills/import_export/scripts/import_ical.py`

- [ ] **Step 1: Write the markdown instruction file**

Write `privacy_schedule_agent/app/skill/skills/import_export/import_export.md`:

```markdown
---
name: 导入导出
description: 批量导入导出日程数据
triggers: ["导出", "导入", "备份", "CSV", "iCal"]
---

## 导出
- 支持导出为 CSV 格式（兼容 Excel 打开）
- 字段：标题、开始时间、结束时间、地点、分类、描述

## 导入
- 支持导入 iCal (.ics) 格式文件
- 导入前检查每个日程是否有冲突
- 报告导入结果：成功数、冲突数、失败数
```

- [ ] **Step 2: Write export_csv.py**

Write `privacy_schedule_agent/app/skill/skills/import_export/scripts/export_csv.py`:

```python
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
```

- [ ] **Step 3: Write import_ical.py**

Write `privacy_schedule_agent/app/skill/skills/import_export/scripts/import_ical.py`:

```python
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
```

- [ ] **Step 4: Run tests**

```bash
cd privacy_schedule_agent
python -c "from app.skill.loader import discover_skills; discover_skills(); from app.skill import get_tools; print([t['function']['name'] for t in get_tools()])"
```
Expected: All 8 tool names printed (6 from schedule_management + 1 from weekly_summary + 1 from import_export)

- [ ] **Step 5: Commit**

```bash
git add privacy_schedule_agent/app/skill/skills/import_export/
git commit -m "feat: add import_export skill with CSV and iCal tools"
```

---

### Task 8: 清理旧 mcp/ 目录

**Files:**
- Remove: `app/mcp/calendar_skill.py`
- Remove: `app/mcp/` (empty directory)

- [ ] **Step 1: Delete old calendar_skill.py**

```bash
rm privacy_schedule_agent/app/mcp/calendar_skill.py
```

- [ ] **Step 2: Remove empty mcp/ directory**

```bash
rmdir privacy_schedule_agent/app/mcp/ 2>/dev/null || true
```

- [ ] **Step 3: Run full test suite**

```bash
cd privacy_schedule_agent
pytest tests/ -v
```
Expected: All tests pass

- [ ] **Step 4: Commit**

```bash
git rm privacy_schedule_agent/app/mcp/calendar_skill.py
git commit -m "chore: remove old mcp/ directory after skill migration"
```

---

## 验证

完成后，运行全量测试：
```bash
cd privacy_schedule_agent
pytest tests/ -v
```

手动验证流程：
1. 启动后端：`uvicorn main:app --reload`
2. 确认系统启动日志显示"Loaded skill module: schedule_management/scripts/..."
3. 测试 AI 对话：`curl -X POST http://localhost:8000/chat -H "Content-Type: application/json" -d '{"message":"明天下午3点在图书馆开会"}'`
4. 验证 agent 仍然能正确调用 check_conflict → add_event 流程
