<template>
  <Transition name="slide">
    <aside v-if="aiPanelVisible"
      ref="panelRef"
      class="bg-white/90 dark:bg-zinc-900/90 backdrop-blur-sm border-l border-zinc-200/60 dark:border-zinc-700/60 flex flex-col shrink-0 overflow-hidden"
      :style="{ width: panelWidth + 'px' }">
      <!-- Resize handle -->
      <div
        class="absolute left-0 top-0 bottom-0 w-1.5 cursor-col-resize group z-10"
        @mousedown.prevent="startDrag">
        <div class="absolute left-0 top-0 bottom-0 w-px bg-zinc-200/50 dark:bg-zinc-700/50 group-hover:bg-primary-400/50 group-hover:w-[2px] transition-all"></div>
        <div class="absolute left-0 top-1/2 -translate-y-1/2 -translate-x-px w-1 h-8 rounded-full bg-zinc-300/0 group-hover:bg-primary-400/40 group-hover:shadow-sm group-hover:shadow-primary-400/30 transition-all"></div>
      </div>
      <!-- Header -->
      <div class="flex items-center justify-between px-4 py-3 border-b border-zinc-200/60 dark:border-zinc-700/60 pl-3">
        <div class="flex items-center gap-2">
          <svg class="w-4 h-4 text-primary-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19.8 15.3M14.25 3.104c.251.023.501.05.75.082M19.8 15.3l-1.57.393A9.065 9.065 0 0112 15a9.065 9.065 0 00-6.23.693L5 14.5m14.8.8l1.402 1.402c1.232 1.232.65 3.318-1.067 3.611A48.309 48.309 0 0112 21c-2.773 0-5.491-.235-8.135-.687-1.718-.293-2.3-2.379-1.067-3.61L5 14.5" />
          </svg>
          <span class="text-xs font-medium text-zinc-600 dark:text-zinc-300 uppercase tracking-wider">AI 助手</span>
          <span class="text-[8px] text-moss-600 dark:text-moss-400 bg-moss-500/10 px-1.5 py-0.5 rounded-full border border-moss-500/20 privacy-badge">本地</span>
        </div>
        <button @click="togglePanel" class="w-7 h-7 flex items-center justify-center rounded-lg text-zinc-400 dark:text-zinc-500 hover:text-zinc-600 dark:hover:text-zinc-300 hover:bg-surface-100 dark:hover:bg-zinc-800 transition-colors">
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
      <ChatMessages />
      <ChatInput />

      <!-- Privacy footer -->
      <div class="px-4 py-2 border-t border-zinc-200/30 dark:border-zinc-700/30">
        <p class="text-[8px] text-zinc-400 dark:text-zinc-500 text-center leading-tight">
          此回复由本地模型生成，数据未离开您的设备
        </p>
      </div>
    </aside>
  </Transition>
</template>

<script setup>
import { ref, onUnmounted } from 'vue'
import { useChat } from '../composables/useChat.js'
import ChatMessages from './ChatMessages.vue'
import ChatInput from './ChatInput.vue'

const { aiPanelVisible, togglePanel } = useChat()

const MIN_WIDTH = 240
const MAX_WIDTH = 500
const STORAGE_KEY = 'ai_panel_width'

const panelWidth = ref(parseInt(localStorage.getItem(STORAGE_KEY)) || 320)
const isDragging = ref(false)
const startX = ref(0)
const startWidth = ref(0)

function startDrag(e) {
  isDragging.value = true
  startX.value = e.clientX
  startWidth.value = panelWidth.value
  document.addEventListener('mousemove', onDrag)
  document.addEventListener('mouseup', stopDrag)
  document.body.style.cursor = 'col-resize'
}

function onDrag(e) {
  if (!isDragging.value) return
  const delta = startX.value - e.clientX
  panelWidth.value = Math.max(MIN_WIDTH, Math.min(MAX_WIDTH, startWidth.value + delta))
}

function stopDrag() {
  isDragging.value = false
  localStorage.setItem(STORAGE_KEY, String(panelWidth.value))
  document.removeEventListener('mousemove', onDrag)
  document.removeEventListener('mouseup', stopDrag)
  document.body.style.cursor = ''
}

onUnmounted(() => {
  document.removeEventListener('mousemove', onDrag)
  document.removeEventListener('mouseup', stopDrag)
})
</script>
