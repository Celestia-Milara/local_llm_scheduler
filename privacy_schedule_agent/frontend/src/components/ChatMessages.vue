<template>
  <div ref="scrollRef" class="flex-1 overflow-y-auto p-3 space-y-3">
    <div v-for="(msg, i) in messages" :key="i"
      :class="['flex', msg.role === 'user' ? 'justify-end' : 'justify-start']">
      <div :class="['max-w-[85%] p-2.5 rounded-xl text-sm',
        msg.role === 'user' ? 'bg-indigo-600 text-white rounded-tr-none' : 'bg-slate-800 text-slate-200 rounded-tl-none border border-slate-700']">
        <div class="pre-wrap">{{ msg.content }}</div>
      </div>
    </div>
    <div v-if="loading" class="flex justify-start">
      <div class="bg-slate-800 p-3 rounded-xl flex items-center gap-1.5">
        <div class="w-1.5 h-1.5 bg-indigo-500 rounded-full animate-bounce"></div>
        <div class="w-1.5 h-1.5 bg-indigo-500 rounded-full animate-bounce [animation-delay:-.3s]"></div>
        <div class="w-1.5 h-1.5 bg-indigo-500 rounded-full animate-bounce [animation-delay:-.5s]"></div>
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
