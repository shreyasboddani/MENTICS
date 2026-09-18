import React from 'react'
import { createRoot, hydrateRoot } from 'react-dom/client'
import { App, CsrfBootstrap } from './App'

const container = document.getElementById('root')
const tree = (
  <React.StrictMode>
    <CsrfBootstrap />
    <App />
  </React.StrictMode>
)

// Only public pages are prerendered. Explicitly selecting those pages avoids
// accidentally hydrating a signed-in game route when a proxy, extension, or
// template whitespace leaves a node in the root.
const prerenderedPages = new Set(['landing', 'ai-sat-prep', 'sat-prep', 'act-prep', 'college-planning', 'login', 'signup', 'privacy', 'terms'])
if (prerenderedPages.has(window.__MENTICS__?.page) && container.hasChildNodes()) {
  hydrateRoot(container, tree)
} else {
  createRoot(container).render(tree)
}
