# 分类功能后端需求文档

## 1. 功能概述

分类功能允许用户为日程添加分类标签，便于组织和筛选日程。前端已实现分类过滤器和分类显示，后端需要提供相应的 API 支持。

## 2. 分类定义

当前支持的分类：

| 分类名称 | 颜色 | 说明 |
|---------|------|------|
| 工作 | 黄色 (#fbbf24) | 工作相关日程 |
| 学习 | 蓝色 (#60a5fa) | 学习相关日程 |
| 生活 | 粉色 (#f472b6) | 生活相关日程 |

## 3. 后端已实现

### 3.1 数据库模型

Schedule 模型已包含 `category` 字段：

```python
category: Mapped[Optional[str]] = mapped_column(String(30))
```

### 3.2 CRUD 操作

以下 Skill 工具已支持 category 参数：

- `add_event` - 创建日程时可传入 category
- `query_events` - 可按 category 过滤日程
- `update_event` - 可更新日程的 category

## 4. 需要新增的 API

### 4.1 获取分类列表

**端点**: `GET /api/categories`

**描述**: 返回所有可用分类及其颜色配置

**响应示例**:
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

### 4.2 获取分类统计

**端点**: `GET /schedules/categories/stats`

**描述**: 返回每个分类的日程数量

**响应示例**:
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

## 5. 前端调用示例

### 获取分类统计

```javascript
// 在 useSchedules.js 中调用
const res = await axios.get('/schedules/categories/stats')
categoryCounts.value = res.data.counts
```

### 按分类过滤日程

```javascript
// 前端已实现，后端 query_events 已支持
const res = await axios.get('/schedules', {
  params: { 
    start: range.start, 
    end: range.end,
    category: activeCategory.value  // 可选：按分类过滤
  }
})
```

## 6. 注意事项

1. **分类名称使用中文**：前端已硬编码"工作"、"学习"、"生活"三个分类
2. **分类是可选的**：允许为空，表示未分类
3. **向后兼容**：已有日程的 category 字段可能为 null，需兼容处理
4. **未来扩展**：如需支持更多分类，前端 CategoryFilter.vue 需同步更新

## 7. 前端实现位置

- **分类过滤器**: `privacy_schedule_agent/frontend/src/components/CategoryFilter.vue`
- **分类统计逻辑**: `privacy_schedule_agent/frontend/src/composables/useSchedules.js`
- **分类显示**: `privacy_schedule_agent/frontend/src/components/ScheduleCard.vue`
