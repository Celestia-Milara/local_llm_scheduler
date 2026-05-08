<template>
  <div class="h-screen flex items-center justify-center bg-warm-50 overflow-hidden relative">
    <!-- Ambient glow -->
    <div class="absolute top-0 left-1/2 -translate-x-1/2 w-[600px] h-[400px] bg-copper-500/8 rounded-full blur-3xl"></div>

    <div class="w-96 relative z-10">
      <!-- Brand -->
      <div class="text-center mb-10">
        <div class="w-16 h-16 mx-auto mb-4 rounded-full bg-copper-400/10 border border-copper-400/20 flex items-center justify-center">
          <svg class="w-7 h-7 text-copper-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
          </svg>
        </div>
        <h1 class="font-display text-3xl text-warm-800">隐私日程助理</h1>
        <p class="text-warm-500 text-sm mt-1 tracking-wide">Privacy-First Schedule Agent</p>
      </div>

      <!-- Card -->
      <div class="bg-white backdrop-blur-sm border border-warm-200/60 rounded-2xl p-8 shadow-xl shadow-black/5">
        <div class="space-y-4">
          <div>
            <input v-model="username" placeholder="用户名"
              class="w-full bg-warm-50 border border-warm-200 rounded-xl px-4 py-2.5 text-sm text-warm-700 placeholder-warm-400 focus:outline-none focus:ring-1 focus:ring-copper-400/50 focus:border-copper-400/50 transition-all">
          </div>
          <div>
            <input v-model="password" type="password" placeholder="密码"
              class="w-full bg-warm-50 border border-warm-200 rounded-xl px-4 py-2.5 text-sm text-warm-700 placeholder-warm-400 focus:outline-none focus:ring-1 focus:ring-copper-400/50 focus:border-copper-400/50 transition-all"
              @keyup.enter="handleLogin">
          </div>
          <p v-if="error" class="text-copper-500 text-sm text-center">{{ error }}</p>
          <button @click="handleLogin"
            class="w-full bg-copper-500 hover:bg-copper-400 active:bg-copper-600 rounded-xl py-2.5 text-sm font-medium text-white transition-all shadow-lg shadow-copper-500/20">
            登录
          </button>
        </div>
      </div>

      <!-- Privacy assurance -->
      <div class="flex items-center justify-center gap-1.5 mt-6">
        <svg class="w-3 h-3 text-moss-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
          <path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
        </svg>
        <p class="text-warm-500 text-xs tracking-wide">
          <span class="text-moss-500">/</span> 数据仅存于本地设备，不会上传至云端
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useAuth } from '../composables/useAuth.js'

const { login } = useAuth()
const emit = defineEmits(['login-success'])

const username = ref('')
const password = ref('')
const error = ref('')

function handleLogin() {
  error.value = ''
  if (login(username.value, password.value)) {
    emit('login-success')
  } else {
    error.value = '用户名或密码错误'
  }
}
</script>
