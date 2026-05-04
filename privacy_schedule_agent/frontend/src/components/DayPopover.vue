<template>
  <div class="absolute inset-4 bg-slate-900 border border-slate-700 rounded-xl shadow-2xl z-20 flex flex-col overflow-hidden">
    <div class="flex items-center justify-between p-3 border-b border-slate-800">
      <h3 class="font-bold text-sm">{{ dateKey }} 日程</h3>
      <button @click="emit('close')" class="text-slate-400 hover:text-slate-200 text-lg">&times;</button>
    </div>
    <div class="flex-1 overflow-y-auto p-3 space-y-2">
      <ScheduleCard v-for="item in dayEvents" :key="item.id" :schedule="item" />
      <p v-if="dayEvents.length === 0" class="text-slate-500 italic text-sm text-center py-8">当天暂无日程</p>
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
  monthEvents.value.filter(e => e.start_time.startsWith(props.dateKey))
)
</script>
