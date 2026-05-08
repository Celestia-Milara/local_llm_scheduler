# 项目参考文档（Project Reference）

本文件存放项目背景、运行命令、架构与环境变量等“参考信息”。  
`CLAUDE.md` 仅保留执行规范与行为约束，避免指令文件过于臃肿。

## 项目概述

隐私保护型日程助理：基于本地 LLM（通过 Ollama）驱动的日程管理助手。通过 Function Calling 在添加日程前检查冲突（含通勤时间冲突），冲突场景下要求用户明确确认后才保存。

## 常用命令

```bash
# 启动服务（在 privacy_schedule_agent/ 目录下）
cd privacy_schedule_agent && python main.py

# 或使用 uvicorn 启动
cd privacy_schedule_agent && uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 安装依赖
cd privacy_schedule_agent && pip install -r requirements.txt

# 前端构建（v3，需 Node.js 18+）
cd privacy_schedule_agent/frontend && npm install
cd privacy_schedule_agent/frontend && npm run build
cd privacy_schedule_agent/frontend && npm run dev

# 需提前运行 Ollama 并拉取模型
# ollama pull qwen2.5:7b
# ollama pull qwen2.5:1.5b   # ROUTER_MODEL，当前未使用
```

测试套件：
- 后端：`pytest`（当前仓库也包含 `unittest` 回归测试）
- 前端日历工具：`cd privacy_schedule_agent/frontend && node --test tests/calendar.test.js`

## 架构

```text
privacy_schedule_agent/
├── main.py                  # FastAPI 应用：/chat、/schedules、静态前端
├── app/
│   ├── core/agent_engine.py # LLM 编排：Ollama 对话 + 工具调用循环
│   ├── mcp/calendar_skill.py# 工具实现：check_conflict、add_event 等
│   ├── services/
│   │   └── location_service.py  # 地点间通勤时间估算
│   └── db/
│       ├── database.py      # SQLAlchemy 异步引擎 + 会话工厂（aiosqlite）
│       └── models.py        # Schedule ORM 模型
├── frontend/
│   ├── index.html           # Vite 入口
│   ├── package.json         # Vue 3 + Tailwind + Vite
│   ├── src/                 # Vue SFC 组件与 composables
│   └── dist/                # 构建产物，由 FastAPI 托管
└── data/schedule.db         # SQLite 数据库（已 gitignore）
```

## 核心流程

1. 对话流程：`POST /chat` → `agent_engine.run_chat()` → 工具调用循环（`check_conflict` → `add_event`）→ 返回自然语言回复。  
2. 冲突检查：`check_conflict()` 结合相邻日程与 `location_service.get_travel_time()` 检测时间/通勤冲突。  
3. 日程创建/更新：支持冲突确认机制，未确认时返回冲突详情，显式确认后可保存为 `conflicted`。

## 设计决策

- 所有 LLM 推理本地完成（Ollama），不调用外部云端 API。  
- 工具调用手动编排：agent 引擎解析 Ollama `tool_calls` 并分发 Python 函数。  
- 前端构建采用 Vite + Vue SFC + Tailwind，构建产物由 FastAPI 静态托管。  

## 环境变量

| 变量 | 默认值 | 用途 |
|---|---|---|
| `BRAIN_MODEL` | `qwen2.5:7b` | 主推理模型 |
| `ROUTER_MODEL` | `qwen2.5:1.5b` | 路由模型（当前未使用） |
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama 服务地址 |
| `DATABASE_URL` | `sqlite+aiosqlite:///./data/schedule.db` | 异步 SQLite 连接字符串 |
| `LOG_LEVEL` | `INFO` | Python 日志级别 |

## 语言约定

代码和界面主要使用简体中文。系统提示词、错误消息、API 响应均采用中文。修改面向用户的文本时请保持此约定。
