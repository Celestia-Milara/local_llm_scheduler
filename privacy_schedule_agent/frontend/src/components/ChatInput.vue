<template>
  <div class="p-3 border-t border-slate-700">
    <div class="flex gap-2">
      <input v-model="text" @keyup.enter="send"
        placeholder="输入指令，例如：明天下午2点在图书馆开会..."
        class="flex-1 bg-slate-800 border border-slate-700 rounded-lg px-3 py-1.5 text-xs focus:outline-none focus:ring-1 focus:ring-indigo-500">
      <button @click="send" :disabled="loading || !text.trim()"
        class="bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors">
        发送
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
