<template>
  <div v-if="checking" class="h-screen flex items-center justify-center bg-surface-50 dark:bg-surface-dark-50">
    <div class="flex items-center gap-2 text-zinc-400 dark:text-zinc-500 text-sm">
      <svg class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
      </svg>
      检测部署模式...
    </div>
  </div>
  <LoginPage v-else-if="!isAuthenticated" @login-success="onLogin" />
  <MainLayout v-else @logout="handleLogout" />
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useAuth, detectDeployMode } from './composables/useAuth.js'
import LoginPage from './components/LoginPage.vue'
import MainLayout from './components/MainLayout.vue'

const { isAuthenticated, logout } = useAuth()
const checking = ref(true)

onMounted(async () => {
  await detectDeployMode()
  checking.value = false
})

function onLogin() { window.location.reload() }
function handleLogout() { logout(); window.location.reload() }
</script>
