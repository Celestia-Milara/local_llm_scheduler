<template>
  <Transition name="slide">
    <aside v-if="aiPanelVisible"
      class="w-80 bg-white/90 backdrop-blur-sm border-l border-warm-200/60 flex flex-col shrink-0 overflow-hidden">
      <!-- Header -->
      <div class="flex items-center justify-between px-4 py-3 border-b border-warm-200/60">
        <div class="flex items-center gap-2">
          <svg class="w-4 h-4 text-copper-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19.8 15.3M14.25 3.104c.251.023.501.05.75.082M19.8 15.3l-1.57.393A9.065 9.065 0 0112 15a9.065 9.065 0 00-6.23.693L5 14.5m14.8.8l1.402 1.402c1.232 1.232.65 3.318-1.067 3.611A48.309 48.309 0 0112 21c-2.773 0-5.491-.235-8.135-.687-1.718-.293-2.3-2.379-1.067-3.61L5 14.5" />
          </svg>
          <span class="text-xs font-medium text-warm-600 uppercase tracking-wider">AI 助手</span>
          <span class="text-[8px] text-moss-600 bg-moss-500/10 px-1.5 py-0.5 rounded-full border border-moss-500/20 privacy-badge">本地</span>
        </div>
        <button @click="togglePanel" class="w-7 h-7 flex items-center justify-center rounded-lg text-warm-400 hover:text-warm-600 hover:bg-warm-100 transition-colors">
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
      <ChatMessages />
      <ChatInput />

      <!-- Privacy footer -->
      <div class="px-4 py-2 border-t border-warm-200/30">
        <p class="text-[8px] text-warm-400 text-center leading-tight">
          此回复由本地模型生成，数据未离开您的设备
        </p>
      </div>
    </aside>
  </Transition>
</template>

<script setup>
import { useChat } from '../composables/useChat.js'
import ChatMessages from './ChatMessages.vue'
import ChatInput from './ChatInput.vue'

const { aiPanelVisible, togglePanel } = useChat()
</script>
