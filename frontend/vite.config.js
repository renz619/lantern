import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  // Let the dev server be opened through a tunnel (the address changes each run).
  server: { allowedHosts: true },
})
