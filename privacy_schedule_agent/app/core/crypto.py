"""应用层加解密工具（Fernet 对称加密）"""

import os
import base64
import logging
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)

# 从环境变量读取密钥，不存在则自动生成
_ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", "")

# 受保护字段列表
PROTECTED_FIELDS = ["title", "description"]

_cipher: Fernet | None = None


def _get_cipher() -> Fernet | None:
    """获取加密器。未配置密钥时返回 None（跳过加密）"""
    global _cipher
    if _cipher is not None:
        return _cipher

    raw_key = _ENCRYPTION_KEY.strip()
    if not raw_key:
        # local 模式：生成会话级密钥（进程重启后无法解密，适合纯本地）
        _cipher = Fernet(Fernet.generate_key())
        logger.info("No ENCRYPTION_KEY set, using ephemeral session key")
        return _cipher

    # 兼容 32 bytes 原始密钥或 base64 编码的 Fernet key
    try:
        if len(raw_key) == 44 and raw_key.endswith("="):
            # 已经是 Fernet key 格式
            _cipher = Fernet(raw_key.encode())
        else:
            # 用 PBKDF2 派生为 32 bytes
            kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=b"schedule-prj", iterations=100000)
            key = base64.urlsafe_b64encode(kdf.derive(raw_key.encode()))
            _cipher = Fernet(key)
        logger.info("Encryption initialized with configured key")
    except Exception as e:
        logger.error(f"Failed to initialize cipher: {e}")
        _cipher = None

    return _cipher


def encrypt_field(plaintext: str | None) -> str | None:
    """加密单字段，None/空字符串 原样返回"""
    if not plaintext:
        return plaintext
    cipher = _get_cipher()
    if cipher is None:
        return plaintext
    return cipher.encrypt(plaintext.encode()).decode()


def decrypt_field(ciphertext: str | None) -> str | None:
    """解密单字段"""
    if not ciphertext:
        return ciphertext
    cipher = _get_cipher()
    if cipher is None:
        return ciphertext
    try:
        return cipher.decrypt(ciphertext.encode()).decode()
    except Exception:
        logger.warning("Decryption failed, returning raw value")
        return ciphertext


def encrypt_dict(data: dict, fields: list[str] | None = None) -> dict:
    """加密字典中的指定字段，原地修改"""
    targets = fields or PROTECTED_FIELDS
    for field in targets:
        if field in data and data[field] is not None:
            data[field] = encrypt_field(str(data[field]))
    return data


def decrypt_dict(data: dict, fields: list[str] | None = None) -> dict:
    """解密字典中的指定字段"""
    targets = fields or PROTECTED_FIELDS
    for field in targets:
        if field in data and data[field] is not None:
            data[field] = decrypt_field(str(data[field]))
    return data
