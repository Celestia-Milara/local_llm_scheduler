import { createApp } from 'vue'
import App from './App.vue'
import './style.css'
import { useTheme } from './composables/useTheme.js'

createApp(App).mount('#app')

// 初始化主题
const { initTheme } = useTheme()
initTheme()
