<template>
  <div class="flex bg-warm-100/80 border border-warm-200/50 rounded-lg text-xs overflow-hidden">
    <button @click="setView('day')"
      class="px-3 py-1 transition-colors font-medium"
      :class="currentView === 'day' ? 'bg-copper-500 text-white' : 'text-warm-500 hover:text-warm-700 hover:bg-warm-100'">
      日
    </button>
    <button @click="setView('week')"
      class="px-3 py-1 transition-colors font-medium border-x border-warm-200/50"
      :class="currentView === 'week' ? 'bg-copper-500 text-white' : 'text-warm-500 hover:text-warm-700 hover:bg-warm-100'">
      周
    </button>
    <button @click="setView('month')"
      class="px-3 py-1 transition-colors font-medium"
      :class="currentView === 'month' ? 'bg-copper-500 text-white' : 'text-warm-500 hover:text-warm-700 hover:bg-warm-100'">
      月
    </button>
  </div>
</template>

<script setup>
import { useView } from '../composables/useView.js'
const { currentView, setView } = useView()
</script>
