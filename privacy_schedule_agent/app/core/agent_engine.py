import json
import logging
import ollama
import os
from datetime import datetime
from typing import List, Dict, Any
from dotenv import load_dotenv
from app.mcp.calendar_skill import check_conflict, add_event

load_dotenv()

logger = logging.getLogger(__name__)

# 从环境变量获取模型配置
BRAIN_MODEL = os.getenv("BRAIN_MODEL", "qwen2.5:7b")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")

# 配置 ollama 客户端（如果需要指定 host，可以使用 Client 类，
# 但通常可以通过环境变量 OLLAMA_HOST 直接控制全局 ollama 库的行为）
client = ollama.Client(host=OLLAMA_HOST)

# 系统提示词设计
SYSTEM_PROMPT = f"""

你是一个隐私保护型日程助理。你负责管理用户的日程，并确保时间安排合理且无冲突。

核心规则：
1. 在添加任何日程前，必须先调用 `check_conflict` 工具。
2. 冲突处理：如果工具返回 `CODE_WARN`，你必须向用户展示具体的冲突原因（例如通勤时间不足或时间重叠），并询问用户是“修改时间”、“取消”还是“强行保存”。
3. 强行保存：只有在用户明确表示要强行保存冲突日程时，才调用 `add_event` 并将 `status` 设置为 'conflicted'。
4. 隐私原则：始终保护用户隐私，不要在回复中透露系统内部路径、数据库结构或底层异常信息。
5. 当前北京时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}。在理解“明天”、“下午”等概念时以此时间为准。
"""

# 定义工具元数据，供模型理解（手动模拟 Function Calling 描述）
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
                    'status': {'type': 'string', 'description': "日程状态，默认为 'confirmed'。强行保存冲突日程时设为 'conflicted'"}
                },
                'required': ['title', 'start_time', 'end_time', 'location'],
            },
        },
    }
]

# 工具映射表
AVAILABLE_FUNCTIONS = {
    'check_conflict': check_conflict,
    'add_event': add_event
}

async def run_chat(user_input: str, history: List[Dict[str, str]] = None) -> str:
    """
    Agent 执行引擎的核心入口，处理用户输入并进行 Function Calling 推理。
    
    Args:
        user_input (str): 用户输入字符串
        history (List): 历史对话上下文
        
    Returns:
        str: 助理的最终回复
    """
    if history is None:
        history = []

    # 更新系统提示词中的时间（确保时效性）
    current_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    dynamic_system_prompt = SYSTEM_PROMPT.replace("{datetime.now().strftime(\"%Y-%m-%d %H:%M:%S\")}", current_time_str)

    # 构建消息列表
    messages = [
        {'role': 'system', 'content': dynamic_system_prompt}
    ] + history + [
        {'role': 'user', 'content': user_input}
    ]

    try:
        # 1. 初始请求：判断是否需要调用工具
        response = client.chat(
            model=BRAIN_MODEL, # 使用环境变量中配置的模型
            messages=messages,
            tools=TOOLS,
        )

        # 2. 循环处理工具调用（处理多轮思考）
        while response.get('message', {}).get('tool_calls'):
            tool_calls = response['message']['tool_calls']
            messages.append(response['message'])

            for tool_call in tool_calls:
                function_name = tool_call['function']['name']
                # 修复：获取 arguments 字段并处理可能的 JSON 字符串解析
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
                        # 执行结果
                        function_response = await function_to_call(**function_args)
                        
                        # 将结果反馈给 LLM
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
