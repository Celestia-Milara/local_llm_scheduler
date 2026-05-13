<template>
  <button @click="showDialog = true"
    class="w-full flex items-center justify-center gap-2 bg-primary-500 hover:bg-primary-400 active:bg-primary-600 text-white rounded-xl px-3 py-2 text-sm font-medium transition-all shadow-sm shadow-primary-500/20"
    title="新建日程">
    <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
      <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
    </svg>
    新建日程
  </button>

  <Transition name="scale">
    <div v-if="showDialog" class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm" @click.self="showDialog = false">
      <div class="bg-white dark:bg-zinc-900 border border-zinc-200/80 dark:border-zinc-700/80 rounded-2xl p-6 w-96 shadow-2xl shadow-black/10">
        <div class="flex items-center justify-between mb-5">
          <h3 class="font-display text-lg text-zinc-800 dark:text-zinc-200">新建日程</h3>
          <button @click="showDialog = false" class="w-7 h-7 flex items-center justify-center rounded-lg text-zinc-400 dark:text-zinc-500 hover:text-zinc-600 dark:hover:text-zinc-300 hover:bg-surface-100 dark:hover:bg-zinc-800 transition-colors">
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        <div class="space-y-3.5">
          <input v-model="form.title" placeholder="标题 *"
            class="w-full bg-surface-50 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 rounded-xl px-4 py-2.5 text-sm text-zinc-700 dark:text-zinc-200 placeholder-zinc-400 dark:placeholder-zinc-500 focus:outline-none focus:ring-1 focus:ring-primary-400/50">

          <div class="flex items-center gap-2">
            <span class="text-xs text-zinc-500 dark:text-zinc-400 w-8 shrink-0">开始</span>
            <input type="date" v-model="formStartDate"
              class="flex-1 bg-surface-50 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 rounded-xl px-3 py-2.5 text-sm text-zinc-700 dark:text-zinc-200 focus:outline-none focus:ring-1 focus:ring-primary-400/50">
            <input type="time" v-model="formStartTime" step="60"
              class="flex-1 bg-surface-50 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 rounded-xl px-3 py-2.5 text-sm text-zinc-700 dark:text-zinc-200 focus:outline-none focus:ring-1 focus:ring-primary-400/50">
          </div>

          <div class="flex items-center gap-2">
            <span class="text-xs text-zinc-500 dark:text-zinc-400 w-8 shrink-0">结束</span>
            <input type="date" v-model="formEndDate"
              class="flex-1 bg-surface-50 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 rounded-xl px-3 py-2.5 text-sm text-zinc-700 dark:text-zinc-200 focus:outline-none focus:ring-1 focus:ring-primary-400/50">
            <input type="time" v-model="formEndTime" step="60"
              class="flex-1 bg-surface-50 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 rounded-xl px-3 py-2.5 text-sm text-zinc-700 dark:text-zinc-200 focus:outline-none focus:ring-1 focus:ring-primary-400/50">
          </div>

          <input v-model="form.location" placeholder="地点"
            class="w-full bg-surface-50 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 rounded-xl px-4 py-2.5 text-sm text-zinc-700 dark:text-zinc-200 placeholder-zinc-400 dark:placeholder-zinc-500 focus:outline-none focus:ring-1 focus:ring-primary-400/50">

          <div>
            <label class="text-xs text-zinc-400 dark:text-zinc-500 mb-1 block">分类</label>
            <select v-model="form.category"
              class="w-full bg-surface-50 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 rounded-xl px-4 py-2.5 text-sm text-zinc-700 dark:text-zinc-200 focus:outline-none focus:ring-1 focus:ring-primary-400/50">
              <option value="">无分类</option>
              <option value="工作">工作</option>
              <option value="学习">学习</option>
              <option value="生活">生活</option>
            </select>
          </div>

          <input v-model="form.description" placeholder="描述（可选）"
            class="w-full bg-surface-50 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 rounded-xl px-4 py-2.5 text-sm text-zinc-700 dark:text-zinc-200 placeholder-zinc-400 dark:placeholder-zinc-500 focus:outline-none focus:ring-1 focus:ring-primary-400/50">

          <div>
            <label class="text-xs text-zinc-400 dark:text-zinc-500 mb-1 block">隐私级别</label>
            <select v-model="form.privacy_level"
              class="w-full bg-surface-50 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 rounded-xl px-4 py-2.5 text-sm text-zinc-700 dark:text-zinc-200 focus:outline-none focus:ring-1 focus:ring-primary-400/50">
              <option :value="1">公开</option>
              <option :value="2">内部</option>
              <option :value="3">绝密</option>
            </select>
          </div>

          <div>
            <label class="text-xs text-zinc-400 dark:text-zinc-500 mb-1 block">重复</label>
            <select v-model="form.recurrence_rule"
              class="w-full bg-surface-50 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 rounded-xl px-4 py-2.5 text-sm text-zinc-700 dark:text-zinc-200 focus:outline-none focus:ring-1 focus:ring-primary-400/50">
              <option value="">不重复</option>
              <option value="daily">每天</option>
              <option value="weekdays">工作日</option>
              <option value="weekly">每周</option>
              <option value="monthly">每月</option>
            </select>
          </div>

          <div v-if="form.recurrence_rule">
            <label class="text-xs text-zinc-400 dark:text-zinc-500 mb-1 block">重复截止</label>
            <input type="date" v-model="formRecurrenceEnd"
              class="w-full bg-surface-50 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 rounded-xl px-3 py-2.5 text-sm text-zinc-700 dark:text-zinc-200 focus:outline-none focus:ring-1 focus:ring-primary-400/50">
          </div>
        </div>
        <div class="flex gap-2 mt-5 justify-end">
          <button @click="showDialog = false" class="px-4 py-2 rounded-xl text-sm text-zinc-400 dark:text-zinc-500 hover:text-zinc-600 dark:hover:text-zinc-300 hover:bg-surface-100 dark:hover:bg-zinc-800 transition-colors">取消</button>
          <button @click="handleCreate" :disabled="!form.title || !formStartDate || !formStartTime || !formEndDate || !formEndTime"
            class="bg-primary-500 hover:bg-primary-400 active:bg-primary-600 disabled:opacity-40 disabled:cursor-not-allowed px-5 py-2 rounded-xl text-sm font-medium text-white transition-all">创建</button>
        </div>
      </div>
    </div>
  </Transition>
</template>

<script setup>
import { reactive, ref } from 'vue'
import axios from 'axios'
import { useSchedules } from '../composables/useSchedules.js'
import { useAuth } from '../composables/useAuth.js'

const { fetchMonth } = useSchedules()
const { userId } = useAuth()
const showDialog = ref(false)
const form = reactive({ title: '', location: '', recurrence_rule: '', category: '', description: '', privacy_level: 1 })
const formStartDate = ref('')
const formStartTime = ref('')
const formEndDate = ref('')
const formEndTime = ref('')
const formRecurrenceEnd = ref('')

function resetForm() {
  form.title = ''; form.location = ''; form.recurrence_rule = ''; form.category = ''; form.description = ''; form.privacy_level = 1
  formStartDate.value = ''; formStartTime.value = ''
  formEndDate.value = ''; formEndTime.value = ''
  formRecurrenceEnd.value = ''
}

async function handleCreate() {
  if (!form.title.trim() || !formStartDate.value || !formStartTime.value || !formEndDate.value || !formEndTime.value) return
  const startTime = `${formStartDate.value} ${formStartTime.value}:00`
  const endTime = `${formEndDate.value} ${formEndTime.value}:00`

  const payload = {
    title: form.title.trim(),
    start_time: startTime,
    end_time: endTime,
    location: form.location || null,
    category: form.category || null,
    description: form.description || null,
    privacy_level: form.privacy_level || 1,
    user_id: userId.value
  }
  if (form.recurrence_rule) {
    payload.recurrence_rule = form.recurrence_rule
    if (formRecurrenceEnd.value) {
      payload.recurrence_end = `${formRecurrenceEnd.value} 23:59:59`
    }
  }

  try {
    await axios.post('/schedules', payload)
    showDialog.value = false
    resetForm()
    await fetchMonth(userId.value)
  } catch {
    alert('创建失败，请重试')
  }
}
</script>
