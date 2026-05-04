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

const { monthMatrix, selectedDate, monthEvents } = useSchedules()
const weekDays = ['日', '一', '二', '三', '四', '五', '六']
const emit = defineEmits(['select-date'])

const flatMatrix = computed(() => monthMatrix.value)
const dateEvents = computed(() => groupEventsByDate(monthEvents.value))

function isToday(dateKey) {
  const today = new Date()
  const key = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`
  return dateKey === key
}
</script>
