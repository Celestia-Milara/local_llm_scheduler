import { ref, computed } from 'vue'
import axios from 'axios'

const TOKEN_KEY = 'schedule_auth'
const token = ref(localStorage.getItem(TOKEN_KEY))
const userId = ref(token.value ? 1 : null)
const username = ref('')
const isCloud = ref(false)

// 检测部署模式
export async function detectDeployMode() {
  try {
    const res = await axios.get('/api/auth/me', {
      headers: { Authorization: `Bearer ${token.value}` }
    })
    if (res.data && res.data.id) {
      isCloud.value = true
      userId.value = res.data.id
      username.value = res.data.username
      return 'cloud'
    }
  } catch {
    // local 模式
  }
  isCloud.value = false
  userId.value = 1
  return 'local'
}

export function useAuth() {
  const isAuthenticated = computed(() => {
    if (!isCloud.value) return true
    return !!token.value
  })

  async function login(usernameVal, passwordVal) {
    try {
      const res = await axios.post('/api/auth/login', {
        username: usernameVal,
        password: passwordVal,
      })
      const data = res.data
 localStorage.setItem(TOKEN_KEY, data.token)
      token.value = data.token
      userId.value = data.user.id
      username.value = data.user.username
      return true
    } catch {
      return false
    }
  }

  async function register(usernameVal, passwordVal) {
    try {
      const res = await axios.post('/api/auth/register', {
        username: usernameVal,
        password: passwordVal,
      })
      const data = res.data
      localStorage.setItem(TOKEN_KEY, data.token)
      token.value = data.token
      userId.value = data.user.id
      username.value = data.user.username
      return true
    } catch {
      return false
    }
  }

  function logout() {
    localStorage.removeItem(TOKEN_KEY)
    token.value = null
    userId.value = null
    username.value = ''
  }

  return { isAuthenticated, userId, username, login, register, logout, isCloud }
}
