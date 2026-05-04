<template>
  <Transition name="slide">
    <aside v-if="aiPanelVisible"
      class="w-80 bg-slate-900 border-l border-slate-800 flex flex-col shrink-0 overflow-hidden">
      <div class="flex items-center justify-between p-3 border-b border-slate-800">
        <span class="text-xs font-medium text-slate-400 uppercase tracking-wider">AI 助手</span>
        <button @click="togglePanel" class="text-slate-400 hover:text-slate-200">&times;</button>
      </div>
      <ChatMessages />
      <ChatInput />
    </aside>
  </Transition>
</template>

<script setup>
import { useChat } from '../composables/useChat.js'
import ChatMessages from './ChatMessages.vue'
import ChatInput from './ChatInput.vue'

const { aiPanelVisible, togglePanel } = useChat()
</script>

<style scoped>
.slide-enter-active, .slide-leave-active { transition: all 0.2s ease; }
.slide-enter-from, .slide-leave-to { transform: translateX(100%); opacity: 0; }
</style>
