<template>
  <LoginPage v-if="!isAuthenticated" @login-success="onLogin" />
  <MainLayout v-else @logout="handleLogout" />
</template>

<script setup>
import { onMounted } from 'vue'
import { useAuth } from './composables/useAuth.js'
import LoginPage from './components/LoginPage.vue'
import MainLayout from './components/MainLayout.vue'

const { isAuthenticated, logout } = useAuth()

function onLogin() {
  window.location.reload()
}

function handleLogout() {
  logout()
  window.location.reload()
}
</script>
