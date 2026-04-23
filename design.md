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
| **推理引擎** | **Ollama** + Qwen 2.5 (1.5B/7B) | 1.5B 用于实时交互，7B 用于深度总结。 |
| **中控协议** | **MCP (Model Context Protocol)** | 采用 JSON-RPC 2.0 规范，通过工具调用实现功能扩展。 |
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
3.  **协议层 (MCP Server)**：
    * **原子 Skill 库**：定义 `add_event`, `check_conflict`, `auto_summarize` 等函数。
    * **逻辑防火墙**：在数据入库前执行强制性的格式校验与硬冲突检查。
4.  **模型层 (Ollama/Qwen)**：作为“逻辑引擎”，识别意图并决定何时调用何种 Skill。



---

## 4. 关键功能逻辑实现

### 4.1 插件式“空间冲突”校验 
- 为接入api预留接口
* **解耦设计**：
    * `check_spatial_conflict` 工具仅调用 `get_travel_time()` 抽象函数。
    * **未来扩展**：若接入高德地图 API，仅需完善函数内部逻辑，无需变动 MCP 协议层。

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
| `title` | String | 任务名称 |
| `start_time` | DateTime | 任务起始时间 |
| `location_ref`| String | 地点标识（用于映射距离矩阵） |
| `status` | String | `confirmed` / `conflicted` |
| `privacy_level`| Integer | 1: 公开, 2: 内部, 3: 绝密 |

### 扩展表：`Summaries` (归档摘要表)
| 字段名 | 类型 | 说明 |
| :--- | :--- | :--- |
| `id` | Integer | 主键 |
| `time_range` | String | 摘要覆盖的时间段 |
| `content` | Text | LLM 生成的语义压缩文本 |

---

## 6. 部署与工程优化 (WSL2 Special)

* **路径隔离**：数据库 `.db` 文件存放于 WSL2 原生路径（如 `/home/user/app/data/`），避免跨系统挂载导致的磁盘性能损耗。
* **网络闭环**：FastAPI 与 Ollama 之间通过 `localhost` 通信，不经过公网，确保极低延迟与数据隐私。
* **视觉补偿**：前端 Vue 实现 Streaming 输出，即时展示 Agent 的 `Action`（如“正在计算距离...”），优化用户等待体验。

---
