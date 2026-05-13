/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,js}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        surface: {
          50: '#fafaf9', 100: '#f5f5f4', 200: '#e7e5e4',
          dark: { 50: '#0a0a0a', 100: '#18181b', 200: '#27272a' },
        },
        primary: {
          50: '#eef2ff', 100: '#e0e7ff', 200: '#c7d2fe', 300: '#a5b4fc',
          400: '#818cf8', 500: '#6366f1', 600: '#4f46e5', 700: '#4338ca',
        },
        cat: {
          work: { 50: '#fffbeb', 400: '#fbbf24', 500: '#f59e0b', 600: '#d97706' },
          study: { 50: '#eff6ff', 400: '#60a5fa', 500: '#3b82f6', 600: '#2563eb' },
          life: { 50: '#fdf2f8', 400: '#f472b6', 500: '#ec4899', 600: '#db2777' },
          default: { 50: '#f0fdf4', 400: '#4ade80', 500: '#22c55e', 600: '#16a34a' },
        },
        moss: {
          50: '#f0fdf4', 100: '#dcfce7', 200: '#bbf7d0',
          300: '#86efac', 400: '#4ade80', 500: '#22c55e', 600: '#16a34a',
        },
        danger: { 50: '#fff1f2', 400: '#fb7185', 500: '#f43f5e', 600: '#e11d48' },
        warn: { 50: '#fffbeb', 400: '#fbbf24', 500: '#f59e0b', 600: '#d97706' },
      },
      fontFamily: {
        display: ['Playfair Display', 'serif'],
        body: ['DM Sans', 'sans-serif'],
      },
    },
  },
}
