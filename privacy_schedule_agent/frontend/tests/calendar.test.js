import { describe, it } from 'node:test'
import assert from 'node:assert/strict'
import { getMonthMatrix, groupEventsByDate, getMonthRange, toDateKey } from '../src/utils/calendar.js'

describe('calendar utils', () => {
  it('getMonthMatrix returns 6x7 grid', () => {
    const matrix = getMonthMatrix(2026, 3)
    assert.equal(matrix.length, 6)
    matrix.forEach(week => assert.equal(week.length, 7))
    const april1 = matrix.flat().find(d => d.dateKey === '2026-04-01')
    assert.ok(april1)
    assert.equal(april1.inMonth, true)
  })

  it('groupEventsByDate groups by dateKey', () => {
    const events = [
      { id: 1, start_time: '2026-04-10 09:00:00' },
      { id: 2, start_time: '2026-04-10 11:00:00' },
      { id: 3, start_time: '2026-04-11 10:00:00' }
    ]
    const grouped = groupEventsByDate(events)
    assert.equal(grouped['2026-04-10'].length, 2)
    assert.equal(grouped['2026-04-11'].length, 1)
  })

  it('getMonthRange returns correct strings', () => {
    const range = getMonthRange(2026, 3)
    assert.equal(range.start, '2026-04-01 00:00:00')
    assert.equal(range.end, '2026-04-30 23:59:59')
  })
})
