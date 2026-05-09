"""测试 @skill 装饰器与注册表"""

import copy
import pytest
from app.skill import skill, get_tools, get_available_functions, execute_tool, clear_registry
from app.skill import _SKILL_REGISTRY


@pytest.fixture(autouse=True)
def isolated_registry():
    """每个测试前后清理注册表，确保测试隔离"""
    clear_registry()
    yield
    clear_registry()


def test_register_and_get_tools():
    """注册一个函数后，get_tools() 应返回包含该工具定义的列表"""

    @skill("test_func", "A test function", {
        "type": "object",
        "properties": {"x": {"type": "string"}},
        "required": ["x"]
    })
    async def _test_func(x: str) -> str:
        return f"hello {x}"

    tools = get_tools()
    assert len(tools) == 1
    assert tools[0]["function"]["name"] == "test_func"


@pytest.mark.asyncio
async def test_execute_tool():
    """execute_tool 应正确调用已注册的 async 函数"""

    @skill("test_func", "A test function", {
        "type": "object",
        "properties": {"x": {"type": "string"}},
        "required": ["x"]
    })
    async def _test_func(x: str) -> str:
        return f"hello {x}"

    result = await execute_tool("test_func", {"x": "world"})
    assert result == "hello world"


@pytest.mark.asyncio
async def test_execute_unknown_tool():
    """未知工具名应返回 ERROR JSON"""
    result = await execute_tool("nonexistent", {})
    assert "ERROR" in result


@pytest.mark.asyncio
async def test_execute_tool_error_handling():
    """工具函数抛出异常时应返回 ERROR JSON"""

    @skill("broken_tool", "A tool that raises", {
        "type": "object",
        "properties": {},
        "required": []
    })
    async def _broken_tool() -> str:
        raise ValueError("something went wrong")

    result = await execute_tool("broken_tool", {})
    assert "ERROR" in result


@pytest.mark.asyncio
async def test_get_available_functions():
    """get_available_functions 应返回 name->function 映射"""

    @skill("test_func", "A test function", {
        "type": "object",
        "properties": {},
        "required": []
    })
    async def _test_func() -> str:
        return "ok"

    funcs = get_available_functions()
    assert "test_func" in funcs
    assert callable(funcs["test_func"])
