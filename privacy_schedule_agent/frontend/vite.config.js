import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    proxy: {
      '/schedules': 'http://localhost:8000',
      '/chat': 'http://localhost:8000'
    }
  }
})
