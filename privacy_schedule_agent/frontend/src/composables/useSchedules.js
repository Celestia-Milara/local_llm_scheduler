import { ref, readonly } from 'vue'
import axios from 'axios'
import { getMonthRange, getMonthMatrix, toDateKey } from '../utils/calendar.js'

const monthEvents = ref([])
const selectedDate = ref(toDateKey(new Date()))
const currentMonth = ref(new Date())
const monthMatrix = ref([])

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
    return monthEvents.value.some(e => e.start_time.startsWith(dateKey))
  }

  async function fetchMonth(userId = 1) {
    refreshMonthMatrix()
    const range = getMonthRange(
      currentMonth.value.getFullYear(),
      currentMonth.value.getMonth()
    )
    try {
      const res = await axios.get('/schedules', {
        params: { start: range.start, end: range.end, user_id: userId }
      })
      monthEvents.value = res.data
    } catch {
      monthEvents.value = []
    }
  }

  async function createSchedule(title, startTime, endTime, userId = 1) {
    try {
      // 通过聊天接口让 LLM 处理新建
      await axios.post('/chat', {
        message: `添加日程：标题="${title}"，开始时间=${startTime}，结束时间=${endTime}`,
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

  return {
    monthEvents: readonly(monthEvents),
    selectedDate,
    currentMonth,
    monthMatrix: readonly(monthMatrix),
    getMonthEvents,
    hasEvents,
    fetchMonth,
    createSchedule,
    updateSchedule,
    deleteSchedule
  }
}
