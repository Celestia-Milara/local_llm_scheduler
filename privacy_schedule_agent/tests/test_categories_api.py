import asyncio
import importlib
import gc
import os
import sqlite3
import sys
import tempfile
import unittest
import warnings
from pathlib import Path

from fastapi.testclient import TestClient


PROJECT_DIR = Path(__file__).resolve().parents[1]
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))


class CategoriesApiLocalTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._old_cwd = Path.cwd()
        cls._env_backup = {
            "DATABASE_URL": os.environ.get("DATABASE_URL"),
            "DEPLOY_MODE": os.environ.get("DEPLOY_MODE"),
        }
        cls.tmp_dir = tempfile.TemporaryDirectory()
        cls.db_file = Path(cls.tmp_dir.name) / "test_categories.db"
        os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{cls.db_file}"
        os.environ["DEPLOY_MODE"] = "local"

        os.chdir(PROJECT_DIR)
        for module_name in list(sys.modules.keys()):
            if module_name == "main" or module_name.startswith("app."):
                del sys.modules[module_name]

        main_module = importlib.import_module("main")
        importlib.reload(main_module)
        cls.client = TestClient(main_module.app)
        cls.client.__enter__()

        with sqlite3.connect(cls.db_file) as conn:
            conn.executescript(
                """
                INSERT INTO schedules (
                    user_id, title, start_time, end_time, location_ref, description,
                    category, status, privacy_level, recurrence_rule, recurrence_end,
                    is_archived, summary_id
                ) VALUES
                    (1, '工作日程', '2026-05-10 09:00:00', '2026-05-10 10:00:00', NULL, NULL, '工作', 'confirmed', 1, NULL, NULL, 0, NULL),
                    (1, '学习日程', '2026-05-10 11:00:00', '2026-05-10 12:00:00', NULL, NULL, '学习', 'confirmed', 1, NULL, NULL, 0, NULL),
                    (1, '未分类日程', '2026-05-11 09:00:00', '2026-05-11 10:00:00', NULL, NULL, NULL, 'confirmed', 1, NULL, NULL, 0, NULL),
                    (1, '未知分类日程', '2026-05-11 11:00:00', '2026-05-11 12:00:00', NULL, NULL, '个人', 'confirmed', 1, NULL, NULL, 0, NULL),
                    (1, '已归档生活日程', '2026-05-10 13:00:00', '2026-05-10 14:00:00', NULL, NULL, '生活', 'confirmed', 1, NULL, NULL, 1, NULL),
                    (2, '其他用户工作日程', '2026-05-10 15:00:00', '2026-05-10 16:00:00', NULL, NULL, '工作', 'confirmed', 1, NULL, NULL, 0, NULL);
                """
            )
            conn.commit()

    @classmethod
    def tearDownClass(cls):
        try:
            cls.client.__exit__(None, None, None)
            from app.db.database import engine

            asyncio.run(engine.dispose())
        finally:
            try:
                cls.tmp_dir.cleanup()
            except PermissionError as exc:
                warnings.warn(
                    f"Temporary directory cleanup failed for {cls.tmp_dir.name}: {exc}",
                    RuntimeWarning,
                    stacklevel=2,
                )
                gc.collect()
                try:
                    cls.tmp_dir.cleanup()
                except PermissionError:
                    raise
            finally:
                for key, value in cls._env_backup.items():
                    if value is None:
                        os.environ.pop(key, None)
                    else:
                        os.environ[key] = value
                os.chdir(cls._old_cwd)

    def test_get_categories_returns_exact_list(self):
        resp = self.client.get("/api/categories")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), {"categories": [
            {"key": "", "label": "全部", "color": "#818cf8"},
            {"key": "工作", "label": "工作", "color": "#fbbf24"},
            {"key": "学习", "label": "学习", "color": "#60a5fa"},
            {"key": "生活", "label": "生活", "color": "#f472b6"},
        ]})

    def test_get_categories_stats_returns_counts(self):
        resp = self.client.get(
            "/schedules/categories/stats",
            params={"start": "2026-05-10", "end": "2026-05-11", "user_id": 1},
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), {"counts": {"": 4, "工作": 1, "学习": 1, "生活": 0}})

    def test_get_categories_stats_missing_params_returns_400(self):
        resp = self.client.get("/schedules/categories/stats", params={"start": "2026-05-10"})
        self.assertEqual(resp.status_code, 400)


if __name__ == "__main__":
    unittest.main()
