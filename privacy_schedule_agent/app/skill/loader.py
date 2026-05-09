"""Skill 加载器：扫描 skills/ 目录，加载 .md 指令和 scripts/ 工具"""

import os
import re
import logging
import importlib.util

logger = logging.getLogger(__name__)

SKILLS_DIR = os.path.join(os.path.dirname(__file__), "skills")

_prompts_cache: dict = {}


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


def load_skill_prompts(force_reload: bool = False) -> str:
    """读取所有 Skill 的 .md 文件，拼接为系统提示词片段"""
    if not force_reload and _prompts_cache.get("value"):
        return _prompts_cache["value"]

    if not os.path.exists(SKILLS_DIR):
        return ""

    parts = []
    for skill_name in sorted(os.listdir(SKILLS_DIR)):
        skill_dir = os.path.join(SKILLS_DIR, skill_name)
        if not os.path.isdir(skill_dir) or skill_name.startswith("_"):
            continue

        for fname in sorted(os.listdir(skill_dir)):
            if not fname.endswith(".md"):
                continue
            md_path = os.path.join(skill_dir, fname)
            try:
                with open(md_path, "r", encoding="utf-8") as f:
                    content = f.read()
                body = content
                if content.startswith("---"):
                    match = re.match(r"^---\s*\n(.*?\n)---\s*\n(.*)", content, re.DOTALL)
                    if match:
                        body = match.group(2).strip()
                parts.append(body)
            except Exception as e:
                logger.error(f"Error reading {md_path}: {e}")

    result = "\n\n".join(parts)
    _prompts_cache["value"] = result
    return result
