import importlib
import asyncio
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


class ConflictConfirmationApiTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp_dir = tempfile.TemporaryDirectory()
        cls.db_file = Path(cls.tmp_dir.name) / "test_schedule.db"
        os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{cls.db_file}"

        for module_name in ["main", "app.db.models", "app.db.database"]:
            if module_name in sys.modules:
                del sys.modules[module_name]

        main_module = importlib.import_module("main")
        importlib.reload(main_module)
        cls.client = TestClient(main_module.app)
        cls.client.__enter__()

    @classmethod
    def tearDownClass(cls):
        cls.client.__exit__(None, None, None)
        from app.db.database import engine
        asyncio.run(engine.dispose())
        cls.tmp_dir.cleanup()

    def setUp(self):
        with sqlite3.connect(self.db_file) as conn:
            conn.execute("DELETE FROM schedules")
            conn.commit()

    def test_create_requires_explicit_conflict_confirmation(self):
        first = {
            "title": "原有会议",
            "start_time": "2026-05-10 10:00:00",
            "end_time": "2026-05-10 11:00:00",
            "location": "图书馆",
        }
        r1 = self.client.post("/schedules", json=first)
        self.assertEqual(r1.status_code, 200)

        conflict = {
            "title": "冲突会议",
            "start_time": "2026-05-10 10:30:00",
            "end_time": "2026-05-10 11:30:00",
            "location": "实验楼",
        }
        r2 = self.client.post("/schedules", json=conflict)
        self.assertEqual(r2.status_code, 409)
        body = r2.json()
        self.assertEqual(body["status"], "conflict_requires_confirmation")
        self.assertTrue(body["conflicts"])

        conflict["confirm_conflict"] = True
        r3 = self.client.post("/schedules", json=conflict)
        self.assertEqual(r3.status_code, 200)
        self.assertEqual(r3.json()["status"], "conflicted")

    def test_update_requires_explicit_conflict_confirmation(self):
        morning = self.client.post(
            "/schedules",
            json={
                "title": "晨会",
                "start_time": "2026-05-11 09:00:00",
                "end_time": "2026-05-11 10:00:00",
                "location": "图书馆",
            },
        )
        self.assertEqual(morning.status_code, 200)

        noon = self.client.post(
            "/schedules",
            json={
                "title": "午会",
                "start_time": "2026-05-11 12:00:00",
                "end_time": "2026-05-11 13:00:00",
                "location": "实验楼",
            },
        )
        self.assertEqual(noon.status_code, 200)
        noon_id = noon.json()["id"]

        r1 = self.client.put(
            f"/schedules/{noon_id}",
            json={
                "start_time": "2026-05-11 09:30:00",
                "end_time": "2026-05-11 10:30:00",
                "location": "实验楼",
            },
        )
        self.assertEqual(r1.status_code, 409)
        self.assertEqual(r1.json()["status"], "conflict_requires_confirmation")

        r2 = self.client.put(
            f"/schedules/{noon_id}",
            json={
                "start_time": "2026-05-11 09:30:00",
                "end_time": "2026-05-11 10:30:00",
                "location": "实验楼",
                "confirm_conflict": True,
            },
        )
        self.assertEqual(r2.status_code, 200)
        self.assertEqual(r2.json()["status"], "conflicted")


if __name__ == "__main__":
    unittest.main()
