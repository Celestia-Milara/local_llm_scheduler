# 分类（Category）API 设计稿

日期：2026-05-13

## 1. 背景

前端已实现分类过滤器与分类展示（固定三类：工作/学习/生活），并在前端基于已加载的日程列表计算分类计数。目前后端已在 `Schedule` 模型中包含 `category` 字段，并且 Skill 工具链（add/query/update）已支持 `category`。

为支持：
- 前端从后端获取“可用分类 + 颜色配置”（避免前端硬编码扩散）
- 后端提供“分类统计”接口（可用于侧栏统计、报表等）

需要新增两个 API：
- `GET /api/categories`
- `GET /schedules/categories/stats`

## 2. 目标与非目标

### 2.1 目标

1. 提供固定分类配置列表（含颜色），与现有前端视觉一致。
2. 提供按时间范围统计的分类计数接口。
3. 与现有系统约束保持一致：
   - cloud 模式启用 JWT 认证
   - local 模式不启用认证
4. 统计默认仅针对“活跃日程”（`is_archived = 0`）。

### 2.2 非目标（本次不做）

- 不引入“用户自定义分类”的增删改（分类仍为固定配置）。
- 不修改前端现有计算分类计数的逻辑（是否切换到后端统计由后续任务决定）。
- 不复用/改造 `POST /api/statistics/summary` 的输出结构（该接口偏智能统计，结构不同）。

## 3. 统一约定

### 3.1 分类配置

固定分类列表（key 与 label 均为中文）：

| key | label | color |
|---|---|---|
| "" | 全部 | #818cf8 |
| 工作 | 工作 | #fbbf24 |
| 学习 | 学习 | #60a5fa |
| 生活 | 生活 | #f472b6 |

说明：
- `key=""` 表示“全部”，仅用于 UI 选择与统计汇总。
- `Schedule.category` 允许为空/NULL，表示未分类。

### 3.2 认证与 user_id 取值

- `DEPLOY_MODE=local`：完全跳过认证。
- `DEPLOY_MODE=cloud`：两条新端点均需要 JWT。
  - `user_id` 从 JWT 解析得到（后端权威来源）
  - 忽略请求中可能携带的 `user_id` query 参数

> 注：若后端当前中间件仅“放行/不放行”但未真正校验 token，本设计仍按“应校验并可解析 user_id”定义；实现时需要与现有 `get_user_id_from_request()` 机制对齐。

### 3.3 时间范围参数

`/schedules/categories/stats` 使用 query 参数：
- `start`：必填，支持 `YYYY-MM-DD` 或 `YYYY-MM-DD HH:MM:SS`
- `end`：必填，支持 `YYYY-MM-DD` 或 `YYYY-MM-DD HH:MM:SS`

解析规则：
- 若传 `YYYY-MM-DD`：
  - `start` 按当天 `00:00:00`
  - `end` 按当天 `23:59:59`
- 若格式非法：返回 400

## 4. API 设计

### 4.1 获取分类列表

**方法**：`GET`

**路径**：`/api/categories`

**认证**：
- local：无需
- cloud：需要 JWT

**请求参数**：无

**响应（200）**：

```json
{
  "categories": [
    { "key": "", "label": "全部", "color": "#818cf8" },
    { "key": "工作", "label": "工作", "color": "#fbbf24" },
    { "key": "学习", "label": "学习", "color": "#60a5fa" },
    { "key": "生活", "label": "生活", "color": "#f472b6" }
  ]
}
```

**错误码**：
- 401（cloud 且无/无效 JWT）

### 4.2 获取分类统计

**方法**：`GET`

**路径**：`/schedules/categories/stats`

**认证**：
- local：无需
- cloud：需要 JWT

**Query 参数**：
- `start`（必填）
- `end`（必填）
- `user_id`（local 可选，默认 1；cloud 忽略）

**统计范围**：
- `Schedule.user_id == user_id`
- `Schedule.is_archived == 0`
- 时间范围过滤（与现有 `/schedules` 保持一致的直觉）：
  - `Schedule.start_time >= start_dt`
  - `Schedule.end_time <= end_dt`

**响应（200）**：

```json
{
  "counts": {
    "": 15,
    "工作": 8,
    "学习": 4,
    "生活": 3
  }
}
```

计数规则：
- `counts[""]`：范围内日程总数（包含：未分类、未知分类、以及三类分类）。
- `counts["工作"|"学习"|"生活"]`：只统计 `category` 精确等于该 key 的记录。
- 未分类（`category` 为 NULL 或空字符串）不单列 key，仅计入 `counts[""]`。
- 未在固定配置中的“未知分类”也不单列 key，仅计入 `counts[""]`。

无数据时：

```json
{ "counts": { "": 0, "工作": 0, "学习": 0, "生活": 0 } }
```

**错误码**：
- 400：缺少 `start/end` 或日期格式非法
- 401：cloud 且无/无效 JWT

## 5. 与现有系统的关系与兼容性

- `Schedule.category` 字段已存在；本设计不改变其存储形式。
- 前端当前在本地计算分类计数；本接口可作为替代/补充（后续可选迁移）。
- `POST /api/statistics/summary` 已有“分类分布”等信息，但分类 key 使用 `"未分类"` 等口径；本设计保持与前端 UI 口径一致（不输出未分类 key）。

## 6. 测试策略（设计层面）

建议新增/扩展 pytest：
1. `GET /api/categories`：返回固定列表与颜色字段。
2. `GET /schedules/categories/stats`：
   - 给定时间范围内插入多条 schedules（含三类、未分类、未知分类、已归档），验证 counts 规则。
   - 日期格式错误返回 400。
3. cloud 模式：缺少 JWT 返回 401（覆盖两端点）。

## 7. 交付物

- 新增设计文档：`docs/superpowers/specs/2026-05-13-category-api-design.md`
- （实现阶段再进入）main.py 新增两条路由与少量常量/辅助函数
