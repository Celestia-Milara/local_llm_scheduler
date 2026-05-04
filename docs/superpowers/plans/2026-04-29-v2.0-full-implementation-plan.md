# v2.0 实施方案 — 可用闭环

> 目标：从"只能添加"变成"基本可用的日程管理器"，用户可通过对话完成日程的增删改查全流程

## 变更总览

| 类别 | 变更项 | 涉及文件 |
|---|---|---|
| 新增工具 | query_events, update_event, delete_event, find_free_slots | `calendar_skill.py` |
| 数据模型 | Schedule 增加 description, category 字段 | `models.py` |
| Agent 引擎 | 扩展 TOOLS 定义 + 更新系统提示词 | `agent_engine.py` |
| 数据库 | 迁移脚本处理已有数据 | `database.py` |
| 后端接口 | /schedules 增强 + /schedules/{id} 接口 | `main.py` |
| 前端离线化 | CDN → 本地文件 | `frontend/` |
| 代码质量 | import 规范、时间替换修复、Summary.now 修复 | 多文件 |

---

## 步骤 1：数据模型更新

**文件**: `app/db/models.py`

Schedule 表新增两个字段：

```python
# 在 Schedule 类中增加
description: Mapped[Optional[str]] = mapped_column(Text)           # 日程描述/备注
category: Mapped[Optional[str]] = mapped_column(String(30))       # 日程分类（工作/学习/生活）
```

同时修复 Summary 表的 bug：
- `created_at` 默认值从 `datetime.now`（引用）改为 `datetime.now` 配合 `default` 参数正确用法

**文件**: `app/db/database.py`

在 `init_db()` 中使用 `checkfirst=True` 避免重复建表，并新增字段迁移逻辑：
- 检测 schedules 表是否缺少 description / category 列
- 若缺少，用 `ALTER TABLE ADD COLUMN` 补充

---

## 步骤 2：新增 Skill 工具实现

**文件**: `app/mcp/calendar_skill.py`

### 2.1 query_events — 日程查询

```python
async def query_events(start_time: str = None, end_time: str = None,
                       keyword: str = None, category: str = None) -> str:
```

- 参数全部可选，至少需要 start_time+end_time 或 keyword 之一
- 按时间范围查询，支持 keyword 模糊搜索（title LIKE %keyword%）
- 支持按 category 过滤
- 返回 JSON 数组，每项包含 id/title/start_time/end_time/location/status/description/category

### 2.2 update_event — 日程修改

```python
async def update_event(event_id: int, title: str = None,
                       start_time: str = None, end_time: str = None,
                       location: str = None, description: str = None,
                       category: str = None) -> str:
```

- 只更新传入的非 None 字段
- 如果修改了 start_time/end_time/location 中任一项，自动重新调用 check_conflict
- 返回更新结果 + 可能的冲突信息

### 2.3 delete_event — 日程删除

```python
async def delete_event(event_id: int) -> str:
```

- 根据 id 删除日程
- 返回删除确认信息

### 2.4 find_free_slots — 空闲时段查找

```python
async def find_free_slots(date: str, duration_minutes: int = 60,
                          start_hour: int = 8, end_hour: int = 22) -> str:
```

- 查找指定日期内的空闲时段
- duration_minutes: 需要的最小连续空闲时长
- start_hour/end_hour: 查找范围（默认 8:00-22:00）
- 返回可用时段列表，如 [{"start": "09:00", "end": "11:30"}, ...]
- 此函数在 check_conflict 返回 WARN 时被 Agent 调用，为用户提供替代建议

### 2.5 增强 check_conflict

现有逻辑保留，增加：与后一个日程的通勤冲突检查（当前只检查前一个）

---

## 步骤 3：Agent 引擎更新

**文件**: `app/core/agent_engine.py`

### 3.1 扩展 TOOLS 定义

在现有 2 个工具基础上，新增 4 个工具的 JSON Schema 描述：

- `query_events`: 查询日程
- `update_event`: 修改日程
- `delete_event`: 删除日程
- `find_free_slots`: 查找空闲时段

### 3.2 更新 AVAILABLE_FUNCTIONS 映射

```python
AVAILABLE_FUNCTIONS = {
    'check_conflict': check_conflict,
    'add_event': add_event,
    'query_events': query_events,
    'update_event': update_event,
    'delete_event': delete_event,
    'find_free_slots': find_free_slots,
}
```

### 3.3 更新系统提示词

扩展 SYSTEM_PROMPT，增加：
- 查询日程的指令："用户询问日程安排时，使用 query_events 工具"
- 修改/删除日程的指令
- 冲突协商流程："检测到冲突时，调用 find_free_slots 查找空闲时段，向用户建议替代时间"
- 隐私原则不变

### 3.4 修复时间替换逻辑

当前实现（第95行）：
```python
dynamic_system_prompt = SYSTEM_PROMPT.replace("{datetime.now().strftime(\"%Y-%m-%d %H:%M:%S\")}", current_time_str)
```

改为使用 f-string 占位符：
```python
SYSTEM_PROMPT_TEMPLATE = """...当前北京时间：{current_time}..."""
dynamic_system_prompt = SYSTEM_PROMPT_TEMPLATE.format(current_time=current_time_str)
```

---

## 步骤 4：后端接口增强

**文件**: `main.py`

### 4.1 代码规范修复

- 将第84-88行的 import 语句移到文件顶部
- 移除第89行的重复注释

### 4.2 新增 /schedules/{id} 接口

```python
@app.get("/schedules/{event_id}")
async def get_schedule(event_id: int):
    # 查询单个日程

@app.delete("/schedules/{event_id}")
async def delete_schedule(event_id: int):
    # 删除日程（供前端直接调用，不经过 LLM）

@app.put("/schedules/{event_id}")
async def update_schedule(event_id: int, ...):
    # 更新日程（供前端直接调用）
```

### 4.3 /schedules 查询增强

支持查询参数过滤：
```python
@app.get("/schedules")
async def get_schedules(start: str = None, end: str = None):
    # 支持按时间范围过滤
```

---

## 步骤 5：前端离线化

**目标**: 去掉 CDN 依赖，所有 JS/CSS 资源本地化

### 5.1 下载资源文件

```
frontend/
├── index.html
├── assets/
│   ├── vue.global.prod.js
│   ├── tailwind.min.js（或 tailwind cdn standalone）
│   ├── axios.min.js
│   └── FiraCode.woff2
```

### 5.2 修改 index.html

将 CDN 引用替换为本地路径：
```html
<script src="/assets/vue.global.prod.js"></script>
<script src="/assets/tailwind.min.js"></script>
<script src="/assets/axios.min.js"></script>
```

---

## 步骤 6：前端展示增强

**文件**: `frontend/index.html`

### 6.1 日程卡片展示 description 和 category

- 卡片增加日程描述（如有）
- 增加 category 标签（不同颜色区分工作/学习/生活）

### 6.2 日程操作按钮

每张卡片增加：
- 删除按钮（调用 DELETE /schedules/{id}）
- 编辑按钮（打开编辑表单，调用 PUT /schedules/{id}）

### 6.3 空闲时段展示

当 LLM 返回冲突建议时，在前端高亮展示建议的替代时段

---

## 实施顺序

```
步骤1 数据模型 → 步骤2 Skill工具 → 步骤3 Agent引擎 → 步骤4 后端接口
                                                              ↓
                                              步骤5 前端离线化 → 步骤6 前端增强
```

步骤 1-4 是后端核心，有依赖关系须按序推进。步骤 5-6 是前端，步骤 5 先行，步骤 6 最后。

---

## 验收检查点

完成全部步骤后，依次验证以下场景：

1. **添加** — "后天下午3点在图书馆开会，大概1小时" → 成功添加
2. **查询** — "我后天有什么安排？" → 返回刚添加的日程
3. **冲突** — 再添加一个后天15:00的日程 → 检测到冲突 + 建议替代时段
4. **修改** — "把图书馆开会改到4点" → 成功修改 + 重新冲突检查
5. **删除** — "删掉图书馆那个会议" → 成功删除
6. **离线** — 断开网络 → 前端仍可正常加载和使用

---

## 风险与注意事项

1. **7B 模型的工具调用可靠性**: 新增 4 个工具后，模型需要在 6 个工具中选择。如果准确率下降，考虑在系统提示词中增加示例（few-shot）
2. **ALTER TABLE 迁移**: SQLite 的 ALTER TABLE 仅支持 ADD COLUMN，不支持修改/删除列。新增字段都允许 NULL，兼容旧数据
3. **前端离线化体积**: Tailwind CDN standalone 版约 300KB，Vue prod 约 40KB，Axios 约 15KB，总计约 400KB，可接受
4. **数据库兼容**: 新增字段均为 Optional，已有的 schedule.db 数据无需手动处理
