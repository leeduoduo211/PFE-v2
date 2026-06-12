import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// API requests go to /api/* and are proxied to the FastAPI service
// (python3 -m uvicorn api.app:app) so the dev server avoids CORS entirely.
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
})
