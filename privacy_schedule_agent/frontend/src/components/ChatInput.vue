<template>
  <div class="p-4 border-t border-warm-200/60">
    <div class="flex gap-2">
      <input v-model="text" @keyup.enter="send"
        placeholder="输入指令，例如：明天下午2点在图书馆开会..."
        class="flex-1 bg-warm-100 border border-warm-200/60 rounded-xl px-4 py-2 text-sm text-warm-700 placeholder-warm-400 focus:outline-none focus:ring-1 focus:ring-copper-400/40 focus:border-copper-400/40 transition-all">
      <button @click="send" :disabled="loading || !text.trim()"
        class="bg-copper-500 hover:bg-copper-400 active:bg-copper-600 disabled:opacity-40 disabled:cursor-not-allowed px-3.5 py-2 rounded-xl text-sm font-medium text-white transition-all">
        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M6 12L3.269 3.126A59.768 59.768 0 0121.485 12 59.77 59.77 0 013.27 20.876L5.999 12zm0 0h7.5" />
        </svg>
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useChat } from '../composables/useChat.js'
import { useAuth } from '../composables/useAuth.js'

const { sendMessage, loading } = useChat()
const { userId } = useAuth()
const text = ref('')

async function send() {
  if (!text.value.trim() || loading.value) return
  const msg = text.value
  text.value = ''
  await sendMessage(msg, userId.value)
}
</script>
