# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 规则

- **必须使用中文回答用户的所有问题。**

## 项目概述

隐私保护型日程助理 — 基于本地 LLM（通过 Ollama）驱动的日程管理助手。使用 Function Calling 机制在添加日程前检查日历冲突（包括通勤时间冲突），并对冲突日程强制要求用户明确确认后才予保存。

## 常用命令

```bash
# 启动服务（在 privacy_schedule_agent/ 目录下）
cd privacy_schedule_agent && python main.py
# 或使用 uvicorn 启动：
cd privacy_schedule_agent && uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 安装依赖
cd privacy_schedule_agent && pip install -r requirements.txt

# 前端构建（v3，需 Node.js 18+）
cd privacy_schedule_agent/frontend && npm install
cd privacy_schedule_agent/frontend && npm run build    # 生产构建
cd privacy_schedule_agent/frontend && npm run dev      # 开发模式

# 需提前运行 Ollama 并拉取模型：
#   ollama pull qwen2.5:7b
#   ollama pull qwen2.5:1.5b  (ROUTER_MODEL，当前未使用)
```

测试套件：
- 后端：使用 `pytest`（需另行配置）
- 前端日历工具：`cd privacy_schedule_agent/frontend && node --test tests/calendar.test.js`

## 架构

```
privacy_schedule_agent/
├── main.py                  # FastAPI 应用：/chat、/schedules、静态前端
├── app/
│   ├── core/agent_engine.py # LLM 编排：Ollama 对话 + 工具调用循环
│   ├── mcp/calendar_skill.py# 工具实现：check_conflict、add_event 等 6 个工具
│   ├── services/
│   │   └── location_service.py  # 地点间通勤时间估算
│   └── db/
│       ├── database.py      # SQLAlchemy 异步引擎 + 会话工厂（aiosqlite）
│       └── models.py        # Schedule ORM 模型（含 user_id 字段）
├── frontend/
│   ├── index.html           # Vite 入口
│   ├── package.json         # Vue 3 + Tailwind + Vite
│   ├── vite.config.js
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   ├── src/                 # Vue SFC 组件
│   │   ├── App.vue
│   │   ├── main.js
│   │   ├── components/      # 17 个组件（Sidebar, MonthView, AiPanel, ScheduleCard 等）
│   │   ├── composables/     # useAuth, useSchedules, useChat
│   │   └── utils/calendar.js
│   └── dist/                # 构建产物，由 FastAPI 托管
└── data/schedule.db         # SQLite 数据库（已 gitignore）
```

### 核心流程

1. **对话流程**：`POST /chat` → `agent_engine.run_chat()` → 携带工具定义的 Ollama LLM → 工具调用循环（check_conflict → add_event）→ 返回自然语言回复。

2. **冲突检查**：`check_conflict()` 查询相邻日程以检测通勤冲突（通过 `location_service.get_travel_time()`）和时间重叠。返回状态码：`OK`、`WARN` 或 `ERROR`。

3. **日程创建**：`add_event()` 通过异步 SQLAlchemy 写入 SQLite。冲突日程标记为 `status='conflicted'`。

### 设计决策

- **所有 LLM 推理均在本地**通过 Ollama 完成，不调用外部 API。通过 `.env` 文件配置（`BRAIN_MODEL`、`OLLAMA_HOST`）。
- **工具调用为手动实现**：agent 引擎手动解析 Ollama 的 tool_calls 响应，分发给 Python 函数，并将结果回传。未使用任何框架（LangChain 等）。
- **会话历史**仅存于内存中（`main.py` 中的字典），每个会话最多保留 20 条消息。
- **数据库**使用 SQLite + aiosqlite 异步驱动，在应用启动时通过 `lifespan()` 初始化。
- **用户管理**（v3）：前端 localStorage 鉴权（root/root），Schedule 表通过 `user_id` 字段实现数据隔离，无后端校验。
- **前端构建**（v3）：Vite + Vue SFC + Tailwind PostCSS，`npm run build` 产出 `dist/` 由 FastAPI 静态托管。

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
