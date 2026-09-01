import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  base: './',
  plugins: [react()],
  server: {
    proxy: {
      '/admin': 'http://localhost:8000',
      '/dashboard': 'http://localhost:8000',
      '/expenses': 'http://localhost:8000',
      '/reports': 'http://localhost:8000',
      '/wallet': 'http://localhost:8000',
      '/sub-vendor': 'http://localhost:8000',
    },
  },
  build: { outDir: 'dist' },
})
