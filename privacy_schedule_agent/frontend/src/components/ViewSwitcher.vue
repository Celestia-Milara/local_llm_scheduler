<template>
  <div class="flex bg-surface-100/80 dark:bg-zinc-800/80 border border-zinc-200/50 dark:border-zinc-700/50 rounded-lg text-xs overflow-hidden">
    <button @click="switchView('day')"
      class="px-3 py-1 transition-colors font-medium"
      :class="currentView === 'day' ? 'bg-primary-500 text-white' : 'text-zinc-500 dark:text-zinc-400 hover:text-zinc-700 dark:hover:text-zinc-200 hover:bg-surface-100 dark:hover:bg-zinc-700'">
      日
    </button>
    <button @click="switchView('week')"
      class="px-3 py-1 transition-colors font-medium border-x border-zinc-200/50 dark:border-zinc-700/50"
      :class="currentView === 'week' ? 'bg-primary-500 text-white' : 'text-zinc-500 dark:text-zinc-400 hover:text-zinc-700 dark:hover:text-zinc-200 hover:bg-surface-100 dark:hover:bg-zinc-700'">
      周
    </button>
    <button @click="switchView('month')"
      class="px-3 py-1 transition-colors font-medium"
      :class="currentView === 'month' ? 'bg-primary-500 text-white' : 'text-zinc-500 dark:text-zinc-400 hover:text-zinc-700 dark:hover:text-zinc-200 hover:bg-surface-100 dark:hover:bg-zinc-700'">
      月
    </button>
  </div>
</template>

<script setup>
import { useView } from '../composables/useView.js'
const { currentView, setView } = useView()

function switchView(view) {
  if (currentView.value !== view) {
    setView(view)
  }
}
</script>
