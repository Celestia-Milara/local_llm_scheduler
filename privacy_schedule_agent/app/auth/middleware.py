"""条件认证中间件（按 DEPLOY_MODE 开关）"""

import os
import logging
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

# 不需要认证的路径（公开端点）
PUBLIC_PATHS = {
    "/api/auth/login",
    "/api/auth/register",
    "/health",
    "/docs",
    "/openapi.json",
}


class AuthMiddleware(BaseHTTPMiddleware):
    """JWT 认证中间件 — 仅在 cloud 模式启用"""

    async def dispatch(self, request: Request, call_next):
        deploy_mode = os.getenv("DEPLOY_MODE", "local")
        path = request.url.path

        # local 模式：完全跳过认证
        if deploy_mode == "local":
            return await call_next(request)

        # cloud 模式：公开路径放行
        if path in PUBLIC_PATHS or path.startswith(("/static", "/assets", "/")):
            return await call_next(request)

        # 其余路径需要 JWT
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            # API 端点返回 401，前端页面继续到登录页
            if path.startswith("/api/"):
                raise HTTPException(status_code=401, detail="缺少认证令牌")
            return await call_next(request)

        return await call_next(request)


def auth_condition_middleware(app):
    """按 DEPLOY_MODE 注册中间件"""
    app.add_middleware(AuthMiddleware)
    logger.info(f"Auth middleware registered (DEPLOY_MODE={os.getenv('DEPLOY_MODE', 'local')})")
