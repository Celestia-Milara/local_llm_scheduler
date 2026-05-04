import { ref } from 'vue'
import axios from 'axios'

const messages = ref([])
const loading = ref(false)
const aiPanelVisible = ref(false)

export function useChat() {
  async function sendMessage(text, userId = 1) {
    if (!text.trim() || loading.value) return

    messages.value.push({ role: 'user', content: text })
    loading.value = true

    try {
      const res = await axios.post('/chat', {
        message: text,
        session_id: `user_${userId}`
      })
      messages.value.push({ role: 'assistant', content: res.data.response })
    } catch {
      messages.value.push({ role: 'assistant', content: '抱歉，系统处理出错，请重试。' })
    } finally {
      loading.value = false
    }
  }

  function togglePanel() {
    aiPanelVisible.value = !aiPanelVisible.value
  }

  function clearMessages() {
    messages.value = []
  }

  return { messages, loading, aiPanelVisible, sendMessage, togglePanel, clearMessages }
}
