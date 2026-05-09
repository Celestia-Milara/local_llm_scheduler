<template>
  <div class="absolute inset-6 z-20 flex items-center justify-center" @click.self="emit('close')">
    <div class="w-full max-w-md bg-white border border-warm-200/80 rounded-2xl shadow-2xl shadow-black/10 ring-1 ring-warm-200/50 overflow-hidden">
      <!-- Header -->
      <div class="flex items-center justify-between px-5 py-4 border-b border-warm-200/50">
        <h3 class="font-display text-lg text-warm-800">{{ formattedDate }}</h3>
        <button @click="emit('close')" class="w-7 h-7 flex items-center justify-center rounded-lg text-warm-400 hover:text-warm-600 hover:bg-warm-100 transition-colors">
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
      <!-- Content -->
      <div class="p-5 space-y-3 max-h-80 overflow-y-auto">
        <ScheduleCard v-for="item in dayEvents" :key="item.id" :schedule="item" />
        <p v-if="dayEvents.length === 0" class="text-warm-400 text-sm text-center py-8">当天暂无日程</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useSchedules } from '../composables/useSchedules.js'
import ScheduleCard from './ScheduleCard.vue'

const props = defineProps({ dateKey: String })
const emit = defineEmits(['close'])

const { monthEvents } = useSchedules()

const dayEvents = computed(() =>
  monthEvents.value.filter(e => {
    const start = e.start_time.slice(0, 10)
    const end = e.end_time.slice(0, 10)
    return props.dateKey >= start && props.dateKey <= end
  })
)

const formattedDate = computed(() => {
  const [y, m, d] = props.dateKey.split('-')
  return `${y}年${parseInt(m)}月${parseInt(d)}日`
})
</script>
