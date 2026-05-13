<template>
  <div class="h-full flex flex-col">
    <!-- Day headers -->
    <div class="grid grid-cols-7 mb-2">
      <div v-for="d in weekDays" :key="d" class="text-center py-2">
        <span class="text-sm font-bold text-zinc-500 dark:text-zinc-400 uppercase tracking-wider">{{ d }}</span>
      </div>
    </div>

    <!-- Calendar grid -->
    <div class="flex-1 grid grid-cols-7 auto-rows-fr gap-px bg-zinc-100/60 dark:bg-zinc-700/40 rounded-xl overflow-hidden border border-zinc-200/50 dark:border-zinc-700/50">
      <button v-for="cell in flatMatrix" :key="cell.dateKey"
        @click="emit('select-date', cell.dateKey)"
        class="relative flex flex-col items-stretch p-2 transition-all duration-150 min-h-[80px] text-left group"
        :class="[
          cell.inMonth
            ? 'bg-white dark:bg-zinc-900 hover:bg-primary-50/20 dark:hover:bg-zinc-800'
            : 'bg-zinc-50/50 dark:bg-zinc-900/50',
          cell.dateKey === selectedDate && !isToday(cell.dateKey)
            ? 'bg-primary-50/40 dark:bg-primary-500/10 ring-2 ring-inset ring-primary-400/30'
            : '',
          isToday(cell.dateKey) && cell.inMonth
            ? 'bg-primary-50/50 dark:bg-primary-500/10'
            : ''
        ]">
        <!-- Date number -->
        <div class="flex items-center justify-center mb-1 shrink-0">
          <span v-if="isToday(cell.dateKey) && cell.inMonth"
            class="w-7 h-7 flex items-center justify-center rounded-full bg-primary-500 text-white text-sm font-semibold shadow-sm shadow-primary-500/25">
            {{ cell.date.getDate() }}
          </span>
          <span v-else
            class="font-display text-sm font-semibold leading-none transition-colors"
            :class="cell.inMonth ? 'text-zinc-700 dark:text-zinc-200' : 'text-zinc-300 dark:text-zinc-600'">
            {{ cell.date.getDate() }}
          </span>
        </div>

        <!-- Event titles — pill style with category color -->
        <div class="flex flex-col gap-[3px] overflow-hidden flex-1">
          <div v-for="event in visibleEvents(cell.dateKey)" :key="event.id"
            class="text-[11px] leading-[16px] truncate rounded-[4px] px-1.5 py-[3px] font-medium border-l-[3px]"
            :class="getEventClass(event)">
            <template v-if="eventMultiDay(event)">
              <span v-if="cell.dateKey === event.start_time.slice(0, 10)" class="opacity-60">↙</span>
              <span v-else-if="cell.dateKey === event.end_time.slice(0, 10)" class="opacity-60">↘</span>
              <span v-else class="opacity-40">│</span>
            </template>
            {{ event.title }}
          </div>
        </div>

        <!-- Overflow indicator — clickable -->
        <div v-if="overflowCount(cell.dateKey) > 0"
          @click.stop="emit('select-date', cell.dateKey)"
          class="text-[10px] text-zinc-400 dark:text-zinc-500 font-medium text-center leading-none mt-1 hover:text-primary-500 cursor-pointer transition-colors">
          +{{ overflowCount(cell.dateKey) }} 更多
        </div>
      </button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useSchedules } from '../composables/useSchedules.js'
import { toDateKey } from '../utils/calendar.js'
import { eventClass as getEventClass } from '../utils/eventStyles.js'

const { monthMatrix, selectedDate, filteredEvents } = useSchedules()
const weekDays = ['一', '二', '三', '四', '五', '六', '日']
const emit = defineEmits(['select-date'])

const flatMatrix = computed(() => monthMatrix.value)
const MAX_VISIBLE = 3

function eventsForDate(dateKey) {
  return (filteredEvents.value || []).filter(e => {
    const start = e.start_time.slice(0, 10)
    const end = e.end_time.slice(0, 10)
    return dateKey >= start && dateKey <= end
  })
}

function visibleEvents(dateKey) {
  return eventsForDate(dateKey).slice(0, MAX_VISIBLE)
}

function overflowCount(dateKey) {
  return Math.max(0, eventsForDate(dateKey).length - MAX_VISIBLE)
}

function eventMultiDay(event) {
  return event.start_time.slice(0, 10) !== event.end_time.slice(0, 10)
}

function isToday(dateKey) {
  return dateKey === toDateKey(new Date())
}
</script>
