<template>
  <div class="h-screen flex flex-col bg-warm-50 text-warm-700 overflow-hidden">
    <Toolbar @logout="$emit('logout')" />
    <div class="flex flex-1 overflow-hidden min-h-0">
      <Sidebar />
      <component :is="activeView" class="flex-1 min-w-0" />
      <AiPanel />
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useView } from '../composables/useView.js'
defineEmits(['logout'])
import Toolbar from './Toolbar.vue'
import Sidebar from './Sidebar.vue'
import MonthView from './MonthView.vue'
import WeekView from './WeekView.vue'
import DayView from './DayView.vue'
import AiPanel from './AiPanel.vue'

const { currentView } = useView()

const activeView = computed(() => {
  switch (currentView.value) {
    case 'week': return WeekView
    case 'day': return DayView
    default: return MonthView
  }
})
</script>
