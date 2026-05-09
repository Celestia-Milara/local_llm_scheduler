<template>
  <div class="h-full flex flex-col">
    <!-- Day headers -->
    <div class="grid grid-cols-7 mb-3">
      <div v-for="d in weekDays" :key="d" class="text-center">
        <span class="text-sm font-medium text-warm-400 uppercase tracking-wider">{{ d }}</span>
      </div>
    </div>

    <!-- Calendar grid -->
    <div class="flex-1 grid grid-cols-7 auto-rows-fr gap-[1px]">
      <button v-for="cell in flatMatrix" :key="cell.dateKey"
        @click="emit('select-date', cell.dateKey)"
        class="relative flex flex-col items-stretch p-1.5 rounded-lg transition-all duration-150 min-h-[70px] text-left"
        :class="[
          cell.inMonth
            ? 'bg-white hover:bg-warm-50 hover:shadow-inner'
            : 'bg-transparent',
          cell.dateKey === selectedDate
            ? 'ring-1 ring-copper-400/40 bg-warm-50'
            : '',
          isToday(cell.dateKey) && cell.inMonth
            ? 'shadow-[inset_0_-1px_6px_-1px_rgba(212,131,90,0.10)]'
            : ''
        ]">
        <!-- Date number + today ring -->
        <div class="flex items-center justify-center mb-0.5 shrink-0"
          :class="isToday(cell.dateKey) ? 'w-6 h-6 rounded-full border border-copper-400/60 -ml-0.5' : ''">
          <span class="font-display text-base leading-none transition-colors"
            :class="[
              cell.inMonth ? 'text-warm-700' : 'text-warm-300',
              isToday(cell.dateKey) ? 'text-copper-500' : ''
            ]">
            {{ cell.date.getDate() }}
          </span>
        </div>

        <!-- Event titles — pill style with category color -->
        <div class="flex flex-col gap-px overflow-hidden flex-1">
          <div v-for="event in visibleEvents(cell.dateKey)" :key="event.id"
            class="text-xs leading-[18px] truncate rounded-sm py-px font-medium border-l-2"
            :class="eventClass(event, cell.dateKey)">
            <template v-if="eventMultiDay(event)">
              <span v-if="cell.dateKey === event.start_time.slice(0, 10)" class="opacity-70">↙</span>
              <span v-else-if="cell.dateKey === event.end_time.slice(0, 10)" class="opacity-70">↘</span>
              <span v-else class="opacity-50">│</span>
            </template>
            {{ event.title }}
          </div>
        </div>

        <!-- Overflow indicator — clickable -->
        <div v-if="overflowCount(cell.dateKey) > 0"
          @click.stop="emit('select-date', cell.dateKey)"
          class="text-xs text-warm-400 font-medium text-center leading-none mt-px hover:text-copper-500 cursor-pointer transition-colors">
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

const { monthMatrix, selectedDate, monthEvents } = useSchedules()
const weekDays = ['一', '二', '三', '四', '五', '六', '日']
const emit = defineEmits(['select-date'])

const flatMatrix = computed(() => monthMatrix.value)
const MAX_VISIBLE = 3

function eventsForDate(dateKey) {
  return (monthEvents.value || []).filter(e => {
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

function eventClass(event, dateKey) {
  if (event.status === 'conflicted') return 'border-copper-400/40 bg-copper-400/10 text-copper-600'
  if (eventMultiDay(event)) {
    return 'border-moss-400/30 bg-moss-400/10 text-moss-600'
  }
  const cat = event.category
  if (cat === '工作') return 'border-gold-400/30 bg-gold-400/10 text-gold-600'
  if (cat === '学习') return 'border-warm-400/30 bg-warm-400/10 text-warm-600'
  if (cat === '生活') return 'border-copper-400/30 bg-copper-400/10 text-copper-600'
  return 'border-moss-400/30 bg-moss-400/10 text-moss-600'
}

function isToday(dateKey) {
  return dateKey === toDateKey(new Date())
}
</script>
