<template>
  <div class="flex-1 flex flex-col overflow-hidden min-h-0">
    <!-- Header -->
    <div class="flex items-center gap-3 px-5 pt-5 pb-3 shrink-0">
      <button @click="goToday"
        class="bg-surface-100 dark:bg-zinc-800 hover:bg-surface-200 dark:hover:bg-zinc-700 px-3 py-1 rounded-lg text-xs font-medium text-zinc-600 dark:text-zinc-300 transition-colors">
        今天
      </button>
      <div class="flex items-center gap-2">
        <button @click="prevDay" class="p-1 text-zinc-400 dark:text-zinc-500 hover:text-zinc-600 dark:hover:text-zinc-300 transition-colors rounded-lg hover:bg-surface-100 dark:hover:bg-zinc-800">
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 19.5L8.25 12l7.5-7.5" />
          </svg>
        </button>
        <h2 class="font-display text-lg font-semibold text-zinc-800 dark:text-zinc-200 w-48 text-center">{{ formattedDate }}</h2>
        <button @click="nextDay" class="p-1 text-zinc-400 dark:text-zinc-500 hover:text-zinc-600 dark:hover:text-zinc-300 transition-colors rounded-lg hover:bg-surface-100 dark:hover:bg-zinc-800">
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
          </svg>
        </button>
      </div>
      <div class="text-xs text-zinc-400 dark:text-zinc-500 ml-2">{{ dayOfWeek }}</div>
    </div>

    <!-- Time grid -->
    <div ref="scrollRef" class="flex-1 overflow-y-auto min-h-0 px-5 pb-5">
      <div class="relative rounded-xl border border-zinc-200/60 dark:border-zinc-700/60 bg-white dark:bg-zinc-900 min-h-full">
        <div class="relative" style="height: 1440px">
          <!-- Hour lines -->
          <div v-for="h in 24" :key="h"
            class="absolute left-14 right-0 border-t border-zinc-200/50 dark:border-zinc-700/50"
            :style="{ top: h * 60 + 'px' }">
            <span class="hidden sm:block absolute -left-14 -top-2.5 w-12 text-right pr-3 text-[11px] text-zinc-400 dark:text-zinc-500 font-semibold select-none">
              {{ String(h).padStart(2, '0') }}:00
            </span>
          </div>

          <!-- Half-hour markers -->
          <div v-for="h in 24" :key="'m-' + h"
            class="absolute left-14 right-0 border-t border-zinc-100 dark:border-zinc-800/80"
            :style="{ top: h * 60 + 30 + 'px' }"></div>

          <!-- Drop target indicator during drag -->
          <div v-if="dragActive"
            class="absolute left-14 right-0 z-20 pointer-events-none border-t-2 border-dashed border-primary-400/50"
            :style="{ top: dragSnappedTop + 'px' }">
            <span class="absolute -left-20 -top-3 w-16 text-right pr-2 text-[10px] font-mono font-medium text-primary-400">
              {{ dragTargetTime }}
            </span>
          </div>

          <!-- Events -->
          <div v-for="event in dayEvents" :key="event.id"
            class="absolute left-16 right-2 rounded-lg px-2.5 py-1 text-xs overflow-hidden border-l-2 z-10 select-none transition-all duration-200 hover:shadow-md hover:z-20 hover:scale-[1.01]"
            :class="[
              getEventClass(event),
              event.status === 'conflicted' ? 'border-danger-400/60' : '',
              dragEventId === event.id
                ? 'z-30 shadow-xl ring-2 ring-primary-400/40 opacity-90 cursor-grabbing'
                : 'cursor-grab hover:shadow-lg hover:shadow-black/20'
            ]"
            :style="eventStyle(event)"
            @mousedown.prevent="startDrag(event, $event)">
            <div class="font-medium truncate leading-tight">{{ event.title }}</div>
            <div v-if="getEventHeight(event) > 28" class="text-[10px] opacity-70 leading-tight mt-0.5">
              {{ formatTime(event) }}
            </div>
          </div>

          <!-- Ghost at original position during drag -->
          <div v-if="dragActive"
            class="absolute left-16 right-2 rounded-lg px-2.5 py-1 text-xs overflow-hidden border-2 border-dashed z-0 pointer-events-none opacity-20"
            :class="dragEvent.status === 'conflicted' ? 'border-danger-400/30 bg-danger-400/10' : 'border-moss-400/30 bg-moss-400/10'"
            :style="{ top: getEventTop(dragEvent) + 'px', height: Math.max(getEventHeight(dragEvent), 20) + 'px' }">
            <div class="font-medium truncate">{{ dragEvent.title }}</div>
          </div>

          <!-- Now indicator with pulse -->
          <div v-if="isToday" class="absolute left-14 right-0 z-20 pointer-events-none animate-pulse-subtle" :style="{ top: nowPos + 'px' }">
            <div class="flex items-center">
              <div class="w-2 h-2 rounded-full bg-primary-400 shadow shadow-primary-400"></div>
              <div class="flex-1 h-px bg-primary-400/60"></div>
            </div>
          </div>
        </div>

        <!-- Empty / loading states -->
        <div v-if="loading" class="absolute inset-0 flex items-center justify-center pointer-events-none">
          <span class="text-zinc-400 dark:text-zinc-500 text-sm">加载中...</span>
        </div>
        <div v-else-if="dayEvents.length === 0" class="absolute inset-0 flex flex-col items-center justify-center pointer-events-none gap-3">
          <svg class="w-12 h-12 text-zinc-200 dark:text-zinc-700" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1">
            <path stroke-linecap="round" stroke-linejoin="round" d="M6.75 3v2.25M17.25 3v2.25M3 18.75V7.5a2.25 2.25 0 012.25-2.25h13.5A2.25 2.25 0 0121 7.5v11.25m-18 0A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75m-18 0v-7.5A2.25 2.25 0 015.25 9h13.5A2.25 2.25 0 0121 11.25v7.5" />
          </svg>
          <p class="text-zinc-400 dark:text-zinc-500 text-sm">当天暂无日程</p>
          <p class="text-zinc-300 dark:text-zinc-600 text-xs">点击左侧日历创建新日程</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, reactive, watch, nextTick, onUnmounted } from 'vue'
import { useSchedules } from '../composables/useSchedules.js'
import { toDateKey, parseTime, formatEventTime, pad2 } from '../utils/calendar.js'
import { eventClass as getEventClass } from '../utils/eventStyles.js'

const { filteredEvents, selectedDate, loading } = useSchedules()
const { updateSchedule } = useSchedules()
const scrollRef = ref(null)

const DAY_KEYS = ['星期日', '星期一', '星期二', '星期三', '星期四', '星期五', '星期六']
const SNAP_MINUTES = 15
const SNAP_PX = SNAP_MINUTES // 1px = 1min at 60px/hour

// --- Drag state ---
const dragActive = ref(false)
const dragEvent = ref(null)
const dragStartMouseY = ref(0)
const dragStartTop = ref(0)
const dragCurrentTop = ref(0)
const dragSnappedTop = ref(0)
const dragTargetTime = ref('')
const dragEventId = computed(() => dragEvent.value?.id ?? null)

function startDrag(event, e) {
  dragEvent.value = event
  dragStartMouseY.value = e.clientY
  dragStartTop.value = getEventTop(event)
  dragCurrentTop.value = dragStartTop.value
  dragSnappedTop.value = dragStartTop.value
  const mins = Math.round(dragStartTop.value)
  dragTargetTime.value = `${pad2(Math.floor(mins / 60))}:${pad2(mins % 60)}`
  dragActive.value = true
  document.addEventListener('mousemove', onDrag)
  document.addEventListener('mouseup', stopDrag)
  document.body.style.cursor = 'grabbing'
}

function onDrag(e) {
  if (!dragActive.value) return
  const delta = e.clientY - dragStartMouseY.value
  const raw = dragStartTop.value + delta
  // Clamp to [0, 1440 - eventHeight]
  const max = 1440 - Math.max(getEventHeight(dragEvent.value), 20)
  const clamped = Math.max(0, Math.min(max, raw))
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

  dragActive.value = false

  // Only update if position actually changed
  if (Math.abs(snapped - getEventTop(event)) < 1) {
    dragEvent.value = null
    return
  }

  const datePart = event.start_time.split(' ')[0]
  const oldStart = parseTime(event.start_time)
  const duration = parseTime(event.end_time) - oldStart
  const newStartMins = Math.round(snapped)
  const newEndMins = newStartMins + duration

  const newStart = `${datePart} ${pad2(Math.floor(newStartMins / 60))}:${pad2(newStartMins % 60)}:00`
  const newEnd = `${datePart} ${pad2(Math.floor(newEndMins / 60))}:${pad2(newEndMins % 60)}:00`

  try {
    await updateSchedule(event.id, { start_time: newStart, end_time: newEnd })
  } catch {
    // Silently fail; data reverts on next fetch
  }
  dragEvent.value = null
}

onUnmounted(() => {
  document.removeEventListener('mousemove', onDrag)
  document.removeEventListener('mouseup', stopDrag)
})

// --- End drag state ---

const currentDay = computed(() => {
  const key = selectedDate.value || toDateKey(new Date())
  const [y, m, d] = key.split('-')
  return new Date(+y, +m - 1, +d)
})

const formattedDate = computed(() => {
  const d = currentDay.value
  return `${d.getFullYear()}年${d.getMonth() + 1}月${d.getDate()}日`
})

const dayOfWeek = computed(() => DAY_KEYS[currentDay.value.getDay()])

const isToday = computed(() => selectedDate.value === toDateKey(new Date()))

const nowPos = computed(() => {
  const now = new Date()
  return (now.getHours() * 60 + now.getMinutes()) / 60 * 60
})

const dayEvents = computed(() =>
  (filteredEvents.value || []).filter(e => e.start_time.startsWith(selectedDate.value))
)

function getEventTop(event) {
  return (parseTime(event.start_time) / 60) * 60
}

function getEventHeight(event) {
  return ((parseTime(event.end_time) - parseTime(event.start_time)) / 60) * 60
}

function eventStyle(event) {
  const isDragging = dragEvent.value?.id === event.id && dragActive.value
  return {
    top: (isDragging ? dragSnappedTop.value : getEventTop(event)) + 'px',
    height: Math.max(getEventHeight(event), 20) + 'px'
  }
}

function formatTime(event) {
  return formatEventTime(event)
}

function navigateDay(delta) {
  const d = currentDay.value
  d.setDate(d.getDate() + delta)
  selectedDate.value = toDateKey(d)
}

function prevDay() { navigateDay(-1) }
function nextDay() { navigateDay(1) }

function goToday() {
  selectedDate.value = toDateKey(new Date())
}

watch(() => selectedDate.value, () => {
  nextTick(() => {
    if (scrollRef.value) {
      scrollRef.value.scrollTop = 8 * 60 - 20
    }
  })
}, { immediate: true })
</script>
