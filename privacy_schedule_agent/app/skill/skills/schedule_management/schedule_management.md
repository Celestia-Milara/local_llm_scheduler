---
name: 日程管理
description: 创建、查询、修改、删除日程
triggers: ["添加日程", "查看安排", "修改会议", "删除日程"]
---

## 创建日程
- 添加前必须先调用 check_conflict 检查冲突
- 冲突时调用 find_free_slots 查找空闲时段，向用户展示替代建议
- 用户明确确认后才调用 add_event
- 时间格式统一为 ISO 8601 (YYYY-MM-DD HH:MM:SS)

## 查询日程
- 使用 query_events 按时间范围查询
- 支持按标题关键词和分类过滤

## 修改日程
- 先用 query_events 找到对应日程获取 event_id
- 修改时间或地点后系统自动重新检查冲突
- 使用 update_event

## 删除日程
- 先用 query_events 找到对应日程获取 event_id
- 使用 delete_event
