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

// Public pages ship with prerendered markup for crawlers and first paint, so
// they hydrate. Signed-in pages have an empty root and mount normally.
if (container.hasChildNodes()) {
  hydrateRoot(container, tree)
} else {
  createRoot(container).render(tree)
}
