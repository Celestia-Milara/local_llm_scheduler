<template>
  <div class="px-3">
    <p class="text-[10px] font-semibold text-zinc-400 dark:text-zinc-500 uppercase tracking-wider mb-2">分类</p>
    <div class="space-y-0.5">
      <button v-for="cat in categories" :key="cat.key"
        @click="activeCategory = cat.key"
        class="w-full flex items-center gap-2.5 px-2.5 py-1.5 rounded-lg text-left transition-colors"
        :class="activeCategory === cat.key
          ? 'bg-primary-50 dark:bg-primary-500/10 text-zinc-700 dark:text-zinc-200'
          : 'text-zinc-500 dark:text-zinc-400 hover:bg-surface-100 dark:hover:bg-zinc-800 hover:text-zinc-700 dark:hover:text-zinc-200'">
        <div class="w-2 h-2 rounded-full shrink-0" :class="cat.dotClass"></div>
        <span class="text-xs flex-1">{{ cat.label }}</span>
        <span class="text-[10px] text-zinc-400 dark:text-zinc-500 tabular-nums">{{ cat.count }}</span>
      </button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useSchedules } from '../composables/useSchedules.js'

const { activeCategory, categoryCounts } = useSchedules()

const categories = computed(() => {
  const counts = categoryCounts.value
  return [
    { key: '', label: '全部', dotClass: 'bg-primary-400', count: counts[''] || 0 },
    { key: '工作', label: '工作', dotClass: 'bg-cat-work-400', count: counts['工作'] || 0 },
    { key: '学习', label: '学习', dotClass: 'bg-cat-study-400', count: counts['学习'] || 0 },
    { key: '生活', label: '生活', dotClass: 'bg-cat-life-400', count: counts['生活'] || 0 },
  ]
})
</script>
