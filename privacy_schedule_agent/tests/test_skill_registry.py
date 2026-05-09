import pytest
from app.skill import skill, get_tools, get_available_functions, execute_tool, clear_registry


@pytest.fixture(autouse=True, scope="module")
def clean_registry():
    yield
    clear_registry()


@skill("test_func", "A test function", {
    "type": "object",
    "properties": {"x": {"type": "string"}},
    "required": ["x"]
})
async def my_test_func(x: str) -> str:
    return f"hello {x}"


@pytest.mark.asyncio
async def test_register_and_get_tools():
    tools = get_tools()
    assert len(tools) == 1
    assert tools[0]["function"]["name"] == "test_func"


@pytest.mark.asyncio
async def test_execute_tool():
    result = await execute_tool("test_func", {"x": "world"})
    assert result == "hello world"


@pytest.mark.asyncio
async def test_execute_unknown_tool():
    result = await execute_tool("nonexistent", {})
    assert "ERROR" in result
