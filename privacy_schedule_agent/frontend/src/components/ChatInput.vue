<template>
  <div class="border-t border-warm-200/60">
    <!-- 快捷操作按钮 -->
    <div class="flex gap-1.5 px-4 pt-3 pb-1.5 overflow-x-auto">
      <button v-for="action in quickActions" :key="action.label"
        @click="quickSend(action.prompt)"
        :disabled="loading"
        class="flex items-center gap-1 shrink-0 px-2.5 py-1.5 rounded-lg text-xs text-warm-500 bg-warm-100/80 border border-warm-200/40 hover:bg-copper-500/10 hover:text-copper-600 hover:border-copper-300/50 disabled:opacity-40 disabled:cursor-not-allowed transition-all">
        <!-- 图标 -->
        <svg v-if="action.icon === 'add'" class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 4v16m8-8H4" />
        </svg>
        <svg v-else-if="action.icon === 'view'" class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
        </svg>
        <svg v-else-if="action.icon === 'free'" class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <svg v-else-if="action.icon === 'summary'" class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
        <svg v-else-if="action.icon === 'export'" class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
        </svg>
        <span>{{ action.label }}</span>
      </button>
    </div>
    <!-- 输入框 -->
    <div class="p-4 pt-2">
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
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useChat } from '../composables/useChat.js'
import { useAuth } from '../composables/useAuth.js'

const { sendMessage, loading } = useChat()
const { userId } = useAuth()
const text = ref('')

const quickActions = [
  { icon: 'add',     label: '添加日程',  prompt: '明天下午3点在图书馆开会' },
  { icon: 'view',    label: '查看本周',  prompt: '我这周有什么安排？' },
  { icon: 'free',    label: '查找空闲',  prompt: '明天有什么空闲时间？' },
  { icon: 'summary', label: '周总结',    prompt: '总结一下这周的安排' },
  { icon: 'export',  label: '导出日程',  prompt: '导出我的日程' },
]

async function send() {
  if (!text.value.trim() || loading.value) return
  const msg = text.value
  text.value = ''
  await sendMessage(msg, userId.value)
}

async function quickSend(prompt) {
  if (loading.value) return
  text.value = prompt
  await send()
}
</script>
