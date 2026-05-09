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

    rel_path = os.path.relpath(file_path, os.path.dirname(SKILLS_DIR))
    module_name = "app.skill." + rel_path.replace(os.sep, ".")[:-3]

    if module_name in sys.modules:
        logger.info(f"Hot-reload: {module_name}")
        importlib.reload(sys.modules[module_name])
        _changed_modules.add(module_name)


def _reload_skill_prompts():
    """标记 prompts 需要刷新"""
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
