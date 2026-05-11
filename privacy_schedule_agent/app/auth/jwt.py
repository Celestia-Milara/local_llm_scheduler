"""JWT 生成与验证（cloud 模式用）"""

import os
import jwt as pyjwt
import logging
from datetime import datetime, timedelta, timezone
from fastapi import Request, HTTPException

logger = logging.getLogger(__name__)

JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-in-production")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 小时


def create_token(user_id: int, username: str) -> str:
    """生成 JWT access token"""
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "username": username,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return pyjwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def verify_token(token: str) -> dict | None:
    """验证 JWT token，返回 payload 或 None"""
    try:
        return pyjwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except pyjwt.ExpiredSignatureError:
        logger.warning("JWT token expired")
        return None
    except pyjwt.InvalidTokenError as e:
        logger.warning(f"Invalid JWT token: {e}")
        return None


async def get_user_id_from_request(request: Request) -> int:
    """从请求上下文获取 user_id（local 模式返回 1，cloud 模式从 JWT 解析）"""
    deploy_mode = os.getenv("DEPLOY_MODE", "local")
    if deploy_mode == "local":
        return 1

    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="缺少认证令牌")

    token = auth_header.removeprefix("Bearer ")
    payload = verify_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="无效或过期的令牌")

    return int(payload.get("sub", 0))
