<template>
  <div class="flex items-center gap-2">
    <button @click="togglePanel"
      class="p-1.5 hover:bg-slate-800 rounded-lg transition-colors"
      :title="aiPanelVisible ? '关闭AI助手' : '打开AI助手'">
      <svg class="w-5 h-5" :class="aiPanelVisible ? 'text-indigo-400' : 'text-slate-400'" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
      </svg>
    </button>
    <div class="relative" @click.outside="showMenu = false">
      <button @click="showMenu = !showMenu"
        class="w-7 h-7 rounded-full bg-indigo-600 flex items-center justify-center text-xs font-medium">
        R
      </button>
      <div v-if="showMenu"
        class="absolute right-0 top-8 bg-slate-800 border border-slate-700 rounded-lg py-1 shadow-xl z-50 w-28">
        <button @click="handleLogout" class="w-full text-left px-3 py-1.5 text-xs hover:bg-slate-700">退出登录</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useChat } from '../composables/useChat.js'

const { aiPanelVisible, togglePanel } = useChat()
const emit = defineEmits(['logout'])
const showMenu = ref(false)

function handleLogout() {
  showMenu.value = false
  emit('logout')
}
</script>
