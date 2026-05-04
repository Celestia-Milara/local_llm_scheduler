<template>
  <button @click="showDialog = true"
    class="w-8 h-8 bg-indigo-600 hover:bg-indigo-500 rounded-xl flex items-center justify-center text-white font-bold transition-colors"
    title="新建日程">
    +
  </button>
  <div v-if="showDialog" class="fixed inset-0 z-50 flex items-center justify-center bg-black/50" @click.self="showDialog = false">
    <div class="bg-slate-900 border border-slate-700 rounded-xl p-6 w-96">
      <h3 class="font-bold mb-4">新建日程</h3>
      <div class="space-y-3">
        <input v-model="form.title" placeholder="标题 *" class="w-full bg-slate-800 border border-slate-700 rounded px-3 py-2 text-sm">
        <input v-model="form.start_time" placeholder="开始时间 (YYYY-MM-DD HH:MM)" class="w-full bg-slate-800 border border-slate-700 rounded px-3 py-2 text-sm">
        <input v-model="form.end_time" placeholder="结束时间 (YYYY-MM-DD HH:MM)" class="w-full bg-slate-800 border border-slate-700 rounded px-3 py-2 text-sm">
        <input v-model="form.location" placeholder="地点" class="w-full bg-slate-800 border border-slate-700 rounded px-3 py-2 text-sm">
      </div>
      <div class="flex gap-2 mt-4 justify-end">
        <button @click="showDialog = false" class="bg-slate-700 hover:bg-slate-600 px-4 py-1.5 rounded text-sm">取消</button>
        <button @click="handleCreate" :disabled="!form.title || !form.start_time"
          class="bg-indigo-600 hover:bg-indigo-500 px-4 py-1.5 rounded text-sm disabled:opacity-50">创建</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useSchedules } from '../composables/useSchedules.js'
import { useAuth } from '../composables/useAuth.js'

const { createSchedule } = useSchedules()
const { userId } = useAuth()
const showDialog = ref(false)
const form = reactive({ title: '', start_time: '', end_time: '', location: '' })

async function handleCreate() {
  await createSchedule(form.title, form.start_time, form.end_time, userId.value)
  showDialog.value = false
  form.title = ''; form.start_time = ''; form.end_time = ''; form.location = ''
}
</script>
