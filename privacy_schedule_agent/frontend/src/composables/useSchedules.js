import { ref, readonly, computed } from 'vue'
import axios from 'axios'
import { getMonthRange, getMonthMatrix, toDateKey, expandRecurrence } from '../utils/calendar.js'

const monthEvents = ref([])
const selectedDate = ref(toDateKey(new Date()))
const currentMonth = ref(new Date())
const monthMatrix = ref([])
const loading = ref(false)
const activeCategory = ref('')
let initialized = false

export function useSchedules() {
  function refreshMonthMatrix() {
    monthMatrix.value = getMonthMatrix(
      currentMonth.value.getFullYear(),
      currentMonth.value.getMonth()
    ).flat()
  }

  function getMonthEvents(dateKey) {
    return monthEvents.value.filter(e => e.start_time.startsWith(dateKey))
  }

  function hasEvents(dateKey) {
    return monthEvents.value.some(e => {
      const start = e.start_time.slice(0, 10)
      const end = e.end_time.slice(0, 10)
      return dateKey >= start && dateKey <= end
    })
  }

  function getEventDotColor(dateKey) {
    const cats = new Set()
    for (const e of monthEvents.value) {
      const start = e.start_time.slice(0, 10)
      const end = e.end_time.slice(0, 10)
      if (dateKey >= start && dateKey <= end && e.category) {
        cats.add(e.category)
      }
    }
    if (cats.has('工作')) return 'bg-cat-work-400'
    if (cats.has('学习')) return 'bg-cat-study-400'
    if (cats.has('生活')) return 'bg-cat-life-400'
    if (cats.size > 0) return 'bg-primary-400'
    return ''
  }

  async function fetchMonth(userId = 1) {
    loading.value = true
    refreshMonthMatrix()
    const range = getMonthRange(
      currentMonth.value.getFullYear(),
      currentMonth.value.getMonth()
    )
    try {
      const res = await axios.get('/schedules', {
        params: { start: range.start, end: range.end, user_id: userId }
      })
      // Expand recurring events
      const expanded = []
      for (const event of res.data) {
        const instances = expandRecurrence(event, range.start, range.end)
        // Only add the original event if it's not recurring (or keep it for non-recurring)
        if (event.recurrence_rule) {
          // Skip non-first original (first instance overlaps with it)
          expanded.push(...instances)
        } else {
          expanded.push(event)
        }
      }
      monthEvents.value = expanded
    } catch {
      monthEvents.value = []
    } finally {
      loading.value = false
    }
  }

  async function createSchedule(title, startTime, endTime, location = '', userId = 1) {
    try {
      // 通过聊天接口让 LLM 处理新建
      let msg = `添加日程：标题="${title}"，开始时间=${startTime}，结束时间=${endTime}`
      if (location) msg += `，地点=${location}`
      await axios.post('/chat', {
        message: msg,
        session_id: `user_${userId}`
      })
    } catch (e) {
      console.warn('createSchedule failed:', e)
      throw e
    } finally {
      await fetchMonth(userId)
    }
  }

  async function updateSchedule(id, data, userId = 1) {
    try {
      await axios.put(`/schedules/${id}`, data)
    } catch (e) {
      console.warn('updateSchedule failed:', e)
      throw e
    } finally {
      await fetchMonth(userId)
    }
  }

  async function deleteSchedule(id, userId = 1) {
    try {
      await axios.delete(`/schedules/${id}`)
    } catch (e) {
      console.warn('deleteSchedule failed:', e)
      throw e
    } finally {
      await fetchMonth(userId)
    }
  }

  if (!initialized) {
    initialized = true
    fetchMonth()
  }

  const filteredEvents = computed(() => {
    if (!activeCategory.value) return monthEvents.value
    return monthEvents.value.filter(e => e.category === activeCategory.value)
  })

  const categoryCounts = computed(() => {
    const counts = { '': monthEvents.value.length }
    for (const e of monthEvents.value) {
      const cat = e.category || ''
      counts[cat] = (counts[cat] || 0) + 1
    }
    return counts
  })

  return {
    monthEvents: readonly(monthEvents),
    filteredEvents,
    activeCategory,
    categoryCounts,
    selectedDate,
    currentMonth,
    monthMatrix: readonly(monthMatrix),
    getMonthEvents,
    hasEvents,
    getEventDotColor,
    loading,
    fetchMonth,
    createSchedule,
    updateSchedule,
    deleteSchedule
  }
}
