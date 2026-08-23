import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { resolve } from 'node:path'

// Server bundle used only by prerender.mjs at build time. It is never shipped
// to the browser, so it is kept out of static/ entirely.
export default defineConfig({
  plugins: [react()],
  root: resolve(import.meta.dirname, 'frontend'),
  build: {
    ssr: resolve(import.meta.dirname, 'frontend/src/entry-server.jsx'),
    outDir: resolve(import.meta.dirname, '.ssr-build'),
    emptyOutDir: true,
    rollupOptions: {
      output: { entryFileNames: 'entry-server.js' }
    }
  }
})
