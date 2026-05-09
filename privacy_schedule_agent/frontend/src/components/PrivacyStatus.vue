<template>
  <div class="relative" ref="containerRef">
    <button @click="expanded = !expanded"
      class="flex items-center gap-2 px-3 py-1.5 rounded-lg hover:bg-warm-100 transition-colors group w-full text-left">
      <span class="w-1.5 h-1.5 rounded-full block"
        :class="statusColor"></span>
      <span class="text-[10px] text-warm-500 group-hover:text-warm-700 transition-colors privacy-badge">
        {{ statusLabel }}
      </span>
    </button>

    <!-- Expanded detail -->
    <Transition name="fade">
      <div v-if="expanded"
        class="absolute bottom-full left-0 mb-2 bg-white border border-warm-200 rounded-xl p-3 shadow-xl shadow-black/10 w-48 z-50">
        <div class="space-y-2 text-[10px]">
          <div class="flex items-center justify-between">
            <span class="text-warm-400">模型</span>
            <span class="text-warm-700 font-medium">{{ modelName }}</span>
          </div>
          <div class="flex items-center justify-between">
            <span class="text-warm-400">状态</span>
            <span class="text-moss-600 flex items-center gap-1">
              <span class="w-1.5 h-1.5 rounded-full bg-moss-500"></span>
              本地运行中
            </span>
          </div>
          <div class="text-warm-400 italic pt-1 border-t border-warm-200/50">
            数据仅存于本地设备
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'

const expanded = ref(false)
const containerRef = ref(null)

function onDocumentClick(e) {
  if (expanded.value && containerRef.value && !containerRef.value.contains(e.target)) {
    expanded.value = false
  }
}

onMounted(() => document.addEventListener('click', onDocumentClick))
onUnmounted(() => document.removeEventListener('click', onDocumentClick))

const props = defineProps({
  connected: { type: Boolean, default: true },
  modelName: { type: String, default: 'Qwen2.5 7B' }
})

const statusColor = computed(() =>
  props.connected ? 'bg-moss-500 shadow-sm shadow-moss-500/30' : 'bg-copper-500/60'
)

const statusLabel = computed(() =>
  props.connected ? '本地 LLM 已连接' : 'LLM 连接中...'
)
</script>
