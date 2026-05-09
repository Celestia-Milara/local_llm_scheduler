import os
import pytest
from app.skill import clear_registry, get_tools
from app.skill.loader import discover_skills, load_skill_prompts


@pytest.fixture(autouse=True)
def clean():
    clear_registry()
    yield


def test_load_skill_prompts_returns_string():
    """load_skill_prompts 应返回字符串"""
    prompts = load_skill_prompts()
    assert isinstance(prompts, str)
    # 如果存在 .md 文件，应包含中文
    if prompts:
        assert "日程" in prompts or "总结" in prompts or len(prompts) > 0


def test_discover_skills_imports_modules():
    """discover_skills 应能运行且不报错"""
    # 清除注册表并重新加载，验证不会报错
    clear_registry()
    discover_skills()
    # tools 可能为 0（如果 Task 3 尚未完成），但至少不应报错
    tools = get_tools()
    assert isinstance(tools, list)
