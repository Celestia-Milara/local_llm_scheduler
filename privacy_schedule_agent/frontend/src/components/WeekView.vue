<template>
  <div class="flex-1 flex flex-col overflow-hidden min-h-0">
    <!-- Header -->
    <div class="flex items-center gap-3 px-5 pt-5 pb-3 shrink-0">
      <button @click="goToday"
        class="bg-warm-100 hover:bg-warm-200 px-3 py-1 rounded-lg text-xs font-medium text-warm-600 transition-colors">
        今天
      </button>
      <div class="flex items-center gap-2">
        <button @click="prevWeek" class="p-1 text-warm-400 hover:text-warm-600 transition-colors rounded-lg hover:bg-warm-100">
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 19.5L8.25 12l7.5-7.5" />
          </svg>
        </button>
        <h2 class="font-display text-sm text-warm-800 w-52 text-center">{{ weekLabel }}</h2>
        <button @click="nextWeek" class="p-1 text-warm-400 hover:text-warm-600 transition-colors rounded-lg hover:bg-warm-100">
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
          </svg>
        </button>
      </div>
    </div>

    <!-- Day headers -->
    <div class="grid grid-cols-[56px_repeat(7,1fr)] px-5 pb-2 shrink-0">
      <div></div>
      <div v-for="d in weekDaysList" :key="d.dateKey" class="text-center py-1"
        :class="d.dateKey === todayKey ? 'bg-copper-500/10 rounded-lg' : ''">
        <div class="text-xs text-warm-400 font-medium">{{ d.weekName }}</div>
        <div class="font-display text-sm leading-tight"
          :class="d.dateKey === todayKey ? 'text-copper-500' : 'text-warm-700'">
          {{ d.day }}
        </div>
      </div>
    </div>

    <!-- All-day events (cross-day) -->
    <div v-if="allDayEvents.length > 0" class="px-5 pb-2 shrink-0">
      <div class="flex items-center gap-1 mb-1">
        <span class="text-[9px] text-warm-400 font-medium uppercase tracking-wider">全天</span>
        <div class="flex-1 h-px bg-warm-200/40"></div>
      </div>
      <div class="grid grid-cols-[56px_repeat(7,1fr)] gap-px">
        <div></div>
        <div v-for="day in weekDaysList" :key="day.dateKey" class="min-h-[22px]">
          <div v-for="event in dayAllDayEvents(day.dateKey)" :key="event.id"
            class="text-[9px] leading-[18px] truncate rounded px-1.5 mb-px font-medium bg-moss-400/10 text-moss-600 border-l border-moss-400/30"
            :title="event.title">
            {{ event.title }}
          </div>
        </div>
      </div>
    </div>

    <!-- Time grid -->
    <div ref="scrollRef" class="flex-1 overflow-y-auto min-h-0 px-5 pb-5">
      <div ref="gridRef" class="relative rounded-xl border border-warm-200/60 bg-white min-h-full">
        <div class="relative" style="height: 1440px">
          <!-- Weekend column background (before grid lines so lines render on top) -->
          <div v-for="idx in weekendIndices" :key="'we-' + idx"
            class="absolute top-0 bottom-0 bg-warm-50 pointer-events-none"
            :style="{ left: `calc(56px + (100% - 56px) * ${idx} / 7)`, width: `calc((100% - 56px) / 7)` }">
          </div>

          <!-- Today column highlight -->
          <div v-if="todayColIndex >= 0"
            class="absolute top-0 bottom-0 bg-copper-400/8 pointer-events-none"
            :style="{ left: `calc(56px + (100% - 56px) * ${todayColIndex} / 7)`, width: `calc((100% - 56px) / 7)` }">
          </div>

          <!-- Hour lines -->
          <div v-for="h in 24" :key="h"
            class="absolute left-0 right-0 border-t border-warm-200/50"
            :style="{ top: h * 60 + 'px' }">
            <span class="absolute left-0 -top-2.5 w-12 text-right pr-3 text-xs text-warm-400 font-medium select-none">
              {{ String(h).padStart(2, '0') }}:00
            </span>
          </div>

          <!-- Half-hour markers -->
          <div v-for="h in 24" :key="'m-' + h"
            class="absolute left-0 right-0 border-t border-warm-100"
            :style="{ top: h * 60 + 30 + 'px' }"></div>

          <!-- Vertical day separators -->
          <div v-for="i in 7" :key="'c-' + i"
            class="absolute top-0 bottom-0 border-l border-warm-200/40 pointer-events-none"
            :style="{ left: `calc(56px + (100% - 56px) * ${i - 1} / 7)`, width: `calc((100% - 56px) / 7)` }">
          </div>

          <!-- Drop target indicator during drag -->
          <div v-if="dragActive"
            class="absolute z-20 pointer-events-none border-t-2 border-dashed border-copper-400/50"
            :style="{
              top: dragSnappedTop + 'px',
              left: `calc(56px + (100% - 56px) * ${dragCol} / 7)`,
              width: `calc((100% - 56px) / 7)`
            }">
            <span class="absolute -left-14 -top-3 w-12 text-right pr-2 text-[10px] font-mono font-medium text-copper-400">
              {{ dragTargetTime }}
            </span>
          </div>

          <!-- Ghost at original position during drag -->
          <div v-if="dragActive"
            class="absolute rounded-lg px-1.5 py-0.5 text-[10px] overflow-hidden border-2 border-dashed z-0 pointer-events-none opacity-20"
            :class="dragEvent.status === 'conflicted' ? 'border-copper-400/30 bg-copper-400/10' : 'border-moss-400/30 bg-moss-400/10'"
            :style="{
              top: dragOriginalTop + 'px',
              height: Math.max(dragOriginalHeight, 18) + 'px',
              left: `calc(56px + (100% - 56px) * ${dragOriginalCol} / 7 + 1px)`,
              width: `calc((100% - 56px) / 7 - 2px)`
            }">
            <div class="font-medium truncate">{{ dragEvent.title }}</div>
          </div>

          <!-- Events -->
          <div v-for="event in positionedEvents" :key="event.id"
            class="absolute rounded-lg px-1.5 py-0.5 text-[10px] overflow-hidden border-l-2 z-10 select-none"
            :class="[
              eventClass(event),
              dragEventId === event.id && dragActive
                ? 'z-30 shadow-xl ring-2 ring-copper-400/40 opacity-90 cursor-grabbing'
                : 'cursor-grab hover:shadow-lg'
            ]"
            :style="weekEventStyle(event)"
            @mousedown.prevent="startDrag(event, $event)">
            <div class="font-medium truncate leading-tight">{{ event.title }}</div>
          </div>
        </div>

        <!-- Empty / loading states -->
        <div v-if="loading" class="absolute inset-0 flex items-center justify-center pointer-events-none">
          <span class="text-warm-500 text-sm">加载中...</span>
        </div>
        <div v-else-if="positionedEvents.length === 0" class="absolute inset-0 flex items-center justify-center pointer-events-none">
          <span class="text-warm-400 text-sm">本周暂无日程</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch, nextTick, onUnmounted } from 'vue'
import { useSchedules } from '../composables/useSchedules.js'
import { toDateKey, getWeekDays, parseTime, formatWeekRange, pad2 } from '../utils/calendar.js'

const { monthEvents, selectedDate, loading, updateSchedule } = useSchedules()
const scrollRef = ref(null)
const gridRef = ref(null)

const SNAP_MINUTES = 15
const SNAP_PX = SNAP_MINUTES

const todayKey = toDateKey(new Date())

// --- Drag state ---
const dragActive = ref(false)
const dragEvent = ref(null)
const dragStartMouseY = ref(0)
const dragStartTop = ref(0)
const dragCurrentTop = ref(0)
const dragSnappedTop = ref(0)
const dragTargetTime = ref('')
const dragCol = ref(0)
const dragOriginalTop = ref(0)
const dragOriginalCol = ref(0)
const dragOriginalHeight = ref(0)
const dragEventId = computed(() => dragEvent.value?.id ?? null)

function startDrag(event, e) {
  dragEvent.value = event
  dragStartMouseY.value = e.clientY
  dragStartTop.value = event.top
  dragOriginalTop.value = event.top
  dragOriginalCol.value = event.col
  dragOriginalHeight.value = event.height
  dragCurrentTop.value = event.top
  dragSnappedTop.value = event.top
  dragCol.value = event.col
  const mins = Math.round(event.top)
  dragTargetTime.value = `${pad2(Math.floor(mins / 60))}:${pad2(mins % 60)}`
  dragActive.value = true
  document.addEventListener('mousemove', onDrag)
  document.addEventListener('mouseup', stopDrag)
  document.body.style.cursor = 'grabbing'
}

function onDrag(e) {
  if (!dragActive.value) return

  // Detect column from mouse X
  if (gridRef.value) {
    const rect = gridRef.value.getBoundingClientRect()
    const x = e.clientX - rect.left - 56
    if (x >= 0) {
      const colWidth = (rect.width - 56) / 7
      dragCol.value = Math.min(6, Math.max(0, Math.floor(x / colWidth)))
    }
  }

  // Calculate time from mouse Y
  const delta = e.clientY - dragStartMouseY.value
  const max = 1440 - Math.max(dragOriginalHeight.value, 18)
  const clamped = Math.max(0, Math.min(max, dragStartTop.value + delta))
  dragCurrentTop.value = clamped
  dragSnappedTop.value = Math.round(clamped / SNAP_PX) * SNAP_PX
  const mins = Math.round(dragSnappedTop.value)
  dragTargetTime.value = `${pad2(Math.floor(mins / 60))}:${pad2(mins % 60)}`
}

async function stopDrag() {
  if (!dragActive.value) return
  document.removeEventListener('mousemove', onDrag)
  document.removeEventListener('mouseup', stopDrag)
  document.body.style.cursor = ''

  const event = dragEvent.value
  const snapped = dragSnappedTop.value
  const targetCol = dragCol.value
  const startedCol = dragOriginalTop.value
  const startedTop = dragOriginalTop.value

  dragActive.value = false

  const colChanged = targetCol !== dragOriginalCol.value
  const topChanged = Math.abs(snapped - startedTop) >= 1

  if (!colChanged && !topChanged) {
    dragEvent.value = null
    return
  }

  // Determine target date
  const targetDateKey = weekDaysList.value[targetCol]?.dateKey
  if (!targetDateKey) {
    dragEvent.value = null
    return
  }

  const datePart = targetDateKey
  const oldStart = parseTime(event.start_time)
  const duration = parseTime(event.end_time) - oldStart
  const newStartMins = Math.round(snapped)
  const newEndMins = newStartMins + duration

  const newStart = `${datePart} ${pad2(Math.floor(newStartMins / 60))}:${pad2(newStartMins % 60)}:00`
  const newEnd = `${datePart} ${pad2(Math.floor(newEndMins / 60))}:${pad2(newEndMins % 60)}:00`

  try {
    await updateSchedule(event.id, { start_time: newStart, end_time: newEnd })
  } catch { /* data reverts on next fetch */ }
  dragEvent.value = null
}

onUnmounted(() => {
  document.removeEventListener('mousemove', onDrag)
  document.removeEventListener('mouseup', stopDrag)
})
// --- End drag state ---

const weekDaysList = computed(() => {
  const base = selectedDate.value || toDateKey(new Date())
  return getWeekDays(new Date(base + 'T00:00:00')).map(d => ({
    date: d,
    dateKey: toDateKey(d),
    weekName: ['日', '一', '二', '三', '四', '五', '六'][d.getDay()],
    day: d.getDate()
  }))
})

const weekLabel = computed(() => formatWeekRange(weekDaysList.value.map(d => d.date)))

const todayColIndex = computed(() =>
  weekDaysList.value.findIndex(d => d.dateKey === todayKey)
)

const weekendIndices = computed(() =>
  weekDaysList.value.reduce((acc, d, i) => {
    const day = d.date.getDay()
    if (day === 0 || day === 6) acc.push(i)
    return acc
  }, [])
)

function eventClass(event) {
  if (event.status === 'conflicted') return 'bg-copper-400/10 text-copper-600 border-copper-400/40'
  const cat = event.category
  if (cat === '工作') return 'bg-gold-400/10 text-gold-600 border-gold-400/30'
  if (cat === '学习') return 'bg-warm-400/10 text-warm-600 border-warm-400/30'
  if (cat === '生活') return 'bg-copper-400/10 text-copper-600 border-copper-400/30'
  return 'bg-moss-400/10 text-moss-600 border-moss-400/30'
}

const positionedEvents = computed(() => {
  const events = []
  weekDaysList.value.forEach((day, colIndex) => {
    const dayEvts = (monthEvents.value || []).filter(e =>
      e.start_time.startsWith(day.dateKey) && !isCrossDayEvent(e)
    )
    dayEvts.forEach(evt => {
      events.push({
        ...evt,
        col: colIndex,
        top: (parseTime(evt.start_time) / 60) * 60,
        height: Math.max(((parseTime(evt.end_time) - parseTime(evt.start_time)) / 60) * 60, 18)
      })
    })
  })
  return events
})

function isCrossDayEvent(event) {
  return event.start_time.slice(0, 10) !== event.end_time.slice(0, 10)
}

const allDayEvents = computed(() => {
  const firstDay = weekDaysList.value[0]?.dateKey
  const lastDay = weekDaysList.value[6]?.dateKey
  if (!firstDay || !lastDay) return []
  return (monthEvents.value || []).filter(e => {
    const start = e.start_time.slice(0, 10)
    const end = e.end_time.slice(0, 10)
    return start !== end && end >= firstDay && start <= lastDay
  })
})

function dayAllDayEvents(dateKey) {
  return allDayEvents.value.filter(e => {
    const start = e.start_time.slice(0, 10)
    const end = e.end_time.slice(0, 10)
    return dateKey >= start && dateKey <= end
  })
}

function weekEventStyle(event) {
  const isDragging = dragEventId.value === event.id && dragActive.value
  const col = isDragging ? dragCol.value : event.col
  const top = isDragging ? dragSnappedTop.value : event.top
  const height = Math.max(event.height, 18)
  return {
    top: top + 'px',
    height: height + 'px',
    left: `calc(56px + (100% - 56px) * ${col} / 7 + 1px)`,
    width: `calc((100% - 56px) / 7 - 2px)`
  }
}

function navigateWeek(delta) {
  const base = selectedDate.value || toDateKey(new Date())
  const d = new Date(base + 'T00:00:00')
  d.setDate(d.getDate() + delta * 7)
  selectedDate.value = toDateKey(d)
}

function prevWeek() { navigateWeek(-1) }
function nextWeek() { navigateWeek(1) }

function goToday() {
  selectedDate.value = todayKey
}

watch(() => selectedDate.value, () => {
  nextTick(() => {
    if (scrollRef.value) {
      scrollRef.value.scrollTop = 8 * 60 - 20
    }
  })
}, { immediate: true })
</script>
