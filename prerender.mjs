// Renders the public pages to static HTML at build time.
//
// Flask injects the result into #root so crawlers and first paint get real
// markup, then React hydrates it in the browser. Only pages that are the same
// for every visitor are prerendered; anything session-specific stays
// client-rendered and is marked noindex.

import { mkdir, writeFile, rm } from 'node:fs/promises'
import { resolve, dirname } from 'node:path'
import { fileURLToPath, pathToFileURL } from 'node:url'

const root = dirname(fileURLToPath(import.meta.url))
const outDir = resolve(root, 'templates/ssr')

// Must stay in sync with PUBLIC_PAGES in seo.py.
const PAGES = [
  { page: 'landing', data: { isLoggedIn: false } },
  { page: 'login', data: {} },
  { page: 'signup', data: {} },
  { page: 'privacy', data: {} },
  { page: 'terms', data: {} }
]

const { render } = await import(
  pathToFileURL(resolve(root, '.ssr-build/entry-server.js')).href
)

await rm(outDir, { recursive: true, force: true })
await mkdir(outDir, { recursive: true })

let total = 0
for (const { page, data } of PAGES) {
  let html
  try {
    html = render(page, data)
  } catch (error) {
    console.error(`\n  prerender failed for "${page}":`, error.message)
    process.exitCode = 1
    continue
  }
  if (!html || html.length < 200) {
    console.error(`\n  prerender produced suspiciously little HTML for "${page}" (${html?.length ?? 0} bytes)`)
    process.exitCode = 1
    continue
  }
  await writeFile(resolve(outDir, `${page}.html`), html, 'utf8')
  console.log(`  prerendered ${page.padEnd(8)} ${String(html.length).padStart(7)} bytes`)
  total += html.length
}

if (process.exitCode) {
  console.error('\nPrerender incomplete. Aborting the build so a broken page cannot ship.')
} else {
  console.log(`\nPrerendered ${PAGES.length} pages, ${(total / 1024).toFixed(1)} KB of markup.`)
}
