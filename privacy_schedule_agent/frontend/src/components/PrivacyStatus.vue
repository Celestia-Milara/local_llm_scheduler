<template>
  <div class="relative" ref="containerRef">
    <button @click="expanded = !expanded"
      class="flex items-center gap-2 px-3 py-2 rounded-xl bg-moss-50 dark:bg-moss-500/10 hover:bg-moss-100/80 dark:hover:bg-moss-500/20 transition-colors group w-full text-left">
      <span class="w-2 h-2 rounded-full block animate-pulse"
        :class="statusColor"></span>
      <span class="text-[11px] text-moss-700 dark:text-moss-400 font-medium group-hover:text-moss-800 dark:group-hover:text-moss-300 transition-colors">
        {{ statusLabel }}
      </span>
    </button>

    <!-- Expanded detail -->
    <Transition name="fade">
      <div v-if="expanded"
        class="absolute bottom-full left-0 mb-2 bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-700 rounded-xl p-3 shadow-xl shadow-black/10 w-48 z-50">
        <div class="space-y-2 text-[10px]">
          <div class="flex items-center justify-between">
            <span class="text-zinc-400 dark:text-zinc-500">模型</span>
            <span class="text-zinc-700 dark:text-zinc-300 font-medium">{{ modelName }}</span>
          </div>
          <div class="flex items-center justify-between">
            <span class="text-zinc-400 dark:text-zinc-500">状态</span>
            <span class="text-moss-600 dark:text-moss-400 flex items-center gap-1">
              <span class="w-1.5 h-1.5 rounded-full bg-moss-500"></span>
              本地运行中
            </span>
          </div>
          <div class="text-zinc-400 dark:text-zinc-500 italic pt-1 border-t border-zinc-200/50 dark:border-zinc-700/50">
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
  props.connected ? 'bg-moss-500 shadow-sm shadow-moss-500/30' : 'bg-zinc-400/60'
)

const statusLabel = computed(() =>
  props.connected ? '本地模型就绪' : '模型连接中...'
)
</script>
