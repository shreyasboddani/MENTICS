import { renderToString } from 'react-dom/server'
import { setBoot } from './boot'
import { App } from './App'

// Called by prerender.mjs once per public page at build time.
export function render(page, data = {}) {
  setBoot({ page, data })
  return renderToString(<App />)
}
