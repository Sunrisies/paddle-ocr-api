import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  base: '',
  server: {
    port: 5173,
    proxy: {
      '/ocr': { target: 'http://localhost:8100', changeOrigin: true },
      '/health': { target: 'http://localhost:8100', changeOrigin: true },
      '/assets': { target: 'http://localhost:8100', changeOrigin: true },
    },
  },
  build: {
    outDir: '../static',
    emptyOutDir: true,
  },
})
