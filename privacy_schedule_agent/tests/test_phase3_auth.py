"""Phase 3 测试：JWT 认证、加密、生命周期"""

import importlib
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[1]
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))


class JWTTest(unittest.TestCase):
    """JWT 单元测试（不需要数据库）"""

    def setUp(self):
        # 清除缓存确保用最新代码
        for mod in list(sys.modules.keys()):
            if mod.startswith("app.auth"):
                del sys.modules[mod]

    def test_create_and_verify_token(self):
        from app.auth.jwt import create_token, verify_token
        token = create_token(42, "testuser")
        self.assertIsInstance(token, str)
        self.assertGreater(len(token), 20)

        payload = verify_token(token)
        self.assertIsNotNone(payload)
        self.assertEqual(payload["sub"], "42")
        self.assertEqual(payload["username"], "testuser")

    def test_verify_invalid_token(self):
        from app.auth.jwt import verify_token
        payload = verify_token("invalid.token.here")
        self.assertIsNone(payload)

    def test_verify_empty_token(self):
        from app.auth.jwt import verify_token
        payload = verify_token("")
        self.assertIsNone(payload)


class CryptoTest(unittest.TestCase):
    """加解密单元测试"""

    def test_encrypt_decrypt_roundtrip(self):
        from app.core.crypto import encrypt_field, decrypt_field
        plain = "明天下午3点在图书馆开会"
        enc = encrypt_field(plain)
        self.assertIsNotNone(enc)
        # 加密后不应和原文相同
        self.assertNotEqual(enc, plain)
        dec = decrypt_field(enc)
        self.assertEqual(dec, plain)

    def test_encrypt_none(self):
        from app.core.crypto import encrypt_field
        self.assertIsNone(encrypt_field(None))
        self.assertEqual(encrypt_field(""), "")

    def test_encrypt_dict(self):
        from app.core.crypto import encrypt_dict, decrypt_dict
        data = {"title": "会议", "description": "重要会议", "location": "Room A"}
        encrypted = encrypt_dict(data, ["title", "description"])
        self.assertNotEqual(encrypted["title"], "会议")
        self.assertNotEqual(encrypted["description"], "重要会议")
        self.assertEqual(encrypted["location"], "Room A")  # 不在加密列表中

        decrypted = decrypt_dict(encrypted, ["title", "description"])
        self.assertEqual(decrypted["title"], "会议")
        self.assertEqual(decrypted["description"], "重要会议")

    def test_decrypt_invalid(self):
        from app.core.crypto import decrypt_field
        # 无效密文应原样返回
        result = decrypt_field("not-valid-ciphertext")
        self.assertEqual(result, "not-valid-ciphertext")


class EncryptionIntegrationTest(unittest.TestCase):
    """加密集成测试：验证 API 端点的加密/解密行为"""

    @classmethod
    def setUpClass(cls):
        cls.tmp_dir = tempfile.TemporaryDirectory()
        cls.db_file = Path(cls.tmp_dir.name) / "test_crypto_integration.db"
        os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{cls.db_file}"
        os.environ["ENCRYPTION_KEY"] = "test-integration-key-for-encryption-testing"
        os.environ["DEPLOY_MODE"] = "local"

        for mod in list(sys.modules.keys()):
            if mod.startswith(("main", "app.")):
                del sys.modules[mod]

        from fastapi.testclient import TestClient
        import main as main_module
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
        os.environ.pop("ENCRYPTION_KEY", None)
        try:
            cls.tmp_dir.cleanup()
        except PermissionError:
            pass

    def test_create_encrypts_in_db(self):
        """创建日程后，数据库中 title/description 应为密文"""
        resp = self.client.post("/schedules", json={
            "title": "秘密会议",
            "start_time": "2026-06-01 10:00:00",
            "end_time": "2026-06-01 11:00:00",
            "location": "会议室A",
            "description": "关于隐私保护方案的讨论",
            "privacy_level": 3,
        })
        self.assertEqual(resp.status_code, 200)
        event_id = resp.json()["id"]

        # 直接查数据库验证密文
        import sqlite3
        conn = sqlite3.connect(self.db_file)
        cur = conn.execute("SELECT title, description FROM schedules WHERE id = ?", (event_id,))
        row = cur.fetchone()
        conn.close()

        self.assertIsNotNone(row)
        db_title, db_desc = row
        # 数据库中的值应和原文不同（已加密）
        self.assertNotEqual(db_title, "秘密会议")
        self.assertNotEqual(db_desc, "关于隐私保护方案的讨论")
        # 密文应为 Fernet 格式（base64 + 签名）
        self.assertIn("==", db_title if db_title else "")

    def test_get_returns_decrypted(self):
        """GET /schedules 应返回解密后的明文"""
        self.client.post("/schedules", json={
            "title": "公开日程",
            "start_time": "2026-06-02 14:00:00",
            "end_time": "2026-06-02 15:00:00",
            "location": "食堂",
            "description": "部门聚餐",
            "privacy_level": 1,
        })
        resp = self.client.get("/schedules")
        self.assertEqual(resp.status_code, 200)
        events = resp.json()
        target = next(e for e in events if e["title"] == "公开日程")
        self.assertEqual(target["description"], "部门聚餐")

    def test_get_single_returns_decrypted(self):
        """GET /schedules/{id} 应返回解密后的明文"""
        resp = self.client.post("/schedules", json={
            "title": "个人学习",
            "start_time": "2026-06-03 09:00:00",
            "end_time": "2026-06-03 10:00:00",
            "location": "图书馆",
            "description": "复习期末考试",
        })
        event_id = resp.json()["id"]
        resp = self.client.get(f"/schedules/{event_id}")
        data = resp.json()
        self.assertEqual(data["title"], "个人学习")
        self.assertEqual(data["description"], "复习期末考试")

    def test_privacy_level_crud(self):
        """验证 privacy_level 的创建、读取和更新"""
        # 创建带 privacy_level 的日程
        resp = self.client.post("/schedules", json={
            "title": "绝密项目",
            "start_time": "2026-06-10 10:00:00",
            "end_time": "2026-06-10 12:00:00",
            "location": "办公室",
            "privacy_level": 3,
        })
        self.assertEqual(resp.status_code, 200)
        event_id = resp.json()["id"]

        # 读取时包含 privacy_level
        resp = self.client.get(f"/schedules/{event_id}")
        self.assertEqual(resp.json()["privacy_level"], 3)

        # 更新 privacy_level
        resp = self.client.put(f"/schedules/{event_id}", json={
            "privacy_level": 2,
            "confirm_conflict": True,
        })
        self.assertEqual(resp.status_code, 200)

        # 确认已更新
        resp = self.client.get(f"/schedules/{event_id}")
        self.assertEqual(resp.json()["privacy_level"], 2)


class AuthEndpointTest(unittest.TestCase):
    """认证端点集成测试"""

    @classmethod
    def setUpClass(cls):
        cls.tmp_dir = tempfile.TemporaryDirectory()
        cls.db_file = Path(cls.tmp_dir.name) / "test_auth.db"
        os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{cls.db_file}"
        os.environ["DEPLOY_MODE"] = "cloud"  # 启用 cloud 模式

        for mod in list(sys.modules.keys()):
            if mod.startswith(("main", "app.")):
                del sys.modules[mod]

        from fastapi.testclient import TestClient
        import main as main_module
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
            pass

    def test_register(self):
        resp = self.client.post("/api/auth/register", json={
            "username": "newuser",
            "password": "pass123",
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("token", data)
        self.assertEqual(data["user"]["username"], "newuser")

    def test_register_duplicate(self):
        self.client.post("/api/auth/register", json={
            "username": "dupuser",
            "password": "pass123",
        })
        resp = self.client.post("/api/auth/register", json={
            "username": "dupuser",
            "password": "pass456",
        })
        self.assertEqual(resp.status_code, 409)

    def test_login(self):
        self.client.post("/api/auth/register", json={
            "username": "logintest",
            "password": "mypassword",
        })
        resp = self.client.post("/api/auth/login", json={
            "username": "logintest",
            "password": "mypassword",
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("token", data)

    def test_login_wrong_password(self):
        resp = self.client.post("/api/auth/login", json={
            "username": "logintest",
            "password": "wrongpass",
        })
        self.assertEqual(resp.status_code, 401)

    def test_auth_me(self):
        reg = self.client.post("/api/auth/register", json={
            "username": "meuser",
            "password": "pass123",
        })
        token = reg.json()["token"]

        resp = self.client.get("/api/auth/me", headers={
            "Authorization": f"Bearer {token}"
        })
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["username"], "meuser")

    def test_auth_me_no_token(self):
        resp = self.client.get("/api/auth/me")
        # cloud 模式下未认证返回 401
        self.assertEqual(resp.status_code, 401)


class LifecycleTest(unittest.TestCase):
    """数据生命周期测试"""

    @classmethod
    def setUpClass(cls):
        cls.tmp_dir = tempfile.TemporaryDirectory()
        cls.db_file = Path(cls.tmp_dir.name) / "test_lifecycle.db"
        os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{cls.db_file}"
        os.environ["DEPLOY_MODE"] = "local"

        for mod in list(sys.modules.keys()):
            if mod.startswith(("main", "app.")):
                del sys.modules[mod]

        import asyncio
        from app.db.database import init_db, AsyncSessionLocal
        from app.db.models import Schedule
        asyncio.run(init_db())

        # 插入过期和未过期日程
        async def seed():
            from datetime import datetime
            async with AsyncSessionLocal() as session:
                # 60 天前的（已过期）
                session.add(Schedule(
                    title="旧会议", user_id=1,
                    start_time=datetime(2026, 3, 1, 10, 0),
                    end_time=datetime(2026, 3, 1, 11, 0),
                    category="工作", is_archived=0,
                ))
                # 5 天前的（未过期）
                session.add(Schedule(
                    title="新会议", user_id=1,
                    start_time=datetime(2026, 5, 5, 10, 0),
                    end_time=datetime(2026, 5, 5, 11, 0),
                    category="工作", is_archived=0,
                ))
                await session.commit()
        asyncio.run(seed())

        cls.db_session = AsyncSessionLocal

    @classmethod
    def tearDownClass(cls):
        import asyncio
        from app.db.database import engine
        asyncio.run(engine.dispose())
        import gc
        gc.collect()
        try:
            cls.tmp_dir.cleanup()
        except PermissionError:
            pass

    def test_archive_old_schedules(self):
        import asyncio
        from app.db.lifecycle import archive_old_schedules

        archived = asyncio.run(archive_old_schedules())
        self.assertGreater(archived, 0)

    def test_archived_schedules_marked(self):
        import asyncio
        from sqlalchemy import select
        from app.db.models import Schedule

        async def check():
            async with self.db_session() as session:
                result = await session.execute(
                    select(Schedule).where(Schedule.is_archived == 1)
                )
                return result.scalars().all()
        archived = asyncio.run(check())
        self.assertGreater(len(archived), 0)
        # 旧会议应被归档
        titles = [e.title for e in archived]
        self.assertIn("旧会议", titles)
