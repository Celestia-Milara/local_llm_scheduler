<template>
  <div class="w-full px-2">
    <div class="flex items-center justify-between mb-2 px-1">
      <button @click="prevMonth" class="text-warm-400 hover:text-warm-600 transition-colors">
        <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 19.5L8.25 12l7.5-7.5" />
        </svg>
      </button>
      <span class="font-display text-sm text-warm-700 font-medium">{{ label }}</span>
      <button @click="nextMonth" class="text-warm-400 hover:text-warm-600 transition-colors">
        <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
        </svg>
      </button>
    </div>
    <div class="grid grid-cols-7 text-xs text-warm-400 mb-1.5">
      <span v-for="d in weekDays" :key="d" class="text-center font-medium">{{ d }}</span>
    </div>
    <div class="grid grid-cols-7 gap-px">
      <button v-for="cell in flatMatrix" :key="cell.dateKey"
        @click="selectDate(cell)"
        class="text-sm w-full aspect-square flex items-center justify-center rounded-full transition-colors"
        :class="[
          cell.inMonth ? 'text-warm-700' : 'text-warm-300',
          cell.dateKey === selectedDate ? 'bg-copper-500 text-white' : 'hover:bg-warm-100'
        ]">
        <span class="relative"
          :class="isTodayCell(cell.dateKey) ? 'w-6 h-6 flex items-center justify-center rounded-full border border-copper-400/50' : ''">
          {{ cell.date.getDate() }}
          <span v-if="hasEvents(cell.dateKey)"
            class="absolute -top-0.5 -right-1.5 w-1.5 h-1.5 rounded-full bg-copper-400/60"></span>
        </span>
      </button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useSchedules } from '../composables/useSchedules.js'
import { toDateKey } from '../utils/calendar.js'

const { currentMonth, selectedDate, monthMatrix, hasEvents, fetchMonth } = useSchedules()
const weekDays = ['一', '二', '三', '四', '五', '六', '日']

const flatMatrix = computed(() => monthMatrix.value)
const label = computed(() => `${currentMonth.value.getFullYear()}年${currentMonth.value.getMonth() + 1}月`)

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

function isTodayCell(dateKey) {
  return dateKey === toDateKey(new Date())
}
</script>
