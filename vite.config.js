import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { resolve } from 'node:path'

export default defineConfig({
  plugins: [react()],
  root: resolve(import.meta.dirname, 'frontend'),
  build: {
    outDir: resolve(import.meta.dirname, 'static/react'),
    emptyOutDir: true,
    rollupOptions: {
      input: resolve(import.meta.dirname, 'frontend/index.html'),
      output: {
        entryFileNames: 'app.js',
        assetFileNames: 'app.[ext]'
      }
    }
  }
})
