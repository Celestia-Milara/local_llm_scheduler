<template>
  <div class="flex items-center gap-2">
    <!-- AI Toggle -->
    <button @click="togglePanel"
      class="p-1.5 hover:bg-warm-100 rounded-lg transition-colors"
      :title="aiPanelVisible ? '关闭AI助手' : '打开AI助手'">
      <svg class="w-5 h-5" :class="aiPanelVisible ? 'text-copper-500' : 'text-warm-400'" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
        <path stroke-linecap="round" stroke-linejoin="round" d="M7.5 8.25h9m-9 3H12m-9.75 1.51c0 1.6 1.123 2.994 2.707 3.227 1.129.166 2.27.293 3.423.379.35.026.67.21.865.501L12 21l2.755-4.133a1.14 1.14 0 01.865-.501 48.172 48.172 0 003.423-.379c1.584-.233 2.707-1.626 2.707-3.228V6.741c0-1.602-1.123-2.995-2.707-3.228A48.394 48.394 0 0012 3c-2.392 0-4.744.175-7.043.513C3.373 3.746 2.25 5.14 2.25 6.741v6.018z" />
      </svg>
    </button>

    <!-- User Menu -->
    <div class="relative" ref="menuRef">
      <button @click="showMenu = !showMenu"
        class="w-7 h-7 rounded-full bg-copper-500 flex items-center justify-center text-xs font-medium text-white shadow-sm">
        R
      </button>
      <Transition name="fade">
        <div v-if="showMenu"
          class="absolute right-0 top-9 bg-white border border-warm-200 rounded-xl py-1 shadow-xl z-50 w-28 overflow-hidden">
          <button @click="handleLogout" class="w-full text-left px-3 py-2 text-xs text-warm-600 hover:bg-warm-100 transition-colors">退出登录</button>
        </div>
      </Transition>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useChat } from '../composables/useChat.js'

const { aiPanelVisible, togglePanel } = useChat()
const emit = defineEmits(['logout'])
const showMenu = ref(false)
const menuRef = ref(null)

function onDocumentClick(e) {
  if (showMenu.value && menuRef.value && !menuRef.value.contains(e.target)) {
    showMenu.value = false
  }
}

onMounted(() => document.addEventListener('click', onDocumentClick))
onUnmounted(() => document.removeEventListener('click', onDocumentClick))

function handleLogout() {
  showMenu.value = false
  emit('logout')
}
</script>
