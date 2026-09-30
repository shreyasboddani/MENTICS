import { useMemo } from 'react'
import { passageHtml } from './passage-text'

// A test passage or stimulus. Long passages scroll inside their own panel so
// the question and answers stay in view, as on the digital test.
export function Passage({ text, className = 'adaptive-passage', label = 'Passage' }) {
  const html = useMemo(() => passageHtml(text), [text])
  const long = String(text || '').length > 900
  return <div className={`${className}${long ? ' is-long' : ''}`} role={long ? 'region' : undefined} aria-label={long ? label : undefined} tabIndex={long ? 0 : undefined} dangerouslySetInnerHTML={{ __html: html }} />
}
