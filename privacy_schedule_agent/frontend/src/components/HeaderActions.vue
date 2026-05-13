<template>
  <div class="flex items-center gap-2">
    <!-- Theme Toggle -->
    <button @click="toggleTheme"
      class="p-1.5 hover:bg-surface-100 dark:hover:bg-zinc-800 rounded-lg transition-colors"
      :title="isDark() ? '切换到浅色模式' : '切换到暗黑模式'">
      <!-- Sun icon for dark mode -->
      <svg v-if="isDark()" class="w-5 h-5 text-yellow-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
        <path stroke-linecap="round" stroke-linejoin="round" d="M12 3v2.25m6.364.386l-1.591 1.591M21 12h-2.25m-.386 6.364l-1.591-1.591M12 18.75V21m-4.773-4.227l-1.591 1.591M5.25 12H3m4.227-4.773L5.636 5.636M15.75 12a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0z" />
      </svg>
      <!-- Moon icon for light mode -->
      <svg v-else class="w-5 h-5 text-zinc-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
        <path stroke-linecap="round" stroke-linejoin="round" d="M21.752 15.002A9.718 9.718 0 0118 15.75c-5.385 0-9.75-4.365-9.75-9.75 0-1.33.266-2.597.748-3.752A9.753 9.753 0 003 11.25C3 16.635 7.365 21 12.75 21a9.753 9.753 0 009.002-5.998z" />
      </svg>
    </button>

    <!-- AI Toggle -->
    <button @click="togglePanel"
      class="p-1.5 hover:bg-surface-100 dark:hover:bg-zinc-800 rounded-lg transition-colors"
      :title="aiPanelVisible ? '关闭AI助手' : '打开AI助手'">
      <svg class="w-5 h-5" :class="aiPanelVisible ? 'text-primary-500' : 'text-zinc-400'" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
        <path stroke-linecap="round" stroke-linejoin="round" d="M7.5 8.25h9m-9 3H12m-9.75 1.51c0 1.6 1.123 2.994 2.707 3.227 1.129.166 2.27.293 3.423.379.35.026.67.21.865.501L12 21l2.755-4.133a1.14 1.14 0 01.865-.501 48.172 48.172 0 003.423-.379c1.584-.233 2.707-1.626 2.707-3.228V6.741c0-1.602-1.123-2.995-2.707-3.228A48.394 48.394 0 0012 3c-2.392 0-4.744.175-7.043.513C3.373 3.746 2.25 5.14 2.25 6.741v6.018z" />
      </svg>
    </button>

    <!-- User Menu -->
    <div class="relative" ref="menuRef">
      <button @click="showMenu = !showMenu"
        class="w-7 h-7 rounded-full bg-primary-500 flex items-center justify-center text-xs font-medium text-white shadow-sm">
        R
      </button>
      <Transition name="fade">
        <div v-if="showMenu"
          class="absolute right-0 top-9 bg-white dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 rounded-xl py-1 shadow-xl z-50 w-28 overflow-hidden">
          <button @click="handleLogout" class="w-full text-left px-3 py-2 text-xs text-zinc-600 dark:text-zinc-300 hover:bg-surface-100 dark:hover:bg-zinc-700 transition-colors">退出登录</button>
        </div>
      </Transition>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useChat } from '../composables/useChat.js'
import { useTheme } from '../composables/useTheme.js'

const { aiPanelVisible, togglePanel } = useChat()
const { toggleTheme, isDark } = useTheme()
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
