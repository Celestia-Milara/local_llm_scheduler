# v2.0 前端交互改造 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在前端实现“左侧月历 + 对话区 / 右侧当天列表”的布局，并支持日期切换、内联编辑、冲突弹窗提示。

**Architecture:** 以纯前端状态管理为主，新增日历工具函数与可测逻辑，UI 变更集中在 index.html。日历与列表通过 `selectedDate` 绑定，数据来自现有 `/schedules` 和 `/chat`。

**Tech Stack:** Vue (CDN), Axios, Tailwind (CDN), Node 内置 test runner

---

## File Structure / Responsibilities

- 新增: `privacy_schedule_agent/frontend/assets/calendar_utils.js`
  - 日历与筛选工具函数（可在浏览器与 Node 测试复用）
- 新增: `privacy_schedule_agent/frontend/tests/calendar_utils.test.js`
  - Node 内置测试，用于日历与筛选逻辑
- 修改: `privacy_schedule_agent/frontend/index.html`
  - 页面布局、状态、事件绑定、内联编辑与冲突弹窗

---

### Task 1: 新增可测试的日历工具函数

**Files:**
- Create: `privacy_schedule_agent/frontend/assets/calendar_utils.js`
- Create: `privacy_schedule_agent/frontend/tests/calendar_utils.test.js`

- [ ] **Step 1: Write failing tests**

```javascript
// privacy_schedule_agent/frontend/tests/calendar_utils.test.js
const test = require('node:test');
const assert = require('node:assert/strict');

const utils = require('../assets/calendar_utils.js');

test('getMonthMatrix returns 6x7 grid and flags inMonth', () => {
  const matrix = utils.getMonthMatrix(2026, 3); // 2026-04
  assert.equal(matrix.length, 6);
  matrix.forEach((week) => assert.equal(week.length, 7));

  const april1 = matrix.flat().find((d) => d.dateKey === '2026-04-01');
  assert.ok(april1);
  assert.equal(april1.inMonth, true);
});

test('groupEventsByDate groups events using dateKey', () => {
  const events = [
    { id: 1, start_time: '2026-04-10 09:00:00' },
    { id: 2, start_time: '2026-04-10 11:00:00' },
    { id: 3, start_time: '2026-04-11 10:00:00' }
  ];
  const grouped = utils.groupEventsByDate(events);
  assert.equal(grouped['2026-04-10'].length, 2);
  assert.equal(grouped['2026-04-11'].length, 1);
});

test('getMonthRange returns correct start/end strings', () => {
  const range = utils.getMonthRange(2026, 3);
  assert.equal(range.start, '2026-04-01 00:00:00');
  assert.equal(range.end, '2026-04-30 23:59:59');
});
```

- [ ] **Step 2: Run tests to verify failure**

Run: `node --test privacy_schedule_agent/frontend/tests/calendar_utils.test.js`

Expected: FAIL with module not found for `calendar_utils.js`.

- [ ] **Step 3: Implement minimal utils**

```javascript
// privacy_schedule_agent/frontend/assets/calendar_utils.js
(function (root, factory) {
  if (typeof module === 'object' && module.exports) {
    module.exports = factory();
  } else {
    root.CalendarUtils = factory();
  }
})(this, function () {
  const pad2 = (n) => String(n).padStart(2, '0');

  const toDateKey = (date) => {
    const yyyy = date.getFullYear();
    const mm = pad2(date.getMonth() + 1);
    const dd = pad2(date.getDate());
    return `${yyyy}-${mm}-${dd}`;
  };

  const getMonthMatrix = (year, monthIndex) => {
    const first = new Date(year, monthIndex, 1);
    const start = new Date(first);
    start.setDate(1 - first.getDay());

    const weeks = [];
    let cursor = new Date(start);
    for (let w = 0; w < 6; w += 1) {
      const week = [];
      for (let d = 0; d < 7; d += 1) {
        const date = new Date(cursor);
        week.push({
          date,
          dateKey: toDateKey(date),
          inMonth: date.getMonth() === monthIndex
        });
        cursor.setDate(cursor.getDate() + 1);
      }
      weeks.push(week);
    }
    return weeks;
  };

  const groupEventsByDate = (events) => {
    return events.reduce((acc, event) => {
      const dateKey = event.start_time.slice(0, 10);
      acc[dateKey] = acc[dateKey] || [];
      acc[dateKey].push(event);
      return acc;
    }, {});
  };

  const getMonthRange = (year, monthIndex) => {
    const start = new Date(year, monthIndex, 1);
    const end = new Date(year, monthIndex + 1, 0);
    const startStr = `${start.getFullYear()}-${pad2(start.getMonth() + 1)}-01 00:00:00`;
    const endStr = `${end.getFullYear()}-${pad2(end.getMonth() + 1)}-${pad2(end.getDate())} 23:59:59`;
    return { start: startStr, end: endStr };
  };

  return { toDateKey, getMonthMatrix, groupEventsByDate, getMonthRange };
});
```

- [ ] **Step 4: Re-run tests**

Run: `node --test privacy_schedule_agent/frontend/tests/calendar_utils.test.js`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add privacy_schedule_agent/frontend/assets/calendar_utils.js \
  privacy_schedule_agent/frontend/tests/calendar_utils.test.js
git commit -m "test: add calendar utils with tests"
```

---

### Task 2: 更新页面布局为左侧月历+对话区，右侧事件列表

**Files:**
- Modify: `privacy_schedule_agent/frontend/index.html`

- [ ] **Step 1: Update HTML layout (Left calendar + chat, Right list)**

Replace the main content section with:

```html
<main class="flex flex-1 overflow-hidden">
  <!-- Left: Calendar + Chat -->
  <section class="w-[45%] border-r border-slate-700 flex flex-col bg-slate-900/30">
    <!-- Calendar -->
    <div class="p-4 border-b border-slate-700">
      <div class="flex items-center justify-between mb-3">
        <button @click="prevMonth" class="text-slate-400 hover:text-slate-200">&#x2039;</button>
        <h3 class="text-sm tracking-widest text-slate-400 uppercase">
          {{ currentMonthLabel }}
        </h3>
        <button @click="nextMonth" class="text-slate-400 hover:text-slate-200">&#x203A;</button>
      </div>
      <div class="grid grid-cols-7 text-xs text-slate-500 mb-2">
        <div v-for="d in weekDays" :key="d" class="text-center">{{ d }}</div>
      </div>
      <div class="grid grid-cols-7 gap-1">
        <button v-for="cell in monthMatrix" :key="cell.dateKey"
                @click="selectDate(cell.dateKey)"
                :class="['h-10 rounded-lg text-xs flex flex-col items-center justify-center',
                  cell.inMonth ? 'text-slate-200' : 'text-slate-600',
                  cell.dateKey === selectedDate ? 'bg-indigo-600/60' : 'hover:bg-slate-800']">
          <span>{{ cell.date.getDate() }}</span>
          <span v-if="hasEvents(cell.dateKey)" class="w-1 h-1 rounded-full bg-indigo-400 mt-0.5"></span>
        </button>
      </div>
    </div>

    <!-- Chat -->
    <div class="flex-1 overflow-y-auto p-4 space-y-4 chat-container" id="chatWindow">
      <div v-for="(msg, index) in messages" :key="index"
           :class="['flex', msg.role === 'user' ? 'justify-end' : 'justify-start']">
        <div :class="['max-w-[85%] p-3 rounded-2xl shadow-lg',
                     msg.role === 'user' ? 'bg-indigo-600 text-white rounded-tr-none' : 'bg-slate-800 text-slate-200 rounded-tl-none border border-slate-700']">
          <div class="text-sm prose prose-invert pre-wrap">{{ msg.content }}</div>
        </div>
      </div>
      <div v-if="loading" class="flex justify-start">
        <div class="bg-slate-800 p-4 rounded-2xl flex items-center gap-2">
          <div class="w-2 h-2 bg-indigo-500 rounded-full animate-bounce"></div>
          <div class="w-2 h-2 bg-indigo-500 rounded-full animate-bounce [animation-delay:-.3s]"></div>
          <div class="w-2 h-2 bg-indigo-500 rounded-full animate-bounce [animation-delay:-.5s]"></div>
        </div>
      </div>
    </div>

    <!-- Input Area -->
    <div class="p-4 border-t border-slate-700 bg-slate-900/50">
      <div class="flex gap-2">
        <input v-model="userInput" @keyup.enter="sendMessage"
               placeholder="输入指令，例如：明天下午2点在图书馆开会..."
               class="flex-1 bg-slate-800 border border-slate-700 rounded-xl px-4 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500 transition-all">
        <button @click="sendMessage" :disabled="loading"
                class="bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 px-4 py-2 rounded-xl font-medium transition-all">
          发送
        </button>
      </div>
    </div>
  </section>

  <!-- Right: Schedule Dashboard -->
  <section class="w-[55%] flex flex-col bg-slate-950">
    <div class="p-4 border-b border-slate-800 flex justify-between items-center">
      <h2 class="font-semibold text-slate-400 tracking-wider text-sm uppercase">
        {{ selectedDate }} 日程
      </h2>
      <div class="flex gap-2 text-xs">
        <div class="flex items-center gap-1"><span class="w-2 h-2 bg-emerald-500 rounded-full"></span> 正常</div>
        <div class="flex items-center gap-1"><span class="w-2 h-2 bg-amber-500 rounded-full"></span> 冲突</div>
      </div>
    </div>
    <div class="flex-1 overflow-y-auto p-6">
      <div class="grid grid-cols-1 gap-4">
        <div v-for="item in daySchedules" :key="item.id"
             class="bg-slate-900 border border-slate-800 p-4 rounded-xl hover:border-slate-600 transition-all group">
          <!-- Card Content will be replaced in Task 3 -->
        </div>
      </div>
      <div v-if="daySchedules.length === 0" class="h-full flex flex-col items-center justify-center text-slate-500 opacity-50 italic">
        <p>&#x2615; 当天暂无日程</p>
      </div>
    </div>
  </section>
</main>
```

- [ ] **Step 2: Update script state and computed values**

Insert these in the `<script>` setup section (replace/add relevant parts):

```javascript
const { createApp, ref, onMounted, nextTick, computed } = Vue;

const weekDays = ['日', '一', '二', '三', '四', '五', '六'];
const selectedDate = ref(new Date().toISOString().slice(0, 10));
const currentMonth = ref(new Date());
const monthMatrix = ref([]);
const monthEvents = ref([]);
const daySchedules = ref([]);

const currentMonthLabel = computed(() => {
  const d = currentMonth.value;
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
});

const refreshMonthMatrix = () => {
  monthMatrix.value = CalendarUtils.getMonthMatrix(
    currentMonth.value.getFullYear(),
    currentMonth.value.getMonth()
  ).flat();
};

const hasEvents = (dateKey) => {
  return monthEvents.value.some((e) => e.start_time.startsWith(dateKey));
};

const selectDate = (dateKey) => {
  selectedDate.value = dateKey;
  daySchedules.value = monthEvents.value.filter((e) => e.start_time.startsWith(dateKey));
};

const prevMonth = async () => {
  const d = new Date(currentMonth.value);
  d.setMonth(d.getMonth() - 1);
  currentMonth.value = d;
  await fetchMonthSchedules();
};

const nextMonth = async () => {
  const d = new Date(currentMonth.value);
  d.setMonth(d.getMonth() + 1);
  currentMonth.value = d;
  await fetchMonthSchedules();
};

const fetchMonthSchedules = async () => {
  const range = CalendarUtils.getMonthRange(
    currentMonth.value.getFullYear(),
    currentMonth.value.getMonth()
  );
  const res = await axios.get(`/schedules?start=${range.start}&end=${range.end}`);
  monthEvents.value = res.data;
  refreshMonthMatrix();
  selectDate(selectedDate.value);
};
```

- [ ] **Step 3: Update onMounted + return**

```javascript
onMounted(() => {
  addLog('Privacy Agent Environment Ready.', 'text-green-500');
  addLog('Local Database Connected: schedule.db', 'text-indigo-400');
  fetchMonthSchedules();
});

return {
  userInput, sessionId, messages, schedules,
  terminalLogs, loading, sendMessage,
  deleteSchedule, getCategoryClass,
  weekDays, selectedDate, currentMonthLabel,
  monthMatrix, daySchedules, hasEvents,
  selectDate, prevMonth, nextMonth
};
```

- [ ] **Step 4: Commit**

```bash
git add privacy_schedule_agent/frontend/index.html
git commit -m "feat: update layout with calendar and day list"
```

---

### Task 3: 卡片内联编辑 + 保存/取消 + 回车保存

**Files:**
- Modify: `privacy_schedule_agent/frontend/index.html`

- [ ] **Step 1: Add edit state and helpers**

```javascript
const editingId = ref(null);
const editForm = ref({ title: '', start_time: '', end_time: '', location: '', description: '', category: '' });

const startEdit = (item) => {
  editingId.value = item.id;
  editForm.value = {
    title: item.title,
    start_time: item.start_time,
    end_time: item.end_time,
    location: item.location || '',
    description: item.description || '',
    category: item.category || ''
  };
};

const cancelEdit = () => {
  editingId.value = null;
};

const saveEdit = async () => {
  if (!editingId.value) return;
  await axios.put(`/schedules/${editingId.value}`, editForm.value);
  editingId.value = null;
  await fetchMonthSchedules();
};
```

- [ ] **Step 2: Replace card body with view/edit toggle**

```html
<div class="flex items-start justify-between">
  <div class="flex gap-4">
    <div class="flex flex-col items-center justify-center bg-slate-800 rounded-lg p-3 min-w-[70px]">
      <span class="text-xs text-slate-400">{{ item.start_time.split(' ')[0].split('-').slice(1).join('/') }}</span>
      <span class="font-bold text-lg text-indigo-400">{{ item.start_time.split(' ')[1].slice(0,5) }}</span>
    </div>

    <div v-if="editingId !== item.id">
      <div class="flex items-center gap-2">
        <h3 class="font-bold text-lg text-slate-100">{{ item.title }}</h3>
        <span v-if="item.category"
              :class="['text-[10px] px-2 py-0.5 rounded-full border', getCategoryClass(item.category)]">
          {{ item.category }}
        </span>
      </div>
      <p class="text-sm text-slate-400 flex items-center gap-1">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
        </svg>
        {{ item.location || '未指定地点' }}
      </p>
      <p v-if="item.description" class="text-xs text-slate-500 mt-1">{{ item.description }}</p>
      <p class="text-xs text-slate-500 mt-1">结束于 {{ item.end_time.split(' ')[1].slice(0,5) }}</p>
    </div>

    <div v-else class="space-y-2">
      <input v-model="editForm.title" class="w-full bg-slate-800 border border-slate-700 rounded px-2 py-1 text-xs" placeholder="标题" @keyup.enter="saveEdit" />
      <div class="flex gap-2">
        <input v-model="editForm.start_time" class="flex-1 bg-slate-800 border border-slate-700 rounded px-2 py-1 text-xs" placeholder="开始时间" @keyup.enter="saveEdit" />
        <input v-model="editForm.end_time" class="flex-1 bg-slate-800 border border-slate-700 rounded px-2 py-1 text-xs" placeholder="结束时间" @keyup.enter="saveEdit" />
      </div>
      <input v-model="editForm.location" class="w-full bg-slate-800 border border-slate-700 rounded px-2 py-1 text-xs" placeholder="地点" @keyup.enter="saveEdit" />
      <input v-model="editForm.description" class="w-full bg-slate-800 border border-slate-700 rounded px-2 py-1 text-xs" placeholder="描述" @keyup.enter="saveEdit" />
      <input v-model="editForm.category" class="w-full bg-slate-800 border border-slate-700 rounded px-2 py-1 text-xs" placeholder="分类" @keyup.enter="saveEdit" />
      <div class="flex gap-2 pt-1">
        <button @click="saveEdit" class="bg-indigo-600 hover:bg-indigo-500 px-3 py-1 rounded text-xs">保存</button>
        <button @click="cancelEdit" class="bg-slate-700 hover:bg-slate-600 px-3 py-1 rounded text-xs">取消</button>
      </div>
    </div>
  </div>

  <div class="flex items-center gap-2">
    <div v-if="item.status === 'conflicted'"
         class="bg-amber-500/10 text-amber-500 border border-amber-500/20 text-[10px] px-2 py-1 rounded-full animate-pulse">
      &#x26A0;&#xFE0F; 冲突
    </div>
    <div v-else class="text-emerald-500/50">
      <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
        <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
      </svg>
    </div>
    <button @click="startEdit(item)" class="opacity-0 group-hover:opacity-100 text-slate-500 hover:text-indigo-400 transition-all p-1" title="编辑日程">
      <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
        <path d="M17.414 2.586a2 2 0 00-2.828 0L7 10.172V13h2.828l7.586-7.586a2 2 0 000-2.828z" />
        <path fill-rule="evenodd" d="M2 15a2 2 0 002 2h12a1 1 0 100-2H4v-2a1 1 0 10-2 0v2z" clip-rule="evenodd" />
      </svg>
    </button>
    <button @click="deleteSchedule(item.id, item.title)"
            class="opacity-0 group-hover:opacity-100 text-slate-500 hover:text-red-400 transition-all p-1"
            title="删除日程">
      <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
        <path fill-rule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z" clip-rule="evenodd" />
      </svg>
    </button>
  </div>
</div>
```

- [ ] **Step 3: Return new methods and state**

```javascript
return {
  ...,
  editingId, editForm,
  startEdit, cancelEdit, saveEdit
};
```

- [ ] **Step 4: Commit**

```bash
git add privacy_schedule_agent/frontend/index.html
git commit -m "feat: add inline edit for schedules"
```

---

### Task 4: 冲突替代时段弹窗

**Files:**
- Modify: `privacy_schedule_agent/frontend/index.html`

- [ ] **Step 1: Add toast state and helper**

```javascript
const toastVisible = ref(false);
const suggestedSlots = ref([]);

const showToast = (slots) => {
  suggestedSlots.value = slots;
  toastVisible.value = true;
  setTimeout(() => { toastVisible.value = false; }, 8000);
};

const parseSuggestedSlots = (text) => {
  const match = text.match(/\[\s*\{[^\]]+\}\s*\]/);
  if (!match) return [];
  try {
    const slots = JSON.parse(match[0]);
    if (Array.isArray(slots)) return slots;
  } catch (e) {}
  return [];
};
```

- [ ] **Step 2: Trigger toast after chat response**

```javascript
const res = await axios.post('/chat', { message: input, session_id: sessionId.value });
messages.value.push({ role: 'assistant', content: res.data.response });
addLog('Engine Response Received.', 'text-emerald-400');

const slots = parseSuggestedSlots(res.data.response || '');
if (slots.length) {
  showToast(slots);
}

await fetchMonthSchedules();
```

- [ ] **Step 3: Add toast UI block**

Insert before closing `</div>` of `#app`:

```html
<div v-if="toastVisible" class="fixed right-6 bottom-6 bg-slate-900 border border-slate-700 shadow-lg rounded-xl p-4 w-80">
  <div class="text-sm text-slate-200 mb-2">检测到冲突，推荐时段：</div>
  <div class="space-y-2">
    <button v-for="(s, i) in suggestedSlots" :key="i"
            class="w-full text-left text-xs bg-slate-800 hover:bg-slate-700 rounded px-2 py-1">
      {{ s.start }} - {{ s.end }}
    </button>
  </div>
</div>
```

- [ ] **Step 4: Commit**

```bash
git add privacy_schedule_agent/frontend/index.html
git commit -m "feat: show conflict suggestion toast"
```

---

## Plan Self-Review

- Spec coverage: 日历布局、对话区、当天列表、内联编辑、冲突弹窗均对应 Task 2-4。
- Placeholder scan: 无 TBD/TODO/模糊描述。
- Type consistency: `selectedDate` 使用 `YYYY-MM-DD`，与 `start_time` 前 10 位一致。

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-04-29-frontend-v2-ui-implementation-plan.md`.

Two execution options:

1. **Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration
2. **Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?
