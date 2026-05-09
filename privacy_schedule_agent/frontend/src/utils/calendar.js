export const pad2 = (n) => String(n).padStart(2, '0')

export const toDateKey = (date) => {
  const yyyy = date.getFullYear()
  const mm = pad2(date.getMonth() + 1)
  const dd = pad2(date.getDate())
  return `${yyyy}-${mm}-${dd}`
}

export const getMonthMatrix = (year, monthIndex) => {
  const first = new Date(year, monthIndex, 1)
  const start = new Date(first)
  // Monday as first day of week
  start.setDate(1 - ((first.getDay() + 6) % 7))

  const weeks = []
  let cursor = new Date(start)
  for (let w = 0; w < 6; w += 1) {
    const week = []
    for (let d = 0; d < 7; d += 1) {
      const date = new Date(cursor)
      week.push({
        date,
        dateKey: toDateKey(date),
        inMonth: date.getMonth() === monthIndex
      })
      cursor.setDate(cursor.getDate() + 1)
    }
    weeks.push(week)
  }
  return weeks
}

export const groupEventsByDate = (events) => {
  return events.reduce((acc, event) => {
    const dateKey = event.start_time.slice(0, 10)
    acc[dateKey] = acc[dateKey] || []
    acc[dateKey].push(event)
    return acc
  }, {})
}

export const getMonthRange = (year, monthIndex) => {
  const start = new Date(year, monthIndex, 1)
  const end = new Date(year, monthIndex + 1, 0)
  const startStr = `${start.getFullYear()}-${pad2(start.getMonth() + 1)}-01 00:00:00`
  const endStr = `${end.getFullYear()}-${pad2(end.getMonth() + 1)}-${pad2(end.getDate())} 23:59:59`
  return { start: startStr, end: endStr }
}

/** Get array of 7 Date objects for the week containing the given date (Monday start) */
export const getWeekDays = (date) => {
  const d = new Date(date)
  const day = d.getDay() // 0=Sun
  const diff = d.getDate() - day + (day === 0 ? -6 : 1) // Monday
  d.setDate(diff)
  d.setHours(0, 0, 0, 0)
  const days = []
  for (let i = 0; i < 7; i++) {
    const d2 = new Date(d)
    d2.setDate(d.getDate() + i)
    days.push(d2)
  }
  return days
}

/** Parse a datetime string "YYYY-MM-DD HH:MM:SS" to minutes from midnight */
export const parseTime = (dt) => {
  const t = (dt || ' ').split(' ')[1] || '00:00:00'
  const [h, m] = t.split(':').map(Number)
  return h * 60 + m
}

/** Calculate event top position in pixels (hourHeight px per hour) */
export const eventTop = (startTime, hourHeight = 60) => {
  return (parseTime(startTime) / 60) * hourHeight
}

/** Calculate event height in pixels */
export const eventHeight = (startTime, endTime, hourHeight = 60) => {
  return ((parseTime(endTime) - parseTime(startTime)) / 60) * hourHeight
}

/** Format event time for display */
export const formatEventTime = (event) => {
  const s = (event.start_time || '').split(' ')[1]?.slice(0, 5) || ''
  const e = (event.end_time || '').split(' ')[1]?.slice(0, 5) || ''
  return `${s} - ${e}`
}

/** Format a week range label, e.g. "5月4日 - 5月10日" */
export const formatWeekRange = (weekDays) => {
  if (!weekDays || weekDays.length < 7) return ''
  const resolve = (d) => (d instanceof Date ? d : d.date)
  const first = resolve(weekDays[0])
  const last = resolve(weekDays[6])
  const fm = (d) => `${d.getMonth() + 1}月${d.getDate()}日`
  if (first.getMonth() === last.getMonth()) {
    return `${fm(first)} - ${last.getDate()}日`
  }
  return `${fm(first)} - ${fm(last)}`
}

/** Expand a recurring event into instances within a date range */
export function expandRecurrence(event, rangeStart, rangeEnd) {
  if (!event.recurrence_rule) return [event]

  const instances = []
  const rule = event.recurrence_rule
  const rangeStartDate = new Date(rangeStart.split(' ')[0] + 'T00:00:00')
  const rangeEndDate = new Date(rangeEnd.split(' ')[0] + 'T00:00:00')
  // Limit expansion to avoid infinite loops
  const absEnd = event.recurrence_end ? new Date(event.recurrence_end) : new Date('2099-12-31')
  const maxEnd = rangeEndDate < absEnd ? rangeEndDate : absEnd

  const eventStart = new Date(event.start_time.replace(' ', 'T'))
  const eventEnd = new Date(event.end_time.replace(' ', 'T'))
  const duration = eventEnd.getTime() - eventStart.getTime()

  // Skip-ahead: jump cursor to roughly rangeStart minus one period
  let cursor = new Date(eventStart)
  if (cursor < rangeStartDate) {
    const diffMs = rangeStartDate.getTime() - cursor.getTime()
    const diffDays = Math.ceil(diffMs / 86400000)
    if (rule === 'daily') cursor.setDate(cursor.getDate() + diffDays)
    else if (rule === 'weekdays') cursor.setDate(cursor.getDate() + Math.round(diffDays * 5 / 7))
    else if (rule === 'weekly') cursor.setDate(cursor.getDate() + Math.floor(diffDays / 7) * 7)
    else if (rule === 'monthly') {
      const months = Math.max(0, (rangeStartDate.getFullYear() - cursor.getFullYear()) * 12 + rangeStartDate.getMonth() - cursor.getMonth() - 1)
      cursor.setMonth(cursor.getMonth() + months)
    }
  }

  let limit = 500 // safety cap

  while (cursor <= maxEnd && limit-- > 0) {
    const cStart = cursor.toISOString().replace('T', ' ').slice(0, 19)
    const cEnd = new Date(cursor.getTime() + duration).toISOString().replace('T', ' ').slice(0, 19)

    if (cStart >= rangeStart && cStart <= rangeEnd) {
      instances.push({ ...event, id: `${event.id}_${cStart.slice(0, 10)}`, start_time: cStart, end_time: cEnd, _recurring: true })
    }

    if (rule === 'daily') cursor.setDate(cursor.getDate() + 1)
    else if (rule === 'weekdays') {
      cursor.setDate(cursor.getDate() + 1)
      while (cursor.getDay() === 0 || cursor.getDay() === 6) cursor.setDate(cursor.getDate() + 1)
    } else if (rule === 'weekly') cursor.setDate(cursor.getDate() + 7)
    else if (rule === 'monthly') cursor.setMonth(cursor.getMonth() + 1)
    else break
  }

  return instances
}
