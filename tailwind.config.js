/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        navy: '#1B3A6B',
        'navy-dark': '#0d2244',
        gold: '#C9A84C',
      }
    }
  },
  plugins: []
}
