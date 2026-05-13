import { ref, watchEffect, onMounted } from 'vue'

const STORAGE_KEY = 'theme_preference'
const theme = ref('light')

function applyTheme(value) {
  const isDark = value === 'dark' || (value === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches)
  document.documentElement.classList.toggle('dark', isDark)
  theme.value = value
}

export function useTheme() {
  function setTheme(value) {
    localStorage.setItem(STORAGE_KEY, value)
    applyTheme(value)
  }

  function toggleTheme() {
    const current = theme.value
    setTheme(current === 'dark' ? 'light' : 'dark')
  }

  function initTheme() {
    const stored = localStorage.getItem(STORAGE_KEY) || 'light'
    applyTheme(stored)

    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
      if (localStorage.getItem(STORAGE_KEY) === 'system') {
        applyTheme('system')
      }
    })
  }

  return {
    theme,
    setTheme,
    toggleTheme,
    initTheme,
    isDark: () => theme.value === 'dark' || (theme.value === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches)
  }
}
