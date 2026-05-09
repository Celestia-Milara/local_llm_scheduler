<template>
  <aside ref="sidebarRef" class="bg-white/60 border-r border-warm-200/50 flex flex-col items-center py-4 gap-3 shrink-0 relative select-none"
    :style="{ width: sidebarWidth + 'px' }">

    <!-- Logo area -->
    <div class="flex flex-col items-center gap-1 px-3 mb-1">
      <svg class="w-5 h-5 text-copper-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
        <path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
      </svg>
      <span class="text-[9px] text-warm-400 privacy-badge">PRIVACY</span>
    </div>

    <CreateButton />
    <div class="border-t border-warm-200/50 w-8 my-1"></div>
    <MiniCalendar />
    <div class="flex-1"></div>

    <!-- Bottom actions -->
    <PrivacyStatus />
    <button @click="exportData"
      class="text-[10px] text-warm-400 hover:text-copper-500 transition-colors py-1 px-3 rounded-lg hover:bg-warm-100 flex items-center gap-1.5">
      <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
        <path stroke-linecap="round" stroke-linejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" />
      </svg>
      导出数据
    </button>

    <!-- Drag handle -->
    <div
      class="absolute right-0 top-0 bottom-0 w-1.5 cursor-col-resize group z-10"
      @mousedown.prevent="startDrag">
      <div class="absolute right-0 top-0 bottom-0 w-px bg-warm-200/50 group-hover:bg-copper-400/50 group-hover:w-[2px] transition-all"></div>
      <div class="absolute right-0 top-1/2 -translate-y-1/2 translate-x-px w-1 h-8 rounded-full bg-warm-300/0 group-hover:bg-copper-400/40 group-hover:shadow-sm group-hover:shadow-copper-400/30 transition-all"></div>
    </div>
  </aside>
</template>

<script setup>
import { ref, onUnmounted } from 'vue'
import CreateButton from './CreateButton.vue'
import MiniCalendar from './MiniCalendar.vue'
import PrivacyStatus from './PrivacyStatus.vue'

const MIN_WIDTH = 160
const MAX_WIDTH = 400
const STORAGE_KEY = 'sidebar_width'

const sidebarWidth = ref(parseInt(localStorage.getItem(STORAGE_KEY)) || 224)
const isDragging = ref(false)

function startDrag(e) {
  isDragging.value = true
  document.addEventListener('mousemove', onDrag)
  document.addEventListener('mouseup', stopDrag)
  document.body.style.cursor = 'col-resize'
}

function onDrag(e) {
  if (!isDragging.value) return
  sidebarWidth.value = Math.max(MIN_WIDTH, Math.min(MAX_WIDTH, e.clientX))
}

function stopDrag() {
  isDragging.value = false
  localStorage.setItem(STORAGE_KEY, String(sidebarWidth.value))
  document.removeEventListener('mousemove', onDrag)
  document.removeEventListener('mouseup', stopDrag)
  document.body.style.cursor = ''
}

function exportData() {
  const a = document.createElement('a')
  a.href = '/schedules/export/json'
  a.download = ''
  a.click()
}

onUnmounted(() => {
  document.removeEventListener('mousemove', onDrag)
  document.removeEventListener('mouseup', stopDrag)
})
</script>
