import json
import logging
import ollama
import os
from datetime import datetime, timezone
from typing import List, Dict, Any
from dotenv import load_dotenv
from app.skill import get_tools, get_available_functions, execute_tool
from app.skill.loader import discover_skills, load_skill_prompts

load_dotenv()

logger = logging.getLogger(__name__)

# 从环境变量获取模型配置
BRAIN_MODEL = os.getenv("BRAIN_MODEL", "qwen2.5:7b")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")

# 配置 ollama 异步客户端（避免阻塞事件循环）
client = ollama.AsyncClient(host=OLLAMA_HOST)

# 启动时扫描并加载所有 Skill
discover_skills()
SKILL_PROMPTS = load_skill_prompts()

# 系统提示词设计
SYSTEM_PROMPT_TEMPLATE = """
你是一个隐私保护型日程助理。你负责管理用户的日程，并确保时间安排合理且无冲突。

核心规则：
1. 在添加任何日程前，必须先调用 `check_conflict` 工具。
2. 冲突处理：如果工具返回 WARN 状态，向用户展示具体冲突原因，并调用 `find_free_slots` 查找空闲时段，给出替代建议。询问用户选择「接受建议」「手动指定时间」「强行保存」还是「取消」。
3. 强行保存：只有在用户明确表示要强行保存冲突日程时，才调用 `add_event` 并将 status 设置为 'conflicted'。
4. 查询日程：用户询问日程安排时，使用 `query_events` 工具。根据用户描述推断时间范围（如「明天」=明天0:00-23:59，「这周」=本周一到周日）。
5. 修改日程：用户要求修改日程时，先用 `query_events` 找到对应日程获取 event_id，再调用 `update_event`。修改时间或地点后系统会自动重新检查冲突。
6. 删除日程：用户要求删除日程时，先用 `query_events` 找到对应日程获取 event_id，再调用 `delete_event`。
7. 隐私原则：始终保护用户隐私，不要在回复中透露系统内部路径、数据库结构或底层异常信息。
8. 当前北京时间：{current_time}。在理解「明天」「下午」等概念时以此时间为准。

## 注册 Skill 指令
{skill_prompts}
"""

# 定义工具元数据，供模型理解
TOOLS = get_tools()

# 工具映射表
AVAILABLE_FUNCTIONS = get_available_functions()

async def run_chat(user_input: str, history: List[Dict[str, str]] = None) -> str:
    """
    Agent 执行引擎的核心入口，处理用户输入并进行 Function Calling 推理。
    """
    if history is None:
        history = []

    # 更新系统提示词中的时间（确保时效性）
    # 使用北京时间（UTC+8），确保「明天」「下午」等概念理解正确
    beijing_tz = timezone.utc  # fallback
    try:
        from zoneinfo import ZoneInfo
        beijing_tz = ZoneInfo("Asia/Shanghai")
    except Exception:
        try:
            import pytz
            beijing_tz = pytz.timezone("Asia/Shanghai")
        except Exception:
            pass
    current_time_str = datetime.now(beijing_tz).strftime("%Y-%m-%d %H:%M:%S")
    dynamic_system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
        current_time=current_time_str,
        skill_prompts=SKILL_PROMPTS
    )

    # 构建消息列表
    messages = [
        {'role': 'system', 'content': dynamic_system_prompt}
    ] + history + [
        {'role': 'user', 'content': user_input}
    ]

    try:
        # 1. 初始请求：判断是否需要调用工具
        response = await client.chat(
            model=BRAIN_MODEL,
            messages=messages,
            tools=TOOLS,
        )

        # 2. 循环处理工具调用，上限 10 次防止无限循环
        MAX_ITERATIONS = 10
        iteration = 0
        while response.get('message', {}).get('tool_calls') and iteration < MAX_ITERATIONS:
            iteration += 1
            tool_calls = response['message']['tool_calls']
            messages.append(response['message'])

            for tool_call in tool_calls:
                function_name = tool_call['function']['name']
                args_raw = tool_call['function'].get('arguments')
                if isinstance(args_raw, str):
                    function_args = json.loads(args_raw)
                else:
                    function_args = args_raw or {}

                logger.debug(f"Calling tool: {function_name} with args: {function_args}")

                # 执行对应的本地函数
                if function_name in AVAILABLE_FUNCTIONS:
                    function_to_call = AVAILABLE_FUNCTIONS[function_name]
                    try:
                        function_response = await function_to_call(**function_args)
                        messages.append({
                            'role': 'tool',
                            'content': function_response,
                            'name': function_name
                        })
                    except Exception as e:
                        logger.error(f"Error executing tool {function_name}: {e}")
                        messages.append({
                            'role': 'tool',
                            'content': json.dumps({"status": "ERROR", "message": f"内部工具错误: {str(e)}"}),
                            'name': function_name
                        })
                else:
                    messages.append({
                        'role': 'tool',
                        'content': json.dumps({"status": "ERROR", "message": f"未知的工具名称: {function_name}"}),
                        'name': function_name
                    })

            # 二次推理：根据工具执行结果生成回复或继续调用
            response = await client.chat(
                model=BRAIN_MODEL,
                messages=messages,
                tools=TOOLS
            )

        if iteration >= MAX_ITERATIONS:
            logger.warning("Agent reached max tool-call iterations, forcing response")

        # 3. 返回最终回复内容
        final_content = response['message'].get('content', "抱歉，我未能生成有效的回复。")
        return final_content

    except Exception as e:
        logger.error(f"Agent Engine Error: {e}")
        return "抱歉，系统引擎在处理您的请求时遇到了点困难，请稍后再试。"
