import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { resolve } from 'node:path'

export default defineConfig({
  plugins: [react()],
  base: '/static/react/',
  root: resolve(import.meta.dirname, 'frontend'),
  build: {
    outDir: resolve(import.meta.dirname, 'static/react'),
    emptyOutDir: true,
    rollupOptions: {
      input: resolve(import.meta.dirname, 'frontend/index.html'),
      output: {
        entryFileNames: 'app.js',
        assetFileNames: 'app.[ext]',
        // Flask versions the entry URL with ?v=. Shared modules must live in
        // their own hashed chunks so lazy routes never import that entry again.
        manualChunks(id) {
          if (id.includes('vite/preload-helper')) return 'app-runtime'
          if (id.includes('/node_modules/') && !id.includes('/three/') && !id.includes('/canvas-confetti/')) return 'vendor'
          if (id.endsWith('/app-runtime.jsx') || id.endsWith('/boot.js')) return 'app-runtime'
        },
      }
    }
  }
})
