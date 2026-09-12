import { Component, useEffect, useRef, useState, useSyncExternalStore } from 'react'
import { createPortal } from 'react-dom'
import { LayoutDashboard, Target, GraduationCap, BarChart3, LineChart, Swords, MessageCircle, Award, Settings, LogOut, Menu, X } from 'lucide-react'
import { boot } from './boot'

export class ArenaRouteBoundary extends Component {
  state = { failed: false }
  static getDerivedStateFromError() { return { failed: true } }
  render() {
    if (!this.state.failed) return this.props.children
    return <AppShell name={boot.data.name}><main className="app-main" role="alert">
      <h1>The Arena could not open.</h1><p>Reload to reconnect. Your saved loadout and progress are kept.</p>
      <button className="button button--primary" onClick={() => window.location.reload()}>Reload Arena</button>
    </main></AppShell>
  }
}

const noopSubscribe = () => () => {}
export function useClientOnly(value, fallback = '') {
  // useSyncExternalStore is the hydration-safe way to read a client-only value:
  // the server snapshot returns the fallback, the client snapshot the real
  // value, so server and client markup agree and React swaps it in after mount.
  return useSyncExternalStore(noopSubscribe, () => value, () => fallback)
}

export function CsrfField() {
  const token = useClientOnly(boot.data.csrfToken || '')
  return <input type="hidden" name="_csrf_token" value={token} />
}


export function Brand({ inverse = false }) {
  return <a className={`brand ${inverse ? 'brand--inverse' : ''}`} href="/" aria-label="Mentics home">MENTICS</a>
}


const navItems = [
  ['/dashboard', LayoutDashboard, 'Home'],
  ['/dashboard/test-path-view', Target, 'Test path'],
  ['/dashboard/college-path-view', GraduationCap, 'College path'],
  ['/dashboard/stats', BarChart3, 'Stats'],
  ['/dashboard/tracker', LineChart, 'Tracker'],
  ['/battles', Swords, 'SAT Battles'],
  ['/forum', MessageCircle, 'Community'],
  ['/points', Award, 'Points & achievements'],
  ['/account', Settings, 'Settings']
]

export function Starfield({ warp = false, tone = 'violet' }) {
  const ref = useRef(null)
  useEffect(() => {
    const canvas = ref.current
    const ctx = canvas?.getContext('2d')
    if (!ctx) return
    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    let frame; let width = 0; let height = 0; let points = []; let active = !document.hidden
    const color = tone === 'indigo' ? [79, 70, 229] : [124, 58, 237]
    const resize = () => {
      const ratio = Math.min(window.devicePixelRatio || 1, 2)
      width = canvas.clientWidth; height = canvas.clientHeight
      canvas.width = width * ratio; canvas.height = height * ratio; ctx.setTransform(ratio, 0, 0, ratio, 0, 0)
      const count = warp ? Math.min(720, Math.floor(width * height / 1200)) : Math.min(120, Math.floor(width * height / 10000))
      points = Array.from({ length: count }, () => warp ? { x: (Math.random() - .5) * width, y: (Math.random() - .5) * height, z: Math.random() * .9 + .1 } : { x: Math.random() * width, y: Math.random() * height, r: Math.random() * 1.4 + .3, v: Math.random() * .12 + .03, a: Math.random() * .55 + .15 })
    }
    const draw = () => {
      if (!active) { frame = undefined; return }
      ctx.clearRect(0, 0, width, height)
      if (warp) {
        const cx = width / 2, cy = height / 2
        points.forEach(p => { p.z -= .012; if (p.z < .02) { p.x = (Math.random() - .5) * width; p.y = (Math.random() - .5) * height; p.z = 1 } const scale = 1 / p.z; const x = cx + p.x * scale * .25; const y = cy + p.y * scale * .25; const tail = 8 + (1 - p.z) * 36; ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(cx + (x - cx) * (1 + tail / Math.max(width, height)), cy + (y - cy) * (1 + tail / Math.max(width, height))); ctx.strokeStyle = `rgba(${color.join(',')},${Math.min(1, 1 - p.z + .2)})`; ctx.lineWidth = Math.max(.5, (1 - p.z) * 2.4); ctx.stroke() })
      } else {
        points.forEach(p => { p.y -= p.v; if (p.y < 0) p.y = height; ctx.beginPath(); ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2); ctx.fillStyle = `rgba(${color.join(',')},${p.a})`; ctx.fill() })
      }
      if (!reduced) frame = requestAnimationFrame(draw)
    }
    const setActive = () => {
      active = !document.hidden
      if (active && !frame && !reduced) frame = requestAnimationFrame(draw)
    }
    resize(); draw(); window.addEventListener('resize', resize); document.addEventListener('visibilitychange', setActive)
    const observer = new IntersectionObserver(([entry]) => {
      active = entry.isIntersecting && !document.hidden
      if (active && !frame && !reduced) frame = requestAnimationFrame(draw)
      if (!active) { cancelAnimationFrame(frame); frame = undefined }
    }, { threshold: 0 })
    observer.observe(canvas)
    return () => { cancelAnimationFrame(frame); observer.disconnect(); window.removeEventListener('resize', resize); document.removeEventListener('visibilitychange', setActive) }
  }, [warp, tone])
  return <canvas ref={ref} className={warp ? 'warp-field' : 'star-field'} aria-hidden="true" />
}

export function AppShell({ children, name }) {
  const [menu, setMenu] = useState(false)
  const [navWarp, setNavWarp] = useState(null)
  const current = typeof window === 'undefined' ? '' : window.location.pathname
  const active = href => current === href || (href === '/dashboard/test-path-view' && current.startsWith('/dashboard/test-path')) || (href === '/dashboard/college-path-view' && current.startsWith('/dashboard/college-path')) || (href !== '/dashboard' && current.startsWith(`${href}/`))
  const travel = (event, href, label) => {
    if (event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey || current === href) return
    const opensPath = href === '/dashboard/test-path-view' || href === '/dashboard/college-path-view'
    if (!opensPath) return
    event.preventDefault(); setMenu(false); setNavWarp({ href, label })
    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    window.setTimeout(() => { window.location.href = href }, reduced ? 60 : 420)
  }
  return <div className="app-shell app-shell--tabs">
    <Starfield />
    <header className="product-nav">
      <Brand />
      <nav id="mobile-product-navigation" className={menu ? 'open' : ''} aria-label="Product navigation">{navItems.map(([href, Icon, label]) => <a key={href} className={active(href) ? 'active' : ''} href={href} aria-current={active(href) ? 'page' : undefined} title={label} onClick={event => travel(event, href, label)}><Icon size={17} /><span>{label}</span></a>)}</nav>
      <div className="product-account"><a href="/account" onClick={event => travel(event, '/account', 'Settings')}><i>{(name || 'M').slice(0, 1).toUpperCase()}</i><span>{name || 'Mentics student'}</span></a><form className="product-logout" method="POST" action="/logout"><CsrfField /><button type="submit" aria-label="Log out"><LogOut size={17} /></button></form></div>
      <button className="product-menu" type="button" onClick={() => setMenu(!menu)} aria-label={menu ? 'Close navigation' : 'Open navigation'} aria-controls="mobile-product-navigation" aria-expanded={menu}>{menu ? <X /> : <Menu />}</button>
    </header>
    {menu && <button className="menu-scrim" onClick={() => setMenu(false)} aria-label="Close navigation" />}
    <div className="app-stage">{['test-builder', 'college-builder', 'edit-stats'].includes(boot.page) && boot.data.error && <div className="shell-error" role="alert">{boot.data.error}</div>}{children}</div>
    {navWarp && createPortal(<div className="warp-overlay warp-overlay--nav" aria-live="polite"><Starfield warp tone="violet" /><div><Brand inverse /><p>Opening {navWarp.label}</p></div></div>, document.body)}
  </div>
}


export async function api(url, options = {}) {
  const method = String(options.method || 'GET').toUpperCase()
  const token = boot.data.csrfToken || ''
  const csrfHeader = !['GET', 'HEAD', 'OPTIONS'].includes(method) && token ? { 'X-CSRF-Token': token } : {}
  const response = await fetch(url, { headers: { 'Content-Type': 'application/json', ...csrfHeader, ...(options.headers || {}) }, ...options })
  const data = await response.json().catch(() => ({}))
  if (!response.ok) throw new Error(data.error || 'Something went wrong. Please try again.')
  return data
}

