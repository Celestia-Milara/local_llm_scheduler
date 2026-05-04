# v3.0 前端重构与用户管理系统设计

> 基于 v2.0 已完成的"日历+对话+内联编辑"功能，进行前端技术栈升级、布局重构、用户体系引入。

**目标：** 在 v2 功能闭环基础上，提升前端工程化水平、改善布局体验、增加多用户数据隔离能力。

---

## 一、关键变更

| 维度 | v2 (当前) | v3 (目标) |
| :--- | :--- | :--- |
| 构建工具 | CDN 加载 (Vue/Tailwind/Axios) | Vite + 本地构建 |
| 组件方式 | 单文件 index.html (450 行) | Vue SFC (`.vue`) 组件化 |
| CSS 方案 | Tailwind CDN + 内联 `<style>` | Tailwind PostCSS + `@apply` |
| 布局 | 左 45% 日历+对话 / 右 55% 列表 | 侧边栏 + 工具栏 + 主画布 + 可收起 AI 面板 |
| 用户 | 无 | root/root 登录，`user_id` 数据隔离 |
| 对话 | 固定左侧，始终可见 | 右侧面板，默认收起，按钮展开 |

---

## 二、布局与组件架构

### 2.1 整体布局

```
┌──────── 48px ────────┬────────── 剩余宽度 ──────────┬── 320px ─┐
┌──────────────────────┬──────────────────────────────┬──────────┐
│                      │ ┌─ 工具栏 (Toolbar) ───────┐ │          │
│ 侧边栏 (Sidebar)     │ │ [今天] < 2026年5月 > 月视图│ │ AI 面板  │
│                      │ │                    [AI] 👤│ │ (AiPanel)│
│ [+ 新建]             │ └──────────────────────────┘ │  可收起  │
│ ──────────           │ ┌─ 主画布 (MonthView) ─────┐ │          │
│ 小日历               │ │ 7×6 月历网格              │ │ 对话    │
│ (MiniCalendar)       │ │ 点击日期 → 弹出当日列表   │ │ 记录    │
│                      │ │ 有事件日期：圆点标记       │ │         │
│  隐私状态            │ │                           │ │         │
│  (● 已连接)          │ └──────────────────────────┘ │          │
└──────────────────────┴──────────────────────────────┴──────────┘
```

### 2.2 组件树

```
App.vue                           ← 根组件：登录守卫
├── LoginPage.vue                 ← root/root 登录页
└── MainLayout.vue                ← 布局容器（登录后）
    ├── Sidebar.vue               ← 左侧导航（48px 固定宽）
    │   ├── CreateButton.vue      ← [+ 新建日程]
    │   ├── MiniCalendar.vue      ← 全局日期导航
    │   └── PrivacyStatus.vue     ← 本地模型连接状态
    ├── Toolbar.vue               ← 顶部操作栏
    │   ├── DateNavigator.vue     ← [今天] < 2026年5月 >
    │   ├── ViewSwitcher.vue      ← [月视图]（日/周预留）
    │   └── HeaderActions.vue     ← [AI 展开] [用户头像/退出]
    ├── MonthView.vue             ← 主画布：月视图
    │   ├── CalendarGrid.vue      ← 7×6 网格 + 圆点标记
    │   └── DayPopover.vue        ← 点击日期弹出的当天列表
    │       └── ScheduleCard.vue  ← 日程卡片（含内联编辑/删除）
    └── AiPanel.vue               ← 右侧 AI 面板 (默认收起)
        ├── ChatMessages.vue      ← 对话消息流
        └── ChatInput.vue         ← 输入框 + 发送按钮
```

### 2.3 组件职责

| 组件 | 职责 | 核心状态 |
| :--- | :--- | :--- |
| `App.vue` | 检查 localStorage token，决定渲染 LoginPage 或 MainLayout | 登录态 |
| `LoginPage.vue` | root/root 比对，写入 localStorage | — |
| `Sidebar.vue` | 固定宽度容器，容纳子组件 | 布局 |
| `MiniCalendar.vue` | 月份切换、日期选择、事件圆点 | `currentMonth`, `selectedDate` |
| `MonthView.vue` | 月历网格渲染，点击日期弹出 DayPopover | `monthEvents` |
| `DayPopover.vue` | 弹出层展示当天日程列表，可关闭 | 来自 `monthEvents` 过滤 |
| `ScheduleCard.vue` | 展示/内联编辑/删除单条日程 | `editingId`, `editForm` |
| `AiPanel.vue` | 控制展开/收起，管理对话消息 | `visible`, `messages`, `loading` |
| `Toolbar.vue` | 日期导航、视图切换、AI/Auth 操作入口 | — |

---

## 三、用户认证流程

### 3.1 登录

```
App.vue mounted
  └→ localStorage 是否有 token?
       ├→ 无 → 渲染 LoginPage
       │       ├→ 输入 root / root
       │       ├→ 前端硬编码比对（无后端校验）
       │       └→ 写入 localStorage: { token: 'root', user_id: 1 }
       └→ 有 → 渲染 MainLayout，所有请求带 user_id=1
```

### 3.2 退出

- 点击工具栏用户头像 → 下拉菜单 → "退出登录"
- 清除 `localStorage` → 回到 LoginPage

> 无注册、无密码找回、无安全检测。仅用 `user_id` 实现数据隔离。

---

## 四、数据流与 API

### 4.1 状态管理 (Composables)

```
useAuth.js          → login(), logout(), isAuthenticated, userId
useSchedules.js     → monthEvents, selectedDate, fetchMonth(), create(), update(), delete()
useChat.js          → messages, send(), loading, aiPanelVisible
```

### 4.2 API 接口

| 方法 | 路径 | 变更 |
| :--- | :--- | :--- |
| `GET /schedules` | `?start=&end=&user_id=` | 新增 `user_id` 过滤参数 |
| `POST /chat` | 不变 | 请求体中加 `user_id` |
| `PUT /schedules/{id}` | 不变 | — |
| `DELETE /schedules/{id}` | 不变 | — |

### 4.3 增删改即时刷新

```
create/update/delete 操作完成
  └→ await fetchMonth() 重新拉取当月日程
     └→ monthEvents 更新 → 日历圆点 / DayPopover 自动同步
```

---

## 五、后端模型变更

### Schedule 表新增字段

```python
user_id: Mapped[int] = mapped_column(Integer, default=1)
```

### 迁移

在 `database.py` 的 `init_db()` 中检测 schedules 表是否缺少 `user_id` 列，若缺少则 `ALTER TABLE ADD COLUMN`。

### 接口调整

`GET /schedules` 增加可选 `user_id` 查询参数，用于过滤。

---

## 六、Vite 构建集成

### 6.1 目录结构

```
privacy_schedule_agent/frontend/
├── package.json
├── vite.config.js
├── tailwind.config.js
├── postcss.config.js
├── index.html              ← Vite 入口
├── src/
│   ├── main.js
│   ├── App.vue
│   ├── components/
│   │   ├── LoginPage.vue
│   │   ├── MainLayout.vue
│   │   ├── Sidebar.vue
│   │   ├── MiniCalendar.vue
│   │   ├── CreateButton.vue
│   │   ├── PrivacyStatus.vue
│   │   ├── Toolbar.vue
│   │   ├── DateNavigator.vue
│   │   ├── ViewSwitcher.vue
│   │   ├── HeaderActions.vue
│   │   ├── MonthView.vue
│   │   ├── CalendarGrid.vue
│   │   ├── DayPopover.vue
│   │   ├── ScheduleCard.vue
│   │   ├── AiPanel.vue
│   │   ├── ChatMessages.vue
│   │   └── ChatInput.vue
│   ├── composables/
│   │   ├── useAuth.js
│   │   ├── useSchedules.js
│   │   └── useChat.js
│   └── utils/
│       └── calendar.js    ← 从 calendar_utils.js 移植
├── tests/
│   └── calendar.test.js
└── dist/                  ← vite build 输出
```

### 6.2 FastAPI 托管构建产物

```python
if os.path.exists("frontend/dist"):
    app.mount("/", StaticFiles(directory="frontend/dist", html=True), name="frontend")
```

---

## 七、错误与边界处理

| 场景 | 处理方式 |
| :--- | :--- |
| API 请求失败 | 轻量 toast 提示，不阻塞 UI |
| 登录密码错误 | 输入框下方红色提示"密码错误" |
| AI 面板模型离线 | 显示"模型连接失败"占位，保留历史消息 |
| 新建日程表单验证 | 标题和时间为必填，前端校验 |
| 删除确认 | confirm("确认删除?") |
| 月视图无数据 | 网格正常渲染，无圆点 |
| DayPopover 空列表 | 显示"当天暂无日程" |

---

## 八、未纳入 v3 范围

- 日视图 / 周视图
- 隐私热力图
- AI 建议日程 (Ghost Events)
- 拖拽调整时间
- 对话历史持久化
- 移动端适配

---

## 九、设计决策记录

| 决策 | 选择 | 原因 |
| :--- | :--- | :--- |
| 前端鉴权 | 纯前端 localStorage | 本地应用，无需后端鉴权负担 |
| 状态管理 | Composables (vs Pinia) | 应用足够简单，composables 零依赖 |
| 组件粒度 | 细粒度拆分 (14 个组件) | 适配 Vite 构建，每组件职责单一 |
| MiniCalendar 与 MonthView 月份同步 | 共享同一 Reactive 引用 | 同一数据源，无需 props 透传 |
| AI 面板 | 右侧 320px 侧滑收起 | 不影响主画布布局 |
| DayPopover | 浮层 (vs 固定右侧列表) | 节省空间，符合"先看月概览，再点击查看"的自然交互 |
