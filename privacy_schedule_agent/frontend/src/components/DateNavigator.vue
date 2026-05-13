<template>
  <div class="flex items-center gap-2 text-sm">
    <button @click="goToday"
      class="bg-surface-100 dark:bg-zinc-800 hover:bg-surface-200 dark:hover:bg-zinc-700 px-3 py-1 rounded-lg text-xs font-medium text-zinc-600 dark:text-zinc-300 transition-colors">
      今天
    </button>
    <button @click="prevMonth" class="text-zinc-400 dark:text-zinc-500 hover:text-zinc-600 dark:hover:text-zinc-300 transition-colors">
      <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
        <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 19.5L8.25 12l7.5-7.5" />
      </svg>
    </button>
    <span class="font-display text-sm text-zinc-700 dark:text-zinc-200 w-28 text-center">{{ currentMonthLabel }}</span>
    <button @click="nextMonth" class="text-zinc-400 dark:text-zinc-500 hover:text-zinc-600 dark:hover:text-zinc-300 transition-colors">
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
