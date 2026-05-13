/**
 * Shared event styling functions for calendar views
 */

export function eventClass(event) {
  if (event.status === 'conflicted') return 'bg-danger-400/10 text-danger-600 border-danger-400/40'
  const cat = event.category
  if (cat === '工作') return 'bg-cat-work-50 text-cat-work-600 border-cat-work-400/30'
  if (cat === '学习') return 'bg-cat-study-50 text-cat-study-600 border-cat-study-400/30'
  if (cat === '生活') return 'bg-cat-life-50 text-cat-life-600 border-cat-life-400/30'
  return 'bg-cat-default-50 text-cat-default-600 border-cat-default-400/30'
}

export function categoryClass(cat) {
  const map = {
    '工作': 'bg-cat-work-50 text-cat-work-500 border-cat-work-400/20',
    '学习': 'bg-cat-study-50 text-cat-study-500 border-cat-study-400/20',
    '生活': 'bg-cat-life-50 text-cat-life-500 border-cat-life-400/20'
  }
  return map[cat] || 'text-zinc-400 bg-cat-default-50 border-cat-default-400/20'
}
