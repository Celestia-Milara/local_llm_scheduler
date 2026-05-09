# 隐私保护型日程管理系统优化方案

## 概述

本文档定义了对《基于 Skill 与本地大语言模型的隐私保护型日程管理系统》的全面优化方案。优化按**主题驱动**方式分三个阶段推进，以 **Skill → AI 体验 → 隐私保护** 三大支柱为主线，UX 打磨和架构债修复贯穿全程。

系统设计时即支持两种部署模式（`DEPLOY_MODE=local | cloud`）：
- **纯本地模式**：当前默认，单用户，零网络依赖，数据不出设备
- **云端部署模式**：自托管 Ollama + 可选 JWT 多用户认证 + 数据加密

---

## Phase 1: Skill 系统升级

### 1.1 目标

将当前硬编码的 6 个 MCP 工具重构为**插件式 Skill 系统**，Skill 的定义方式与 Claude Code 风格一致：**一个目录 = 一个 Skill**。

### 1.2 Skill 结构定义

```
app/skill/skills/<skill-name>/
├── <skill-name>.md              # 自然语言指令（必选）
├── additional-notes.md          # 附加说明（可选）
└── scripts/                     # 工具脚本（可选）
    ├── tool_one.py
    └── tool_two.py
```

- **`.md` 文件**：包含 frontmatter（name, triggers, tools）和 body（行为规则、约束条件）。系统启动时自动解析并拼入 LLM 系统提示词。
- **`scripts/`**：Python 脚本，每个函数通过 `@skill` 装饰器注册为 LLM 可调用的 Tool。

### 1.3 Skill 加载器

**文件：** `app/skill/loader.py`

启动流程：
1. 遍历 `app/skill/skills/` 下每个子目录
2. 读取所有 `.md` 文件 → 解析 frontmatter + body → 拼接为系统提示词
3. 扫描 `scripts/` → 导入 `.py` 文件，通过 `@skill` 装饰器自动注册
4. 返回：`skill_prompts`（注入 agent_engine 系统提示词）、`tools`（LLM tool 定义列表）

**热加载（hot_reload.py）：** 依赖 `watchfiles` 监听 `skills/` 目录：
- `.md` 文件变化 → 重新生成 `skill_prompts`
- `.py` 文件变化 → 重新 import → 更新 `tools` 注册表

### 1.4 @skill 装饰器

**文件：** `app/skill/__init__.py`

```python
_SKILL_REGISTRY = {}

def skill(name: str, description: str, parameters: dict):
    def decorator(func):
        _SKILL_REGISTRY[name] = {"function": func, "description": description, "parameters": parameters}
        return func
    return decorator

def get_tools():    # → LLM tool schema 列表
def execute_tool(name, args):  # → 按名称调用函数
```

### 1.5 现有的 6 个工具迁移

| 当前文件 | 迁移目标 | 改动 |
|---------|---------|------|
| `app/mcp/calendar_skill.py` | `app/skill/skills/schedule-management/scripts/` | 拆分为独立文件，加 `@skill` 装饰器 |
| `app/mcp/` 目录 | 删除 | 迁移后清理 |

### 1.6 新增 Skill

1. **`schedule-management/`**（从现有迁移）：add_event, query_events, update_event, delete_event, check_conflict, find_free_slots
2. **`weekly-summary/`**（新增）：generate_summary → LLM 生成指定时间范围日程总结
3. **`import-export/`**（新增）：import_ical, export_csv → 批量导入导出

### 1.7 agent_engine.py 改动

- `TOOLS` 常量 → `get_tools()` 动态加载
- 系统提示词 → 拼入所有 `.md` 内容的 `skill_prompts`
- 工具执行 → `execute_tool()` 统一路由

---

## Phase 2: AI 体验增强

### 2.1 流式输出 (SSE)

**后端改动（main.py）：**
- 新增 `GET /chat/stream` SSE 端点
- 事件类型：
  - `step`（推理步骤：`thinking` / `tool_call` / `tool_result`）
  - `token`（LLM 逐字输出）
  - `done`（完成信号）

**前端改动（ChatMessages.vue）：**
- 使用 `EventSource` 或 `fetch + ReadableStream` 接收 SSE
- 推理步骤显示为折叠式状态卡片：🔍 思考中 → ⚡ 调用工具 → 📋 工具结果
- LLM 输出逐步渲染为打字机效果

### 2.2 对话历史持久化

**数据库新增表：**

```sql
chat_sessions: id (UUID), user_id, created_at, updated_at
chat_messages: id, session_id, role (user/assistant/tool), content, tool_calls (JSON), created_at
```

**上下文管理：** 滑动窗口 + LLM 摘要压缩
- 历史超过 N 条时，将早期消息压缩为一条 LLM 生成的摘要，保留最近 K 条完整消息

**前端（AiPanel.vue）：** 会话列表侧栏、新建会话按钮、历史会话恢复

### 2.3 快捷操作面板

ChatInput 上方显示 5 个快捷按钮：
- 📅 添加日程 → "明天下午3点在图书馆开会"
- 📋 查看本周 → "我这周有什么安排？"
- ⚡ 查找空闲 → "明天有什么空闲时间？"
- 📊 周总结 → "总结一下这周的安排"
- 📤 导出日程 → "导出我的日程"

### 2.4 智能日程分析

- 后端：新增 `POST /api/statistics/summary` 端点（可选）
- 功能：按分类统计、每日分布、空闲模式识别
- 用户可通过 AI 自然语言触发（"我这个月工作多不多？"）

---

## Phase 3: 隐私保护深化

### 3.1 配置化认证

| 模式 | 行为 |
|------|------|
| `DEPLOY_MODE=local` | 跳过认证，`user_id` 固定为 1 |
| `DEPLOY_MODE=cloud` | 启用 JWT 中间件，多用户隔离 |

**新增文件：**
- `app/auth/jwt.py` — JWT 生成 / 验证
- `app/auth/middleware.py` — FastAPI 条件中间件（按 `DEPLOY_MODE` 开关）

**新增端点：**
- `POST /api/auth/login` → `{ token, user }`
- `POST /api/auth/register` → `{ username, password }`

**现有前端 useAuth.js 适配：** local 模式直接进入，cloud 模式显示登录页

### 3.2 数据加密

- 依赖：`cryptography` 包（`Fernet` 对称加密）
- cloud 模式自动启用，local 模式跳过
- 加密范围：`title`、`description` 等敏感内容字段
- 索引字段（id、时间、user_id）不加密以支持查询
- 应用层加解密，数据库存密文

### 3.3 数据生命周期管理

**文件：** `app/db/lifecycle.py`

- 后台任务每日运行（`asyncio` + APScheduler）
- 过期日程（超过 30 天）处理：
  1. 按周分组
  2. 调用 LLM 生成自然语言摘要（→ 写入 Summaries 表）
  3. 软删除原日程（`is_archived` 标记）
- 前端：归档可查看摘要，不可编辑

---

## 贯穿优化

### UX 打磨

| 项 | 说明 | 阶段 |
|----|------|------|
| 冲突确认 UI | CreateButton / ScheduleDetail 捕获 409 → 弹窗显示冲突详情 → 用户确认后重试 | Phase 1+2 |
| 创建双路径统一 | 明确区分"直接 API 创建"（POST /schedules）和"AI 对话创建"（/chat） | Phase 1 |
| 重复事件系列操作 | 编辑/删除时询问"仅此实例"或"全部实例" | Phase 1 |
| 离线/错误降级 | Ollama 不可用时显示友好提示，不白屏 | Phase 2 |

### 架构债

| 项 | 说明 | 阶段 |
|----|------|------|
| Skill 系统测试 | loader、注册器、热加载单元测试 | Phase 1 |
| SSE 流式测试 | SSE 端点集成测试 | Phase 2 |
| 认证系统测试 | JWT 中间件、登录/注册测试 | Phase 3 |
| 清理旧 mcp/ 目录 | 迁移后删除 | Phase 1 |
| 前端测试补充 | AiPanel、ChatMessages 等组件测试 | Phase 2 |

---

## 文件变更清单

### 新增文件

| 路径 | 用途 |
|------|------|
| `app/skill/__init__.py` | @skill 装饰器 + 注册表 |
| `app/skill/loader.py` | 目录扫描 + .md 解析 + 自动注册 |
| `app/skill/hot_reload.py` | watchfiles 热加载 |
| `app/skill/skills/schedule-management/schedule-management.md` | 日程管理 Skill 指令 |
| `app/skill/skills/schedule-management/scripts/*.py` | 现有工具迁移 |
| `app/skill/skills/weekly-summary/weekly-summary.md` | 周总结 Skill 指令 |
| `app/skill/skills/weekly-summary/scripts/generate_summary.py` | 总结生成工具 |
| `app/skill/skills/import-export/import-export.md` | 导入导出 Skill 指令 |
| `app/skill/skills/import-export/scripts/*.py` | 导入导出工具 |
| `app/auth/jwt.py` | JWT 生成/验证 |
| `app/auth/middleware.py` | 条件认证中间件 |
| `app/db/lifecycle.py` | 数据生命周期管理 |
| `app/core/crypto.py` | 应用层加解密 |

### 修改文件

| 路径 | 改动 |
|------|------|
| `app/core/agent_engine.py` | TOOLS 改为动态加载，系统提示词拼入 skill_prompts |
| `app/db/models.py` | 新增 ChatSession、ChatMessage、is_archived |
| `app/db/database.py` | 新增表创建逻辑 |
| `main.py` | SSE 端点、认证端点、条件中间件 |
| `frontend/src/composables/useChat.js` | SSE 流式处理、会话管理 |
| `frontend/src/composables/useAuth.js` | 支持 local/cloud 双模式 |
| `frontend/src/components/AiPanel.vue` | 会话列表、新建会话 |
| `frontend/src/components/ChatMessages.vue` | 推理步骤渲染、打字机效果 |
| `frontend/src/components/ChatInput.vue` | 快捷操作按钮 |

### 删除文件

| 路径 | 原因 |
|------|------|
| `app/mcp/calendar_skill.py` | 迁移至 skill/skills/ |
| `app/mcp/` 空目录 | 不再需要 |

---

## 测试计划

| 范围 | 工具 | 覆盖内容 |
|------|------|---------|
| Skill 加载器 | pytest | 目录扫描、.md 解析、注册 |
| SSE 端点 | pytest + httpx | 流式事件推送 |
| 认证 | pytest + httpx | JWT 签发/验证/过期 |
| 数据生命周期 | pytest | 归档逻辑、LLM 摘要 |
| 前端 Skill | node --test | AiPanel SSE 渲染、快捷操作 |
| 现有测试保持 | pytest / node --test | 回归覆盖 |
