# **《基于 Skill 与本地大语言模型的隐私保护型日程管理系统》技术设计与实现规格说明书**


# 技术设计与实现规格说明书

## 1. 项目定位与核心哲学
本系统旨在构建一个**完全本地化**的智能日程 Agent。
* **隐私第一**：所有计算（LLM）与存储（SQLite）均物理留存于用户设备。
* **Agentic 架构**：利用 MCP 协议实现大脑（模型）与手脚（工具）的解耦。
* **用户主权**：系统提供智能建议，但最终决定权（如冲突保存）由用户掌握。

---

## 2. 技术栈清单

| 维度 | 技术选型 | 备注 |
| :--- | :--- | :--- |
| **推理引擎** | **Ollama** + Qwen 2.5 (7B) | 本地 LLM 推理，支持工具调用（Function Calling）。 |
| **中控协议** | **Skill 插件系统**（替代 MCP） | 基于 `@skill` 装饰器的注册表，自动扫描 `skills/` 目录发现工具。 |
| **后端框架** | **FastAPI** | 支持异步协程，处理 LLM 高延迟推理时不阻塞 I/O。 |
| **数据存储** | **SQLite** + SQLAlchemy 2.0 | 单文件存储，免运维，支持复杂的事务处理。 |
| **前端界面** | **Vue 3** + Tailwind CSS | 提供 Web 端的实时流式（Streaming）交互体验。 |
| **运行环境** | **Windows 11 (WSL2)** |  |

---

## 3. 核心架构设计

### 3.1 模块化分层
1.  **表现层 (Frontend)**：Vue 3 编写。包含 `ProcessingTerminal`（展示思考链）和日程仪表盘。
2.  **控制层 (FastAPI Host)**：
    * **Session 管理**：维护多轮对话状态。
    * **上下文注入**：为 Prompt 自动补全当前时间、地点及用户隐私偏好。
3.  **协议层 (Skill 系统)**：
    *   **Skill 注册表**：`@skill` 装饰器将函数注册为 LLM 可调用的工具，支持 `get_tools()` 动态加载。
    *   **自动发现**：`loader.py` 扫描 `app/skill/skills/` 目录，加载 `.md` 指令文件（注入系统提示词）和 `scripts/` 中的 Python 模块。
    *   **热加载**：`hot_reload.py` 监听 `skills/` 目录变化，无需重启即可更新工具。
    *   **逻辑防火墙**：在数据入库前执行强制性的格式校验与硬冲突检查。
4.  **模型层 (Ollama/Qwen)**：作为“逻辑引擎”，识别意图并决定何时调用何种 Skill。



---

## 4. 关键功能逻辑实现

### 4.1 插件式”空间冲突”校验 
- 为接入 API 预留接口
* **解耦设计**：
    * `check_conflict` 工具仅调用 `get_travel_time()` 抽象函数。
    * **未来扩展**：若接入高德地图 API，仅需完善函数内部逻辑，无需变动 Skill 注册表层。

### 4.2 智能冲突处理循环 (Confirmation Loop)
1.  **检测**：MCP 返回 `CODE_WARN`（时间/空间冲突）。
2.  **建议**：LLM 结合数据库空闲时段，生成重排方案：“14:00 有冲突，是否改到 16:00？”
3.  **决断**：用户可选择“接受建议”、“手动选择新事件时间”、“更改原有事件时间”或“取消”。

### 4.3 数据生命周期管理 (Lifecycle Management)
* **主动维护**：后台定时任务调用 Qwen 2.5 压缩“温数据”，将明细转为“语义摘要”存入 `Summaries` 表。
* **按需报告**：用户输入“总结上周工作”，Agent 跨表检索“摘要+明细”生成 Markdown 报告。

---

## 5. 数据库模型设计 (Data Schema)

### 核心表：`Schedules` (日程表)
| 字段名 | 类型 | 说明 |
| :--- | :--- | :--- |
| `id` | Integer | 主键 |
| `user_id` | Integer | 用户标识（默认 1，cloud 模式关联 users 表） |
| `title` | String | 任务名称 |
| `start_time` | DateTime | 任务起始时间 |
| `end_time` | DateTime | 任务结束时间 |
| `location_ref`| String | 地点标识（用于映射距离矩阵） |
| `description` | Text | 日程描述（可选） |
| `category` | String(30) | 日程分类（可选：工作/学习/生活） |
| `status` | String | `confirmed` / `conflicted` |
| `privacy_level`| Integer | 1: 公开, 2: 内部, 3: 绝密 |
| `recurrence_rule`| String | 重复规则：daily / weekly / monthly / weekdays |
| `recurrence_end`| DateTime | 重复结束日期 |
| `is_archived` | Integer | 归档标记：0=活跃, 1=已归档（Phase 3） |
| `summary_id` | Integer | 外键 → Summaries 表（Phase 3） |

### 扩展表：`Summaries` (归档摘要表)
| 字段名 | 类型 | 说明 |
| :--- | :--- | :--- |
| `id` | Integer | 主键 |
| `time_range` | String | 摘要覆盖的时间段（如 "2026-W16"） |
| `content` | Text | LLM 生成的语义压缩文本 |
| `created_at` | DateTime | 创建时间 |

### 扩展表：`ChatSessions` (AI 对话会话表，Phase 2)
| 字段名 | 类型 | 说明 |
| :--- | :--- | :--- |
| `id` | String(36) | UUID 主键 |
| `user_id` | Integer | 用户标识 |
| `created_at` | DateTime | 创建时间 |
| `updated_at` | DateTime | 更新时间 |

### 扩展表：`ChatMessages` (AI 对话消息表，Phase 2)
| 字段名 | 类型 | 说明 |
| :--- | :--- | :--- |
| `id` | Integer | 主键 |
| `session_id` | String(36) | 外键 → ChatSessions |
| `role` | String(20) | user / assistant / tool |
| `content` | Text | 消息内容 |
| `tool_calls` | JSON | 工具调用元数据 |
| `created_at` | DateTime | 创建时间 |

### 扩展表：`Users` (用户表，Phase 3)
| 字段名 | 类型 | 说明 |
| :--- | :--- | :--- |
| `id` | Integer | 主键 |
| `username` | String(50) | 用户名（唯一） |
| `password_hash` | String(256) | PBKDF2 密码哈希 |
| `created_at` | DateTime | 创建时间 |

---

## 6. 部署与工程优化 (WSL2 Special)

* **路径隔离**：数据库 `.db` 文件存放于 WSL2 原生路径（如 `/home/user/app/data/`），避免跨系统挂载导致的磁盘性能损耗。
* **网络闭环**：FastAPI 与 Ollama 之间通过 `localhost` 通信，不经过公网，确保极低延迟与数据隐私。
* **视觉补偿**：前端 Vue 实现 Streaming 输出，即时展示 Agent 的 `Action`（如”正在计算距离...”），优化用户等待体验。

---

## 7. 平台演进记录

### v3.0 前端重构 (2026-05)

详见 `docs/superpowers/specs/2026-05-04-frontend-v3-design.md`。

| 维度 | v2 状态 | v3 变更 |
| :--- | :--- | :--- |
| 前端构建 | CDN 加载 | Vite + Vue SFC + Tailwind PostCSS |
| 组件化 | 单文件 index.html (450行) | 17 个 .vue 组件，按职责拆分 |
| 布局 | 左 45% 日历+对话，右 55% 列表 | 侧边栏(48px) + 工具栏 + 月视图主画布 + 可收起 AI 面板(320px) |
| AI 对话 | 固定左侧，始终可见 | 右侧面板，默认收起，按钮展开 |

### Phase 1: Skill 系统升级 (2026-05-09)

详见 `docs/superpowers/plans/2026-05-09-phase1-skill-system.md`。

| 维度 | 变更前 | 变更后 |
| :--- | :--- | :--- |
| 工具注册 | MCP JSON-RPC 硬编码 | `@skill` 装饰器 + 注册表，动态加载 |
| 系统提示词 | 固定字符串 | `load_skill_prompts()` 从 `.md` 文件动态注入 |
| 新增 Skill | 需修改代码 | 放一个目录 = 一个 Skill，自动发现 |
| 工具列表 | 6 个硬编码工具 | 9 个工具（新增 weekly_summary + import_export） |
| 热加载 | 不支持 | watchfiles 监听 skills/ 变化，无需重启 |

### Phase 2: AI 体验增强 (2026-05-10)

| 维度 | 变更前 | 变更后 |
| :--- | :--- | :--- |
| 对话接口 | `POST /chat` 同步返回 | `POST /chat/stream` SSE 流式（step/token/done 事件） |
| 消息渲染 | 一次性显示 | 打字机逐字输出 + 推理步骤折叠卡片 |
| 对话持久化 | 内存 Dict（重启丢失） | `ChatSession` + `ChatMessage` 表持久化 |
| 输入体验 | 纯文本输入框 | 5 个快捷操作按钮 + 输入框 |
| 智能分析 | 无 | `POST /api/statistics/summary` 统计端点 |

### Phase 3: 隐私保护深化 (2026-05-10)

| 维度 | 变更前 | 变更后 |
| :--- | :--- | :--- |
| 部署模式 | 纯本地 | 双模式：local / cloud（`DEPLOY_MODE` 控制） |
| 认证 | root/root 前端硬编码 | local 模式免认证，cloud 模式 JWT 多用户 |
| 加密 | 无 | `crypto.py` Fernet 应用层加密（title/description） |
| 生命周期 | 无 | `lifecycle.py` 30 天过期归档 + 摘要生成 + 软删除 |

---
