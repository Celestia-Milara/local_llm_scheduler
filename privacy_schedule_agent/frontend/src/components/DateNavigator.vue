<template>
  <div class="flex items-center gap-2 text-sm">
    <button @click="goToday"
      class="bg-warm-100 hover:bg-warm-200 px-3 py-1 rounded-lg text-xs font-medium text-warm-600 transition-colors">
      今天
    </button>
    <button @click="prevMonth" class="text-warm-400 hover:text-warm-600 transition-colors">
      <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
        <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 19.5L8.25 12l7.5-7.5" />
      </svg>
    </button>
    <span class="font-display text-sm text-warm-700 w-28 text-center">{{ currentMonthLabel }}</span>
    <button @click="nextMonth" class="text-warm-400 hover:text-warm-600 transition-colors">
      <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
        <path stroke-linecap="round" stroke-linejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
      </svg>
    </button>
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
  const m = currentMonth.value
  if (m.getFullYear() === today.getFullYear() && m.getMonth() === today.getMonth()) return
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
