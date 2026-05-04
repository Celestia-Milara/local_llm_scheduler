import { ref, computed } from 'vue'

const TOKEN_KEY = 'schedule_auth'
const token = ref(localStorage.getItem(TOKEN_KEY))
const userId = ref(token.value ? 1 : null)

export function useAuth() {
  const isAuthenticated = computed(() => !!token.value)

  function login(username, password) {
    if (username === 'root' && password === 'root') {
      localStorage.setItem(TOKEN_KEY, 'root')
      token.value = 'root'
      userId.value = 1
      return true
    }
    return false
  }

  function logout() {
    localStorage.removeItem(TOKEN_KEY)
    token.value = null
    userId.value = null
  }

  return { isAuthenticated, userId, login, logout }
}
