import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: "0.0.0.0", // required to be reachable inside Docker
    port: 3000,
    proxy: {
      // Proxy /api calls to Django so no CORS issues in dev
      "/api": {
        target: "http://backend:8000",
        changeOrigin: true,
      },
    },
    watch: { usePolling: true },
  },
  preview: {
    host: "0.0.0.0",
    port: 3000,
  },
});
