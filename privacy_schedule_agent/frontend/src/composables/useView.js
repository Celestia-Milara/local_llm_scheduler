import { ref } from 'vue'

const currentView = ref('month') // 'month' | 'week' | 'day'

export function useView() {
  function setView(view) {
    currentView.value = view
  }

  return { currentView, setView }
}
