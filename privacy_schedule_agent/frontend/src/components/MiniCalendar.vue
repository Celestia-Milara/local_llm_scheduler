<template>
  <div class="w-full px-1">
    <div class="flex items-center justify-between mb-1">
      <button @click="prevMonth" class="text-slate-400 hover:text-slate-200 text-xs">‹</button>
      <span class="text-[10px] text-slate-400 font-medium">{{ label }}</span>
      <button @click="nextMonth" class="text-slate-400 hover:text-slate-200 text-xs">›</button>
    </div>
    <div class="grid grid-cols-7 text-[8px] text-slate-500 mb-0.5">
      <span v-for="d in weekDays" :key="d" class="text-center">{{ d }}</span>
    </div>
    <div class="grid grid-cols-7 gap-0">
      <button v-for="cell in flatMatrix" :key="cell.dateKey"
        @click="selectDate(cell)"
        class="text-[10px] w-full aspect-square flex items-center justify-center rounded-full"
        :class="[
          cell.inMonth ? 'text-slate-300' : 'text-slate-600',
          cell.dateKey === selectedDate ? 'bg-indigo-600 text-white' : 'hover:bg-slate-800'
        ]">
        <span class="relative">
          {{ cell.date.getDate() }}
          <span v-if="hasEvents(cell.dateKey)"
            class="absolute -top-0.5 -right-1.5 w-1 h-1 rounded-full bg-indigo-400"></span>
        </span>
      </button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useSchedules } from '../composables/useSchedules.js'

const { currentMonth, selectedDate, monthMatrix, hasEvents, fetchMonth } = useSchedules()
const weekDays = ['日', '一', '二', '三', '四', '五', '六']

const flatMatrix = computed(() => monthMatrix.value)
const label = computed(() => `${currentMonth.value.getMonth() + 1}月`)

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
</script>
