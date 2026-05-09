<template>
  <div ref="scrollRef" class="flex-1 overflow-y-auto px-4 py-4 space-y-3">
    <div v-for="(msg, i) in messages" :key="i"
      :class="['flex', msg.role === 'user' ? 'justify-end' : 'justify-start']">
      <div :class="['max-w-[85%] p-3 text-sm leading-relaxed',
        msg.role === 'user'
          ? 'bg-copper-500 text-white rounded-2xl rounded-tr-md'
          : 'bg-warm-100 text-warm-700 rounded-2xl rounded-tl-md border border-warm-200/50']">
        <div class="pre-wrap">{{ msg.content }}</div>
      </div>
    </div>
    <div v-if="loading" class="flex justify-start">
      <div class="bg-warm-100 border border-warm-200/50 px-4 py-3 rounded-2xl rounded-tl-md flex items-center gap-1.5">
        <div class="w-1.5 h-1.5 bg-copper-400 rounded-full animate-bounce" style="animation-delay: 0s"></div>
        <div class="w-1.5 h-1.5 bg-copper-400 rounded-full animate-bounce" style="animation-delay: 0.15s"></div>
        <div class="w-1.5 h-1.5 bg-copper-400 rounded-full animate-bounce" style="animation-delay: 0.3s"></div>
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
