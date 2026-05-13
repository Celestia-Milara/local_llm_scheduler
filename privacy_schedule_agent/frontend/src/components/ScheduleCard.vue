<template>
  <div>
    <!-- Schedule card (clickable) -->
    <div class="bg-white dark:bg-zinc-900 border border-zinc-200/60 dark:border-zinc-700/60 rounded-xl p-3.5 hover:border-zinc-300/50 dark:hover:border-zinc-600/50 hover:bg-surface-50 dark:hover:bg-zinc-800 hover-lift group cursor-pointer"
      @click="openDetail('view')">
      <div class="flex items-start justify-between gap-3">
        <div class="flex-1 min-w-0">
          <div class="flex items-center gap-2 mb-1.5">
            <span class="text-[10px] font-medium text-zinc-400 dark:text-zinc-500 bg-surface-100 dark:bg-zinc-800 px-2 py-0.5 rounded-md border border-zinc-200/50 dark:border-zinc-700/50">{{ schedule.start_time?.split(' ')[1]?.slice(0,5) }}</span>
            <h4 class="text-sm font-medium text-zinc-800 dark:text-zinc-200 truncate">{{ schedule.title }}</h4>
            <span v-if="schedule.category"
              class="text-[10px] px-1.5 py-0.5 rounded-full border"
              :class="categoryClass(schedule.category)">
              {{ schedule.category }}
            </span>
            <span v-if="schedule.privacy_level && schedule.privacy_level > 1"
              class="text-[10px]" :title="privacyLabel(schedule.privacy_level)">
              {{ schedule.privacy_level === 3 ? '🔒' : '🔐' }}
            </span>
            <span v-if="schedule.recurrence_rule"
              class="text-[9px] text-zinc-400 dark:text-zinc-500 font-medium" title="重复日程">↻</span>
          </div>
          <p v-if="schedule.location" class="text-xs text-zinc-500 dark:text-zinc-400 flex items-center gap-1">
            <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"/></svg>
            {{ schedule.location }}
          </p>
          <p v-if="schedule.description" class="text-xs text-zinc-400 dark:text-zinc-500 mt-1 line-clamp-1">{{ schedule.description }}</p>
        </div>
        <div class="flex items-center gap-1 shrink-0" @click.stop>
          <span v-if="schedule.status === 'conflicted'" class="text-[10px] text-danger-400 bg-danger-400/10 px-1.5 py-0.5 rounded-full border border-danger-400/20">冲突</span>
          <button @click="openDetail('edit')" class="opacity-0 group-hover:opacity-100 text-zinc-500 dark:text-zinc-400 hover:text-primary-400 p-1 transition-all" title="编辑">
            <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0115.75 21H5.25A2.25 2.25 0 013 18.75V8.25A2.25 2.25 0 015.25 6H10" />
            </svg>
          </button>
          <button @click="handleDelete" class="opacity-0 group-hover:opacity-100 text-zinc-500 dark:text-zinc-400 hover:text-danger-500 p-1 transition-all" title="删除">
            <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" />
            </svg>
          </button>
        </div>
      </div>
    </div>

    <!-- Detail modal -->
    <ScheduleDetail :schedule="schedule" :visible="detailVisible" @close="detailVisible = false" @update="$emit('update')" />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useSchedules } from '../composables/useSchedules.js'
import { useAuth } from '../composables/useAuth.js'
import ScheduleDetail from './ScheduleDetail.vue'
import { categoryClass } from '../utils/eventStyles.js'

const props = defineProps({ schedule: Object })
defineEmits(['update'])

const { deleteSchedule } = useSchedules()
const { userId } = useAuth()

const detailVisible = ref(false)
const detailMode = ref('view')

function openDetail(mode) {
  detailMode.value = mode
  detailVisible.value = true
}

async function handleDelete() {
  if (confirm(`确认删除「${props.schedule.title}」？`)) {
    await deleteSchedule(props.schedule.id, userId.value)
  }
}

function privacyLabel(level) {
  const map = { 1: '公开', 2: '内部', 3: '绝密' }
  return map[level] || '公开'
}
</script>
