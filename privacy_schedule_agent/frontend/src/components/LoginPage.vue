<template>
  <div class="h-screen flex items-center justify-center bg-slate-950">
    <div class="w-80 bg-slate-900 border border-slate-700 rounded-2xl p-8 shadow-2xl">
      <h1 class="text-xl font-bold text-center mb-6">
        <span class="text-indigo-400">&#x1f6e1;&#xfe0f;</span> 隐私日程助理
      </h1>
      <div class="space-y-4">
        <input v-model="username" placeholder="用户名"
          class="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500">
        <input v-model="password" type="password" placeholder="密码"
          class="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          @keyup.enter="handleLogin">
        <p v-if="error" class="text-red-400 text-sm text-center">{{ error }}</p>
        <button @click="handleLogin"
          class="w-full bg-indigo-600 hover:bg-indigo-500 rounded-xl py-2 font-medium transition-all">
          登录
        </button>
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
