import json
import logging
import ollama
import os
from datetime import datetime
from typing import List, Dict, Any
from dotenv import load_dotenv
from app.mcp.calendar_skill import (
    check_conflict, add_event, query_events,
    update_event, delete_event, find_free_slots
)

load_dotenv()

logger = logging.getLogger(__name__)

# 从环境变量获取模型配置
BRAIN_MODEL = os.getenv("BRAIN_MODEL", "qwen2.5:7b")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")

# 配置 ollama 客户端
client = ollama.Client(host=OLLAMA_HOST)

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
"""

# 定义工具元数据，供模型理解
TOOLS = [
    {
        'type': 'function',
        'function': {
            'name': 'check_conflict',
            'description': '检查指定时间段的日程是否存在物理或时间上的冲突',
            'parameters': {
                'type': 'object',
                'properties': {
                    'start_time': {'type': 'string', 'description': '计划开始时间 (YYYY-MM-DD HH:MM:SS)'},
                    'end_time': {'type': 'string', 'description': '计划结束时间 (YYYY-MM-DD HH:MM:SS)'},
                    'location': {'type': 'string', 'description': '计划地点'}
                },
                'required': ['start_time', 'end_time', 'location'],
            },
        },
    },
    {
        'type': 'function',
        'function': {
            'name': 'add_event',
            'description': '将新日程写入数据库',
            'parameters': {
                'type': 'object',
                'properties': {
                    'title': {'type': 'string', 'description': '日程标题'},
                    'start_time': {'type': 'string', 'description': '开始时间 (YYYY-MM-DD HH:MM:SS)'},
                    'end_time': {'type': 'string', 'description': '结束时间 (YYYY-MM-DD HH:MM:SS)'},
                    'location': {'type': 'string', 'description': '地点'},
                    'description': {'type': 'string', 'description': '日程描述或备注'},
                    'category': {'type': 'string', 'description': '日程分类（如：工作、学习、生活）'},
                    'status': {'type': 'string', 'description': "日程状态，默认为 'confirmed'。强行保存冲突日程时设为 'conflicted'"}
                },
                'required': ['title', 'start_time', 'end_time', 'location'],
            },
        },
    },
    {
        'type': 'function',
        'function': {
            'name': 'query_events',
            'description': '查询日程列表。可按时间范围、关键词或分类查询，至少需要时间范围或关键词',
            'parameters': {
                'type': 'object',
                'properties': {
                    'start_time': {'type': 'string', 'description': '查询起始时间 (YYYY-MM-DD HH:MM:SS)'},
                    'end_time': {'type': 'string', 'description': '查询结束时间 (YYYY-MM-DD HH:MM:SS)'},
                    'keyword': {'type': 'string', 'description': '按标题模糊搜索的关键词'},
                    'category': {'type': 'string', 'description': '按分类过滤'}
                },
                'required': [],
            },
        },
    },
    {
        'type': 'function',
        'function': {
            'name': 'update_event',
            'description': '修改已有日程。只更新传入的字段，修改时间或地点会自动重新检查冲突',
            'parameters': {
                'type': 'object',
                'properties': {
                    'event_id': {'type': 'integer', 'description': '日程ID'},
                    'title': {'type': 'string', 'description': '新标题'},
                    'start_time': {'type': 'string', 'description': '新开始时间 (YYYY-MM-DD HH:MM:SS)'},
                    'end_time': {'type': 'string', 'description': '新结束时间 (YYYY-MM-DD HH:MM:SS)'},
                    'location': {'type': 'string', 'description': '新地点'},
                    'description': {'type': 'string', 'description': '新描述'},
                    'category': {'type': 'string', 'description': '新分类'}
                },
                'required': ['event_id'],
            },
        },
    },
    {
        'type': 'function',
        'function': {
            'name': 'delete_event',
            'description': '删除指定日程',
            'parameters': {
                'type': 'object',
                'properties': {
                    'event_id': {'type': 'integer', 'description': '要删除的日程ID'}
                },
                'required': ['event_id'],
            },
        },
    },
    {
        'type': 'function',
        'function': {
            'name': 'find_free_slots',
            'description': '查找指定日期的空闲时段。冲突时可用于向用户建议替代时间',
            'parameters': {
                'type': 'object',
                'properties': {
                    'date': {'type': 'string', 'description': '日期 (YYYY-MM-DD)'},
                    'duration_minutes': {'type': 'integer', 'description': '需要的最小时长（分钟），默认60'},
                    'start_hour': {'type': 'integer', 'description': '查找范围起始小时，默认8'},
                    'end_hour': {'type': 'integer', 'description': '查找范围结束小时，默认22'}
                },
                'required': ['date'],
            },
        },
    }
]

# 工具映射表
AVAILABLE_FUNCTIONS = {
    'check_conflict': check_conflict,
    'add_event': add_event,
    'query_events': query_events,
    'update_event': update_event,
    'delete_event': delete_event,
    'find_free_slots': find_free_slots,
}

async def run_chat(user_input: str, history: List[Dict[str, str]] = None) -> str:
    """
    Agent 执行引擎的核心入口，处理用户输入并进行 Function Calling 推理。
    """
    if history is None:
        history = []

    # 更新系统提示词中的时间（确保时效性）
    current_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    dynamic_system_prompt = SYSTEM_PROMPT_TEMPLATE.format(current_time=current_time_str)

    # 构建消息列表
    messages = [
        {'role': 'system', 'content': dynamic_system_prompt}
    ] + history + [
        {'role': 'user', 'content': user_input}
    ]

    try:
        # 1. 初始请求：判断是否需要调用工具
        response = client.chat(
            model=BRAIN_MODEL,
            messages=messages,
            tools=TOOLS,
        )

        # 2. 循环处理工具调用（处理多轮思考）
        while response.get('message', {}).get('tool_calls'):
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
            response = client.chat(
                model=BRAIN_MODEL,
                messages=messages,
                tools=TOOLS
            )

        # 3. 返回最终回复内容
        final_content = response['message'].get('content', "抱歉，我未能生成有效的回复。")
        return final_content

    except Exception as e:
        logger.error(f"Agent Engine Error: {e}")
        return "抱歉，系统引擎在处理您的请求时遇到了点困难，请稍后再试。"
