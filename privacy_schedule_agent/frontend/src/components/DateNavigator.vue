<template>
  <div class="flex items-center gap-2 text-sm">
    <button @click="goToday"
      class="bg-slate-800 hover:bg-slate-700 px-3 py-1 rounded-lg text-xs font-medium transition-colors">
      今天
    </button>
    <button @click="prevMonth" class="text-slate-400 hover:text-slate-200 text-lg leading-none">&#x2039;</button>
    <span class="text-sm font-medium w-28 text-center">{{ currentMonthLabel }}</span>
    <button @click="nextMonth" class="text-slate-400 hover:text-slate-200 text-lg leading-none">&#x203a;</button>
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
