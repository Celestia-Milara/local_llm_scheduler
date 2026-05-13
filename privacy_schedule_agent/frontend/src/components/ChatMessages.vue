<template>
  <div ref="scrollRef" class="flex-1 overflow-y-auto px-4 py-4 space-y-3">
    <div v-for="(msg, i) in messages" :key="i"
      :class="['flex', msg.role === 'user' ? 'justify-end' : 'justify-start']">
      <div :class="['max-w-[85%] text-sm leading-relaxed',
        msg.role === 'user'
          ? 'bg-primary-500 text-white rounded-2xl rounded-tr-md p-3'
          : 'bg-surface-100 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-200 rounded-2xl rounded-tl-md border border-zinc-200/50 dark:border-zinc-700/50']">
        <!-- 推理步骤（仅 assistant 消息） -->
        <div v-if="msg.steps && msg.steps.length > 0" class="mb-2">
          <div v-for="(step, si) in msg.steps" :key="si"
            class="flex items-center gap-1.5 text-xs text-zinc-500 dark:text-zinc-400 mb-0.5">
            <template v-if="step.type === 'thinking'">
              <svg class="w-3 h-3 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              <span class="italic">{{ step.message || '分析中...' }}</span>
            </template>
            <template v-else-if="step.type === 'tool_call'">
              <svg class="w-3 h-3 text-primary-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                <path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
              <span>调用工具：<code class="font-mono text-primary-600 dark:text-primary-400 bg-primary-500/10 px-1 rounded">{{ step.name }}</code></span>
            </template>
            <template v-else-if="step.type === 'tool_result'">
              <svg class="w-3 h-3 text-moss-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span><code class="font-mono text-moss-600 dark:text-moss-400 bg-moss-500/10 px-1 rounded">{{ step.name }}</code> 执行完毕</span>
            </template>
          </div>
        </div>
        <!-- 消息内容 -->
        <div :class="[msg.role === 'user' ? '' : msg.steps && msg.steps.length ? '' : 'p-3']">
          <span class="pre-wrap">{{ msg.content }}</span>
          <span v-if="msg.streaming" class="inline-block w-1.5 h-4 bg-primary-400 animate-pulse ml-0.5 align-text-bottom"></span>
        </div>
      </div>
    </div>
    <div v-if="loading && messages.length > 0 && !messages[messages.length-1]?.streaming" class="flex justify-start">
      <div class="bg-surface-100 dark:bg-zinc-800 border border-zinc-200/50 dark:border-zinc-700/50 px-4 py-3 rounded-2xl rounded-tl-md flex items-center gap-1.5">
        <div class="w-1.5 h-1.5 bg-primary-400 rounded-full animate-bounce" style="animation-delay: 0s"></div>
        <div class="w-1.5 h-1.5 bg-primary-400 rounded-full animate-bounce" style="animation-delay: 0.15s"></div>
        <div class="w-1.5 h-1.5 bg-primary-400 rounded-full animate-bounce" style="animation-delay: 0.3s"></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue'
import { useChat } from '../composables/useChat.js'

const { messages, loading } = useChat()
const scrollRef = ref(null)

watch([messages, loading], async () => {
  await nextTick()
  if (scrollRef.value) scrollRef.value.scrollTop = scrollRef.value.scrollHeight
}, { deep: true })
</script>
