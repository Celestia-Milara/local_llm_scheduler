import { ref } from 'vue'

const messages = ref([])
const loading = ref(false)
const aiPanelVisible = ref(false)

/** 解析 SSE 字节流，返回解析出的事件列表和剩余 buffer */
function parseSSEBuffer(buffer, bytes) {
  const text = new TextDecoder().decode(bytes)
  buffer += text
  const events = []
  const parts = buffer.split('\n\n')
  // 最后一个片段可能不完整，留在 buffer 中
  buffer = parts.pop() || ''

  for (const part of parts) {
    if (!part.trim()) continue
    const lines = part.split('\n')
    let eventType = ''
    let dataStr = ''
    for (const line of lines) {
      if (line.startsWith('event: ')) {
        eventType = line.slice(7)
      } else if (line.startsWith('data: ')) {
        dataStr = line.slice(6)
      }
    }
    if (eventType && dataStr) {
      try {
        events.push({ type: eventType, data: JSON.parse(dataStr) })
      } catch { /* skip malformed */ }
    }
  }
  return { events, buffer }
}

export function useChat() {
  async function sendMessage(text, userId = 1) {
    if (!text.trim() || loading.value) return

    messages.value.push({ role: 'user', content: text })

    // 创建 assistant 消息占位
    const assistantMsg = { role: 'assistant', content: '', steps: [], streaming: true }
    messages.value.push(assistantMsg)
    loading.value = true

    try {
      const response = await fetch('/chat/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text, session_id: `user_${userId}` })
      })

      if (!response.ok || !response.body) {
        throw new Error(`HTTP ${response.status}`)
      }

      const reader = response.body.getReader()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const { events, buffer: remaining } = parseSSEBuffer(buffer, value)
        buffer = remaining

        for (const evt of events) {
          if (evt.type === 'step') {
            assistantMsg.steps.push(evt.data)
            // 强制 Vue 检测 steps 变更
            assistantMsg.steps = [...assistantMsg.steps]
          } else if (evt.type === 'token') {
            assistantMsg.content += evt.data.text || ''
            // 触发响应式更新
            assistantMsg.content = assistantMsg.content
          } else if (evt.type === 'done') {
            assistantMsg.streaming = false
          }
        }
      }
    } catch {
      // 如果已经有部分内容，保留；否则显示错误信息
      if (!assistantMsg.content) {
        assistantMsg.content = '抱歉，系统处理出错，请重试。'
      }
      assistantMsg.streaming = false
    } finally {
      loading.value = false
    }
  }

  function togglePanel() {
    aiPanelVisible.value = !aiPanelVisible.value
  }

  function clearMessages() {
    messages.value.splice(0) // preserve ref, clear in-place
  }

  return { messages, loading, aiPanelVisible, sendMessage, togglePanel, clearMessages }
}
