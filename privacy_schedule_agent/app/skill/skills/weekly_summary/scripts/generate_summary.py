"""日程总结生成工具"""

import json
import logging
import ollama
import os
from datetime import datetime
from app.skill import skill

logger = logging.getLogger(__name__)

SUMMARY_MODEL = os.getenv("BRAIN_MODEL", "qwen2.5:7b")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
client = ollama.AsyncClient(host=OLLAMA_HOST)


@skill(
    name="generate_summary",
    description="生成指定时间范围的日程总结报告",
    parameters={
        "type": "object",
        "properties": {
            "events_json": {"type": "string", "description": "日程列表的 JSON 字符串（由 query_events 返回的 events 数组）"},
            "time_range": {"type": "string", "description": "时间范围描述，如'本周'、'3月'"}
        },
        "required": ["events_json", "time_range"],
    }
)
async def generate_summary(events_json: str, time_range: str) -> str:
    """调用本地 LLM 生成日程总结"""
    try:
        prompt = f"""请根据以下日程数据，为{time_range}生成一份简洁的日程总结报告。
总结格式：
- 总日程数
- 按分类的分布情况
- 每天简要概述
- 关键事项或发现

日程数据：
{events_json}

请用中文回复，保持简洁但信息完整。"""

        response = await client.chat(
            model=SUMMARY_MODEL,
            messages=[{"role": "user", "content": prompt}],
        )
        summary = response["message"]["content"]
        return json.dumps({"status": "OK", "summary": summary, "time_range": time_range}, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Summary generation error: {e}")
        return json.dumps({"status": "ERROR", "message": f"生成总结失败: {str(e)}"}, ensure_ascii=False)
