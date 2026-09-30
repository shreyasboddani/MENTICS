import DOMPurify from 'dompurify'
import { marked } from 'marked'

const escapeHtml = text => text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')

// ACT English marks the tested words as [underlined 7: words]; SAT items mark a blank as _____.
const decorate = text => text
  .replace(/\[underlined(?: (\d+))?:\s*([^\]]+)\]/gi, (_, number, words) => `${number ? `<sup>${number}</sup>` : ''}<u>${words}</u>`)
  .replace(/_{3,}/g, '<span class="blank" role="img" aria-label="blank"></span>')

const hasTable = text => /^\s*\|.*\|\s*\n\s*\|[\s:|-]+\|/m.test(text)

// Stimuli are plain text, often with a small table. Only tables go through
// Markdown, so asterisks and underscores in math are never reinterpreted.
export function passageHtml(text) {
  const source = String(text || '')
  const html = hasTable(source)
    ? marked.parse(decorate(source), { breaks: true })
    : decorate(escapeHtml(source)).replace(/\n/g, '<br>')
  return DOMPurify.sanitize(html)
}
