const test = require('node:test');
const assert = require('node:assert/strict');

const utils = require('../assets/calendar_utils.js');

test('getMonthMatrix returns 6x7 grid and flags inMonth', () => {
  const matrix = utils.getMonthMatrix(2026, 3); // 2026-04
  assert.equal(matrix.length, 6);
  matrix.forEach((week) => assert.equal(week.length, 7));

  const april1 = matrix.flat().find((d) => d.dateKey === '2026-04-01');
  assert.ok(april1);
  assert.equal(april1.inMonth, true);
});

test('groupEventsByDate groups events using dateKey', () => {
  const events = [
    { id: 1, start_time: '2026-04-10 09:00:00' },
    { id: 2, start_time: '2026-04-10 11:00:00' },
    { id: 3, start_time: '2026-04-11 10:00:00' }
  ];
  const grouped = utils.groupEventsByDate(events);
  assert.equal(grouped['2026-04-10'].length, 2);
  assert.equal(grouped['2026-04-11'].length, 1);
});

test('getMonthRange returns correct start/end strings', () => {
  const range = utils.getMonthRange(2026, 3);
  assert.equal(range.start, '2026-04-01 00:00:00');
  assert.equal(range.end, '2026-04-30 23:59:59');
});
