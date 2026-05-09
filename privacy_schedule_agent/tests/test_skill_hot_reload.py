import os
from app.skill.loader import _prompts_cache


def test_prompts_cache_clears():
    _prompts_cache["value"] = "cached"
    assert _prompts_cache.get("value") == "cached"
    _prompts_cache.clear()
    assert not _prompts_cache.get("value")


def test_prompts_cache_empty_initially():
    """确保测试不会污染 cache"""
    orig = _prompts_cache.get("value")
    _prompts_cache.clear()
    assert not _prompts_cache.get("value")
    if orig is not None:
        _prompts_cache["value"] = orig
