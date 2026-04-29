(function (root, factory) {
  if (typeof module === 'object' && module.exports) {
    module.exports = factory();
  } else {
    root.CalendarUtils = factory();
  }
})(this, function () {
  const pad2 = (n) => String(n).padStart(2, '0');

  const toDateKey = (date) => {
    const yyyy = date.getFullYear();
    const mm = pad2(date.getMonth() + 1);
    const dd = pad2(date.getDate());
    return `${yyyy}-${mm}-${dd}`;
  };

  const getMonthMatrix = (year, monthIndex) => {
    const first = new Date(year, monthIndex, 1);
    const start = new Date(first);
    start.setDate(1 - first.getDay());

    const weeks = [];
    let cursor = new Date(start);
    for (let w = 0; w < 6; w += 1) {
      const week = [];
      for (let d = 0; d < 7; d += 1) {
        const date = new Date(cursor);
        week.push({
          date,
          dateKey: toDateKey(date),
          inMonth: date.getMonth() === monthIndex
        });
        cursor.setDate(cursor.getDate() + 1);
      }
      weeks.push(week);
    }
    return weeks;
  };

  const groupEventsByDate = (events) => {
    return events.reduce((acc, event) => {
      const dateKey = event.start_time.slice(0, 10);
      acc[dateKey] = acc[dateKey] || [];
      acc[dateKey].push(event);
      return acc;
    }, {});
  };

  const getMonthRange = (year, monthIndex) => {
    const start = new Date(year, monthIndex, 1);
    const end = new Date(year, monthIndex + 1, 0);
    const startStr = `${start.getFullYear()}-${pad2(start.getMonth() + 1)}-01 00:00:00`;
    const endStr = `${end.getFullYear()}-${pad2(end.getMonth() + 1)}-${pad2(end.getDate())} 23:59:59`;
    return { start: startStr, end: endStr };
  };

  return { toDateKey, getMonthMatrix, groupEventsByDate, getMonthRange };
});
