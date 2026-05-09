/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,js}'],
  theme: {
    extend: {
      colors: {
        warm: {
          50: '#f8f4ee', 100: '#ece3d8', 200: '#d4c4b0',
          300: '#b8a48c', 400: '#9c8e7c', 500: '#7a6b58',
          600: '#5a4a3a', 650: '#4d3f32', 700: '#362e25',
          750: '#2d2620', 800: '#241e19', 850: '#1c1713',
          900: '#161210', 950: '#0d0b09',
        },
        copper: {
          50: '#fdf2ed', 100: '#f9e0d4', 200: '#f2c0aa',
          300: '#e69a7a', 400: '#d4835a', 500: '#c46a3e',
          600: '#a85532',
        },
        gold: {
          50: '#faf5ec', 100: '#f0e4cc', 200: '#e0cba3',
          300: '#c4a87a', 400: '#b8946a', 500: '#a07a52',
          600: '#8a6a42',
        },
        moss: {
          50: '#f2f7ed', 100: '#e0ebd3', 200: '#c0d9a8',
          300: '#97be75', 400: '#75a34e', 500: '#5a8338',
          600: '#45672d',
        },
      },
      fontFamily: {
        display: ['Playfair Display', 'serif'],
        body: ['DM Sans', 'sans-serif'],
      },
    },
  },
}
