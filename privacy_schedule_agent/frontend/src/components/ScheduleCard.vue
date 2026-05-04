<template>
  <div class="bg-slate-800 border border-slate-700 rounded-lg p-3 hover:border-slate-600 transition-all group">
    <!-- View Mode -->
    <div v-if="editingId !== schedule.id" class="flex items-start justify-between gap-2">
      <div class="flex-1 min-w-0">
        <div class="flex items-center gap-2 mb-1">
          <span class="text-[10px] text-slate-400 bg-slate-700 px-1.5 py-0.5 rounded">{{ schedule.start_time?.split(' ')[1]?.slice(0,5) }}</span>
          <h4 class="font-medium text-sm truncate">{{ schedule.title }}</h4>
          <span v-if="schedule.category"
            class="text-[10px] px-1.5 py-0.5 rounded-full border"
            :class="categoryClass(schedule.category)">
            {{ schedule.category }}
          </span>
        </div>
        <p v-if="schedule.location" class="text-xs text-slate-400 flex items-center gap-1">
          <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"/></svg>
          {{ schedule.location }}
        </p>
        <p v-if="schedule.description" class="text-xs text-slate-500 mt-0.5">{{ schedule.description }}</p>
      </div>
      <div class="flex items-center gap-1 shrink-0">
        <span v-if="schedule.status === 'conflicted'" class="text-[10px] text-amber-400 bg-amber-500/10 px-1.5 py-0.5 rounded-full">⚠ 冲突</span>
        <button @click="startEdit" class="opacity-0 group-hover:opacity-100 text-slate-500 hover:text-indigo-400 p-1" title="编辑">
          <svg class="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20"><path d="M17.414 2.586a2 2 0 00-2.828 0L7 10.172V13h2.828l7.586-7.586a2 2 0 000-2.828z"/></svg>
        </button>
        <button @click="handleDelete" class="opacity-0 group-hover:opacity-100 text-slate-500 hover:text-red-400 p-1" title="删除">
          <svg class="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20"><path d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z"/></svg>
        </button>
      </div>
    </div>

    <!-- Edit Mode -->
    <div v-else class="space-y-2">
      <input v-model="editForm.title" class="w-full bg-slate-700 border border-slate-600 rounded px-2 py-1 text-sm" placeholder="标题" @keyup.enter="saveEdit">
      <div class="flex gap-2">
        <input v-model="editForm.start_time" class="flex-1 bg-slate-700 border border-slate-600 rounded px-2 py-1 text-xs" placeholder="开始时间">
        <input v-model="editForm.end_time" class="flex-1 bg-slate-700 border border-slate-600 rounded px-2 py-1 text-xs" placeholder="结束时间">
      </div>
      <input v-model="editForm.location" class="w-full bg-slate-700 border border-slate-600 rounded px-2 py-1 text-xs" placeholder="地点">
      <div class="flex gap-2 pt-1">
        <button @click="saveEdit" class="bg-indigo-600 hover:bg-indigo-500 px-3 py-1 rounded text-xs">保存</button>
        <button @click="cancelEdit" class="bg-slate-600 hover:bg-slate-500 px-3 py-1 rounded text-xs">取消</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useSchedules } from '../composables/useSchedules.js'
import { useAuth } from '../composables/useAuth.js'

const props = defineProps({ schedule: Object })
const { updateSchedule, deleteSchedule } = useSchedules()
const { userId } = useAuth()

const editingId = ref(null)
const editForm = reactive({ title: '', start_time: '', end_time: '', location: '', description: '', category: '' })

function startEdit() {
  editingId.value = props.schedule.id
  Object.assign(editForm, {
    title: props.schedule.title,
    start_time: props.schedule.start_time,
    end_time: props.schedule.end_time,
    location: props.schedule.location || '',
    description: props.schedule.description || '',
    category: props.schedule.category || ''
  })
}

function cancelEdit() { editingId.value = null }

async function saveEdit() {
  await updateSchedule(props.schedule.id, { ...editForm }, userId.value)
  editingId.value = null
}

async function handleDelete() {
  if (confirm(`确认删除"${props.schedule.title}"？`)) {
    await deleteSchedule(props.schedule.id, userId.value)
  }
}

function categoryClass(cat) {
  const map = {
    '工作': 'bg-indigo-500/10 text-indigo-300 border-indigo-500/30',
    '学习': 'text-cyan-300 bg-cyan-500/10 border-cyan-500/30',
    '生活': 'text-orange-300 bg-orange-500/10 border-orange-500/30'
  }
  return map[cat] || 'text-slate-400 bg-slate-500/10 border-slate-500/30'
}
</script>
