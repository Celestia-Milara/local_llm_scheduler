# Category API Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 新增两个后端端点 `GET /api/categories` 与 `GET /schedules/categories/stats`，并在 local/cloud 两种部署模式下满足固定分类配置、按时间范围统计、cloud 强制 JWT 的需求。

**Architecture:** 复用现有 FastAPI 单文件路由风格（`privacy_schedule_agent/main.py`）。统计端点直接查询 `schedules` 表并在应用层聚合计数；cloud 模式下通过 `app.auth.jwt.get_user_id_from_request()` 在端点内显式校验 JWT。

**Tech Stack:** FastAPI、SQLAlchemy Async（aiosqlite）、pytest（运行 unittest 风格用例）、SQLite。

---

## 0. 代码结构与改动面

**将修改/新增的文件：**
- Modify: `privacy_schedule_agent\main.py`（在导出接口附近新增 2 个路由 + 少量常量/日期解析 helper）
- Create: `privacy_schedule_agent\tests\test_categories_api.py`（新增端点的 local 行为与 cloud 鉴权测试）

**为什么不新建 service 层：**本仓库的 API 路由集中在 `main.py`，本计划遵循既有模式，避免引入与本需求无关的重构。

**重要注意：**当前 `AuthMiddleware` 不保证能覆盖所有路径的 JWT 校验（已有端点 `GET /api/auth/me` 也是在 handler 内部调用 `get_user_id_from_request()` 来强制鉴权）。因此本需求的两条新端点必须在 handler 内显式调用 `get_user_id_from_request()`（cloud 模式）。

---

### Task 1: 新增 local 模式的失败测试（TDD 起步）

**Files:**
- Create: `privacy_schedule_agent\tests\test_categories_api.py`

- [ ] **Step 1: 写入 local 模式测试（此时应失败：404 或断言失败）**

在 `privacy_schedule_agent\tests\test_categories_api.py` 写入以下完整内容：

```python
import importlib
import os
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient


PROJECT_DIR = Path(__file__).resolve().parents[1]
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))


class CategoriesApiLocalTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp_dir = tempfile.TemporaryDirectory()
        cls.db_file = Path(cls.tmp_dir.name) / "test_categories_local.db"
        os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{cls.db_file}"
        os.environ["DEPLOY_MODE"] = "local"

        # 清理模块缓存，确保读取最新环境变量与路由
        for mod in list(sys.modules.keys()):
            if mod.startswith(("main", "app.")):
                del sys.modules[mod]

        main_module = importlib.import_module("main")
        importlib.reload(main_module)
        cls.client = TestClient(main_module.app)
        cls.client.__enter__()

        # 插入测试数据（表由 app lifespan/init_db 创建）
        with sqlite3.connect(cls.db_file) as conn:
            conn.executescript(
                """
                DELETE FROM schedules;

                INSERT INTO schedules (title, start_time, end_time, category, user_id, status, privacy_level, is_archived)
                VALUES ('A-工作', '2026-05-10 09:00:00', '2026-05-10 10:00:00', '工作', 1, 'confirmed', 1, 0);

                INSERT INTO schedules (title, start_time, end_time, category, user_id, status, privacy_level, is_archived)
                VALUES ('B-学习', '2026-05-10 11:00:00', '2026-05-10 12:00:00', '学习', 1, 'confirmed', 1, 0);

                -- 未分类（category NULL）：应计入总数 counts[""]，不单列
                INSERT INTO schedules (title, start_time, end_time, category, user_id, status, privacy_level, is_archived)
                VALUES ('C-未分类', '2026-05-11 09:00:00', '2026-05-11 10:00:00', NULL, 1, 'confirmed', 1, 0);

                -- 未知分类：应计入总数 counts[""]，不单列
                INSERT INTO schedules (title, start_time, end_time, category, user_id, status, privacy_level, is_archived)
                VALUES ('D-未知分类', '2026-05-11 11:00:00', '2026-05-11 12:00:00', '个人', 1, 'confirmed', 1, 0);

                -- 已归档：默认不计入统计
                INSERT INTO schedules (title, start_time, end_time, category, user_id, status, privacy_level, is_archived)
                VALUES ('E-生活-已归档', '2026-05-10 13:00:00', '2026-05-10 14:00:00', '生活', 1, 'confirmed', 1, 1);

                -- 其他用户：不计入 user_id=1 的统计
                INSERT INTO schedules (title, start_time, end_time, category, user_id, status, privacy_level, is_archived)
                VALUES ('F-其他用户-工作', '2026-05-10 15:00:00', '2026-05-10 16:00:00', '工作', 2, 'confirmed', 1, 0);
                """
            )
            conn.commit()

    @classmethod
    def tearDownClass(cls):
        cls.client.__exit__(None, None, None)
        import asyncio
        from app.db.database import engine
        asyncio.run(engine.dispose())
        try:
            cls.tmp_dir.cleanup()
        except PermissionError:
            pass

    def test_get_categories_returns_fixed_config(self):
        resp = self.client.get("/api/categories")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("categories", data)
        self.assertEqual(
            data["categories"],
            [
                {"key": "", "label": "全部", "color": "#818cf8"},
                {"key": "工作", "label": "工作", "color": "#fbbf24"},
                {"key": "学习", "label": "学习", "color": "#60a5fa"},
                {"key": "生活", "label": "生活", "color": "#f472b6"},
            ],
        )

    def test_get_category_stats_counts_expected(self):
        resp = self.client.get(
            "/schedules/categories/stats",
            params={"start": "2026-05-10", "end": "2026-05-11", "user_id": 1},
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(
            data["counts"],
            {"": 4, "工作": 1, "学习": 1, "生活": 0},
        )

    def test_get_category_stats_missing_params_400(self):
        resp = self.client.get("/schedules/categories/stats", params={"start": "2026-05-10"})
        self.assertEqual(resp.status_code, 400)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 运行测试，确认失败**

Run（在仓库根目录）：

```powershell
cd privacy_schedule_agent
pytest -q tests\test_categories_api.py::CategoriesApiLocalTest
```

Expected：FAIL（在实现前通常是 404 Not Found 或断言不成立）。

- [ ] **Step 3: 提交仅测试文件**

```powershell
git add privacy_schedule_agent\tests\test_categories_api.py
git commit -m "test: add category endpoints contract tests" -m "Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

---

### Task 2: 在 main.py 实现两个端点（让 local 测试通过）

**Files:**
- Modify: `privacy_schedule_agent\main.py`（建议插入在 `GET /schedules/export/json` 之后、`StatsQuery` 之前，约 `main.py:533-538` 位置附近）

- [ ] **Step 1: 在 main.py 添加固定分类配置常量**

在 `privacy_schedule_agent\main.py` 中（靠近路由区域，便于复用）添加：

```python
CATEGORY_CONFIG = [
    {"key": "", "label": "全部", "color": "#818cf8"},
    {"key": "工作", "label": "工作", "color": "#fbbf24"},
    {"key": "学习", "label": "学习", "color": "#60a5fa"},
    {"key": "生活", "label": "生活", "color": "#f472b6"},
]

CATEGORY_KEYS = ["工作", "学习", "生活"]
```

- [ ] **Step 2: 添加日期解析 helper（严格校验，符合 spec）**

在 `main.py` 同一位置添加：

```python
def _parse_date_or_datetime(value: str, *, is_end: bool, param_name: str) -> datetime:
    if not value:
        raise HTTPException(status_code=400, detail=f"缺少参数: {param_name}")

    # 1) 完整时间
    try:
        return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        pass

    # 2) 仅日期
    try:
        d = datetime.strptime(value, "%Y-%m-%d")
        if is_end:
            return d.replace(hour=23, minute=59, second=59)
        return d.replace(hour=0, minute=0, second=0)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"{param_name} 格式应为 YYYY-MM-DD 或 YYYY-MM-DD HH:MM:SS")
```

- [ ] **Step 3: 实现 `GET /api/categories`**

在 `main.py` 中加入：

```python
@app.get("/api/categories")
async def get_categories(request: Request):
    # local 模式会返回 1；cloud 模式会校验 JWT
    await get_user_id_from_request(request)
    return {"categories": CATEGORY_CONFIG}
```

- [ ] **Step 4: 实现 `GET /schedules/categories/stats`（local 允许 query user_id，cloud 从 JWT 获取）**

在 `main.py` 中加入：

```python
@app.get("/schedules/categories/stats")
async def get_category_stats(
    request: Request,
    start: str = None,
    end: str = None,
    user_id: int = 1,
):
    deploy_mode = os.getenv("DEPLOY_MODE", "local")

    if deploy_mode == "cloud":
        effective_user_id = await get_user_id_from_request(request)
    else:
        effective_user_id = user_id or 1

    dt_start = _parse_date_or_datetime(start, is_end=False, param_name="start")
    dt_end = _parse_date_or_datetime(end, is_end=True, param_name="end")

    async with AsyncSessionLocal() as session:
        stmt = (
            select(Schedule.category)
            .where(Schedule.user_id == effective_user_id)
            .where(Schedule.is_archived == 0)
            .where(Schedule.start_time >= dt_start)
            .where(Schedule.end_time <= dt_end)
        )
        result = await session.execute(stmt)
        categories = result.scalars().all()

    counts = {"": len(categories), "工作": 0, "学习": 0, "生活": 0}
    for cat in categories:
        if cat in CATEGORY_KEYS:
            counts[cat] += 1

    return {"counts": counts}
```

- [ ] **Step 5: 运行 local 测试，确认通过**

```powershell
cd privacy_schedule_agent
pytest -q tests\test_categories_api.py::CategoriesApiLocalTest
```

Expected：PASS。

- [ ] **Step 6: 提交实现**

```powershell
git add privacy_schedule_agent\main.py
git commit -m "feat: add category config and stats endpoints" -m "Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

---

### Task 3: 新增 cloud 鉴权测试（确保 401/忽略 query user_id）

**Files:**
- Modify: `privacy_schedule_agent\tests\test_categories_api.py`

- [ ] **Step 1: 追加 cloud 测试类（先失败/再通过）**

在同一文件底部 `CategoriesApiLocalTest` 之后追加：

```python
class CategoriesApiCloudAuthTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp_dir = tempfile.TemporaryDirectory()
        cls.db_file = Path(cls.tmp_dir.name) / "test_categories_cloud.db"
        os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{cls.db_file}"
        os.environ["DEPLOY_MODE"] = "cloud"

        for mod in list(sys.modules.keys()):
            if mod.startswith(("main", "app.")):
                del sys.modules[mod]

        main_module = importlib.import_module("main")
        importlib.reload(main_module)
        cls.client = TestClient(main_module.app)
        cls.client.__enter__()

        # 构造 token（不要求用户必须存在于 users 表，因为 get_user_id_from_request 只校验签名与 exp）
        from app.auth.jwt import create_token
        cls.token_user42 = create_token(42, "user42")

        with sqlite3.connect(cls.db_file) as conn:
            conn.executescript(
                """
                DELETE FROM schedules;

                INSERT INTO schedules (title, start_time, end_time, category, user_id, status, privacy_level, is_archived)
                VALUES ('U42-工作', '2026-05-10 09:00:00', '2026-05-10 10:00:00', '工作', 42, 'confirmed', 1, 0);

                INSERT INTO schedules (title, start_time, end_time, category, user_id, status, privacy_level, is_archived)
                VALUES ('U1-学习', '2026-05-10 11:00:00', '2026-05-10 12:00:00', '学习', 1, 'confirmed', 1, 0);
                """
            )
            conn.commit()

    @classmethod
    def tearDownClass(cls):
        cls.client.__exit__(None, None, None)
        import asyncio
        from app.db.database import engine
        asyncio.run(engine.dispose())
        try:
            cls.tmp_dir.cleanup()
        except PermissionError:
            pass

    def test_cloud_requires_token_for_categories(self):
        r = self.client.get("/api/categories")
        self.assertEqual(r.status_code, 401)

    def test_cloud_requires_token_for_stats(self):
        r = self.client.get(
            "/schedules/categories/stats",
            params={"start": "2026-05-10", "end": "2026-05-10", "user_id": 1},
        )
        self.assertEqual(r.status_code, 401)

    def test_cloud_stats_uses_user_id_from_jwt(self):
        r = self.client.get(
            "/schedules/categories/stats",
            params={"start": "2026-05-10", "end": "2026-05-10", "user_id": 1},
            headers={"Authorization": f"Bearer {self.token_user42}"},
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["counts"], {"": 1, "工作": 1, "学习": 0, "生活": 0})

    def test_cloud_categories_ok_with_token(self):
        r = self.client.get(
            "/api/categories",
            headers={"Authorization": f"Bearer {self.token_user42}"},
        )
        self.assertEqual(r.status_code, 200)
```

- [ ] **Step 2: 运行 cloud 测试**

```powershell
cd privacy_schedule_agent
pytest -q tests\test_categories_api.py::CategoriesApiCloudAuthTest
```

Expected：PASS。

- [ ] **Step 3: 提交测试更新**

```powershell
git add privacy_schedule_agent\tests\test_categories_api.py
git commit -m "test: cover category endpoints auth in cloud mode" -m "Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

---

### Task 4: 回归验证（全量测试）

**Files:**
- Test: `privacy_schedule_agent\tests\*`

- [ ] **Step 1: 跑后端全量测试**

```powershell
cd privacy_schedule_agent
pytest
```

Expected：PASS。

- [ ] **Step 2: （可选）跑前端工具测试（与本改动无直接依赖，但便于回归）**

```powershell
cd privacy_schedule_agent\frontend
node --test tests\calendar.test.js
```

Expected：PASS。

---

## 计划自检（写完就做）

- 覆盖 spec：
  - `GET /api/categories` 固定配置 ✅（Task 1/2）
  - `GET /schedules/categories/stats` 按时间范围统计、is_archived=0、未分类/未知分类仅计入总数 ✅（Task 1/2）
  - cloud 模式强制 JWT，stats 使用 JWT user_id ✅（Task 3/2）

- 占位符扫描：计划中无 TBD/TODO/“自行处理”等模糊描述 ✅
