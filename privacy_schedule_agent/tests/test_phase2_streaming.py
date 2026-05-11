"""Phase 2 测试：SSE 流式端点、对话持久化、统计接口"""

import importlib
import json
import os
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[1]
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))


class ChatStreamEndpointTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp_dir = tempfile.TemporaryDirectory()
        cls.db_file = Path(cls.tmp_dir.name) / "test_schedule.db"
        os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{cls.db_file}"

        for mod in list(sys.modules.keys()):
            if mod.startswith(("main", "app.")):
                del sys.modules[mod]

        from fastapi.testclient import TestClient
        main_module = importlib.import_module("main")
        importlib.reload(main_module)
        cls.client = TestClient(main_module.app)
        cls.client.__enter__()

    @classmethod
    def tearDownClass(cls):
        cls.client.__exit__(None, None, None)
        import asyncio
        from app.db.database import engine
        asyncio.run(engine.dispose())
        import gc
        gc.collect()
        try:
            cls.tmp_dir.cleanup()
        except PermissionError:
            import warnings
            warnings.warn(f"Cleanup of {cls.tmp_dir.name} deferred (file locked)")

    def setUp(self):
        with sqlite3.connect(self.db_file) as conn:
            for table in ["chat_messages", "chat_sessions", "schedules"]:
                conn.execute(f"DELETE FROM {table}")
            conn.commit()

    def test_chat_stream_returns_sse(self):
        """/chat/stream 应返回 text/event-stream 且包含 done 事件"""
        resp = self.client.post("/chat/stream", json={
            "message": "你好",
        })
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.headers.get("content-type", "").startswith("text/event-stream"), resp.headers.get("content-type"))

        body = resp.text
        # 应包含事件
        self.assertIn("event:", body)
        # 应最终有 done 事件
        self.assertIn("event: done", body)

    def test_chat_stream_event_format(self):
        """SSE 事件应包含 type 和 data 字段"""
        resp = self.client.post("/chat/stream", json={
            "message": "你好",
        })
        body = resp.text

        has_step_or_token = False
        for line in body.split("\n"):
            if line.startswith("event: step") or line.startswith("event: token"):
                has_step_or_token = True
                break
        # 至少有一个 step 或 token 事件（thinking 或最终回复）
        self.assertTrue(has_step_or_token, f"No step/token events found in:\n{body[:500]}")

    def test_chat_stream_saves_history(self):
        """对话后消息应持久化到 chat_messages 表"""
        self.client.post("/chat/stream", json={
            "message": "测试历史",
            "session_id": "test_session_001",
        })

        with sqlite3.connect(self.db_file) as conn:
            cur = conn.execute(
                "SELECT role, content FROM chat_messages WHERE session_id=? ORDER BY created_at",
                ("test_session_001",)
            )
            rows = cur.fetchall()

        # 应有 user 和 assistant 消息
        roles = [r[0] for r in rows]
        self.assertIn("user", roles)
        self.assertIn("assistant", roles)

    def test_chat_stream_custom_session(self):
        """指定 session_id 应创建对应会话"""
        sid = "my_custom_session"
        resp = self.client.post("/chat/stream", json={
            "message": "测试",
            "session_id": sid,
        })
        self.assertEqual(resp.status_code, 200)

        with sqlite3.connect(self.db_file) as conn:
            cur = conn.execute(
                "SELECT id FROM chat_sessions WHERE id=?", (sid,)
            )
            self.assertIsNotNone(cur.fetchone())


class StatisticsEndpointTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp_dir = tempfile.TemporaryDirectory()
        cls.db_file = Path(cls.tmp_dir.name) / "test_stats.db"
        os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{cls.db_file}"

        for mod in list(sys.modules.keys()):
            if mod.startswith(("main", "app.")):
                del sys.modules[mod]

        from fastapi.testclient import TestClient
        main_module = importlib.import_module("main")
        importlib.reload(main_module)
        cls.client = TestClient(main_module.app)
        cls.client.__enter__()

        # 插入测试数据（privacy_level 有默认值 1）
        with sqlite3.connect(cls.db_file) as conn:
            conn.executescript("""
                INSERT INTO schedules (title, start_time, end_time, category, user_id, status, privacy_level, is_archived)
                VALUES ('会议A', '2026-05-10 09:00:00', '2026-05-10 10:00:00', '工作', 1, 'confirmed', 1, 0);
                INSERT INTO schedules (title, start_time, end_time, category, user_id, status, privacy_level, is_archived)
                VALUES ('会议B', '2026-05-10 14:00:00', '2026-05-10 15:30:00', '工作', 1, 'confirmed', 1, 0);
                INSERT INTO schedules (title, start_time, end_time, category, user_id, status, privacy_level, is_archived)
                VALUES ('午餐',  '2026-05-11 12:00:00', '2026-05-11 13:00:00', '个人', 1, 'confirmed', 1, 0);
                INSERT INTO schedules (title, start_time, end_time, category, user_id, status, privacy_level, is_archived)
                VALUES ('健身',  '2026-05-11 18:00:00', '2026-05-11 19:00:00', '个人', 1, 'confirmed', 1, 0);
                INSERT INTO schedules (title, start_time, end_time, category, user_id, status, privacy_level, is_archived)
                VALUES ('其他用户', '2026-05-10 11:00:00', '2026-05-10 12:00:00', '工作', 2, 'confirmed', 1, 0);
            """)
            conn.commit()

    @classmethod
    def tearDownClass(cls):
        cls.client.__exit__(None, None, None)
        import asyncio
        from app.db.database import engine
        # 强制关闭所有连接
        asyncio.run(engine.dispose())
        import gc
        gc.collect()
        try:
            cls.tmp_dir.cleanup()
        except PermissionError:
            import warnings
            warnings.warn(f"Cleanup of {cls.tmp_dir.name} deferred (file locked)")
            # 在 Windows 上 SQLite 文件锁定是已知问题，忽略

    def test_statistics_summary_returns_counts(self):
        """统计接口应返回日程总数和分类分布"""
        resp = self.client.post("/api/statistics/summary", json={
            "start": "2026-05-10",
            "end": "2026-05-11",
            "user_id": 1,
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.json()

        self.assertEqual(data["total_events"], 4)  # 不含 user_id=2 的
        self.assertIn("category_distribution", data)
        self.assertEqual(data["category_distribution"]["工作"], 2)
        self.assertEqual(data["category_distribution"]["个人"], 2)

    def test_statistics_daily_distribution(self):
        """统计接口应返回每日分布"""
        resp = self.client.post("/api/statistics/summary", json={
            "start": "2026-05-10",
            "end": "2026-05-11",
            "user_id": 1,
        })
        data = resp.json()
        daily = data["daily_distribution"]
        days = {d["date"]: d["count"] for d in daily}
        self.assertEqual(days.get("2026-05-10"), 2)
        self.assertEqual(days.get("2026-05-11"), 2)

    def test_statistics_empty_range(self):
        """无日程的时间段应返回空统计"""
        resp = self.client.post("/api/statistics/summary", json={
            "start": "2025-01-01",
            "end": "2025-01-02",
            "user_id": 1,
        })
        data = resp.json()
        self.assertEqual(data["total_events"], 0)

    def test_statistics_invalid_date(self):
        """无效日期应返回 400"""
        resp = self.client.post("/api/statistics/summary", json={
            "start": "invalid",
            "end": "2026-05-11",
        })
        self.assertEqual(resp.status_code, 400)
