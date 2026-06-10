import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  base: '/market-watch/',
  server: {
    port: 5173,
    proxy: {
      '/market-watch/api': { target: 'http://127.0.0.1:8000', changeOrigin: true, rewrite: p => p.replace(/^\/market-watch\/api/, '/api') },
      '/api': { target: 'http://127.0.0.1:8000', changeOrigin: true },
    },
    fs: { strict: false }
  },
  build: { outDir: 'dist' }
})
