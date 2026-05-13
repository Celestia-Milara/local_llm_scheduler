<template>
  <div class="h-screen flex items-center justify-center bg-surface-50 dark:bg-surface-dark-50 overflow-hidden relative">
    <!-- Ambient glow -->
    <div class="absolute top-0 left-1/2 -translate-x-1/2 w-[600px] h-[400px] bg-primary-500/8 rounded-full blur-3xl"></div>

    <div class="w-96 relative z-10">
      <!-- Brand -->
      <div class="text-center mb-10">
        <div class="w-16 h-16 mx-auto mb-4 rounded-full bg-primary-400/10 border border-primary-400/20 flex items-center justify-center">
          <svg class="w-7 h-7 text-primary-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
          </svg>
        </div>
        <h1 class="font-display text-3xl text-zinc-800 dark:text-zinc-200">隐私日程助理</h1>
        <p class="text-zinc-500 dark:text-zinc-400 text-sm mt-1 tracking-wide">Privacy-First Schedule Agent</p>
      </div>

      <!-- Card -->
      <div class="bg-white dark:bg-zinc-900 backdrop-blur-sm border border-zinc-200/60 dark:border-zinc-700/60 rounded-2xl p-8 shadow-xl shadow-black/5">
        <div class="space-y-4">
          <div>
            <input v-model="username" placeholder="用户名"
              class="w-full bg-surface-50 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 rounded-xl px-4 py-2.5 text-sm text-zinc-700 dark:text-zinc-200 placeholder-zinc-400 dark:placeholder-zinc-500 focus:outline-none focus:ring-1 focus:ring-primary-400/50 focus:border-primary-400/50 transition-all">
          </div>
          <div>
            <input v-model="password" type="password" placeholder="密码"
              class="w-full bg-surface-50 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 rounded-xl px-4 py-2.5 text-sm text-zinc-700 dark:text-zinc-200 placeholder-zinc-400 dark:placeholder-zinc-500 focus:outline-none focus:ring-1 focus:ring-primary-400/50 focus:border-primary-400/50 transition-all"
              @keyup.enter="handleLogin">
          </div>
          <p v-if="error" class="text-danger-500 text-sm text-center">{{ error }}</p>
          <button @click="handleLogin" :disabled="loading"
            class="w-full bg-primary-500 hover:bg-primary-400 active:bg-primary-600 disabled:opacity-50 rounded-xl py-2.5 text-sm font-medium text-white transition-all shadow-lg shadow-primary-500/20">
            {{ loading ? '处理中...' : isRegisterMode ? '注册并登录' : '登录' }}
          </button>
          <p class="text-center text-xs text-zinc-400 dark:text-zinc-500">
            <button @click="toggleMode" class="hover:text-primary-500 transition-colors">
              {{ isRegisterMode ? '已有账号？去登录' : '没有账号？去注册' }}
            </button>
          </p>
        </div>
      </div>

      <!-- Mode indicator & privacy -->
      <div class="flex items-center justify-center gap-1.5 mt-6">
        <svg class="w-3 h-3 text-moss-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
          <path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
        </svg>
        <p class="text-zinc-500 dark:text-zinc-400 text-xs tracking-wide">
          <span class="text-moss-500">/</span>
          <template v-if="isCloud">连接到云端服务 · 数据加密传输</template>
          <template v-else>数据仅存于本地设备，不会上传至云端</template>
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useAuth } from '../composables/useAuth.js'

const { login, register, isCloud } = useAuth()
const emit = defineEmits(['login-success'])

const username = ref('')
const password = ref('')
const error = ref('')
const isRegisterMode = ref(false)
const loading = ref(false)

async function handleLogin() {
  error.value = ''
  loading.value = true
  try {
    let ok
    if (isRegisterMode.value) {
      ok = await register(username.value, password.value)
      if (!ok) error.value = '注册失败，用户名可能已存在'
    } else {
      ok = await login(username.value, password.value)
      if (!ok) error.value = '用户名或密码错误'
    }
    if (ok) emit('login-success')
  } catch {
    error.value = '操作失败，请重试'
  } finally {
    loading.value = false
  }
}

function toggleMode() {
  isRegisterMode.value = !isRegisterMode.value
  error.value = ''
}
</script>
