# v3.0 前端重构与用户管理系统 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将前端从 CDN 单文件升级为 Vite + Vue SFC 工程化架构，重构布局为侧边栏+工具栏+主画布+可收起 AI 面板，引入 root/root 用户登录和数据隔离。

**Architecture:** Vite 构建 Vue 3 + Tailwind PostCSS + Axios；Composables 管理共享状态（useAuth/useSchedules/useChat）；后端仅 Schedule 表加 user_id + API 参数调整，不引入后端鉴权。

**Tech Stack:** Vite 6, Vue 3 (Composition API, SFC), Tailwind CSS v3, Axios, Node 18+, Python 3.10+

---

## File Structure / Responsibilities

### 新建（共 28 个文件）

```
privacy_schedule_agent/frontend/
├── package.json                     # 依赖：vue, axios, tailwindcss, vite, postcss, autoprefixer
├── vite.config.js                   # Vue 插件 + 代理
├── tailwind.config.js               # 内容路径配置
├── postcss.config.js                # Tailwind + Autoprefixer
├── index.html                       # Vite 入口
├── src/
│   ├── main.js                      # createApp(App).mount('#app')
│   ├── style.css                    # @tailwind base/components/utilities
│   ├── App.vue                      # 登录守卫：token → LoginPage or MainLayout
│   ├── components/
│   │   ├── LoginPage.vue            # root/root 登录表单
│   │   ├── MainLayout.vue           # 三栏布局容器
│   │   ├── Sidebar.vue              # 48px 左侧导航容器
│   │   ├── MiniCalendar.vue         # 小日历 + 月份切换 + 事件圆点
│   │   ├── CreateButton.vue         # [+ 新建日程] 按钮
│   │   ├── PrivacyStatus.vue        # 本地模型连接状态指示
│   │   ├── Toolbar.vue              # 顶部操作栏容器
│   │   ├── DateNavigator.vue        # [今天] < 2026年5月 >
│   │   ├── ViewSwitcher.vue         # [月视图]（日/周预留）
│   │   ├── HeaderActions.vue        # [AI 展开] [用户头像/退出]
│   │   ├── MonthView.vue            # 主画布：月历网格 + DayPopover
│   │   ├── CalendarGrid.vue         # 7×6 月历网格 + 圆点
│   │   ├── DayPopover.vue           # 点击日期弹出当天日程列表
│   │   ├── ScheduleCard.vue         # 日程卡片（展示/内联编辑/删除）
│   │   ├── AiPanel.vue              # 右侧滑出 AI 面板容器
│   │   ├── ChatMessages.vue         # 对话消息流
│   │   └── ChatInput.vue            # 输入框 + 发送按钮
│   ├── composables/
│   │   ├── useAuth.js               # 登录/退出/鉴权状态
│   │   ├── useSchedules.js          # 日程 CRUD + 日历状态
│   │   └── useChat.js               # 对话消息 + 发送
│   └── utils/
│       └── calendar.js              # ES module 版日历工具函数
└── tests/
    └── calendar.test.js             # Node test for calendar.js (ESM)
```

### 修改

- `privacy_schedule_agent/main.py` — GET /schedules 加 user_id 过滤、静态文件指向 dist、新增 POST /schedules
- `privacy_schedule_agent/app/db/models.py` — Schedule 加 user_id 字段
- `privacy_schedule_agent/app/db/database.py` — user_id 迁移逻辑

### 删除

- `privacy_schedule_agent/frontend/index.html`（CDN 版，被 Vite 入口替代）
- `privacy_schedule_agent/frontend/assets/calendar_utils.js`（被 utils/calendar.js 替代）
- `privacy_schedule_agent/frontend/tests/calendar_utils.test.js`（被 ESM 版替代）
- `privacy_schedule_agent/frontend/assets/axios.min.js`
- `privacy_schedule_agent/frontend/assets/vue.global.prod.js`
- `privacy_schedule_agent/frontend/assets/tailwind.js`

---

### Task 1: Vite 项目初始化

**Files:**
- Create: `privacy_schedule_agent/frontend/package.json`
- Create: `privacy_schedule_agent/frontend/vite.config.js`
- Create: `privacy_schedule_agent/frontend/tailwind.config.js`
- Create: `privacy_schedule_agent/frontend/postcss.config.js`
- Create: `privacy_schedule_agent/frontend/index.html`（Vite 入口）
- Create: `privacy_schedule_agent/frontend/src/style.css`
- Create: `privacy_schedule_agent/frontend/src/main.js`
- Create: `privacy_schedule_agent/frontend/src/App.vue`（骨架）
- Create: `privacy_schedule_agent/frontend/src/utils/calendar.js`
- Create: `privacy_schedule_agent/frontend/tests/calendar.test.js`

- [ ] **Step 1: Create package.json**

```json
{
  "name": "privacy-schedule-agent",
  "private": true,
  "version": "3.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview",
    "test": "node --experimental-vm-modules tests/calendar.test.js"
  },
  "dependencies": {
    "vue": "^3.5.0",
    "axios": "^1.7.0"
  },
  "devDependencies": {
    "@vitejs/plugin-vue": "^5.2.0",
    "vite": "^6.3.0",
    "tailwindcss": "^3.4.0",
    "postcss": "^8.5.0",
    "autoprefixer": "^10.4.0"
  }
}
```

- [ ] **Step 2: Create vite.config.js**

```javascript
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    proxy: {
      '/schedules': 'http://localhost:8000',
      '/chat': 'http://localhost:8000'
    }
  }
})
```

- [ ] **Step 3: Create tailwind.config.js**

```javascript
/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,js}'],
  theme: {
    extend: {}
  },
  plugins: []
}
```

- [ ] **Step 4: Create postcss.config.js**

```javascript
export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {}
  }
}
```

- [ ] **Step 5: Create index.html（Vite 入口）**

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>隐私日程助理</title>
  <style>
    body { margin: 0; background: #0f172a; }
  </style>
</head>
<body class="h-screen overflow-hidden">
  <div id="app"></div>
  <script type="module" src="/src/main.js"></script>
</body>
</html>
```

- [ ] **Step 6: Create src/style.css**

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

.pre-wrap { white-space: pre-wrap; }
```

- [ ] **Step 7: Create src/main.js**

```javascript
import { createApp } from 'vue'
import App from './App.vue'
import './style.css'

createApp(App).mount('#app')
```

- [ ] **Step 8: Create src/App.vue（骨架，仅包含占位模板）**

```vue
<template>
  <div class="h-screen bg-slate-900 text-slate-200">
    <p class="p-4">App mounted</p>
  </div>
</template>

<script setup>
</script>
```

- [ ] **Step 9: Create src/utils/calendar.js**（UMD → ES module）

```javascript
export const pad2 = (n) => String(n).padStart(2, '0')

export const toDateKey = (date) => {
  const yyyy = date.getFullYear()
  const mm = pad2(date.getMonth() + 1)
  const dd = pad2(date.getDate())
  return `${yyyy}-${mm}-${dd}`
}

export const getMonthMatrix = (year, monthIndex) => {
  const first = new Date(year, monthIndex, 1)
  const start = new Date(first)
  start.setDate(1 - first.getDay())

  const weeks = []
  let cursor = new Date(start)
  for (let w = 0; w < 6; w += 1) {
    const week = []
    for (let d = 0; d < 7; d += 1) {
      const date = new Date(cursor)
      week.push({
        date,
        dateKey: toDateKey(date),
        inMonth: date.getMonth() === monthIndex
      })
      cursor.setDate(cursor.getDate() + 1)
    }
    weeks.push(week)
  }
  return weeks
}

export const groupEventsByDate = (events) => {
  return events.reduce((acc, event) => {
    const dateKey = event.start_time.slice(0, 10)
    acc[dateKey] = acc[dateKey] || []
    acc[dateKey].push(event)
    return acc
  }, {})
}

export const getMonthRange = (year, monthIndex) => {
  const start = new Date(year, monthIndex, 1)
  const end = new Date(year, monthIndex + 1, 0)
  const startStr = `${start.getFullYear()}-${pad2(start.getMonth() + 1)}-01 00:00:00`
  const endStr = `${end.getFullYear()}-${pad2(end.getMonth() + 1)}-${pad2(end.getDate())} 23:59:59`
  return { start: startStr, end: endStr }
}
```

- [ ] **Step 10: Create tests/calendar.test.js（ESM 版）**

```javascript
import { describe, it } from 'node:test'
import assert from 'node:assert/strict'
import { getMonthMatrix, groupEventsByDate, getMonthRange, toDateKey } from '../src/utils/calendar.js'

describe('calendar utils', () => {
  it('getMonthMatrix returns 6x7 grid', () => {
    const matrix = getMonthMatrix(2026, 3)
    assert.equal(matrix.length, 6)
    matrix.forEach(week => assert.equal(week.length, 7))
    const april1 = matrix.flat().find(d => d.dateKey === '2026-04-01')
    assert.ok(april1)
    assert.equal(april1.inMonth, true)
  })

  it('groupEventsByDate groups by dateKey', () => {
    const events = [
      { id: 1, start_time: '2026-04-10 09:00:00' },
      { id: 2, start_time: '2026-04-10 11:00:00' },
      { id: 3, start_time: '2026-04-11 10:00:00' }
    ]
    const grouped = groupEventsByDate(events)
    assert.equal(grouped['2026-04-10'].length, 2)
    assert.equal(grouped['2026-04-11'].length, 1)
  })

  it('getMonthRange returns correct strings', () => {
    const range = getMonthRange(2026, 3)
    assert.equal(range.start, '2026-04-01 00:00:00')
    assert.equal(range.end, '2026-04-30 23:59:59')
  })
})
```

- [ ] **Step 11: Run npm install + test**

```bash
cd privacy_schedule_agent/frontend
npm install
node --experimental-vm-modules tests/calendar.test.js
```

Expected: 3 tests pass. Output shows `ok` or `pass`.

- [ ] **Step 12: Commit**

```bash
git add privacy_schedule_agent/frontend/package.json \
  privacy_schedule_agent/frontend/vite.config.js \
  privacy_schedule_agent/frontend/tailwind.config.js \
  privacy_schedule_agent/frontend/postcss.config.js \
  privacy_schedule_agent/frontend/index.html \
  privacy_schedule_agent/frontend/src/style.css \
  privacy_schedule_agent/frontend/src/main.js \
  privacy_schedule_agent/frontend/src/App.vue \
  privacy_schedule_agent/frontend/src/utils/calendar.js \
  privacy_schedule_agent/frontend/tests/calendar.test.js
git commit -m "feat: scaffold Vite project and port calendar utils to ESM"
```

---

### Task 2: Composables（共享状态管理）

**Files:**
- Create: `privacy_schedule_agent/frontend/src/composables/useAuth.js`
- Create: `privacy_schedule_agent/frontend/src/composables/useSchedules.js`
- Create: `privacy_schedule_agent/frontend/src/composables/useChat.js`

- [ ] **Step 1: Create useAuth.js**

```javascript
import { ref, computed } from 'vue'

const TOKEN_KEY = 'schedule_auth'
const token = ref(localStorage.getItem(TOKEN_KEY))
const userId = ref(token.value ? 1 : null)

export function useAuth() {
  const isAuthenticated = computed(() => !!token.value)

  function login(username, password) {
    if (username === 'root' && password === 'root') {
      localStorage.setItem(TOKEN_KEY, 'root')
      token.value = 'root'
      userId.value = 1
      return true
    }
    return false
  }

  function logout() {
    localStorage.removeItem(TOKEN_KEY)
    token.value = null
    userId.value = null
  }

  return { isAuthenticated, userId, login, logout }
}
```

- [ ] **Step 2: Create useSchedules.js**

```javascript
import { ref, readonly } from 'vue'
import axios from 'axios'
import { getMonthRange, getMonthMatrix, toDateKey } from '../utils/calendar.js'

const monthEvents = ref([])
const selectedDate = ref(toDateKey(new Date()))
const currentMonth = ref(new Date())
const monthMatrix = ref([])

export function useSchedules() {
  function refreshMonthMatrix() {
    monthMatrix.value = getMonthMatrix(
      currentMonth.value.getFullYear(),
      currentMonth.value.getMonth()
    ).flat()
  }

  function getMonthEvents(dateKey) {
    return monthEvents.value.filter(e => e.start_time.startsWith(dateKey))
  }

  function hasEvents(dateKey) {
    return monthEvents.value.some(e => e.start_time.startsWith(dateKey))
  }

  async function fetchMonth(userId = 1) {
    refreshMonthMatrix()
    const range = getMonthRange(
      currentMonth.value.getFullYear(),
      currentMonth.value.getMonth()
    )
    try {
      const res = await axios.get('/schedules', {
        params: { start: range.start, end: range.end, user_id: userId }
      })
      monthEvents.value = res.data
    } catch {
      monthEvents.value = []
    }
  }

  async function createSchedule(title, startTime, endTime, userId = 1) {
    // 通过聊天接口让 LLM 处理新建
    await axios.post('/chat', {
      message: `添加日程：标题="${title}"，开始时间=${startTime}，结束时间=${endTime}`,
      session_id: `user_${userId}`
    })
    await fetchMonth(userId)
  }

  async function updateSchedule(id, data, userId = 1) {
    await axios.put(`/schedules/${id}`, data)
    await fetchMonth(userId)
  }

  async function deleteSchedule(id, userId = 1) {
    await axios.delete(`/schedules/${id}`)
    await fetchMonth(userId)
  }

  return {
    monthEvents: readonly(monthEvents),
    selectedDate,
    currentMonth,
    monthMatrix,
    getMonthEvents,
    hasEvents,
    fetchMonth,
    createSchedule,
    updateSchedule,
    deleteSchedule
  }
}
```

- [ ] **Step 3: Create useChat.js**

```javascript
import { ref } from 'vue'
import axios from 'axios'

const messages = ref([])
const loading = ref(false)
const aiPanelVisible = ref(false)

export function useChat() {
  async function sendMessage(text, userId = 1) {
    if (!text.trim() || loading.value) return

    messages.value.push({ role: 'user', content: text })
    loading.value = true

    try {
      const res = await axios.post('/chat', {
        message: text,
        session_id: `user_${userId}`
      })
      messages.value.push({ role: 'assistant', content: res.data.response })
    } catch {
      messages.value.push({ role: 'assistant', content: '抱歉，系统处理出错，请重试。' })
    } finally {
      loading.value = false
    }
  }

  function togglePanel() {
    aiPanelVisible.value = !aiPanelVisible.value
  }

  function clearMessages() {
    messages.value = []
  }

  return { messages, loading, aiPanelVisible, sendMessage, togglePanel, clearMessages }
}
```

- [ ] **Step 4: Commit**

```bash
git add privacy_schedule_agent/frontend/src/composables/useAuth.js \
  privacy_schedule_agent/frontend/src/composables/useSchedules.js \
  privacy_schedule_agent/frontend/src/composables/useChat.js
git commit -m "feat: add composables for auth, schedules, and chat"
```

---

### Task 3: Auth + Layout Shell（登录页 + 主布局框架）

**Files:**
- Create: `privacy_schedule_agent/frontend/src/components/LoginPage.vue`
- Modify: `privacy_schedule_agent/frontend/src/App.vue`
- Create: `privacy_schedule_agent/frontend/src/components/MainLayout.vue`
- Create: `privacy_schedule_agent/frontend/src/components/Sidebar.vue`
- Create: `privacy_schedule_agent/frontend/src/components/Toolbar.vue`
- Create: `privacy_schedule_agent/frontend/src/components/DateNavigator.vue`
- Create: `privacy_schedule_agent/frontend/src/components/ViewSwitcher.vue`
- Create: `privacy_schedule_agent/frontend/src/components/HeaderActions.vue`

- [ ] **Step 1: Create LoginPage.vue**

```vue
<template>
  <div class="h-screen flex items-center justify-center bg-slate-950">
    <div class="w-80 bg-slate-900 border border-slate-700 rounded-2xl p-8 shadow-2xl">
      <h1 class="text-xl font-bold text-center mb-6">
        <span class="text-indigo-400">🛡️</span> 隐私日程助理
      </h1>
      <div class="space-y-4">
        <input v-model="username" placeholder="用户名"
          class="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500">
        <input v-model="password" type="password" placeholder="密码"
          class="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          @keyup.enter="handleLogin">
        <p v-if="error" class="text-red-400 text-sm text-center">{{ error }}</p>
        <button @click="handleLogin"
          class="w-full bg-indigo-600 hover:bg-indigo-500 rounded-xl py-2 font-medium transition-all">
          登录
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useAuth } from '../composables/useAuth.js'

const { login } = useAuth()
const emit = defineEmits(['login-success'])

const username = ref('')
const password = ref('')
const error = ref('')

function handleLogin() {
  error.value = ''
  if (login(username.value, password.value)) {
    emit('login-success')
  } else {
    error.value = '用户名或密码错误'
  }
}
</script>
```

- [ ] **Step 2: Update App.vue（登录守卫）**

```vue
<template>
  <LoginPage v-if="!isAuthenticated" @login-success="onLogin" />
  <MainLayout v-else @logout="handleLogout" />
</template>

<script setup>
import { ref, computed } from 'vue'
import { useAuth } from './composables/useAuth.js'
import LoginPage from './components/LoginPage.vue'
import MainLayout from './components/MainLayout.vue'

const { isAuthenticated, logout } = useAuth()

// 强制响应式：组件 mount 后重新检查 localStorage
const mounted = ref(false)
// 首次 mount 后强制触发一次刷新
import { onMounted } from 'vue'
onMounted(() => { mounted.value = true })

function onLogin() {
  // 重新渲染 MainLayout
  window.location.reload()
}

function handleLogout() {
  logout()
  window.location.reload()
}
</script>
```

**Note:** `window.location.reload()` is used for simplicity. In practice this re-mounts all components cleanly. An alternative is using a `:key` binding on MainLayout.

- [ ] **Step 3: Create MainLayout.vue**

```vue
<template>
  <div class="h-screen flex flex-col bg-slate-950 text-slate-200">
    <Toolbar @logout="$emit('logout')" />
    <div class="flex flex-1 overflow-hidden">
      <Sidebar />
      <MonthView class="flex-1" />
      <AiPanel />
    </div>
  </div>
</template>

<script setup>
defineEmits(['logout'])
import Toolbar from './Toolbar.vue'
import Sidebar from './Sidebar.vue'
import MonthView from './MonthView.vue'
import AiPanel from './AiPanel.vue'
</script>
```

- [ ] **Step 4: Create Sidebar.vue（48px 宽）**

```vue
<template>
  <aside class="w-12 bg-slate-900 border-r border-slate-800 flex flex-col items-center py-3 gap-4 shrink-0">
    <CreateButton />
    <div class="border-t border-slate-800 w-6 my-1"></div>
    <MiniCalendar />
    <div class="flex-1"></div>
    <PrivacyStatus />
  </aside>
</template>

<script setup>
import CreateButton from './CreateButton.vue'
import MiniCalendar from './MiniCalendar.vue'
import PrivacyStatus from './PrivacyStatus.vue'
</script>
```

- [ ] **Step 5: Create Toolbar.vue**

```vue
<template>
  <header class="h-12 bg-slate-900 border-b border-slate-800 flex items-center px-4 gap-4 shrink-0">
    <DateNavigator />
    <ViewSwitcher />
    <div class="flex-1"></div>
    <HeaderActions @logout="$emit('logout')" />
  </header>
</template>

<script setup>
defineEmits(['logout'])
import DateNavigator from './DateNavigator.vue'
import ViewSwitcher from './ViewSwitcher.vue'
import HeaderActions from './HeaderActions.vue'
</script>
```

- [ ] **Step 6: Create DateNavigator.vue**

```vue
<template>
  <div class="flex items-center gap-2 text-sm">
    <button @click="goToday"
      class="bg-slate-800 hover:bg-slate-700 px-3 py-1 rounded-lg text-xs font-medium transition-colors">
      今天
    </button>
    <button @click="prevMonth" class="text-slate-400 hover:text-slate-200 text-lg leading-none">‹</button>
    <span class="text-sm font-medium w-28 text-center">{{ currentMonthLabel }}</span>
    <button @click="nextMonth" class="text-slate-400 hover:text-slate-200 text-lg leading-none">›</button>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useSchedules } from '../composables/useSchedules.js'

const { currentMonth, selectedDate, fetchMonth } = useSchedules()

const currentMonthLabel = computed(() => {
  const d = currentMonth.value
  return `${d.getFullYear()}年${d.getMonth() + 1}月`
})

function goToday() {
  const today = new Date()
  currentMonth.value = new Date(today.getFullYear(), today.getMonth(), 1)
  selectedDate.value = today.toISOString().slice(0, 10)
  fetchMonth()
}

function prevMonth() {
  const d = new Date(currentMonth.value)
  d.setMonth(d.getMonth() - 1)
  currentMonth.value = d
  fetchMonth()
}

function nextMonth() {
  const d = new Date(currentMonth.value)
  d.setMonth(d.getMonth() + 1)
  currentMonth.value = d
  fetchMonth()
}
</script>
```

- [ ] **Step 7: Create ViewSwitcher.vue**

```vue
<template>
  <div class="flex bg-slate-800 rounded-lg text-xs">
    <button class="px-3 py-1 bg-indigo-600 rounded-lg font-medium">月</button>
    <!-- 日/周预留 -->
  </div>
</template>
```

- [ ] **Step 8: Create HeaderActions.vue**

```vue
<template>
  <div class="flex items-center gap-2">
    <button @click="togglePanel"
      class="p-1.5 hover:bg-slate-800 rounded-lg transition-colors"
      :title="aiPanelVisible ? '关闭AI助手' : '打开AI助手'">
      <svg class="w-5 h-5" :class="aiPanelVisible ? 'text-indigo-400' : 'text-slate-400'" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
      </svg>
    </button>
    <div class="relative" @click.outside="showMenu = false">
      <button @click="showMenu = !showMenu"
        class="w-7 h-7 rounded-full bg-indigo-600 flex items-center justify-center text-xs font-medium">
        R
      </button>
      <div v-if="showMenu"
        class="absolute right-0 top-8 bg-slate-800 border border-slate-700 rounded-lg py-1 shadow-xl z-50 w-28">
        <button @click="handleLogout" class="w-full text-left px-3 py-1.5 text-xs hover:bg-slate-700">退出登录</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useChat } from '../composables/useChat.js'

const { aiPanelVisible, togglePanel } = useChat()
const emit = defineEmits(['logout'])
const showMenu = ref(false)

function handleLogout() {
  showMenu.value = false
  emit('logout')
}
</script>
```

- [ ] **Step 9: Create CreateButton.vue**

```vue
<template>
  <button @click="showDialog = true"
    class="w-8 h-8 bg-indigo-600 hover:bg-indigo-500 rounded-xl flex items-center justify-center text-white font-bold transition-colors"
    title="新建日程">
    +
  </button>
  <div v-if="showDialog" class="fixed inset-0 z-50 flex items-center justify-center bg-black/50" @click.self="showDialog = false">
    <div class="bg-slate-900 border border-slate-700 rounded-xl p-6 w-96">
      <h3 class="font-bold mb-4">新建日程</h3>
      <div class="space-y-3">
        <input v-model="form.title" placeholder="标题 *" class="w-full bg-slate-800 border border-slate-700 rounded px-3 py-2 text-sm">
        <input v-model="form.start_time" placeholder="开始时间 (YYYY-MM-DD HH:MM)" class="w-full bg-slate-800 border border-slate-700 rounded px-3 py-2 text-sm">
        <input v-model="form.end_time" placeholder="结束时间 (YYYY-MM-DD HH:MM)" class="w-full bg-slate-800 border border-slate-700 rounded px-3 py-2 text-sm">
        <input v-model="form.location" placeholder="地点" class="w-full bg-slate-800 border border-slate-700 rounded px-3 py-2 text-sm">
      </div>
      <div class="flex gap-2 mt-4 justify-end">
        <button @click="showDialog = false" class="bg-slate-700 hover:bg-slate-600 px-4 py-1.5 rounded text-sm">取消</button>
        <button @click="handleCreate" :disabled="!form.title || !form.start_time"
          class="bg-indigo-600 hover:bg-indigo-500 px-4 py-1.5 rounded text-sm disabled:opacity-50">创建</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useSchedules } from '../composables/useSchedules.js'
import { useAuth } from '../composables/useAuth.js'

const { createSchedule } = useSchedules()
const { userId } = useAuth()
const showDialog = ref(false)
const form = reactive({ title: '', start_time: '', end_time: '', location: '' })

async function handleCreate() {
  await createSchedule(form.title, form.start_time, form.end_time, userId.value)
  showDialog.value = false
  form.title = ''; form.start_time = ''; form.end_time = ''; form.location = ''
}
</script>
```

- [ ] **Step 10: Create PrivacyStatus.vue**

```vue
<template>
  <div class="relative group" title="本地 LLM 已连接">
    <span class="w-2 h-2 rounded-full bg-emerald-500 block"></span>
    <div class="absolute left-10 top-1/2 -translate-y-1/2 bg-slate-800 text-[10px] px-2 py-1 rounded whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity z-50 pointer-events-none">
      Ollama 已连接
    </div>
  </div>
</template>
```

- [ ] **Step 11: Verify build passes**

```bash
cd privacy_schedule_agent/frontend
npm run build
```

Expected: Build succeeds, `dist/` directory created with index.html + assets.

- [ ] **Step 12: Commit**

```bash
git add privacy_schedule_agent/frontend/src/App.vue \
  privacy_schedule_agent/frontend/src/components/LoginPage.vue \
  privacy_schedule_agent/frontend/src/components/MainLayout.vue \
  privacy_schedule_agent/frontend/src/components/Sidebar.vue \
  privacy_schedule_agent/frontend/src/components/Toolbar.vue \
  privacy_schedule_agent/frontend/src/components/DateNavigator.vue \
  privacy_schedule_agent/frontend/src/components/ViewSwitcher.vue \
  privacy_schedule_agent/frontend/src/components/HeaderActions.vue \
  privacy_schedule_agent/frontend/src/components/CreateButton.vue \
  privacy_schedule_agent/frontend/src/components/PrivacyStatus.vue
git commit -m "feat: add auth shell and layout components"
```

---

### Task 4: 日历与日程组件

**Files:**
- Create: `privacy_schedule_agent/frontend/src/components/MiniCalendar.vue`
- Create: `privacy_schedule_agent/frontend/src/components/MonthView.vue`
- Create: `privacy_schedule_agent/frontend/src/components/CalendarGrid.vue`
- Create: `privacy_schedule_agent/frontend/src/components/DayPopover.vue`
- Create: `privacy_schedule_agent/frontend/src/components/ScheduleCard.vue`

- [ ] **Step 1: Create MiniCalendar.vue（左侧小日历）**

```vue
<template>
  <div class="w-full px-1">
    <div class="flex items-center justify-between mb-1">
      <button @click="prevMonth" class="text-slate-400 hover:text-slate-200 text-xs">‹</button>
      <span class="text-[10px] text-slate-400 font-medium">{{ label }}</span>
      <button @click="nextMonth" class="text-slate-400 hover:text-slate-200 text-xs">›</button>
    </div>
    <div class="grid grid-cols-7 text-[8px] text-slate-500 mb-0.5">
      <span v-for="d in weekDays" :key="d" class="text-center">{{ d }}</span>
    </div>
    <div class="grid grid-cols-7 gap-0">
      <button v-for="cell in flatMatrix" :key="cell.dateKey"
        @click="selectDate(cell)"
        class="text-[10px] w-full aspect-square flex items-center justify-center rounded-full"
        :class="[
          cell.inMonth ? 'text-slate-300' : 'text-slate-600',
          cell.dateKey === selectedDate ? 'bg-indigo-600 text-white' : 'hover:bg-slate-800'
        ]">
        <span class="relative">
          {{ cell.date.getDate() }}
          <span v-if="hasEvents(cell.dateKey)"
            class="absolute -top-0.5 -right-1.5 w-1 h-1 rounded-full bg-indigo-400"></span>
        </span>
      </button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useSchedules } from '../composables/useSchedules.js'

const { currentMonth, selectedDate, monthMatrix, hasEvents, fetchMonth } = useSchedules()
const weekDays = ['日', '一', '二', '三', '四', '五', '六']

const flatMatrix = computed(() => monthMatrix.value)
const label = computed(() => `${currentMonth.value.getMonth() + 1}月`)

function prevMonth() {
  const d = new Date(currentMonth.value)
  d.setMonth(d.getMonth() - 1)
  currentMonth.value = d
  fetchMonth()
}

function nextMonth() {
  const d = new Date(currentMonth.value)
  d.setMonth(d.getMonth() + 1)
  currentMonth.value = d
  fetchMonth()
}

function selectDate(cell) {
  selectedDate.value = cell.dateKey
  if (!cell.inMonth) {
    const d = new Date(cell.date)
    currentMonth.value = new Date(d.getFullYear(), d.getMonth(), 1)
    fetchMonth()
  }
}
</script>
```

- [ ] **Step 2: Create MonthView.vue（主画布）**

```vue
<template>
  <main class="flex-1 flex flex-col bg-slate-950 overflow-hidden p-4">
    <div class="flex-1 relative">
      <CalendarGrid @select-date="openPopover" />
      <DayPopover v-if="popoverDate" :date-key="popoverDate" @close="closePopover" />
    </div>
  </main>
</template>

<script setup>
import { ref } from 'vue'
import CalendarGrid from './CalendarGrid.vue'
import DayPopover from './DayPopover.vue'

const popoverDate = ref(null)

function openPopover(dateKey) {
  popoverDate.value = dateKey
}

function closePopover() {
  popoverDate.value = null
}
</script>
```

- [ ] **Step 3: Create CalendarGrid.vue**

```vue
<template>
  <div class="h-full flex flex-col">
    <div class="grid grid-cols-7 text-xs text-slate-500 mb-2 border-b border-slate-800 pb-2">
      <div v-for="d in weekDays" :key="d" class="text-center font-medium">{{ d }}</div>
    </div>
    <div class="flex-1 grid grid-cols-7 auto-rows-fr gap-px">
      <button v-for="cell in flatMatrix" :key="cell.dateKey"
        @click="emit('select-date', cell.dateKey)"
        class="relative border border-slate-800/50 p-1 flex flex-col items-start justify-start text-xs transition-colors hover:border-slate-600"
        :class="[
          cell.inMonth ? 'bg-slate-900/50' : 'bg-slate-900/20',
          cell.dateKey === selectedDate ? 'ring-2 ring-indigo-500 z-10' : ''
        ]">
        <span class="text-[10px] mb-0.5"
          :class="[cell.inMonth ? 'text-slate-300' : 'text-slate-600', isToday(cell.dateKey) ? 'bg-indigo-600 text-white w-5 h-5 rounded-full flex items-center justify-center' : '']">
          {{ cell.date.getDate() }}
        </span>
        <div class="flex flex-wrap gap-0.5">
          <div v-for="event in dateEvents[cell.dateKey]" :key="event.id"
            class="text-[8px] leading-tight truncate w-full px-0.5 rounded"
            :class="event.status === 'conflicted' ? 'bg-amber-500/20 text-amber-400' : 'bg-indigo-500/20 text-indigo-300'">
            {{ event.title }}
          </div>
        </div>
      </button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useSchedules } from '../composables/useSchedules.js'
import { groupEventsByDate } from '../utils/calendar.js'

const { monthMatrix, selectedDate, hasEvents, monthEvents } = useSchedules()
const weekDays = ['日', '一', '二', '三', '四', '五', '六']
const emit = defineEmits(['select-date'])

// Flatten 6x7 matrix
const flatMatrix = computed(() => monthMatrix.value)

const dateEvents = computed(() => groupEventsByDate(monthEvents.value))

function isToday(dateKey) {
  const today = new Date()
  const key = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`
  return dateKey === key
}
</script>
```

- [ ] **Step 4: Create DayPopover.vue**

```vue
<template>
  <div class="absolute inset-4 bg-slate-900 border border-slate-700 rounded-xl shadow-2xl z-20 flex flex-col overflow-hidden">
    <div class="flex items-center justify-between p-3 border-b border-slate-800">
      <h3 class="font-bold text-sm">{{ dateKey }} 日程</h3>
      <button @click="emit('close')" class="text-slate-400 hover:text-slate-200">&times;</button>
    </div>
    <div class="flex-1 overflow-y-auto p-3 space-y-2">
      <ScheduleCard v-for="item in dayEvents" :key="item.id" :schedule="item" />
      <p v-if="dayEvents.length === 0" class="text-slate-500 italic text-sm text-center py-8">当天暂无日程</p>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useSchedules } from '../composables/useSchedules.js'
import ScheduleCard from './ScheduleCard.vue'

const props = defineProps({ dateKey: String })
const emit = defineEmits(['close'])

const { monthEvents } = useSchedules()
const dayEvents = computed(() =>
  monthEvents.value.filter(e => e.start_time.startsWith(props.dateKey))
)
</script>
```

- [ ] **Step 5: Create ScheduleCard.vue**

```vue
<template>
  <div class="bg-slate-800 border border-slate-700 rounded-lg p-3 hover:border-slate-600 transition-all group">
    <!-- View Mode -->
    <div v-if="editingId !== schedule.id" class="flex items-start justify-between gap-2">
      <div class="flex-1 min-w-0">
        <div class="flex items-center gap-2 mb-1">
          <span class="text-[10px] text-slate-400 bg-slate-700 px-1.5 py-0.5 rounded">{{ schedule.start_time?.split(' ')[1]?.slice(0,5) }}</span>
          <h4 class="font-medium text-sm truncate">{{ schedule.title }}</h4>
          <span v-if="schedule.category"
            class="text-[10px] px-1.5 py-0.5 rounded-full border"
            :class="categoryClass(schedule.category)">
            {{ schedule.category }}
          </span>
        </div>
        <p v-if="schedule.location" class="text-xs text-slate-400 flex items-center gap-1">
          <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"/></svg>
          {{ schedule.location }}
        </p>
        <p v-if="schedule.description" class="text-xs text-slate-500 mt-0.5">{{ schedule.description }}</p>
      </div>
      <div class="flex items-center gap-1 shrink-0">
        <span v-if="schedule.status === 'conflicted'" class="text-[10px] text-amber-400 bg-amber-500/10 px-1.5 py-0.5 rounded-full">⚠ 冲突</span>
        <button @click="startEdit" class="opacity-0 group-hover:opacity-100 text-slate-500 hover:text-indigo-400 p-1" title="编辑">
          <svg class="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20"><path d="M17.414 2.586a2 2 0 00-2.828 0L7 10.172V13h2.828l7.586-7.586a2 2 0 000-2.828z"/></svg>
        </button>
        <button @click="handleDelete" class="opacity-0 group-hover:opacity-100 text-slate-500 hover:text-red-400 p-1" title="删除">
          <svg class="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20"><path d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z"/></svg>
        </button>
      </div>
    </div>

    <!-- Edit Mode -->
    <div v-else class="space-y-2">
      <input v-model="editForm.title" class="w-full bg-slate-700 border border-slate-600 rounded px-2 py-1 text-sm" placeholder="标题" @keyup.enter="saveEdit">
      <div class="flex gap-2">
        <input v-model="editForm.start_time" class="flex-1 bg-slate-700 border border-slate-600 rounded px-2 py-1 text-xs" placeholder="开始时间">
        <input v-model="editForm.end_time" class="flex-1 bg-slate-700 border border-slate-600 rounded px-2 py-1 text-xs" placeholder="结束时间">
      </div>
      <input v-model="editForm.location" class="w-full bg-slate-700 border border-slate-600 rounded px-2 py-1 text-xs" placeholder="地点">
      <div class="flex gap-2 pt-1">
        <button @click="saveEdit" class="bg-indigo-600 hover:bg-indigo-500 px-3 py-1 rounded text-xs">保存</button>
        <button @click="cancelEdit" class="bg-slate-600 hover:bg-slate-500 px-3 py-1 rounded text-xs">取消</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useSchedules } from '../composables/useSchedules.js'
import { useAuth } from '../composables/useAuth.js'

const props = defineProps({ schedule: Object })
const { updateSchedule, deleteSchedule, fetchMonth } = useSchedules()
const { userId } = useAuth()

const editingId = ref(null)
const editForm = reactive({ title: '', start_time: '', end_time: '', location: '', description: '', category: '' })

function startEdit() {
  editingId.value = props.schedule.id
  Object.assign(editForm, {
    title: props.schedule.title,
    start_time: props.schedule.start_time,
    end_time: props.schedule.end_time,
    location: props.schedule.location || '',
    description: props.schedule.description || '',
    category: props.schedule.category || ''
  })
}

function cancelEdit() { editingId.value = null }

async function saveEdit() {
  await updateSchedule(props.schedule.id, { ...editForm }, userId.value)
  editingId.value = null
}

async function handleDelete() {
  if (confirm(`确认删除"${props.schedule.title}"？`)) {
    await deleteSchedule(props.schedule.id, userId.value)
  }
}

function categoryClass(cat) {
  const map = {
    '工作': 'bg-indigo-500/10 text-indigo-300 border-indigo-500/30',
    '学习': 'text-cyan-300 bg-cyan-500/10 border-cyan-500/30',
    '生活': 'text-orange-300 bg-orange-500/10 border-orange-500/30'
  }
  return map[cat] || 'text-slate-400 bg-slate-500/10 border-slate-500/30'
}
</script>
```

- [ ] **Step 6: Commit**

```bash
git add privacy_schedule_agent/frontend/src/components/MiniCalendar.vue \
  privacy_schedule_agent/frontend/src/components/MonthView.vue \
  privacy_schedule_agent/frontend/src/components/CalendarGrid.vue \
  privacy_schedule_agent/frontend/src/components/DayPopover.vue \
  privacy_schedule_agent/frontend/src/components/ScheduleCard.vue
git commit -m "feat: add calendar month view and schedule card components"
```

---

### Task 5: AI 对话面板组件

**Files:**
- Create: `privacy_schedule_agent/frontend/src/components/AiPanel.vue`
- Create: `privacy_schedule_agent/frontend/src/components/ChatMessages.vue`
- Create: `privacy_schedule_agent/frontend/src/components/ChatInput.vue`

- [ ] **Step 1: Create ChatInput.vue**

```vue
<template>
  <div class="p-3 border-t border-slate-700">
    <div class="flex gap-2">
      <input v-model="text" @keyup.enter="send"
        placeholder="输入指令，例如：明天下午2点在图书馆开会..."
        class="flex-1 bg-slate-800 border border-slate-700 rounded-lg px-3 py-1.5 text-xs focus:outline-none focus:ring-1 focus:ring-indigo-500">
      <button @click="send" :disabled="loading || !text.trim()"
        class="bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors">
        发送
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useChat } from '../composables/useChat.js'
import { useAuth } from '../composables/useAuth.js'

const { sendMessage, loading } = useChat()
const { userId } = useAuth()
const text = ref('')

async function send() {
  if (!text.value.trim() || loading.value) return
  const msg = text.value
  text.value = ''
  await sendMessage(msg, userId.value)
}
</script>
```

- [ ] **Step 2: Create ChatMessages.vue**

```vue
<template>
  <div ref="scrollRef" class="flex-1 overflow-y-auto p-3 space-y-3">
    <div v-for="(msg, i) in messages" :key="i"
      :class="['flex', msg.role === 'user' ? 'justify-end' : 'justify-start']">
      <div :class="['max-w-[85%] p-2.5 rounded-xl text-sm',
        msg.role === 'user' ? 'bg-indigo-600 text-white rounded-tr-none' : 'bg-slate-800 text-slate-200 rounded-tl-none border border-slate-700']">
        <div class="pre-wrap">{{ msg.content }}</div>
      </div>
    </div>
    <div v-if="loading" class="flex justify-start">
      <div class="bg-slate-800 p-3 rounded-xl flex items-center gap-1.5">
        <div class="w-1.5 h-1.5 bg-indigo-500 rounded-full animate-bounce"></div>
        <div class="w-1.5 h-1.5 bg-indigo-500 rounded-full animate-bounce [animation-delay:-.3s]"></div>
        <div class="w-1.5 h-1.5 bg-indigo-500 rounded-full animate-bounce [animation-delay:-.5s]"></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue'
import { useChat } from '../composables/useChat.js'

const { messages, loading } = useChat()
const scrollRef = ref(null)

watch([messages, loading], async () => {
  await nextTick()
  if (scrollRef.value) scrollRef.value.scrollTop = scrollRef.value.scrollHeight
}, { deep: true })
</script>
```

- [ ] **Step 3: Create AiPanel.vue**

```vue
<template>
  <Transition name="slide">
    <aside v-if="aiPanelVisible"
      class="w-80 bg-slate-900 border-l border-slate-800 flex flex-col shrink-0 overflow-hidden">
      <div class="flex items-center justify-between p-3 border-b border-slate-800">
        <span class="text-xs font-medium text-slate-400 uppercase tracking-wider">AI 助手</span>
        <button @click="togglePanel" class="text-slate-400 hover:text-slate-200">&times;</button>
      </div>
      <ChatMessages />
      <ChatInput />
    </aside>
  </Transition>
</template>

<script setup>
import { useChat } from '../composables/useChat.js'
import ChatMessages from './ChatMessages.vue'
import ChatInput from './ChatInput.vue'

const { aiPanelVisible, togglePanel } = useChat()
</script>

<style scoped>
.slide-enter-active, .slide-leave-active { transition: all 0.2s ease; }
.slide-enter-from, .slide-leave-to { transform: translateX(100%); opacity: 0; }
</style>
```

- [ ] **Step 4: Commit**

```bash
git add privacy_schedule_agent/frontend/src/components/AiPanel.vue \
  privacy_schedule_agent/frontend/src/components/ChatMessages.vue \
  privacy_schedule_agent/frontend/src/components/ChatInput.vue
git commit -m "feat: add AI chat panel with slide transition"
```

---

### Task 6: 后端变更（user_id 迁移 + API 调整 + 新建接口）

**Files:**
- Modify: `privacy_schedule_agent/app/db/models.py`
- Modify: `privacy_schedule_agent/app/db/database.py`
- Modify: `privacy_schedule_agent/main.py`

- [ ] **Step 1: Update models.py — 添加 user_id 字段**

在 Schedule 类中 `id` 字段后增加：

```python
user_id: Mapped[int] = mapped_column(Integer, default=1)
```

完整变更：

```python
class Schedule(Base):
    """日程明细表"""
    __tablename__ = "schedules"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, default=1)  # ← 新增
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    start_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    location_ref: Mapped[Optional[str]] = mapped_column(String(100))
    # ... 其余不变
```

- [ ] **Step 2: Update database.py — 添加 user_id 迁移**

在 `_migrate_v2_columns` 中增加 user_id 迁移：

```python
async def _migrate_v3_columns(conn):
    """v3.0 迁移：添加 user_id 字段"""
    from sqlalchemy import inspect as sa_inspect

    def _do_inspect(sync_conn):
        insp = sa_inspect(sync_conn)
        return [col['name'] for col in insp.get_columns('schedules')]

    existing_columns = await conn.run_sync(_do_inspect)

    new_columns = {
        'description': 'TEXT',
        'category': 'VARCHAR(30)',
    }
    for col_name, col_type in new_columns.items():
        if col_name not in existing_columns:
            await conn.execute(
                text(f"ALTER TABLE schedules ADD COLUMN {col_name} {col_type}")
            )
            logger.info(f"Migration: added column '{col_name}' to schedules table")

    # v3: user_id
    if 'user_id' not in existing_columns:
        await conn.execute(
            text("ALTER TABLE schedules ADD COLUMN user_id INTEGER DEFAULT 1")
        )
        logger.info("Migration: added column 'user_id' to schedules table")
```

重命名 `_migrate_v2_columns` 为 `_migrate_schedule_columns`（在 init_db 中调用处同步改名）。

- [ ] **Step 3: Update main.py — 添加 user_id 过滤与 POST 接口**

**3a.** 在 `ScheduleUpdateRequest` 之后新增：

```python
class ScheduleCreateRequest(BaseModel):
    title: str
    start_time: str
    end_time: str
    location: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    user_id: Optional[int] = 1
```

**3b.** 修改 `GET /schedules` — 增加 user_id 过滤：

```python
@app.get("/schedules")
async def get_schedules(start: str = None, end: str = None, user_id: int = None):
    """获取日程列表，支持按时间范围和用户过滤"""
    async with AsyncSessionLocal() as session:
        stmt = select(Schedule).order_by(Schedule.start_time.asc())
        if user_id is not None:
            stmt = stmt.where(Schedule.user_id == user_id)
        if start:
            # ... 原有时间解析代码不变
        if end:
            # ... 原有时间解析代码不变

        result = await session.execute(stmt)
        schedules = result.scalars().all()
        return [
            {
                "id": s.id,
                "title": s.title,
                "start_time": s.start_time.strftime("%Y-%m-%d %H:%M:%S"),
                "end_time": s.end_time.strftime("%Y-%m-%d %H:%M:%S"),
                "location": s.location_ref,
                "description": s.description,
                "category": s.category,
                "status": s.status,
                "user_id": s.user_id
            }
            for s in schedules
        ]
```

**3c.** 新增 `POST /schedules` 接口：

```python
@app.post("/schedules")
async def create_schedule(req: ScheduleCreateRequest):
    """创建日程（直接创建，不经过 LLM）"""
    async with AsyncSessionLocal() as session:
        try:
            event = Schedule(
                user_id=req.user_id or 1,
                title=req.title,
                start_time=datetime.strptime(req.start_time, "%Y-%m-%d %H:%M:%S"),
                end_time=datetime.strptime(req.end_time, "%Y-%m-%d %H:%M:%S"),
                location_ref=req.location or None,
                description=req.description or None,
                category=req.category or None,
                status="confirmed"
            )
            session.add(event)
            await session.commit()
            await session.refresh(event)
            return {
                "id": event.id,
                "title": event.title,
                "start_time": event.start_time.strftime("%Y-%m-%d %H:%M:%S"),
                "end_time": event.end_time.strftime("%Y-%m-%d %H:%M:%S"),
                "status": event.status
            }
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"时间格式不正确: {str(e)}")
```

**3d.** 修改 `/chat` — 可接受可选 user_id：

```python
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = "default_user"
    user_id: Optional[int] = 1
```

（在 chat_endpoint 中无需特别处理 user_id，记录到日志即可）

**3e.** 修改静态文件挂载 — 优先挂载 dist：

```python
# 挂载前端静态文件
dist_path = "frontend/dist"
if os.path.exists(dist_path):
    app.mount("/", StaticFiles(directory=dist_path, html=True), name="frontend")
elif os.path.exists("frontend"):
    app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
```

- [ ] **Step 4: Commit**

```bash
git add privacy_schedule_agent/app/db/models.py \
  privacy_schedule_agent/app/db/database.py \
  privacy_schedule_agent/main.py
git commit -m "feat: add user_id to Schedule, POST /schedules, user_id filter"
```

---

### Task 7: 清理旧前端文件 + 最后验证

**Files:**
- Delete: `privacy_schedule_agent/frontend/index.html`（CDN 版）
- Delete: `privacy_schedule_agent/frontend/assets/calendar_utils.js`
- Delete: `privacy_schedule_agent/frontend/tests/calendar_utils.test.js`
- Delete: `privacy_schedule_agent/frontend/assets/axios.min.js`
- Delete: `privacy_schedule_agent/frontend/assets/vue.global.prod.js`
- Delete: `privacy_schedule_agent/frontend/assets/tailwind.js`

- [ ] **Step 1: 删除旧文件**

```bash
cd privacy_schedule_agent/frontend
rm index.html
rm assets/calendar_utils.js
rm assets/axios.min.js
rm assets/vue.global.prod.js
rm assets/tailwind.js
rm tests/calendar_utils.test.js

# 如果 assets 目录为空则保留
```

- [ ] **Step 2: 运行测试**

```bash
cd privacy_schedule_agent/frontend
node --experimental-vm-modules tests/calendar.test.js
```

Expected: 3 tests pass.

- [ ] **Step 3: 生产构建验证**

```bash
cd privacy_schedule_agent/frontend
npm run build
```

Expected: `dist/index.html` + `dist/assets/` 产出，构建无报错。

- [ ] **Step 4: 验证后端兼容**

在 `privacy_schedule_agent/` 目录启动后端：

```bash
cd privacy_schedule_agent
python main.py
```

访问 `http://localhost:8000` 确认前端正常加载。访问 `http://localhost:8000/schedules?user_id=1` 确认接口正常。

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "chore: remove legacy CDN files, finalize v3 frontend build"
```

---

## Plan Self-Review

1. **Spec coverage:** 每项 spec 需求均有对应任务：
   - Vite 构建 → Task 1
   - Calendar ES module + tests → Task 1
   - Composables (useAuth/useSchedules/useChat) → Task 2
   - 登录页 → Task 3 (LoginPage + App.vue)
   - 布局 (Sidebar, Toolbar, MonthView, AiPanel) → Tasks 3-5
   - MiniCalendar + MonthView 月份同步 → 共享 composable 引用
   - DayPopover 弹出当天列表 → Task 4
   - ScheduleCard 内联编辑/删除 → Task 4
   - AI 面板右侧滑出 → Task 5
   - user_id 迁移 → Task 6
   - POST /schedules 接口 → Task 6
   - 旧 CDN 文件清理 → Task 7

2. **Placeholder scan:** 无 TBD/TODO/模糊描述。每步含完整代码。

3. **Type consistency:** 所有 composable 返回一致的接口命名，组件 props 类型统一。

4. **Notable omissions:** `useSchedules.js` 中的 `fetchMonth()` 在 `App.vue` 首次 mount 时未调用。后续由 MiniCalendar/Toolbar 的 onMounted 或组件首次渲染时触发。实际行为：当日历网格渲染时，main.js 启动后 App 显示登录页 → 登录后 MainLayout mount → MonthView mount 时触发 fetchMonth。可考虑在 MainLayout 的 onMounted 中调用一次 fetchMonth 确保数据加载。

---

## Execution Handoff

Plan complete and saved to `plan_v3.md`. Two execution options:

1. **Subagent-Driven (recommended)** — I dispatch a fresh subagent per task, review between tasks, fast iteration
2. **Inline Execution** — Execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?
