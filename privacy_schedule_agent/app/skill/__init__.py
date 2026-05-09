"""Skill 注册表：@skill 装饰器 + 动态工具加载"""

from typing import Callable, Dict, Any, List
import json
import logging

logger = logging.getLogger(__name__)

_SKILL_REGISTRY: Dict[str, Dict[str, Any]] = {}


def skill(name: str, description: str, parameters: dict):
    """装饰器：将函数注册为 LLM 可调用的 Tool"""
    def decorator(func: Callable):
        _SKILL_REGISTRY[name] = {
            "function": func,
            "description": description,
            "parameters": parameters,
        }
        logger.debug(f"Registered skill: {name}")
        return func
    return decorator


def get_tools() -> List[dict]:
    """返回 LLM Function Calling 所需的 tools 列表"""
    return [
        {
            "type": "function",
            "function": {
                "name": name,
                "description": meta["description"],
                "parameters": meta["parameters"],
            }
        }
        for name, meta in _SKILL_REGISTRY.items()
    ]


def get_available_functions() -> Dict[str, Callable]:
    """返回 {name: function} 映射表"""
    return {
        name: meta["function"]
        for name, meta in _SKILL_REGISTRY.items()
    }


async def execute_tool(name: str, args: dict) -> str:
    """按名称执行 Skill（所有 Skill 函数均为 async），返回 JSON 字符串"""
    if name not in _SKILL_REGISTRY:
        return json.dumps({"status": "ERROR", "message": f"未知的工具名称: {name}"})
    func = _SKILL_REGISTRY[name]["function"]
    try:
        return await func(**args)
    except Exception as e:
        logger.exception(f"Error executing skill '{name}': {e}")
        return json.dumps({"status": "ERROR", "message": f"工具执行错误: {str(e)}"})


def clear_registry():
    """清空注册表（测试用）"""
    _SKILL_REGISTRY.clear()
