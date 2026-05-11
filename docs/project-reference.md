# 项目参考文档（Project Reference）

本文件存放项目背景、运行命令、架构与环境变量等"参考信息"。  
`CLAUDE.md` 仅保留执行规范与行为约束，避免指令文件过于臃肿。

## 项目概述

隐私保护型日程助理：基于**本地 LLM（Ollama）** 驱动的日程管理助手。系统支持两种部署模式：

- **local 模式**（默认）：纯本地运行，单用户，零网络依赖，数据不出设备
- **cloud 模式**：`DEPLOY_MODE=cloud`，启用 JWT 多用户认证 + 可选数据加密

核心功能通过 Skill 插件系统实现，Skill = 目录下的 `.md` 指令文件 + `scripts/` 中的 Python 工具脚本。

## 常用命令

```bash
# 启动服务（在 privacy_schedule_agent/ 目录下）
cd privacy_schedule_agent && python main.py

# 或使用 uvicorn 启动（开发模式热重载）
cd privacy_schedule_agent && uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 安装依赖
cd privacy_schedule_agent && pip install -r requirements.txt

# 前端构建（v3，需 Node.js 18+）
cd privacy_schedule_agent/frontend && npm install
cd privacy_schedule_agent/frontend && npm run build
cd privacy_schedule_agent/frontend && npm run dev

# 需提前运行 Ollama 并拉取模型
# ollama pull qwen2.5:7b
```

测试套件：
- 后端：`cd privacy_schedule_agent && pytest`
- 前端日历工具：`cd privacy_schedule_agent/frontend && node --test tests/calendar.test.js`

## 架构

```text
privacy_schedule_agent/
├── main.py                        # FastAPI 应用入口：17 条路由
├── app/
│   ├── core/
│   │   ├── agent_engine.py        # LLM 编排：run_chat / run_chat_stream
│   │   └── crypto.py              # Fernet 应用层加解密
│   ├── skill/
│   │   ├── __init__.py            # @skill 装饰器 + 注册表（get_tools / execute_tool）
│   │   ├── loader.py              # 扫描 skills/ 目录，加载 .md 指令 + scripts/
│   │   ├── hot_reload.py          # watchfiles 热加载
│   │   └── skills/
│   │       ├── schedule_management/   # 6 个工具：add_event, query_events, update_event, delete_event, check_conflict, find_free_slots
│   │       ├── weekly_summary/        # 1 个工具：generate_summary（LLM 生成周总结）
│   │       └── import_export/         # 2 个工具：export_csv, import_ical
│   ├── auth/
│   │   ├── jwt.py                 # JWT 生成与验证（cloud 模式用）
│   │   └── middleware.py          # 条件认证中间件
│   ├── db/
│   │   ├── database.py            # SQLAlchemy 异步引擎 + 迁移逻辑
│   │   ├── models.py              # Schedule / Summary / ChatSession / ChatMessage / User
│   │   └── lifecycle.py           # 数据生命周期管理（过期归档 + 摘要生成）
│   └── services/
│       └── location_service.py    # 地点间通勤时间估算
├── frontend/
│   ├── index.html                 # Vite 入口
│   ├── package.json               # Vue 3 + Tailwind + Vite
│   ├── src/
│   │   ├── App.vue                # 根组件：部署模式检测 → 登录页 / 主布局
│   │   ├── composables/
│   │   │   ├── useChat.js         # SSE 流式对话 + 消息管理
│   │   │   ├── useAuth.js         # 双模式认证（local 跳过 / cloud API）
│   │   │   ├── useSchedules.js    # 日程 CRUD
│   │   │   └── useView.js         # 视图切换
│   │   ├── components/            # 16 个 Vue SFC 组件
│   │   │   ├── LoginPage.vue      # 登录/注册页（cloud 模式）
│   │   │   ├── MainLayout.vue     # 主布局 + 侧栏 + AI 面板
│   │   │   ├── ChatMessages.vue   # 流式消息 + 推理步骤展示
│   │   │   ├── ChatInput.vue      # 快捷操作面板 + 输入框
│   │   │   ├── AiPanel.vue        # AI 助手侧栏
│   │   │   ├── CalendarGrid.vue   # 日历网格
│   │   │   ├── DayPopover.vue     # 日弹出详情
│   │   │   └── ...                # 其余视图组件
│   │   └── style.css              # Tailwind + 自定义样式
│   └── dist/                      # 构建产物，由 FastAPI 静态托管
├── tests/                         # 29 个测试（pytest + unittest）
│   ├── test_skill_registry.py     # @skill 注册表 5 个测试
│   ├── test_skill_loader.py       # loader 2 个测试
│   ├── test_skill_hot_reload.py   # 热加载 2 个测试
│   ├── test_conflict_confirmation_api.py  # 冲突确认 2 个测试
│   ├── test_chat_history.py       # 对话持久化 3 个测试
│   ├── test_phase2_streaming.py   # SSE + 统计 8 个测试
│   └── test_phase3_auth.py        # JWT + 加密 + 生命周期 15 个测试
└── data/schedule.db               # SQLite 数据库（已 gitignore）
```

## API 路由

| 端点 | 用途 | 引入阶段 |
|---|---|---|
| `POST /chat` | 非流式对话（兼容旧版） | v1.0 |
| `POST /chat/stream` | SSE 流式对话（step/token/done 事件） | Phase 2 |
| `GET /schedules` | 获取日程列表 | v1.0 |
| `POST /schedules` | 创建日程（含冲突检查） | v1.0 |
| `GET /schedules/{id}` | 获取单个日程 | v1.0 |
| `PUT /schedules/{id}` | 更新日程（含冲突重检） | v1.0 |
| `DELETE /schedules/{id}` | 删除日程 | v1.0 |
| `GET /schedules/export/json` | 导出日程 JSON | v1.0 |
| `POST /api/statistics/summary` | 智能日程统计（分类/每日/空闲分析） | Phase 2 |
| `POST /api/auth/register` | 用户注册（cloud 模式） | Phase 3 |
| `POST /api/auth/login` | 用户登录 | Phase 3 |
| `GET /api/auth/me` | 当前用户信息 | Phase 3 |

## 核心流程

1. **对话流程**：`POST /chat/stream` → `agent_engine.run_chat_stream()` → 工具调用循环（检测冲突→执行→二次推理）→ SSE 流式返回 token。
2. **SSE 事件类型**：`step`（推理步骤：thinking/tool_call/tool_result）→ `token`（逐字输出）→ `done`（完成）
3. **冲突检查**：`check_conflict()` 结合相邻日程与 `location_service.get_travel_time()` 检测时间/通勤冲突。
4. **日程创建/更新**：支持冲突确认机制，未确认时返回 409 + 冲突详情，显式确认后可保存为 `conflicted`。
5. **认证**：`DEPLOY_MODE=local` 跳过认证；`DEPLOY_MODE=cloud` 启用 JWT 中间件。
6. **数据生命周期**：超 30 天未归档日程自动按周分组生成摘要并软删除（`is_archived`）。

## Skill 插件系统

**结构规范**：一个目录 = 一个 Skill

```
app/skill/skills/<skill-name>/
├── <skill-name>.md              # 自然语言指令（必选，frontmatter + body）
└── scripts/                     # 工具脚本（可选）
    ├── tool_one.py              # 用 @skill 装饰器注册
    └── tool_two.py
```

- **自动发现**：`loader.py` 在启动时扫描 `skills/` 目录，加载所有 `.md` 指令和 `scripts/` 中的 Python 模块。
- **@skill 装饰器**：`@skill(name, description, parameters)` 将异步函数注册到 `_SKILL_REGISTRY`，LLM 可通过 Function Calling 调用。
- **热加载**：`hot_reload.py` 监听 `skills/` 目录变化，`.md` 变化重载提示词缓存，`.py` 变化重载模块。

当前已注册 3 个 Skill、9 个工具。

## 设计决策

- 所有 LLM 推理本地完成（Ollama），不调用外部云端 API。
- 工具调用手动编排：agent 引擎解析 Ollama `tool_calls` 并分发 Python 函数。
- 前端构建采用 Vite + Vue SFC + Tailwind，构建产物由 FastAPI 静态托管。
- 双部署模式设计：local（纯本地单用户）vs cloud（JWT 多用户 + 加密）。
- 隐私字段（`title`、`description`）使用 Fernet 对称加密，索引字段不加密。

## 环境变量

| 变量 | 默认值 | 用途 |
|---|---|---|
| `BRAIN_MODEL` | `qwen2.5:7b` | 主推理模型 |
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama 服务地址 |
| `DATABASE_URL` | `sqlite+aiosqlite:///./data/schedule.db` | 异步 SQLite 连接字符串 |
| `DEPLOY_MODE` | `local` | local（单用户） / cloud（JWT 多用户） |
| `ENCRYPTION_KEY` | （空，自动生成会话密钥） | Fernet 加密密钥（cloud 模式建议设置） |
| `JWT_SECRET` | `dev-secret-change-in-production` | JWT 签名密钥（cloud 模式必须修改） |
| `LOG_LEVEL` | `INFO` | Python 日志级别 |

## 语言约定

代码和界面主要使用简体中文。系统提示词、错误消息、API 响应均采用中文。修改面向用户的文本时请保持此约定。
