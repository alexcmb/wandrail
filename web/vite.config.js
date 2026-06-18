import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    // Proxy /api vers le backend FastAPI en dev (evite les soucis CORS).
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
})
