import { useEffect, useMemo, useRef, useState, useSyncExternalStore } from 'react'
import { createPortal } from 'react-dom'
import DOMPurify from 'dompurify'
import { marked } from 'marked'
import { Toaster, toast } from 'sonner'
import {
  ArrowLeft, ArrowRight, Award, BarChart3, BookOpen, Brain, CalendarDays,
  Check, Clock3, Flame,
  GraduationCap, Hand, Headphones, House, LayoutDashboard, LineChart,
  LockKeyhole, LogOut, Mail, Menu, MessageCircle, PenLine, Plus, RotateCcw, SkipForward,
  Search, Send, Settings, ShieldCheck, Sparkles, Swords, Target, Trophy, UserRound,
  UsersRound, X, Zap
} from 'lucide-react'
import './styles.css'
import './experience.css'
import './brand-system.css'
import './liquid-glass.css'
import './mentics-redesign.css'
import './story-system.css'
import './design-system.css'  // last: owns materials, motion, typography, a11y
import './lesson-player.css'
import './mentics-ui.css'  // last: owns chat guide, task modal, and map performance

import { boot } from './boot'

// The CSRF token is per-session, so it cannot be baked into prerendered HTML.
// Rendering empty on the server and filling in after mount keeps the server and
// client markup identical, which is what hydration requires.
const noopSubscribe = () => () => {}
function useClientOnly(value, fallback = '') {
  // useSyncExternalStore is the hydration-safe way to read a client-only value:
  // the server snapshot returns the fallback, the client snapshot the real
  // value, so server and client markup agree and React swaps it in after mount.
  return useSyncExternalStore(noopSubscribe, () => value, () => fallback)
}

function CsrfField() {
  const token = useClientOnly(boot.data.csrfToken || '')
  return <input type="hidden" name="_csrf_token" value={token} />
}

function CsrfBootstrap() {
  useEffect(() => {
    const attach = event => {
      const form = event.target
      if (!(form instanceof HTMLFormElement) || String(form.method).toLowerCase() !== 'post') return
      const existing = form.querySelector('input[name="_csrf_token"]')
      if (existing) { existing.value = boot.data.csrfToken || ''; return }
      const field = document.createElement('input')
      field.type = 'hidden'; field.name = '_csrf_token'; field.value = boot.data.csrfToken || ''; form.appendChild(field)
    }
    document.addEventListener('submit', attach, true)
    return () => document.removeEventListener('submit', attach, true)
  }, [])
  return null
}

function Brand({ inverse = false }) {
  return <a className={`brand ${inverse ? 'brand--inverse' : ''}`} href="/" aria-label="Mentics home">MENTICS</a>
}

function Landing() {
  const loggedIn = useClientOnly(boot.data.isLoggedIn, false)
  useEffect(() => {
    const nodes = [...document.querySelectorAll('.landing-facts > div,.story-chapter,.section-heading,.process-grid article,.signal-story-visual,.signal-story-beats article,.journey-showcase-copy,.journey-demo,.platform-copy,.feature-stack > div,.suite-heading,.suite-grid article,.week-heading,.week-flow article,.faq details,.closing')]
    nodes.forEach(node => node.classList.add('mx-reveal'))
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) { nodes.forEach(node => node.classList.add('is-visible')); return }
    const observer = new IntersectionObserver(entries => entries.forEach(entry => { if (entry.isIntersecting) { entry.target.classList.add('is-visible'); observer.unobserve(entry.target) } }), { threshold: .12, rootMargin: '0px 0px -7% 0px' })
    nodes.forEach(node => observer.observe(node))
    return () => observer.disconnect()
  }, [])
  return <div className="landing">
    <div className="story-progress" aria-hidden="true" />
    <Starfield />
    <header className="public-nav">
      <Brand />
      <nav aria-label="Main navigation">
        <a href="#how-it-works">How it works</a>
        <a href="#platform">Platform</a>
        <a href="#suite">Suite</a>
        <a href="#faq">Questions</a>
      </nav>
      <a className="button button--small button--dark" href={loggedIn ? '/dashboard' : '/login'}>
        {loggedIn ? 'Open dashboard' : 'Log in'} <ArrowRight size={15} />
      </a>
    </header>

    <main>
      <section className="hero">
        <div className="hero-glow hero-glow--one" />
        <div className="hero-glow hero-glow--two" />
        <svg className="hero-route" viewBox="0 0 620 420" aria-hidden="true">
          <path d="M22 355 C115 355 103 205 214 205 S318 72 420 72 S497 204 598 204" />
          <circle cx="22" cy="355" r="6" /><circle cx="214" cy="205" r="6" /><circle cx="420" cy="72" r="6" /><circle cx="598" cy="204" r="6" />
        </svg>
        <div className="hero-copy">
          <div className="eyebrow"><span /> Built for high school ambition</div>
          <h1>MENTICS</h1>
          <p className="hero-tagline">Your high school ambition, clarified.<br />Stop guessing. <strong>Start achieving.</strong></p>
          <div className="hero-actions">
            <a className="button button--primary" href={loggedIn ? '/dashboard' : '/signup'}>
              {loggedIn ? 'Continue your path' : 'Build your free path'} <ArrowRight size={18} />
            </a>
            <a className="button button--quiet" href="#how-it-works">See how it works</a>
          </div>
          <div className="hero-signal" aria-label="How Mentics keeps you moving">
            <span><b>01</b> Find the signal</span>
            <i />
            <span><b>02</b> Do the work</span>
            <i />
            <span><b>03</b> Adapt the path</span>
          </div>
        </div>

        <div className="product-frame" aria-label="Mentics product preview">
          <div className="frame-float frame-float--signal" aria-hidden="true"><Sparkles /> Path recalibrated</div>
          <div className="frame-float frame-float--focus" aria-hidden="true"><Target /> One clear move</div>
          <div className="frame-top"><span /><span /><span /><div>mentics.vercel.app</div></div>
          <div className="preview-shell">
            <aside className="preview-rail"><Brand /><div className="preview-nav active"><House size={16} /> Home</div><div className="preview-nav"><Target size={16} /> My path</div><div className="preview-nav"><BarChart3 size={16} /> Progress</div></aside>
            <div className="preview-main">
              <div className="preview-heading"><div><small>MONDAY, AUGUST 14</small><h3>Good morning, Alex.</h3><p>One clear step at a time.</p></div><div className="streak-pill"><Flame size={15} /> 6 day focus</div></div>
              <div className="preview-grid">
                <div className="preview-plan">
                  <div className="card-kicker">TODAY'S PATH</div>
                  {[['01', 'Review linear functions', '20 min'], ['02', 'Complete a focused sprint', '15 min'], ['03', 'Log missed questions', '10 min']].map((item, i) => <div className={`preview-task ${i === 0 ? 'current' : ''}`} key={item[0]}><b>{item[0]}</b><span>{item[1]}</span><small>{item[2]}</small></div>)}
                </div>
                <div className="preview-score"><div className="card-kicker">SAT PROGRESS</div><strong>1420</strong><span>+60 this month</span><div className="mini-chart"><i /><i /><i /><i /><i /><i /></div></div>
              </div>
            </div>
          </div>
        </div>
        <div className="hero-scroll-cue" aria-hidden="true"><span>Follow the path</span><i /></div>
      </section>

      <section className="trust-strip"><span>A path that adapts</span><span>Focused daily action</span><span>Progress you can see</span><span>Guidance when you need it</span></section>

      <section className="landing-facts" aria-label="Mentics at a glance">
        <div><strong>5</strong><span><b>steps at a time</b><small>Enough direction to move. Never enough noise to freeze.</small></span></div>
        <div><strong>2</strong><span><b>connected tracks</b><small>Test preparation and college planning, finally in one rhythm.</small></span></div>
        <div><strong>1</strong><span><b>place to keep moving</b><small>Your plan, practice, feedback, progress, and people.</small></span></div>
      </section>

      <section className="section process story-chapter" data-chapter="01" id="how-it-works">
        <div className="section-heading"><div className="eyebrow"><span /> THE MENTICS METHOD</div><h2>Clarity changes everything.</h2><p>Mentics turns a distant goal into the next right move—then learns from what happens.</p></div>
        <div className="process-grid">
          <article><b>01</b><Target /><h3>Tell us where you are</h3><p>Share your goals, timing, strengths, and the areas that need attention.</p></article>
          <article><b>02</b><Sparkles /><h3>Get a five-step path</h3><p>Receive a focused roadmap built around your actual priorities—not a generic checklist.</p></article>
          <article><b>03</b><BarChart3 /><h3>Improve with evidence</h3><p>Complete work, track results, and let every new path build on real progress.</p></article>
        </div>
      </section>

      <section className="signal-story story-chapter" data-chapter="02" aria-labelledby="signal-story-title">
        <div className="signal-story-intro">
          <div className="eyebrow"><span /> FROM AMBITION TO ACTION</div>
          <h2 id="signal-story-title">Mentics turns uncertainty into momentum.</h2>
          <p>Not with a giant checklist. With a living path that gets clearer every time you move.</p>
        </div>
        <div className="signal-story-layout">
          <div className="signal-story-visual" aria-hidden="true">
            <div className="signal-glass">
              <span className="signal-glass-shine" />
              <div className="signal-orbit signal-orbit--one" />
              <div className="signal-orbit signal-orbit--two" />
              <div className="signal-core"><Target /></div>
              <svg viewBox="0 0 440 540">
                <path d="M220 84 C220 150 104 150 104 242 S336 330 336 418 S220 455 220 490" />
                <circle cx="220" cy="84" r="8" /><circle cx="104" cy="242" r="8" /><circle cx="336" cy="418" r="8" /><circle cx="220" cy="490" r="8" />
              </svg>
              <span className="signal-tag signal-tag--goal"><small>01</small><b>Your goal</b></span>
              <span className="signal-tag signal-tag--path"><small>02</small><b>Five clear steps</b></span>
              <span className="signal-tag signal-tag--proof"><small>03</small><b>Real evidence</b></span>
              <span className="signal-tag signal-tag--adapt"><small>04</small><b>A smarter next path</b></span>
            </div>
          </div>
          <div className="signal-story-beats">
            <article><span>01</span><div><small>FIND THE SIGNAL</small><h3>Start with what is true now.</h3><p>Your scores, goals, timing, strengths, and friction become useful context—not another form that disappears into a database.</p></div></article>
            <article><span>02</span><div><small>MAKE IT FINISHABLE</small><h3>See only the next five moves.</h3><p>Mentics cuts through the noise and builds a Duolingo-style route where the next useful action is always obvious.</p></div></article>
            <article><span>03</span><div><small>LEARN FROM THE WORK</small><h3>Every result changes the picture.</h3><p>Practice, quiz sources, completed tasks, and updated scores become evidence the system can actually use.</p></div></article>
            <article><span>04</span><div><small>ADAPT WITHOUT STARTING OVER</small><h3>Your path grows with you.</h3><p>Regenerate when life changes or progress lands. Mentics keeps the context and gives you a sharper next chapter.</p></div></article>
          </div>
        </div>
      </section>

      <section className="journey-showcase story-chapter" data-chapter="03" aria-labelledby="journey-title">
        <div className="journey-showcase-copy">
          <div className="eyebrow eyebrow--light"><span /> A PATH YOU CAN FEEL</div>
          <h2 id="journey-title">Progress should feel alive.</h2>
          <p>Your next move stays obvious. Finish a step, watch the route open up, and keep your attention on what is ready now—not a wall of future obligations.</p>
          <ul>
            <li><Check /> One active step keeps the day focused</li>
            <li><Zap /> Practice and feedback live inside the route</li>
            <li><Trophy /> Milestones make the work worth celebrating</li>
          </ul>
          <a href={loggedIn ? '/dashboard/test-path-view' : '/signup'}>See your path <ArrowRight size={17} /></a>
        </div>
        <div className="journey-demo" aria-hidden="true">
          <div className="journey-demo-glow" />
          <svg viewBox="0 0 420 650"><path className="demo-route-base" d="M210 58 C210 120 105 128 105 200 S315 280 315 350 S105 430 105 500 S210 550 210 598" /><path className="demo-route-live" d="M210 58 C210 120 105 128 105 200 S315 280 315 350" /></svg>
          {[
            { x: 50, y: 9, state: 'done', label: 'Set your baseline', icon: <Check /> },
            { x: 25, y: 31, state: 'done', label: 'Build the skill', icon: <Check /> },
            { x: 75, y: 54, state: 'current', label: 'Focused sprint', icon: <Zap /> },
            { x: 25, y: 77, state: 'locked', label: 'Review the evidence', icon: <LockKeyhole /> },
            { x: 50, y: 92, state: 'milestone', label: 'Milestone', icon: <Trophy /> }
          ].map((step, index) => <div className={`demo-step ${step.state}`} style={{ left: `${step.x}%`, top: `${step.y}%` }} key={step.label}><i>{step.icon}</i><span>{index === 2 && <small>UP NEXT</small>}{step.label}</span></div>)}
        </div>
      </section>

      <section className="battle-landing story-chapter" data-chapter="04" aria-labelledby="battle-landing-title">
        <div className="battle-landing-copy"><div className="eyebrow"><span /> SAT BATTLE ARENA</div><h2 id="battle-landing-title">A faster way to prove what you know.</h2><p>Meet one student in a clean, timed five-question SAT round. Both of you get the same original questions. Accuracy decides it; speed breaks the tie.</p><a className="button button--primary" href={loggedIn ? '/battles' : '/signup'}><Swords /> {loggedIn ? 'Enter the arena' : 'Build your path first'} <ArrowRight size={17} /></a></div>
        <div className="battle-landing-preview" aria-hidden="true"><header><span><i /> LIVE ROUND</span><strong><Clock3 /> 1:18</strong></header><div><small>QUESTION 3 · ALGEBRA</small><b>If 3x + 8 = 29, what is x?</b><span><i>A</i> 5</span><span className="selected"><i>B</i> 7 <Check /></span><span><i>C</i> 9</span></div><footer><span>YOU <b>2</b></span><i>VS</i><span><b>2</b> RIVAL</span></footer></div>
      </section>

      <section className="section platform story-chapter" data-chapter="05" id="platform">
        <div className="platform-copy"><div className="eyebrow eyebrow--light"><span /> ONE FOCUSED WORKSPACE</div><h2>Less noise.<br />More momentum.</h2><p>Test prep, college planning, progress, and contextual guidance belong in one calm place.</p><a href={loggedIn ? '/dashboard' : '/signup'}>Explore the platform <ArrowRight size={17} /></a></div>
        <div className="feature-stack">
          <div><Target /><span><b>Adaptive paths</b><small>Five clear steps that respond to your goals and performance.</small></span></div>
          <div><MessageCircle /><span><b>Contextual guidance</b><small>Ask for help without losing the context of what you are working on.</small></span></div>
          <div><GraduationCap /><span><b>College planning</b><small>Turn applications, essays, and deadlines into manageable progress.</small></span></div>
          <div><BarChart3 /><span><b>Visible progress</b><small>Track scores, streaks, milestones, and the work behind them.</small></span></div>
        </div>
      </section>

      <section className="suite-section story-chapter" data-chapter="05" id="suite">
        <div className="suite-heading"><div className="eyebrow"><span /> THE COMPLETE MENTICS SUITE</div><h2>Everything your ambition needs.<br />Nothing it doesn’t.</h2><p>The tools already inside Mentics, brought into one expressive workspace.</p></div>
        <div className="suite-grid">
          <article className="suite-path"><Target /><small>ADAPTIVE PATHS</small><h3>Five steps. One clear direction.</h3><p>Personalized SAT, ACT, and college-planning roadmaps that respond to your progress.</p><div className="mini-road"><i>1</i><span /><i>2</i><span /><i>3</i><span /><i>4</i><span /><i>5</i></div></article>
          <article className="suite-sprint"><Zap /><small>FOCUSED SPRINTS</small><h3>Practice with purpose.</h3><p>Short assessments, strategy articles, and immediate explanations make every session count.</p></article>
          <article className="suite-essay"><PenLine /><small>ESSAY FEEDBACK</small><h3>Make every word stronger.</h3><p>Get structured feedback while keeping your voice, story, and ideas unmistakably yours.</p></article>
          <article className="suite-progress"><LineChart /><small>VISIBLE PROGRESS</small><h3>See the work adding up.</h3><p>Scores, milestones, history, points, and streaks reveal the pattern behind improvement.</p></article>
          <article className="suite-community"><UsersRound /><small>COMMUNITY</small><h3>Move forward together.</h3><p>Ask questions, share approaches, and celebrate real consistency on the leaderboard.</p></article>
        </div>
      </section>

      <section className="week-section story-chapter" data-chapter="06">
        <div className="week-heading"><div className="eyebrow"><span /> MOMENTUM, NOT BUSYWORK</div><h2>A week inside Mentics.</h2><p>The plan bends around real student life. Each session has a purpose, a finish line, and a visible place in the bigger picture.</p></div>
        <div className="week-flow">
          {[
            ['MON', 'Find the signal', 'Check your path and start with the highest-impact move.', Target],
            ['TUE', 'Practice on purpose', 'Run a short sprint, then understand every missed question.', Zap],
            ['WED', 'Make the story stronger', 'Shape an essay without sanding away your own voice.', PenLine],
            ['THU', 'Ask while it is fresh', 'Get guidance with the context of your path still attached.', MessageCircle],
            ['FRI', 'See what changed', 'Log the result, close the loop, and unlock what comes next.', LineChart]
          ].map(([day, title, copy, Icon], index) => <article key={day}><span>{day}</span><i><Icon /></i><div><small>0{index + 1}</small><h3>{title}</h3><p>{copy}</p></div></article>)}
        </div>
      </section>

      <section className="section faq story-chapter" data-chapter="07" id="faq"><div className="section-heading"><h2>Good questions.</h2></div>
        {[['Is Mentics free to use?', 'Yes. The current early-access product is free and does not require a credit card.'], ['Does it support both SAT and ACT?', 'Yes. Your test-prep path can focus on the SAT, ACT, or both.'], ['Can my plan change as I improve?', 'Yes. Regenerate a path after new scores, completed work, or a change in goals. Mentics uses that context to plan the next five steps.']].map(([q, a]) => <details key={q}><summary>{q}<Plus size={18} /></summary><p>{a}</p></details>)}
      </section>

      <section className="closing"><div><Brand inverse /><h2>Know what to do next.</h2><p>Build a path that makes your ambition feel possible.</p><a className="button button--light" href={loggedIn ? '/dashboard' : '/signup'}>{loggedIn ? 'Open dashboard' : 'Get started free'} <ArrowRight size={18} /></a></div></section>
    </main>
    <footer><Brand /><span>© 2026 Mentics. All rights reserved.</span><div><a href="/terms">Terms</a><a href="/privacy">Privacy</a><a href="mailto:support@mentics.com">Contact</a></div></footer>
  </div>
}

const navItems = [
  ['/dashboard', LayoutDashboard, 'Home'],
  ['/dashboard/test-path-view', Target, 'Test path'],
  ['/dashboard/college-path-view', GraduationCap, 'College path'],
  ['/dashboard/stats', BarChart3, 'Stats'],
  ['/dashboard/tracker', LineChart, 'Tracker'],
  ['/battles', Swords, 'SAT Battles'],
  ['/forum', MessageCircle, 'Community'],
  ['/leaderboard', Trophy, 'Leaderboard'],
  ['/account', Settings, 'Settings']
]

function Starfield({ warp = false, tone = 'violet' }) {
  const ref = useRef(null)
  useEffect(() => {
    const canvas = ref.current
    const ctx = canvas?.getContext('2d')
    if (!ctx) return
    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    let frame; let width = 0; let height = 0; let points = []
    const color = tone === 'indigo' ? [79, 70, 229] : [124, 58, 237]
    const resize = () => {
      const ratio = Math.min(window.devicePixelRatio || 1, 2)
      width = canvas.clientWidth; height = canvas.clientHeight
      canvas.width = width * ratio; canvas.height = height * ratio; ctx.setTransform(ratio, 0, 0, ratio, 0, 0)
      const count = warp ? Math.min(720, Math.floor(width * height / 1200)) : Math.min(120, Math.floor(width * height / 10000))
      points = Array.from({ length: count }, () => warp ? { x: (Math.random() - .5) * width, y: (Math.random() - .5) * height, z: Math.random() * .9 + .1 } : { x: Math.random() * width, y: Math.random() * height, r: Math.random() * 1.4 + .3, v: Math.random() * .12 + .03, a: Math.random() * .55 + .15 })
    }
    const draw = () => {
      ctx.clearRect(0, 0, width, height)
      if (warp) {
        const cx = width / 2, cy = height / 2
        points.forEach(p => { p.z -= .012; if (p.z < .02) { p.x = (Math.random() - .5) * width; p.y = (Math.random() - .5) * height; p.z = 1 } const scale = 1 / p.z; const x = cx + p.x * scale * .25; const y = cy + p.y * scale * .25; const tail = 8 + (1 - p.z) * 36; ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(cx + (x - cx) * (1 + tail / Math.max(width, height)), cy + (y - cy) * (1 + tail / Math.max(width, height))); ctx.strokeStyle = `rgba(${color.join(',')},${Math.min(1, 1 - p.z + .2)})`; ctx.lineWidth = Math.max(.5, (1 - p.z) * 2.4); ctx.stroke() })
      } else {
        points.forEach(p => { p.y -= p.v; if (p.y < 0) p.y = height; ctx.beginPath(); ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2); ctx.fillStyle = `rgba(${color.join(',')},${p.a})`; ctx.fill() })
      }
      if (!reduced) frame = requestAnimationFrame(draw)
    }
    resize(); draw(); window.addEventListener('resize', resize)
    return () => { cancelAnimationFrame(frame); window.removeEventListener('resize', resize) }
  }, [warp, tone])
  return <canvas ref={ref} className={warp ? 'warp-field' : 'star-field'} aria-hidden="true" />
}

function AppShell({ children, name }) {
  const [menu, setMenu] = useState(false)
  const [navWarp, setNavWarp] = useState(null)
  const current = window.location.pathname
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

function PortalSelector({ open, onClose }) {
  const [warping, setWarping] = useState('')
  const [error, setError] = useState('')
  useEffect(() => { document.body.style.overflow = open ? 'hidden' : ''; return () => { document.body.style.overflow = '' } }, [open])
  const choose = async type => {
    setError(''); setWarping(type)
    const test = type === 'test'
    const request = fetch(test ? '/api/test-path-status' : '/api/college-path-status').then(r => r.ok ? r.json() : Promise.reject(new Error('Could not check this path.')))
    try {
      const [data] = await Promise.all([request, new Promise(resolve => window.setTimeout(resolve, 1450))])
      window.location.href = data.has_path ? (test ? '/dashboard/test-path-view' : '/dashboard/college-path-view') : (test ? '/dashboard/test-path-builder' : '/dashboard/college-path-builder')
    } catch (e) { setWarping(''); setError(e.message) }
  }
  if (!open && !warping) return null
  return createPortal(<>
    <div className={`portal-overlay ${open ? 'visible' : ''}`} role="dialog" aria-modal="true" aria-label="Choose your path">
      <div className="portal-heading"><small>MENTICS PATH BUILDER</small><h2>Choose your path</h2><p>Step through the portal that matches what you want to move forward.</p></div>
      <div className="portal-pair">
        <button className="portal portal--test" onClick={() => choose('test')} disabled={Boolean(warping)}><svg viewBox="0 0 220 220" aria-hidden="true"><defs><radialGradient id="portal-test"><stop offset="0" stopColor="#c084fc" /><stop offset=".48" stopColor="#7c3aed" /><stop offset="1" stopColor="#312e81" /></radialGradient></defs><circle cx="110" cy="110" r="92" /><circle cx="110" cy="110" r="76" /><circle cx="110" cy="110" r="62" fill="url(#portal-test)" /></svg><span><BookOpen /><b>Test Prep</b><small>SAT / ACT journey</small></span></button>
        <button className="portal portal--college" onClick={() => choose('college')} disabled={Boolean(warping)}><svg viewBox="0 0 220 220" aria-hidden="true"><defs><radialGradient id="portal-college"><stop offset="0" stopColor="#818cf8" /><stop offset=".48" stopColor="#4f46e5" /><stop offset="1" stopColor="#172554" /></radialGradient></defs><circle cx="110" cy="110" r="92" /><circle cx="110" cy="110" r="76" /><circle cx="110" cy="110" r="62" fill="url(#portal-college)" /></svg><span><GraduationCap /><b>College Plan</b><small>Applications and more</small></span></button>
      </div>
      {error && <p className="portal-error">{error}</p>}
      <button className="portal-close" onClick={onClose} aria-label="Close path selector"><X /></button>
    </div>
    {warping && <div className="warp-overlay"><Starfield warp tone={warping === 'college' ? 'indigo' : 'violet'} /><div><Brand inverse /><p>Connecting to your path</p></div></div>}
  </>, document.body)
}

function Dashboard() {
  const d = boot.data
  const trophies = d.earnedAchievements || []
  const [suggestion, setSuggestion] = useState('Reviewing your latest progress…')
  const [portalOpen, setPortalOpen] = useState(false)
  useEffect(() => { fetch('/api/get-suggestion').then(r => r.json()).then(x => setSuggestion(x.suggestion || 'Your next clear step is waiting.')).catch(() => setSuggestion('Keep the next step small, specific, and finishable.')) }, [])
  const chart = d.activityData?.data || [0, 0, 0, 0, 0, 0, 0]
  const max = Math.max(...chart, 1)
  const first = String(d.name || 'Student').split(' ')[0]
  const today = new Intl.DateTimeFormat(undefined, { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' }).format(new Date())
  return <AppShell name={d.name}><main className="app-main dashboard-page dashboard-original">
    <section className="dashboard-welcome"><div><small>{today}</small><h1>Welcome back, <span>{first}</span></h1><p>Your dashboard is ready. Let’s build momentum.</p></div><div className="dashboard-totals"><span><Flame /><b>{d.gameStats?.streak || 0}</b><small>DAY STREAK</small></span><span><Zap /><b>{d.gameStats?.points || 0}</b><small>POINTS</small></span></div></section>
    <section className="command-grid">
      <button className="path-launcher" onClick={() => setPortalOpen(true)}><span className="path-launcher-grid" /><div><small>THE CORE EXPERIENCE</small><h2>Path Builder</h2><p>Launch the Mentics portal to generate or update your personalized roadmap.</p><b>Open portal <ArrowRight /></b></div><div className="path-radar"><i /><i /><i /><Target /></div></button>
      <a className="dash-module battle-dashboard-card" href="/battles"><div><small>SAT BATTLE ARENA</small><h2>Put your speed to the test.</h2><p>Race a matched student through five SAT-style questions. Accuracy wins; speed settles the tie.</p><b>Enter the arena <ArrowRight /></b></div><span><Swords /><i>1:1</i><small>LIVE</small></span></a>
      <ProgressTile type="test" value={d.testPrepCompleted || 0} /><ProgressTile type="college" value={d.collegePlanningCompleted || 0} />
      <article className="dash-module activity-module"><header><div><small>ACTIVITY TREND</small><h2>Focus intensity</h2></div><BarChart3 /></header><div className="command-chart">{chart.map((v, i) => <div key={i}><b>{v}</b><i style={{ height: `${Math.max(7, v / max * 100)}%` }} /><small>{d.activityData?.labels?.[i]}</small></div>)}</div></article>
      <article className="dash-module vital-module"><header><small>VITAL STATS</small><a href="/dashboard/stats/edit">Update</a></header><dl><div><dt>GPA</dt><dd>{d.gpa}</dd></div><div><dt>SAT</dt><dd>{d.satTotal}</dd></div><div><dt>ACT</dt><dd>{d.actAverage}</dd></div></dl></article>
      <article className="dash-module insight-module"><div className="countdown">{d.testDateInfo?.days_left != null ? <><strong>{d.testDateInfo.days_left}</strong><span>DAYS TO {d.testDateInfo.test_type}</span><small>{d.testDateInfo.date_str}</small></> : <><CalendarDays /><span>NO TEST DATE SET</span><a href="/dashboard/test-path-builder">Set your date</a></>}</div><div className="insight"><Brain /><small>MENTICS INSIGHT</small><p>{suggestion}</p></div></article>
      <article className="dash-module updates-module"><header><div><small>LATEST SIGNALS</small><h2>Recent updates</h2></div><Clock3 /></header><div>{d.recentActivities?.length ? d.recentActivities.slice(0, 4).map((a, i) => <span key={i}><i><Check /></i><p><b>{activityTitle(a)}</b><small>{activityDetail(a)}</small></p></span>) : <div className="empty-state"><Target /><p>Your completed work will show up here.</p></div>}</div></article>
      <article className={`dash-module trophies-module ${trophies.length ? '' : 'trophies-module--empty'}`}><header><div><small>MILESTONES</small><h2>Trophies</h2></div>{trophies.length ? <span className="trophy-total">{trophies.length} earned</span> : <Award />}</header><div className="trophy-list">{trophies.length ? trophies.slice(0, 6).map(item => <div className="trophy-item" key={item.id}><i><Trophy /></i><div><b>{item.title}</b><small>{item.description}</small></div></div>) : <div className="trophy-empty"><i><Trophy /></i><div><b>No trophies yet</b><small>Complete your first path task to earn one.</small></div></div>}</div><a href="/leaderboard">View leaderboard <ArrowRight /></a></article>
    </section>
    <PortalSelector open={portalOpen} onClose={() => setPortalOpen(false)} />
  </main></AppShell>
}

function ProgressTile({ type, value }) {
  const test = type === 'test'
  const Icon = test ? BookOpen : GraduationCap
  return <a className={`dash-module progress-tile progress-tile--${type}`} href={test ? '/dashboard/test-path-view' : '/dashboard/college-path-view'}><header><Icon /><small>{test ? 'TEST PREP' : 'COLLEGE PLAN'}</small></header><div><strong><b>{value}</b><i>/5</i></strong><span>{value === 5 ? 'PATH COMPLETE' : 'TASKS DONE'}</span></div><em><i style={{ width: `${value / 5 * 100}%` }} /></em></a>
}

function activityTitle(a) {
  return ({ task_completed: 'Task completed', path_generated: 'New path created', stat_updated: 'Progress updated', task_added: 'Task added' })[a.type] || 'Progress recorded'
}
function activityDetail(a) { return a.details?.description || a.details?.stat_name || 'A step forward on your Mentics path' }

async function api(url, options = {}) {
  const method = String(options.method || 'GET').toUpperCase()
  const token = boot.data.csrfToken || ''
  const csrfHeader = !['GET', 'HEAD', 'OPTIONS'].includes(method) && token ? { 'X-CSRF-Token': token } : {}
  const response = await fetch(url, { headers: { 'Content-Type': 'application/json', ...csrfHeader, ...(options.headers || {}) }, ...options })
  const data = await response.json().catch(() => ({}))
  if (!response.ok) throw new Error(data.error || 'Something went wrong. Please try again.')
  return data
}

function Markdown({ children }) {
  const html = useMemo(() => DOMPurify.sanitize(marked.parse(children || '', { breaks: true })), [children])
  return <div className="markdown" dangerouslySetInnerHTML={{ __html: html }} />
}

// What each node type is and what pressing the button will actually do. The
// student should never have to guess what a step is asking of them.
const nodeKinds = {
  lesson: { label: 'Lesson', icon: BookOpen, cta: 'Start lesson', resume: 'Continue lesson', blurb: 'Mentics teaches this skill step by step, checking your understanding as you go.' },
  practice_sprint: { label: 'Practice', icon: Zap, cta: 'Start practice', resume: 'Keep practicing', blurb: 'Short drill on what you just learned. Instant feedback on every answer.' },
  quiz: { label: 'Review', icon: Brain, cta: 'Start review', resume: 'Keep reviewing', blurb: 'A mixed review of everything this unit covered.' },
  boss_battle: { label: 'Boss battle', icon: Trophy, cta: 'Open official test', resume: 'Open official test', blurb: 'A full, timed official practice test. Log your score when you finish.' },
  milestone: { label: 'Milestone', icon: Award, cta: 'Start this milestone', resume: 'Finish this milestone', blurb: 'Real work outside Mentics. Log what you produced and the next unit builds on it.' }
}

function taskKind(task) {
  if (task.node_type && nodeKinds[task.node_type]) return task.node_type
  if (nodeKinds[task.task_format]) return task.task_format
  if (task.type === 'milestone' || String(task.description).toLowerCase().includes('boss battle')) return 'boss_battle'
  return null
}

function firstLink(text) { const m = /\[([^\]]+)\]\(([^)]+)\)/.exec(String(text || '')); return m ? m[2] : null }

function PathPage() {
  const category = boot.data.category
  const isTest = category === 'Test Prep'
  const [tasks, setTasks] = useState([])
  const [loading, setLoading] = useState(true)
  const [regenerating, setRegenerating] = useState(false)
  const [error, setError] = useState('')
  const [selected, setSelected] = useState(null)
  const [chatOpen, setChatOpen] = useState(() => window.matchMedia('(min-width: 1050px)').matches)
  const [adding, setAdding] = useState(false)
  const [essayOpen, setEssayOpen] = useState(false)
  const pathRequest = useRef(0)
  const builder = isTest ? '/dashboard/test-path-builder' : '/dashboard/college-path-builder'
  const loadTasks = async (regenerate = false) => {
    const requestId = ++pathRequest.current
    setLoading(true); setRegenerating(regenerate); setError('')
    try {
      const data = await api(`/api/tasks?category=${encodeURIComponent(category)}`, regenerate ? { method: 'POST' } : {})
      if (!Array.isArray(data)) throw new Error('Your path could not be loaded.')
      if (requestId === pathRequest.current) setTasks(data.map(normalizeTask))
    } catch (e) { if (requestId === pathRequest.current) setError(e.message) } finally { if (requestId === pathRequest.current) { setLoading(false); setRegenerating(false) } }
  }
  useEffect(() => {
    const requestId = ++pathRequest.current
    let mounted = true
    api(`/api/tasks?category=${encodeURIComponent(category)}`)
      .then(data => {
        if (!Array.isArray(data)) throw new Error('Your path could not be loaded.')
        if (mounted && requestId === pathRequest.current) setTasks(data.map(normalizeTask))
      })
      .catch(e => { if (mounted && requestId === pathRequest.current) setError(e.message) })
      .finally(() => { if (mounted && requestId === pathRequest.current) setLoading(false) })
    return () => { mounted = false }
  }, [category])
  useEffect(() => {
    const desktop = window.matchMedia('(min-width: 1050px)')
    const keepPathVisible = event => { if (!event.matches) setChatOpen(false) }
    // A page can hydrate at desktop width and then be restored on a smaller
    // viewport. Check immediately as well as on later changes so the guide
    // never obscures the path on phones.
    keepPathVisible(desktop)
    desktop.addEventListener('change', keepPathVisible)
    return () => desktop.removeEventListener('change', keepPathVisible)
  }, [])
  const coreTasks = tasks.filter(t => !t.is_user_added)
  const completed = coreTasks.filter(t => t.is_completed).length
  const progressTotal = coreTasks.length || 5
  const activeIndex = tasks.findIndex(t => !t.is_completed)
  const journeyHeight = Math.max(790, 180 + (tasks.length - 1) * 155)
  const journeyXs = [320, 170, 320, 470, 320]
  const journeyPoints = tasks.map((_, index) => ({ x: journeyXs[index % journeyXs.length], y: 90 + index * 155 }))
  const journeyCurve = journeyPoints.reduce((path, point, index) => { if (index === 0) return `M ${point.x} ${point.y}`; const previous = journeyPoints[index - 1]; const mid = (previous.y + point.y) / 2; return `${path} C ${previous.x} ${mid}, ${point.x} ${mid}, ${point.x} ${point.y}` }, '')
  const finishTask = (next, replacementTasks = null) => {
    if (replacementTasks) {
      setTasks(replacementTasks.map(normalizeTask))
      setSelected(null)
      return
    }
    const coreWasComplete = coreTasks.length === 5 && coreTasks.every(t => t.is_completed)
    const updated = tasks.map(t => t.id === next.id ? next : t)
    setTasks(updated)
    setSelected(null)
    const updatedCore = updated.filter(t => !t.is_user_added)
    if (!coreWasComplete && updatedCore.length === 5 && updatedCore.every(t => t.is_completed)) {
      window.setTimeout(async () => {
        if (window.confirm('You finished all five steps. Build the next five-step path now?')) await loadTasks(true)
      }, 250)
    }
  }
  return <AppShell name={boot.data.name}><main className={`app-main path-page ${chatOpen ? 'chat-docked' : ''}`}>
    <div className="path-header"><div><div className="eyebrow"><span /> {category.toUpperCase()}</div><h1>Your five-step path.</h1><p>Finish what is in front of you. The path adapts from there.</p></div><div className="path-header-actions">{!isTest && <button className="button button--quiet" onClick={() => setEssayOpen(true)}><PenLine size={17} /> Essay feedback</button>}{!chatOpen && <button className="button button--quiet" onClick={() => setChatOpen(true)}><MessageCircle size={17} /> Ask Mentics</button>}<a className="button button--dark" href={builder}>Edit goals <ArrowRight size={16} /></a></div></div>
    <div className="path-progress"><span style={{ width: `${completed / progressTotal * 100}%` }} /><p><b><span>{completed}</span><i>/</i><span>{progressTotal}</span></b><span>core steps complete</span></p></div>
    {error && <div className="error-banner">{error}<button onClick={() => loadTasks()}>Try again</button></div>}
    {loading && !tasks.length ? <PathSkeleton /> : <section className={`journey-map ${regenerating ? 'journey-map--regenerating' : ''}`} style={{ height: journeyHeight }} aria-label={`${category} learning journey`} aria-busy={regenerating}>
      <svg className="journey-route" viewBox={`0 0 640 ${journeyHeight}`} preserveAspectRatio="none" aria-hidden="true"><defs><linearGradient id="journey-gradient" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#8b5cf6" /><stop offset="1" stopColor="#4f46e5" /></linearGradient></defs><path className="journey-route-shadow" d={journeyCurve} /><path className="journey-route-progress" d={journeyCurve} pathLength="100" style={{ strokeDasharray: `${tasks.length ? Math.min(100, completed / tasks.length * 100) : 0} 100` }} /></svg>
      {tasks.map((task, index) => {
        const locked = index > activeIndex && activeIndex !== -1; const kind = taskKind(task); const meta = kind ? nodeKinds[kind] : null; const milestone = kind === 'boss_battle'; const NodeIcon = meta?.icon; const point = journeyPoints[index]; const status = task.is_skipped ? 'skipped' : task.is_completed ? 'completed' : index === activeIndex ? 'current' : 'locked'; return <button key={task.id || index} disabled={locked} style={{ left: `${point.x / 640 * 100}%`, top: point.y }} className={`journey-step ${task.is_completed ? 'done' : index === activeIndex ? 'current' : 'locked'} ${task.is_skipped ? 'skipped' : ''} ${milestone ? 'milestone' : ''} ${kind ? `journey-step--${kind}` : ''}`} onClick={() => setSelected(task)} aria-haspopup="dialog" aria-current={index === activeIndex ? 'step' : undefined}>
          <span className="sr-only">Step {index + 1}, {status}{locked ? `: ${task.description}` : '.'} </span>
          {index === activeIndex && !task.is_completed && <span className="journey-next">START</span>}
          <span className="journey-node"><i>{task.is_skipped ? <SkipForward /> : task.is_completed ? <Check /> : locked ? <LockKeyhole /> : NodeIcon ? <NodeIcon /> : index + 1}</i></span>
          <span className={`journey-label ${point.x < 320 ? 'label-right' : point.x > 320 ? 'label-left' : index % 2 ? 'label-left' : 'label-right'}`}><small>{task.is_skipped ? 'SKIPPED' : task.is_completed ? 'COMPLETED' : task.is_user_added ? 'PERSONAL STEP' : meta ? meta.label.toUpperCase() : `STEP ${index + 1}`}</small><b><PlainText value={task.description} /></b>{task.skill_label && kind !== 'boss_battle' && <em className="journey-skill">{task.skill_label}</em>}{task.due_date && <em><CalendarDays /> {task.due_date}</em>}</span>
        </button>
      })}
      {regenerating && <div className="path-regenerating-overlay" role="status" aria-live="polite"><span className="path-regenerating-orbit"><Sparkles /></span><div><b>Rebuilding your path</b><small>Mentics is shaping your next five steps.</small></div></div>}
    </section>}
    <div className="path-footer-actions"><button className="button button--quiet" onClick={() => setAdding(true)} disabled={regenerating}><Plus /> Add your own step</button><button className="text-button" onClick={() => loadTasks(true)} disabled={regenerating}><RotateCcw /> {regenerating ? 'Rebuilding your path…' : isTest ? 'Regenerate five steps' : 'Start next coaching loop'}</button></div>
    {selected && <TaskModal task={selected} category={category} onClose={() => setSelected(null)} onUpdate={(next) => { setTasks(items => items.map(t => t.id === next.id ? next : t)); setSelected(next) }} onCompleted={finishTask} onReported={tasks => finishTask(null, tasks)} />}
    {adding && <AddTask category={category} onClose={() => setAdding(false)} onAdded={t => { setTasks(items => [...items, normalizeTask(t)]); setAdding(false) }} />}
    {essayOpen && <EssayCoach onClose={() => setEssayOpen(false)} />}
    <ChatPanel open={chatOpen} onClose={() => setChatOpen(false)} category={category} onNewPath={items => setTasks(items.map(normalizeTask))} />
    {!chatOpen && <button className="floating-chat" onClick={() => setChatOpen(true)} aria-label="Ask Mentics"><MessageCircle /><span>Ask Mentics</span></button>}
  </main></AppShell>
}

function PlainText({ value }) { return <>{String(value || '').replace(/\[([^\]]+)\]\([^)]+\)/g, '$1').replace(/[*_#`]/g, '')}</> }
function normalizeTask(t) { return { ...t, is_completed: Boolean(t.is_completed), is_skipped: Boolean(t.is_skipped), subtasks: Array.isArray(t.subtasks) ? t.subtasks : [], task_format: t.task_format || 'link' } }

function PathSkeleton() { return <section className="journey-map journey-map--loading">{[0, 1, 2, 3, 4].map(i => <span className="journey-skeleton skeleton" style={{ left: `${[50, 27, 50, 73, 50][i]}%`, top: 90 + i * 155 }} key={i} />)}</section> }

function Modal({ children, onClose, wide = false, label = 'Dialog' }) {
  const modalRef = useRef(null)
  useEffect(() => {
    const previouslyFocused = document.activeElement
    const previousOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    const frame = requestAnimationFrame(() => {
      const preferred = modalRef.current?.querySelector('[autofocus], [data-modal-autofocus], button:not(:disabled), a[href], input:not(:disabled), textarea:not(:disabled), select:not(:disabled)')
      ;(preferred || modalRef.current)?.focus()
    })
    const handleKeyDown = event => {
      if (event.key === 'Escape') { event.preventDefault(); onClose(); return }
      if (event.key !== 'Tab' || !modalRef.current) return
      const focusable = [...modalRef.current.querySelectorAll('button:not(:disabled), a[href], input:not(:disabled), textarea:not(:disabled), select:not(:disabled), [tabindex]:not([tabindex="-1"])')]
        .filter(node => node.getClientRects().length)
      if (!focusable.length) { event.preventDefault(); modalRef.current.focus(); return }
      const first = focusable[0]; const last = focusable[focusable.length - 1]
      if (event.shiftKey && (document.activeElement === first || !modalRef.current.contains(document.activeElement))) { event.preventDefault(); last.focus() }
      else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus() }
    }
    document.addEventListener('keydown', handleKeyDown)
    return () => {
      cancelAnimationFrame(frame)
      document.removeEventListener('keydown', handleKeyDown)
      document.body.style.overflow = previousOverflow
      if (previouslyFocused instanceof HTMLElement && previouslyFocused.isConnected) previouslyFocused.focus()
    }
  }, [onClose])
  return createPortal(<div className="modal-wrap" role="dialog" aria-modal="true" aria-label={label} onPointerDown={event => event.target === event.currentTarget && onClose()}><div ref={modalRef} tabIndex={-1} className={`modal ${wide ? 'modal--wide' : ''}`}><button className="modal-close" onClick={onClose} aria-label="Close"><X /></button>{children}</div></div>, document.body)
}

const milestoneStats = {
  gpa: { label: 'New GPA', placeholder: 'Enter your GPA', min: 0, max: 5, step: .01 },
  sat_math: { label: 'New SAT Math score', placeholder: '200–800', min: 200, max: 800 },
  sat_ebrw: { label: 'New SAT Reading & Writing score', placeholder: '200–800', min: 200, max: 800 },
  sat_total: { label: 'Full SAT practice score', placeholder: '400–1600', min: 400, max: 1600 },
  act_math: { label: 'New ACT Math score', placeholder: '1–36', min: 1, max: 36 },
  act_reading: { label: 'New ACT Reading score', placeholder: '1–36', min: 1, max: 36 },
  act_science: { label: 'New ACT Science score', placeholder: '1–36', min: 1, max: 36 },
  act_composite: { label: 'Full ACT practice score', placeholder: '1–36', min: 1, max: 36 },
  colleges_researched: { label: 'Colleges researched', placeholder: 'Enter a number', min: 0, max: 1000 },
  applications_submitted: { label: 'Applications submitted', placeholder: 'Enter a number', min: 0, max: 1000 },
  essay_progress: { label: 'Essay progress', placeholder: '1 = draft, 2 = final', min: 1, max: 2 }
}

// A boss battle is the one step whose work happens outside Mentics, so the
// score is the only evidence it happened. This captures section scores rather
// than a bare total: the total alone cannot tell the planner which half of the
// test moved, and it never reaches the stats page.
function BossBattle({ task, onClose, onCompleted }) {
  const [detail, setDetail] = useState(null)
  const [scores, setScores] = useState({})
  const [result, setResult] = useState(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    let live = true
    api(`/api/boss_battle/${task.id}`).then(d => {
      if (!live) return
      setDetail(d)
      setScores(Object.fromEntries(d.sections.map(s => [s.key, s.previous ? String(s.previous) : ''])))
    }).catch(e => { if (live) setError(e.message) })
    return () => { live = false }
  }, [task.id])

  const link = firstLink(task.description) || 'https://satsuite.collegeboard.org/sat/practice-preparation/practice-tests'
  const ready = detail && detail.sections.every(s => String(scores[s.key] ?? '').trim() !== '')

  const submit = async () => {
    setBusy(true); setError('')
    try {
      setResult(await api(`/api/boss_battle/${task.id}/result`, { method: 'POST', body: JSON.stringify({ scores }) }))
    } catch (e) { setError(e.message) } finally { setBusy(false) }
  }

  if (result) {
    const up = result.delta != null && result.delta > 0
    return <Modal onClose={() => onCompleted({ ...task, is_completed: true })}>
      <div className="boss-result">
        <div className="boss-result-mark"><Trophy /></div>
        <div className="modal-kicker">TEST LOGGED</div>
        <h2>{result.composite_label} {result.composite}</h2>
        {result.delta != null && <p className={`boss-delta ${up ? 'up' : result.delta < 0 ? 'down' : ''}`}>
          {up ? '▲' : result.delta < 0 ? '▼' : '—'} {Math.abs(result.delta)} point{Math.abs(result.delta) === 1 ? '' : 's'} vs your last {result.composite_label.toLowerCase()}
        </p>}
        <div className="boss-sections">
          {Object.entries(result.sections).map(([key, value]) => <div key={key}>
            <small>{(detail?.sections.find(s => s.key === key)?.label) || key}</small><b>{value}</b>
          </div>)}
        </div>
        {result.xp_earned > 0 && <div className="player-xp-award"><Zap /> +{result.xp_earned} XP</div>}
        <p className="boss-note">Your scores are saved to your stats and tracker, and your next path will be built around whichever section moved least.</p>
        <button className="button button--primary task-start" onClick={() => onCompleted({ ...task, is_completed: true })}>Build on this <ArrowRight /></button>
      </div>
    </Modal>
  }

  return <Modal onClose={onClose}>
    <div className="modal-kicker">BOSS BATTLE · {detail?.test_type || 'Official test'}</div>
    <h2>Take a full official test, then log the score.</h2>

    <div className="task-kind task-kind--boss_battle">
      <span className="task-kind-icon"><Trophy /></span>
      <div><b>Timed and official</b><p>Everything this unit drilled in short bursts, under real pacing and fatigue.</p></div>
      {task.xp_reward ? <span className="task-kind-xp"><Zap /> {task.xp_reward} XP</span> : null}
    </div>

    <ol className="boss-steps">
      <li><span>1</span><div><b>Sit the test</b><p>Full length, timed, no interruptions — the score only means something if the conditions are real.</p>
        <a className="button button--primary task-start" href={link} target="_blank" rel="noreferrer">Open official practice <ArrowRight /></a></div></li>
      <li><span>2</span><div><b>Log your section scores</b><p>Enter what you actually scored. This is what tells Mentics which section to attack next.</p>
        {detail ? <div className="boss-score-grid">
          {detail.sections.map(s => <label key={s.key}>
            {s.label}
            <input type="number" inputMode="numeric" min={s.min} max={s.max} value={scores[s.key] ?? ''}
              onChange={e => setScores(v => ({ ...v, [s.key]: e.target.value }))} placeholder={`${s.min}–${s.max}`} />
            {s.previous ? <em>last: {s.previous}</em> : null}
          </label>)}
        </div> : <div className="boss-score-grid boss-score-grid--loading"><span className="skeleton" /><span className="skeleton" /></div>}
      </div></li>
    </ol>

    {error && <p className="form-error">{error}</p>}
    <button className="button button--primary task-start" disabled={!ready || busy} onClick={submit}>
      {busy ? 'Saving…' : 'Log my score and finish'} <Check />
    </button>
    <p className="boss-note">You need a real score to finish this step — it is what the next path is built from.</p>
  </Modal>
}

// A college unit ends in real work rather than a practice test. The number the
// student records here is the evidence it happened, and it is what the next
// unit is planned against.
function MilestoneStep({ task, onClose, onCompleted }) {
  const [detail, setDetail] = useState(null)
  const [value, setValue] = useState('')
  const [result, setResult] = useState(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    let live = true
    api(`/api/milestone/${task.id}`).then(d => {
      if (!live) return
      setDetail(d)
      if (d.previous != null) setValue(String(d.previous))
    }).catch(e => { if (live) setError(e.message) })
    return () => { live = false }
  }, [task.id])

  const needsValue = Boolean(detail?.stat_name)
  const ready = detail && (!needsValue || String(value).trim() !== '')

  const submit = async () => {
    setBusy(true); setError('')
    try {
      setResult(await api(`/api/milestone/${task.id}/result`, { method: 'POST', body: JSON.stringify({ value: needsValue ? value : null }) }))
    } catch (e) { setError(e.message) } finally { setBusy(false) }
  }

  if (result) {
    const up = result.delta != null && result.delta > 0
    return <Modal onClose={() => onCompleted({ ...task, is_completed: true })}>
      <div className="boss-result">
        <div className="boss-result-mark boss-result-mark--milestone"><Award /></div>
        <div className="modal-kicker">MILESTONE COMPLETE</div>
        <h2>{result.value != null ? `${result.value} ${result.unit || ''}`.trim() : 'Logged'}</h2>
        {up && <p className="boss-delta up">▲ {result.delta} more than last time</p>}
        {result.xp_earned > 0 && <div className="player-xp-award"><Zap /> +{result.xp_earned} XP</div>}
        <p className="boss-note">Saved to your stats and tracker. Your next unit is planned from where this leaves you.</p>
        <button className="button button--primary task-start" onClick={() => onCompleted({ ...task, is_completed: true })}>Keep going <ArrowRight /></button>
      </div>
    </Modal>
  }

  return <Modal onClose={onClose}>
    <div className="modal-kicker">COLLEGE PLANNING · MILESTONE</div>
    <h2><PlainText value={task.description} /></h2>

    <div className="task-kind task-kind--milestone">
      <span className="task-kind-icon"><Award /></span>
      <div><b>Real work</b><p>This is the part an admissions officer actually sees. The unit taught the judgement; now produce the thing.</p></div>
      {task.xp_reward ? <span className="task-kind-xp"><Zap /> {task.xp_reward} XP</span> : null}
    </div>

    {detail?.objective && <p className="task-objective"><Target /> {detail.objective}</p>}
    {task.reason && <div className="task-why"><small>WHY THIS STEP</small><Markdown>{task.reason}</Markdown></div>}

    {needsValue && <div className="milestone-log">
      <label>{detail.label}
        {detail.stat_name === 'essay_progress'
          ? <select value={value} onChange={e => setValue(e.target.value)}>
            <option value="">Choose one…</option>
            <option value="1">First full draft done</option>
            <option value="2">Revised and final</option>
          </select>
          : <input type="number" inputMode="numeric" min={detail.min} max={detail.max} value={value}
            onChange={e => setValue(e.target.value)} placeholder={`${detail.min}–${detail.max}`} />}
      </label>
      {detail.previous != null && <em>Last recorded: {detail.previous}</em>}
    </div>}

    {error && <p className="form-error">{error}</p>}
    <button className="button button--primary task-start" disabled={!ready || busy} onClick={submit}>
      {busy ? 'Saving…' : needsValue ? 'Log it and finish' : 'Mark this done'} <Check />
    </button>
  </Modal>
}

function CollegeReportStep({ task, onClose, onReported }) {
  const [report, setReport] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const submit = async e => {
    e.preventDefault(); if (busy || report.trim().length < 20) return
    setBusy(true); setError('')
    try {
      const result = await api('/api/college_task_report', { method: 'POST', body: JSON.stringify({ taskId: task.id, report }) })
      toast.success('Mentics updated your next step')
      onReported(result.tasks || [])
    } catch (cause) { setError(cause.message) } finally { setBusy(false) }
  }
  return <Modal onClose={onClose} label="Report back to Mentics">
    <div className="modal-kicker">COLLEGE COACHING LOOP</div>
    <h2>{task.description}</h2>
    <p className="milestone-copy">Do the real work, then tell Mentics what happened. Your report—not a quiz—shapes the next lesson and assignment.</p>
    {task.objective && <div className="task-why"><small>YOUR ASSIGNMENT</small><Markdown>{task.objective}</Markdown></div>}
    <form className="modal-form college-report-form" onSubmit={submit}>
      <label>What did you do, what did you produce, and what felt difficult?
        <textarea autoFocus value={report} onChange={e => setReport(e.target.value)} minLength={20} maxLength={4000} placeholder="Example: I compared three colleges on cost and engineering opportunities. Two feel like a fit, but I need help deciding whether the third belongs on my list." disabled={busy} />
      </label>
      {error && <p className="form-error" role="alert">{error}</p>}
      <button className="button button--primary task-start" disabled={busy || report.trim().length < 20}>{busy ? 'Updating your path…' : 'Report back and continue'} <ArrowRight /></button>
    </form>
  </Modal>
}

function TaskModal({ task, category, onClose, onUpdate, onCompleted, onReported }) {
  const [note, setNote] = useState(''); const [busy, setBusy] = useState(false); const [playing, setPlaying] = useState(false); const [dueDate, setDueDate] = useState(task.due_date || ''); const [statPrompt, setStatPrompt] = useState(false); const [statValue, setStatValue] = useState(''); const [error, setError] = useState(''); const [detailsOpen, setDetailsOpen] = useState(false)
  const stat = milestoneStats[task.stat_to_update]
  const kind = taskKind(task)
  const meta = kind ? nodeKinds[kind] : null
  const complete = async () => { setBusy(true); setError(''); try { await api('/api/update_task_status', { method: 'POST', body: JSON.stringify({ taskId: task.id, status: 'complete' }) }); const next = { ...task, is_completed: true }; onUpdate(next); if (stat) setStatPrompt(true); else onCompleted(next) } catch (e) { setError(e.message) } finally { setBusy(false) } }
  const finishMilestone = async (save) => { setBusy(true); setError(''); try { if (save) await api('/api/update_stats', { method: 'POST', body: JSON.stringify({ stat_name: task.stat_to_update, stat_value: statValue }) }); onCompleted({ ...task, is_completed: true }) } catch (e) { setError(e.message) } finally { setBusy(false) } }
  const addNote = async () => { if (!note.trim() || busy) return; setBusy(true); setError(''); try { const r = await api('/api/add_subtask', { method: 'POST', body: JSON.stringify({ parent_task_id: task.id, description: note }) }); onUpdate({ ...task, subtasks: [...task.subtasks, r.subtask] }); setNote('') } catch (e) { setError(e.message) } finally { setBusy(false) } }
  const toggleNote = async (s) => { if (busy) return; setBusy(true); setError(''); try { await api('/api/update_subtask', { method: 'POST', body: JSON.stringify({ subtaskId: s.id, is_completed: !s.is_completed }) }); onUpdate({ ...task, subtasks: task.subtasks.map(x => x.id === s.id ? { ...x, is_completed: !x.is_completed } : x) }) } catch (e) { setError(e.message) } finally { setBusy(false) } }
  const saveDeadline = async () => { try { await api('/api/update_task_deadline', { method: 'POST', body: JSON.stringify({ taskId: task.id, dueDate: dueDate || null }) }); onUpdate({ ...task, due_date: dueDate || null }); toast.success('Target date saved') } catch (e) { toast.error('Could not save the target date', { description: e.message }) } }
  const skipTask = async () => { setBusy(true); setError(''); try { await api('/api/skip_task', { method: 'POST', body: JSON.stringify({ taskId: task.id }) }); const next = { ...task, is_completed: true, is_skipped: true }; onUpdate(next); onCompleted(next) } catch (e) { setError(e.message) } finally { setBusy(false) } }

  // Finishing the activity is what completes the step. The student does not have
  // to separately remember to tick a box.
  const finishPlay = async () => {
    setPlaying(false)
    if (task.is_completed) { onClose(); return }
    const next = { ...task, is_completed: true }; onUpdate(next)
    if (stat) setStatPrompt(true); else onCompleted(next)
  }

  // A boss battle has its own flow: sit the official test, then log real
  // section scores. It is the only step that cannot be "marked complete".
  if (kind === 'boss_battle' && !task.is_completed) return <BossBattle task={task} onClose={onClose} onCompleted={onCompleted} />
  if (kind === 'milestone' && category === 'College Planning' && !task.is_completed) return <CollegeReportStep task={task} onClose={onClose} onReported={onReported} />
  if (kind === 'milestone' && !task.is_completed) return <MilestoneStep task={task} onClose={onClose} onCompleted={onCompleted} />
  if (playing && kind === 'lesson') return <LessonPlayer task={task} onClose={() => setPlaying(false)} onCompleted={finishPlay} />
  if (playing) return <AssessmentPlayer task={task} onClose={() => setPlaying(false)} onCompleted={finishPlay} />

  if (statPrompt) return <Modal onClose={() => finishMilestone(false)}><div className="milestone-mark"><Trophy /></div><div className="modal-kicker">MILESTONE COMPLETE</div><h2>Record the progress behind the win.</h2><p className="milestone-copy">This keeps your stats, tracker, and next path grounded in what actually changed.</p><label className="milestone-input">{stat.label}<input autoFocus type="number" value={statValue} onChange={e => setStatValue(e.target.value)} placeholder={stat.placeholder} min={stat.min} max={stat.max} step={stat.step || 1} /></label>{error && <p className="form-error">{error}</p>}<div className="modal-actions"><button className="button button--quiet" onClick={() => finishMilestone(false)} disabled={busy}>Skip for now</button><button className="button button--primary" onClick={() => finishMilestone(true)} disabled={busy || statValue === ''}>Save progress <ArrowRight /></button></div></Modal>

  const Icon = meta?.icon
  const bossLink = kind === 'boss_battle' ? (firstLink(task.description) || 'https://satsuite.collegeboard.org/sat/practice-preparation/practice-tests') : null
  const playable = ['lesson', 'practice_sprint', 'quiz'].includes(kind)

  return <Modal onClose={onClose} label={`${meta?.label || 'Task'} details`}>
    <div className="modal-kicker">{category} · {meta ? meta.label : task.type === 'milestone' ? 'Milestone' : 'Action step'}{task.skill_label ? ` · ${task.skill_label}` : ''}</div>
    <h2><PlainText value={task.description} /></h2>
    {task.objective && <p className="task-objective"><Target /> {task.objective}</p>}

    {meta && <div className={`task-kind task-kind--${kind}`}>
      <span className="task-kind-icon"><Icon /></span>
      <div><b>{meta.label}</b><p>{meta.blurb}</p></div>
      {task.xp_reward ? <span className="task-kind-xp"><Zap /> {task.xp_reward} XP</span> : null}
    </div>}

    {/* The primary action sits directly under the description so there is exactly
        one obvious thing to do next. */}
    <div className="task-primary">
      {playable && <button className="button button--primary task-start" onClick={() => setPlaying(true)} disabled={busy}>
        {task.is_completed ? 'Practice again' : meta.cta} <ArrowRight />
      </button>}
      {kind === 'boss_battle' && <a className="button button--primary task-start" href={bossLink} target="_blank" rel="noreferrer">
        {meta.cta} <ArrowRight />
      </a>}
      {!playable && kind !== 'boss_battle' && <button className="button button--primary task-start" onClick={complete} disabled={busy || task.is_completed}>
        {task.is_completed ? 'Completed' : 'Mark complete'} <Check />
      </button>}
    </div>

    {/* Paths built before the lesson engine keep their guide in a separate article. */}
    {!task.node_type && task.secondary_content_id && <a className="button button--quiet task-legacy-guide" href={`/strategy_article/${task.id}`} target="_blank" rel="noreferrer"><BookOpen /> Strategy guide</a>}
    {task.reason && <div className="task-why"><small>WHY THIS STEP</small><Markdown>{task.reason}</Markdown></div>}
    {error && <p className="form-error">{error}</p>}

    <button className="task-more" onClick={() => setDetailsOpen(o => !o)} aria-expanded={detailsOpen}>
      {detailsOpen ? 'Hide' : 'Notes, target date, and other options'}
    </button>
    {detailsOpen && <div className="task-details">
      <div className="task-deadline"><label>Target date<input type="date" value={dueDate} onChange={e => setDueDate(e.target.value)} /></label><button onClick={saveDeadline}>Save date</button></div>
      <div className="task-notes"><label>Notes and sub-steps</label>{task.subtasks.map(s => <button key={s.id} className={s.is_completed ? 'checked' : ''} onClick={() => toggleNote(s)} disabled={busy}><span>{s.is_completed && <Check />}</span>{s.description}</button>)}<div><input value={note} onChange={e => setNote(e.target.value)} onKeyDown={e => e.key === 'Enter' && addNote()} placeholder="Add a note or smaller step" disabled={busy} /><button onClick={addNote} disabled={busy || !note.trim()} aria-label="Add note or sub-step"><Plus /></button></div></div>
      <div className="modal-actions">
        {(kind === 'boss_battle' || !playable) && !task.is_completed && <button className="button button--quiet" onClick={complete} disabled={busy}>Mark complete <Check /></button>}
        {playable && !task.is_skipped && !task.is_completed && <button className="button button--quiet" onClick={skipTask} disabled={busy}>Skip this step</button>}
      </div>
    </div>}
  </Modal>
}

function AddTask({ category, onClose, onAdded }) { const [description, setDescription] = useState(''); const [date, setDate] = useState(''); const [error, setError] = useState(''); const [busy, setBusy] = useState(false); const submit = async e => { e.preventDefault(); if (busy) return; setBusy(true); setError(''); try { const r = await api('/api/add_task', { method: 'POST', body: JSON.stringify({ description, category, due_date: date || null }) }); onAdded(r.task) } catch (x) { setError(x.message) } finally { setBusy(false) } }; return <Modal onClose={onClose} label="Add a personal step"><div className="modal-kicker">ADD A PERSONAL STEP</div><h2>Make the path yours.</h2><form className="modal-form" onSubmit={submit}><label>What do you want to do?<textarea autoFocus value={description} onChange={e => setDescription(e.target.value)} placeholder="Write a clear, finishable action" maxLength={500} disabled={busy} /></label><label>Due date <span>optional</span><input type="date" value={date} onChange={e => setDate(e.target.value)} disabled={busy} /></label>{error && <p className="form-error" role="alert">{error}</p>}<button className="button button--primary" disabled={busy || !description.trim()}>{busy ? 'Adding…' : 'Add to path'} <ArrowRight /></button></form></Modal> }

// --- Duolingo-style player -------------------------------------------------
// One step on screen at a time, an answer graded the moment it is given, and a
// missed item pushed back into the queue so the session cannot end until the
// student has actually got it right.

const START_HEARTS = 5
const REFILL_HEARTS = 2

function PlayerShell({ kicker, progress, hearts, xp, onClose, children }) {
  return createPortal(
    <div className="player-wrap" role="dialog" aria-modal="true">
      <div className="player">
        <header className="player-bar">
          <button className="player-quit" onClick={onClose} aria-label="Leave"><X /></button>
          <div className="player-progress" role="progressbar" aria-valuenow={Math.round(progress * 100)} aria-valuemin={0} aria-valuemax={100}>
            <span style={{ width: `${Math.max(2, Math.round(progress * 100))}%` }} />
          </div>
          {hearts != null && <div className={`player-hearts ${hearts <= 1 ? 'low' : ''}`} aria-label={`${hearts} hearts left`}>
            <Flame /> <b>{hearts}</b>
          </div>}
          <div className="player-xp" aria-label={`${xp} XP this session`}><Zap /> <b>{xp}</b></div>
        </header>
        <div className="player-body">
          {kicker && <div className="player-kicker">{kicker}</div>}
          {children}
        </div>
      </div>
    </div>, document.body)
}

function CoachBox({ kind, refId, seed }) {
  const [open, setOpen] = useState(false)
  const [question, setQuestion] = useState('')
  const [reply, setReply] = useState('')
  const [busy, setBusy] = useState(false)
  const ask = async (text) => {
    setBusy(true); setReply('')
    try {
      const r = await api('/api/coach', { method: 'POST', body: JSON.stringify({ kind, ref_id: refId, message: text }) })
      setReply(r.reply)
    } catch (e) { setReply(e.message) } finally { setBusy(false); setQuestion('') }
  }
  if (!open) return <button className="coach-open" onClick={() => { setOpen(true); if (!reply) ask(seed || 'Explain this to me another way.') }}>
    <Sparkles /> Ask Mentics about this
  </button>
  return <div className="coach-box">
    <div className="coach-head"><span><Sparkles /> Mentics tutor</span><button onClick={() => setOpen(false)} aria-label="Close tutor"><X /></button></div>
    {busy && !reply ? <div className="coach-thinking"><i /><i /><i /></div> : <Markdown>{reply}</Markdown>}
    <form onSubmit={e => { e.preventDefault(); if (question.trim() && !busy) ask(question.trim()) }}>
      <input value={question} onChange={e => setQuestion(e.target.value)} placeholder="Ask a follow-up about this step…" maxLength={600} />
      <button disabled={!question.trim() || busy} aria-label="Send"><Send /></button>
    </form>
  </div>
}

function TeachStep({ step, onNext, isLast }) {
  return <div className="teach-step">
    <h3>{step.title}</h3>
    <Markdown>{step.body}</Markdown>
    {step.worked_example && <div className="teach-example">
      <small>WORKED EXAMPLE</small>
      <Markdown>{step.worked_example}</Markdown>
    </div>}
    {step.takeaway && <div className="teach-takeaway"><Target /> <p>{step.takeaway}</p></div>}
    {step.trap && <div className="teach-trap"><Hand /> <p><b>Watch out.</b> {step.trap}</p></div>}
    <CoachBox kind="lesson_step" refId={step.id} seed="Explain this card in a different way, with another example." />
    <div className="player-actions">
      <button className="button button--primary player-cta" onClick={onNext}>{isLast ? 'Finish' : 'Got it'} <ArrowRight /></button>
    </div>
  </div>
}

function CheckStep({ step, coachKind, feedback, selected, onSelect, onCheck, onContinue, busy, replay }) {
  const letters = ['A', 'B', 'C', 'D', 'E', 'F']
  return <div className={`check-step ${feedback ? (feedback.is_correct ? 'is-right' : 'is-wrong') : ''}`}>
    {replay && <div className="check-replay"><RotateCcw /> Second look — you missed this one earlier.</div>}
    {step.source_or_prompt && <div className="check-source"><small>PASSAGE / SETUP</small><Markdown>{step.source_or_prompt}</Markdown></div>}
    <p className="check-question">{step.question_text}</p>
    <div className="check-options">
      {(step.options || []).map((option, index) => {
        const state = !feedback ? (selected === index ? 'picked' : '')
          : index === feedback.correct_option ? 'right'
            : selected === index ? 'wrong' : ''
        return <button key={index} className={`check-option ${state}`} disabled={Boolean(feedback) || busy} onClick={() => onSelect(index)}>
          <i>{letters[index]}</i><span>{option}</span>
        </button>
      })}
    </div>
    {feedback && <div className="check-feedback">
      <h4>{feedback.is_correct ? 'Correct.' : 'Not quite.'}</h4>
      <Markdown>{feedback.explanation}</Markdown>
      <CoachBox kind={coachKind} refId={step.id} seed="Why is that the right answer? Walk me through it." />
    </div>}
    <div className="player-actions">
      {feedback
        ? <button className="button button--primary player-cta" onClick={onContinue}>Continue <ArrowRight /></button>
        : <button className="button button--primary player-cta" disabled={selected == null || busy} onClick={onCheck}>{busy ? 'Checking…' : 'Check'}</button>}
    </div>
  </div>
}

function PlayerDone({ title, correct, total, xp, note, onClose }) {
  const accuracy = total ? Math.round(correct / total * 100) : null
  return <div className="player-done">
    <div className="player-done-mark"><Trophy /></div>
    <h2>{title}</h2>
    {accuracy != null && <p className="player-score">{correct} of {total} correct <span>{accuracy}%</span></p>}
    {xp > 0 && <div className="player-xp-award"><Zap /> +{xp} XP</div>}
    {note && <div className="player-recap"><Markdown>{note}</Markdown></div>}
    <button className="button button--primary player-cta" onClick={onClose}>Back to your path <ArrowRight /></button>
  </div>
}

function OutOfHearts({ missed, onContinue }) {
  return <div className="player-refill">
    <h2>Let's reset for a second.</h2>
    <p>You missed a few. Read these back, then keep going — the questions you missed are still in the queue.</p>
    <div className="refill-list">
      {missed.map((item, index) => <div key={index} className="refill-item">
        <p className="refill-question">{item.question_text}</p>
        <Markdown>{item.explanation}</Markdown>
      </div>)}
    </div>
    <button className="button button--primary player-cta" onClick={onContinue}>I'm ready <ArrowRight /></button>
  </div>
}

// Shared queue mechanics for both drivers: a missed item is re-queued, and the
// run is only finished when the queue is exhausted. The run components mount
// only once their content has loaded, so the queue initialises from a real
// length and never has to reset itself.
function useStepQueue(length) {
  const [queue, setQueue] = useState(() => Array.from({ length }, (_, i) => i))
  const [cursor, setCursor] = useState(0)
  return {
    queue, cursor,
    requeue: (index) => setQueue(q => [...q, index]),
    advance: () => setCursor(c => c + 1),
    progress: queue.length ? cursor / queue.length : 0,
    done: cursor >= queue.length,
  }
}

// Hearts, XP, and the missed-item log behave identically in a lesson and in a
// drill, so both runs share one piece of state.
function useRunState() {
  const [hearts, setHearts] = useState(START_HEARTS)
  const [xp, setXp] = useState(0)
  const [missed, setMissed] = useState([])
  const [refill, setRefill] = useState(false)
  const [selected, setSelected] = useState(null)
  const [feedback, setFeedback] = useState(null)
  const [busy, setBusy] = useState(false)
  const registerWrong = (item) => {
    setMissed(m => [...m, item])
    setHearts(h => Math.max(0, h - 1))
  }
  const clearStep = () => { setSelected(null); setFeedback(null) }
  return {
    hearts, setHearts, xp, setXp, missed, refill, setRefill,
    selected, setSelected, feedback, setFeedback, busy, setBusy,
    registerWrong, clearStep,
  }
}

function PlayerLoading({ onClose }) {
  return <PlayerShell progress={0} xp={0} onClose={onClose}>
    <div className="player-loading"><span className="skeleton" /><span className="skeleton" /><span className="skeleton" /></div>
  </PlayerShell>
}

function PlayerError({ title, message, onClose }) {
  return <PlayerShell progress={0} xp={0} onClose={onClose}>
    <div className="player-error"><h2>{title}</h2><p>{message}</p>
      <button className="button button--primary player-cta" onClick={onClose}>Back to your path</button></div>
  </PlayerShell>
}

function useContent(url, deps) {
  const [data, setData] = useState(null)
  const [error, setError] = useState('')
  useEffect(() => {
    let live = true
    api(url).then(d => { if (live) setData(d) }).catch(e => { if (live) setError(e.message) })
    return () => { live = false }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps)
  return { data, error }
}

function LessonPlayer({ task, onClose, onCompleted }) {
  const { data, error } = useContent(`/api/lesson/${task.id}`, [task.id])
  if (error) return <PlayerError title="This lesson could not open." message={error} onClose={onClose} />
  if (!data) return <PlayerLoading onClose={onClose} />
  return <LessonRun key={data.lesson_id} lesson={data} task={task} onClose={onClose} onCompleted={onCompleted} />
}

function LessonRun({ lesson, task, onClose, onCompleted }) {
  const steps = lesson.steps || []
  const run = useRunState()
  const [summary, setSummary] = useState(null)
  const { queue, cursor, requeue, advance, progress, done } = useStepQueue(steps.length)

  useEffect(() => {
    if (done) return
    api(`/api/lesson/${task.id}/progress`, { method: 'POST', body: JSON.stringify({ current_step: cursor }) }).catch(() => { })
  }, [cursor, task.id, done])

  useEffect(() => {
    if (!done || summary) return
    let live = true
    api(`/api/lesson/${task.id}/finish`, { method: 'POST', body: JSON.stringify({}) })
      .then(r => { if (live) setSummary(r) })
      .catch(e => { if (live) setSummary({ correct: 0, total: 0, xp_earned: 0, recap: '', error: e.message }) })
    return () => { live = false }
  }, [done, summary, task.id])

  if (summary) return <PlayerShell progress={1} hearts={run.hearts} xp={run.xp} onClose={onClose}>
    <PlayerDone title="Lesson complete." correct={summary.correct} total={summary.total}
      xp={summary.xp_earned || 0} note={summary.recap} onClose={() => onCompleted(summary)} />
  </PlayerShell>

  if (run.refill) return <PlayerShell progress={progress} hearts={run.hearts} xp={run.xp} onClose={onClose}>
    <OutOfHearts missed={run.missed.slice(-3)} onContinue={() => { run.setHearts(REFILL_HEARTS); run.setRefill(false) }} />
  </PlayerShell>

  const index = queue[cursor]
  const step = steps[index]
  if (!step) return <PlayerLoading onClose={onClose} />

  const checkAnswer = async () => {
    run.setBusy(true)
    try {
      const r = await api(`/api/lesson/${task.id}/answer`, {
        method: 'POST', body: JSON.stringify({ step_id: step.id, selected_option: run.selected })
      })
      run.setFeedback(r)
      if (r.is_correct) run.setXp(x => x + 5)
      else { requeue(index); run.registerWrong({ question_text: step.question_text, explanation: r.explanation }) }
    } catch (e) { toast.error('Could not check that answer', { description: e.message }) } finally { run.setBusy(false) }
  }

  const next = () => {
    const wasWrong = run.feedback && !run.feedback.is_correct
    run.clearStep(); advance()
    if (wasWrong && run.hearts <= 1) run.setRefill(true)
  }

  return <PlayerShell kicker={`${lesson.skill_label || lesson.subject} · Lesson`} progress={progress}
    hearts={run.hearts} xp={run.xp} onClose={onClose}>
    {cursor === 0 && lesson.intro && step.step_type !== 'check' && <div className="lesson-intro">
      {lesson.objective && <span className="lesson-objective"><Target /> {lesson.objective}</span>}
      <Markdown>{lesson.intro}</Markdown>
    </div>}
    {step.step_type === 'check'
      ? <CheckStep step={step} coachKind="lesson_step" feedback={run.feedback} selected={run.selected}
        busy={run.busy} replay={cursor >= steps.length} onSelect={run.setSelected}
        onCheck={checkAnswer} onContinue={next} />
      : <TeachStep step={step} isLast={cursor === queue.length - 1} onNext={next} />}
  </PlayerShell>
}

function AssessmentPlayer({ task, onClose, onCompleted }) {
  const kind = task.task_format === 'quiz' ? 'quiz' : 'sprint'
  const url = kind === 'quiz' ? `/api/quiz/${task.id}` : `/api/practice_sprint/${task.id}`
  const { data, error } = useContent(url, [task.id, kind])
  if (error) return <PlayerError title="This activity could not open." message={error} onClose={onClose} />
  if (!data) return <PlayerLoading onClose={onClose} />
  return <AssessmentRun key={task.id} data={data} kind={kind} task={task} onClose={onClose} onCompleted={onCompleted} />
}

function AssessmentRun({ data, kind, task, onClose, onCompleted }) {
  const questions = data.questions || []
  const run = useRunState()
  const [tally, setTally] = useState({ correct: 0, total: 0 })
  const [summary, setSummary] = useState(null)
  const { queue, cursor, requeue, advance, progress, done } = useStepQueue(questions.length)

  useEffect(() => {
    if (!done || summary) return
    let live = true
    api('/api/assessment/finish', { method: 'POST', body: JSON.stringify({ task_id: task.id }) })
      .then(r => { if (live) setSummary(r) })
      .catch(() => { if (live) setSummary({ xp_earned: 0 }) })
    return () => { live = false }
  }, [done, summary, task.id])

  if (summary) return <PlayerShell progress={1} hearts={run.hearts} xp={run.xp} onClose={onClose}>
    <PlayerDone title={kind === 'quiz' ? 'Review complete.' : 'Practice complete.'}
      correct={tally.correct} total={tally.total} xp={summary.xp_earned || 0}
      note={tally.total && tally.correct / tally.total < 0.7
        ? 'That accuracy says this skill needs another pass. Your next path will build on exactly what you missed here.'
        : 'Strong run. Mentics logged which sub-skills held up, so the next unit can move you forward.'}
      onClose={() => onCompleted(summary)} />
  </PlayerShell>

  if (run.refill) return <PlayerShell progress={progress} hearts={run.hearts} xp={run.xp} onClose={onClose}>
    <OutOfHearts missed={run.missed.slice(-3)} onContinue={() => { run.setHearts(REFILL_HEARTS); run.setRefill(false) }} />
  </PlayerShell>

  const index = queue[cursor]
  const question = questions[index]
  if (!question) return <PlayerLoading onClose={onClose} />

  const checkAnswer = async () => {
    run.setBusy(true)
    try {
      const r = await api('/api/assessment/answer', {
        method: 'POST', body: JSON.stringify({ kind, question_id: question.id, selected_option: run.selected })
      })
      run.setFeedback(r)
      setTally(t => ({ correct: t.correct + (r.is_correct ? 1 : 0), total: t.total + 1 }))
      if (r.is_correct) run.setXp(x => x + 5)
      else { requeue(index); run.registerWrong({ question_text: question.question_text, explanation: r.explanation }) }
    } catch (e) { toast.error('Could not check that answer', { description: e.message }) } finally { run.setBusy(false) }
  }

  const next = () => {
    const wasWrong = run.feedback && !run.feedback.is_correct
    run.clearStep(); advance()
    if (wasWrong && run.hearts <= 1) run.setRefill(true)
  }

  return <PlayerShell kicker={`${data.title} · ${kind === 'quiz' ? 'Review' : 'Practice'}`} progress={progress}
    hearts={run.hearts} xp={run.xp} onClose={onClose}>
    <CheckStep step={question} coachKind={kind} feedback={run.feedback} selected={run.selected}
      busy={run.busy} replay={cursor >= questions.length} onSelect={run.setSelected}
      onCheck={checkAnswer} onContinue={next} />
  </PlayerShell>
}

function EssayCoach({ onClose }) { const [prompt, setPrompt] = useState(''); const [essay, setEssay] = useState(''); const [feedback, setFeedback] = useState(''); const [busy, setBusy] = useState(false); const analyze = async () => { if (essay.trim().length < 50) return; setBusy(true); try { setFeedback((await api('/api/analyze_essay', { method: 'POST', body: JSON.stringify({ essay_text: essay, essay_prompt: prompt || 'a general college application essay' }) })).feedback) } catch (e) { setFeedback(e.message) } finally { setBusy(false) } }; return <Modal onClose={onClose} wide><div className="modal-kicker">MENTICS ESSAY COACH</div><h2>Strengthen the essay without losing your voice.</h2><div className="essay-workspace"><label>Essay prompt<input value={prompt} onChange={e => setPrompt(e.target.value)} placeholder="Common App prompt or supplemental question" /></label><label>Essay draft<textarea value={essay} onChange={e => setEssay(e.target.value)} rows="12" maxLength="20000" placeholder="Paste your draft here..." /></label><button className="button button--primary" onClick={analyze} disabled={busy || essay.trim().length < 50}>{busy ? 'Analyzing…' : 'Get structured feedback'} <Sparkles /></button>{feedback && <div className="essay-feedback"><Markdown>{feedback}</Markdown></div>}</div></Modal> }

// Starter prompts do real work: a blank chat gets asked nothing, and these name
// the things the guide is actually good at from where the student is standing.
const chatStarters = {
  'Test Prep': [
    { icon: Target, label: 'What should I focus on?' },
    { icon: Brain, label: 'Explain my weakest skill' },
    { icon: RotateCcw, label: 'Rebuild my path around math' },
    { icon: CalendarDays, label: 'Am I on pace for my test date?' },
  ],
  'College Planning': [
    { icon: Target, label: 'What should I do this month?' },
    { icon: GraduationCap, label: 'Is my college list balanced?' },
    { icon: PenLine, label: 'Help me start my personal statement' },
    { icon: RotateCcw, label: 'Rebuild my path around applications' },
  ],
}

function ChatPanel({ open, onClose, category, onNewPath }) {
  const [messages, setMessages] = useState([]); const [input, setInput] = useState(''); const [busy, setBusy] = useState(false); const [historyError, setHistoryError] = useState(''); const scroller = useRef(null); const composer = useRef(null)
  const starters = chatStarters[category] || chatStarters['Test Prep']
  const conversationStarted = messages.some(m => m.role === 'user')

  useEffect(() => { if (open && messages.length === 0) { api(`/api/chat_history?category=${encodeURIComponent(category)}`).then(h => setMessages(Array.isArray(h) && h.length ? h : [{ role: 'assistant', content: `I'm here with your ${category.toLowerCase()} path. Ask about any step, concept, or roadblock — I can see exactly where you are.` }])).catch(() => { setHistoryError('I could not restore the earlier conversation, but you can start a new one here.'); setMessages([{ role: 'assistant', content: `I'm ready to help with your ${category.toLowerCase()} path.` }]) }) } }, [open, category, messages.length])
  useEffect(() => { const node = scroller.current; if (node) node.scrollTo({ top: node.scrollHeight, behavior: 'smooth' }) }, [messages, busy])

  // The composer grows with the draft instead of scrolling a one-line box.
  useEffect(() => {
    const node = composer.current
    if (!node) return
    node.style.height = 'auto'
    node.style.height = `${Math.min(node.scrollHeight, 140)}px`
  }, [input])

  const ask = async (text) => {
    if (!text.trim() || busy) return
    const next = [...messages, { role: 'user', content: text.trim() }]
    setMessages(next); setInput(''); setBusy(true)
    try {
      const r = await api(`/api/chat?category=${encodeURIComponent(category)}`, { method: 'POST', body: JSON.stringify({ history: next }) })
      if (Object.prototype.hasOwnProperty.call(r, 'new_path')) {
        if (!Array.isArray(r.new_path) || r.new_path.length !== 5) throw new Error('Mentics could not build a complete five-step path. Your current path is unchanged.')
        onNewPath(r.new_path)
        setMessages([...next, { role: 'assistant', content: r.reply || 'Your new path is ready. I used our conversation to shape it.' }])
      } else setMessages([...next, { role: 'assistant', content: r.reply }])
    } catch (x) { setMessages([...next, { role: 'assistant', content: x.message }]) } finally { setBusy(false) }
  }

  const send = e => { e.preventDefault(); ask(input) }
  const reset = async () => { try { await api('/api/reset_chat', { method: 'POST', body: JSON.stringify({ category }) }); setHistoryError(''); setMessages([{ role: 'assistant', content: `Fresh start. What would you like help with on your ${category.toLowerCase()} path?` }]) } catch (error) { setHistoryError(error.message) } }

  return <aside className={`chat-panel ${open ? 'chat-panel--open' : ''}`} aria-hidden={!open} inert={!open || undefined}>
    <header className="chat-head">
      <span className="chat-identity">
        <span className="chat-wordmark">MENTICS</span>
        <span>
          <b>Path guide</b>
          <small><em className="chat-live" /> Here with your {category.toLowerCase()} path</small>
        </span>
      </span>
      <div className="chat-head-actions">
        <button onClick={reset} aria-label="Start a new conversation" title="New conversation"><RotateCcw /></button>
        <button onClick={onClose} aria-label="Close chat" title="Close"><X /></button>
      </div>
    </header>

    {historyError && <div className="chat-notice" role="status">{historyError}</div>}

    <div className="chat-messages" ref={scroller}>
      {messages.map((m, i) => <div className={`chat-message chat-message--${m.role}`} key={i}>
        {m.role === 'assistant' && <i className="chat-avatar" aria-hidden="true">M</i>}
        <div className="chat-bubble">{m.role === 'assistant' ? <Markdown>{m.content}</Markdown> : m.content}</div>
      </div>)}
      {busy && <div className="chat-message chat-message--assistant"><i className="chat-avatar" aria-hidden="true">M</i><div className="chat-bubble chat-bubble--thinking"><span /><span /><span /></div></div>}
      {!conversationStarted && !busy && <div className="chat-starters">
        <small>TRY ASKING</small>
        {starters.map(({ label }) => <button key={label} onClick={() => ask(label)}><span aria-hidden="true">→</span>{label}</button>)}
      </div>}
    </div>

    <form className="chat-composer" onSubmit={send}>
      <div className="chat-composer-field">
        <textarea ref={composer} name="message" aria-label={`Ask Mentics about your ${category.toLowerCase()} path`} value={input} onChange={e => setInput(e.target.value)} onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(e) } }} placeholder="Ask about your path…" rows={1} maxLength={4000} />
        <button disabled={!input.trim() || busy} aria-label="Send message"><Send /></button>
      </div>
      <p>Mentics can make mistakes. Check important information.</p>
    </form>
  </aside>
}

function PageIntro({ kicker, title, copy, actions }) {
  return <div className="page-intro page-intro--color"><div><div className="eyebrow"><span /> {kicker}</div><h1>{title}</h1>{copy && <p>{copy}</p>}</div>{actions && <div className="page-actions">{actions}</div>}</div>
}

function AuthPage({ mode }) {
  const signup = mode === 'signup'
  return <div className="auth-page"><div className="auth-brand"><Brand /></div><div className="auth-art"><span className="shape shape--peach" /><span className="shape shape--mint" /><div><small>YOUR NEXT CHAPTER</small><h1>Ambition feels better with a plan.</h1><p>Build momentum across test prep, college planning, and every goal between.</p></div></div><main className="auth-panel"><div className="auth-copy"><small>{signup ? 'START YOUR PATH' : 'WELCOME BACK'}</small><h2>{signup ? 'Join Mentics.' : 'Continue building.'}</h2><p>{signup ? 'Your focused workspace is a minute away.' : 'Your goals and progress are waiting.'}</p></div>{boot.data.error && <div className="form-error" role="alert">{boot.data.error}</div>}<form method="POST" className="react-form"><CsrfField />{signup && <label>Full name<input name="name" autoComplete="name" required maxLength="100" placeholder="Your name" /></label>}<label>Email address<input type="email" name="email" autoComplete="email" required placeholder="you@example.com" /></label><label>Password<input type="password" name="password" autoComplete={signup ? 'new-password' : 'current-password'} minLength={signup ? 8 : undefined} maxLength="128" required placeholder={signup ? 'At least 8 characters' : 'Your password'} /></label>{signup && <label className="legal-consent"><input type="checkbox" name="legal_acceptance" value="accepted" required /> <span>I agree to the <a href="/terms" target="_blank" rel="noreferrer">Terms of Service</a> and <a href="/privacy" target="_blank" rel="noreferrer">Privacy Policy</a>.</span></label>}<button className="button button--primary" type="submit">{signup ? 'Create my account' : 'Sign in'} <ArrowRight /></button></form><div className="form-divider"><span>or</span></div><a className="google-button" href="/google-login"><span>G</span> Continue with Google</a><p className="oauth-legal-notice">By continuing with Google, you agree to the <a href="/terms" target="_blank" rel="noreferrer">Terms of Service</a> and acknowledge the <a href="/privacy" target="_blank" rel="noreferrer">Privacy Policy</a>.</p><p className="auth-switch">{signup ? 'Already have an account?' : 'New to Mentics?'} <a href={signup ? '/login' : '/signup'}>{signup ? 'Sign in' : 'Create an account'}</a></p></main></div>
}

const learningOptions = [['visual', 'Visual', Sparkles, 'I learn by seeing'], ['auditory', 'Auditory', Headphones, 'I learn by hearing'], ['reading_writing', 'Reading / writing', PenLine, 'I learn through words'], ['kinesthetic', 'Hands-on', Hand, 'I learn by doing']]
function Onboarding() {
  const [step, setStep] = useState(0)
  const [goal, setGoal] = useState('')
  const [style, setStyle] = useState('')
  const [anxieties, setAnxieties] = useState('')
  const allowSubmit = useRef(false)
  const canNext = step === 0 ? goal : style

  const submitOnlyFromButton = event => {
    if (!allowSubmit.current) {
      event.preventDefault()
      return
    }
    allowSubmit.current = false
  }

  const finishOnboarding = event => {
    const form = event.currentTarget.form
    if (!form?.reportValidity()) return
    allowSubmit.current = true
    form.requestSubmit()
  }

  return <div className="onboarding-page"><header><Brand /><span>Step {step + 1} of 3</span></header><main><div className="onboarding-progress"><i style={{ width: `${(step + 1) / 3 * 100}%` }} /></div>{boot.data.error && <div className="form-error">{boot.data.error}</div>}<form method="POST" onSubmit={submitOnlyFromButton}><section className={step === 0 ? 'active' : ''}><div className="eyebrow"><span /> START WITH DIRECTION</div><h1>What are we building toward?</h1><p>This sets the first version of your Mentics workspace.</p><div className="choice-grid choice-grid--two">{[['test_prep', 'Test preparation', BookOpen, 'Build confidence for the SAT or ACT'], ['college_planning', 'College planning', GraduationCap, 'Turn applications into a clear process']].map(([value, label, Icon, copy]) => <label className={goal === value ? 'selected' : ''} key={value}><input type="radio" name="goal" value={value} required checked={goal === value} onChange={() => setGoal(value)} /><Icon /><b>{label}</b><small>{copy}</small></label>)}</div></section><section className={step === 1 ? 'active' : ''}><div className="eyebrow"><span /> MAKE IT YOURS</div><h1>How do you learn best?</h1><p>Your tasks and explanations will use this preference.</p><div className="choice-grid">{learningOptions.map(([value, label, Icon, copy]) => <label className={style === value ? 'selected' : ''} key={value}><input type="radio" name="learning_style" value={value} required checked={style === value} onChange={() => setStyle(value)} /><Icon /><b>{label}</b><small>{copy}</small></label>)}</div></section><section className={step === 2 ? 'active' : ''}><div className="eyebrow"><span /> ONE LAST THING</div><h1>What feels hardest right now?</h1><p>Be honest. This helps Mentics meet you where you are.</p><textarea name="anxieties" rows="6" value={anxieties} onChange={event => setAnxieties(event.target.value)} onKeyDown={event => event.stopPropagation()} placeholder="Time management, test anxiety, essays, choosing schools..." /></section><div className="onboarding-actions">{step > 0 ? <button type="button" className="button button--quiet" onClick={() => setStep(step - 1)}><ArrowLeft /> Back</button> : <span />}{step < 2 ? <button type="button" className="button button--primary" disabled={!canNext} onClick={() => setStep(step + 1)}>Continue <ArrowRight /></button> : <button type="button" className="button button--primary" onClick={finishOnboarding}>Build my workspace <ArrowRight /></button>}</div></form></main></div>
}

// --- Charts ---------------------------------------------------------------
// One series per chart, so identity never rides on color alone and no legend is
// needed: the title names the series. Grid and axes stay recessive; the value
// labels wear text tokens rather than the series color.

function niceScale(min, max) {
  if (!Number.isFinite(min) || !Number.isFinite(max)) return { lo: 0, hi: 1, ticks: [0, 1] }
  if (min === max) { const pad = Math.max(1, Math.abs(min) * .1); min -= pad; max += pad }
  const span = max - min
  const step = Math.pow(10, Math.floor(Math.log10(span / 4)))
  const norm = span / 4 / step
  const nice = (norm <= 1 ? 1 : norm <= 2 ? 2 : norm <= 5 ? 5 : 10) * step
  const lo = Math.floor(min / nice) * nice
  const hi = Math.ceil(max / nice) * nice
  const ticks = []
  for (let v = lo; v <= hi + nice / 2; v += nice) ticks.push(Math.round(v * 100) / 100)
  return { lo, hi, ticks }
}

function TrendChart({ records = [], label, height = 230 }) {
  const [hover, setHover] = useState(null)
  const wrap = useRef(null)
  const points = records.map(r => ({ date: String(r.date), value: Number(r.value) })).filter(p => Number.isFinite(p.value))

  if (points.length === 0) return <div className="chart-empty"><BarChart3 /><p>No data logged yet. Finish a boss battle or update your scores and this fills in.</p></div>

  const W = 720, H = height, padL = 46, padR = 18, padT = 16, padB = 30
  const values = points.map(p => p.value)
  const { lo, hi, ticks } = niceScale(Math.min(...values), Math.max(...values))
  const x = i => padL + (points.length === 1 ? (W - padL - padR) / 2 : i * (W - padL - padR) / (points.length - 1))
  const y = v => padT + (H - padT - padB) * (1 - (v - lo) / (hi - lo || 1))
  const line = points.map((p, i) => `${i ? 'L' : 'M'}${x(i).toFixed(1)},${y(p.value).toFixed(1)}`).join(' ')
  const area = `${line} L${x(points.length - 1).toFixed(1)},${H - padB} L${x(0).toFixed(1)},${H - padB} Z`
  const last = points[points.length - 1]
  const first = points[0]
  const change = points.length > 1 ? last.value - first.value : null

  const onMove = e => {
    const box = wrap.current?.getBoundingClientRect()
    if (!box) return
    const px = (e.clientX - box.left) / box.width * W
    let best = 0
    points.forEach((_, i) => { if (Math.abs(x(i) - px) < Math.abs(x(best) - px)) best = i })
    setHover(best)
  }

  return <div className="chart" ref={wrap} onMouseMove={onMove} onMouseLeave={() => setHover(null)}>
    <div className="chart-head">
      <div><small>{label}</small><strong>{last.value.toLocaleString()}</strong></div>
      {change != null && change !== 0 && <span className={`chart-change ${change > 0 ? 'up' : 'down'}`}>
        {change > 0 ? '▲' : '▼'} {Math.abs(Math.round(change * 100) / 100)} since {first.date.slice(5)}
      </span>}
    </div>
    <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label={`${label} over time, currently ${last.value}`} preserveAspectRatio="none" className="chart-svg">
      <defs>
        <linearGradient id="chart-fill" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="var(--viz-series-1)" stopOpacity=".18" />
          <stop offset="1" stopColor="var(--viz-series-1)" stopOpacity="0" />
        </linearGradient>
      </defs>
      {ticks.map(t => <g key={t}>
        <line className="chart-grid" x1={padL} x2={W - padR} y1={y(t)} y2={y(t)} />
        <text className="chart-tick" x={padL - 8} y={y(t)} textAnchor="end" dominantBaseline="middle">{t}</text>
      </g>)}
      {points.length > 1 && <path d={area} fill="url(#chart-fill)" />}
      <path d={line} className="chart-line" />
      {points.map((p, i) => (i === points.length - 1 || i === hover || points.length <= 8) &&
        <circle key={i} cx={x(i)} cy={y(p.value)} r={i === hover ? 6 : 4.5} className={`chart-dot ${i === hover ? 'active' : ''}`} />)}
      {hover != null && <line className="chart-crosshair" x1={x(hover)} x2={x(hover)} y1={padT} y2={H - padB} />}
      {points.map((p, i) => (i === 0 || i === points.length - 1) &&
        <text key={`d${i}`} className="chart-tick" x={x(i)} y={H - 10} textAnchor={i === 0 ? 'start' : 'end'}>{p.date.slice(5)}</text>)}
    </svg>
    {hover != null && <div className="chart-tip" style={{ left: `${x(hover) / W * 100}%` }}>
      <b>{points[hover].value.toLocaleString()}</b><small>{points[hover].date}</small>
    </div>}
  </div>
}

function MasteryRow({ skill, subject, accuracy, attempts, level }) {
  const tone = accuracy >= 85 ? 'strong' : accuracy >= 65 ? 'fair' : 'weak'
  return <li className={`mastery-row mastery-row--${tone}`}>
    <div className="mastery-label"><b>{skill}</b><small>{subject} · {attempts} question{attempts === 1 ? '' : 's'}</small></div>
    <div className="mastery-track"><i style={{ width: `${Math.max(4, accuracy)}%` }} /></div>
    <span className="mastery-value">{accuracy}%</span>
    <span className="mastery-level" title={`Mastery level ${level} of 5`}>{'●'.repeat(level)}{'○'.repeat(5 - level)}</span>
  </li>
}

function PathProgressCard({ title, snapshot, href, accent }) {
  if (!snapshot) return <article className={`path-card path-card--${accent} path-card--empty`}>
    <h3>{title}</h3><p>No path yet.</p>
    <a className="button button--quiet" href={href}>Build one <ArrowRight /></a>
  </article>
  const pct = snapshot.total ? Math.round(snapshot.completed / snapshot.total * 100) : 0
  return <article className={`path-card path-card--${accent}`}>
    <header><h3>{title}</h3><span>{snapshot.completed}/{snapshot.total}</span></header>
    {snapshot.unitTitle && <p className="path-card-unit">{snapshot.unitTitle}</p>}
    <div className="path-card-track"><i style={{ width: `${pct}%` }} /></div>
    <ol className="path-card-steps">
      {snapshot.steps.map(s => <li key={s.order} className={s.done ? 'done' : s.order === snapshot.currentStep ? 'current' : ''}>
        <i>{s.done ? <Check /> : s.order}</i>
        <span>{s.skill || s.nodeType || `Step ${s.order}`}</span>
      </li>)}
    </ol>
    <a className="button button--quiet" href={href}>{snapshot.currentStep ? 'Continue' : 'Open path'} <ArrowRight /></a>
  </article>
}

function GoalMeter({ label, current, goal, min }) {
  if (!current) return null
  const pct = goal && goal > min ? Math.min(100, Math.round((current - min) / (goal - min) * 100)) : null
  return <div className="goal-meter">
    <div><small>{label}</small><strong>{current}</strong>{goal ? <em>goal {goal}</em> : null}</div>
    {pct != null && <><div className="goal-track"><i style={{ width: `${pct}%` }} /></div>
      <span className="goal-caption">{pct >= 100 ? 'Goal reached' : `${goal - current} points to go`}</span></>}
  </div>
}

function StatsPage() {
  const d = boot.data
  const p = d.practice || {}
  const hasMastery = (d.weakest?.length || 0) > 0
  const score = value => value ?? '—'

  return <AppShell name={d.name}><main className="app-main">
    <PageIntro kicker="ACADEMIC PROFILE" title="Your progress, at a glance."
      copy="Your latest test scores, skill evidence, and next steps—kept in one clear view."
      actions={<a className="button button--primary" href="/dashboard/stats/edit">Update scores <ArrowRight /></a>} />

    <section className="score-overview" aria-label="Latest academic scores">
      <article className="score-card score-card--sat"><div><small>LATEST SAT</small><strong>{score(d.satTotal)}</strong><p>{d.satEbrw || d.satMath ? `R&W ${score(d.satEbrw)} · Math ${score(d.satMath)}` : 'Add your section scores'}</p></div><span>/ 1600</span></article>
      <article className="score-card score-card--act"><div><small>ACT COMPOSITE</small><strong>{score(d.actComposite || d.actAverage)}</strong><p>{d.actMath || d.actReading || d.actScience ? `Math ${score(d.actMath)} · Reading ${score(d.actReading)} · Science ${score(d.actScience)}` : 'Add your section scores'}</p></div><span>/ 36</span></article>
      <article className="score-card score-card--gpa"><div><small>CURRENT GPA</small><strong>{score(d.gpa)}</strong><p>Your academic foundation</p></div><span>PROFILE</span></article>
    </section>

    <section className="stat-tiles">
      <article className="stat-tile stat-tile--accent"><small>TOTAL XP</small><strong>{d.points.toLocaleString()}</strong><p>Earned from completed steps</p></article>
      <article className="stat-tile"><small>DAY STREAK</small><strong>{d.streak}<i><Flame /></i></strong><p>{d.streak > 0 ? 'Keep it alive today' : 'Finish a step to start one'}</p></article>
      <article className="stat-tile"><small>QUESTIONS ANSWERED</small><strong>{p.answered || 0}</strong><p>{p.accuracy != null ? `${p.accuracy}% correct overall` : 'Across lessons and practice'}</p></article>
      <article className="stat-tile"><small>TEST DATE</small><strong>{d.testDate ? new Date(`${d.testDate}T00:00:00`).toLocaleDateString(undefined, { month: 'short', day: 'numeric' }) : '—'}</strong><p>{d.testDate ? 'Your next scheduled test' : 'Set one in your test path'}</p></article>
    </section>

    <section className="stat-columns">
      <div className="stat-col">
        <h2 className="section-title">Where you stand</h2>
        <div className="goal-grid">
          <GoalMeter label="SAT total" current={d.satTotal} goal={d.goalSat} min={400} />
          <GoalMeter label="ACT composite" current={d.actAverage} goal={d.goalAct} min={1} />
        </div>
        <div className="section-scores">
          <span><small>SAT Reading &amp; Writing</small><b>{score(d.satEbrw)}</b></span>
          <span><small>SAT Math</small><b>{score(d.satMath)}</b></span>
          <span><small>ACT Math</small><b>{score(d.actMath)}</b></span>
          <span><small>ACT Reading</small><b>{score(d.actReading)}</b></span>
          <span><small>ACT Science</small><b>{score(d.actScience)}</b></span>
        </div>

        <h2 className="section-title">Skill mastery</h2>
        {hasMastery ? <>
          <p className="section-note">Measured from every question you have answered in Mentics. Your next path is built from the bottom of this list.</p>
          <ul className="mastery-list">
            {d.weakest.map(m => <MasteryRow key={m.skill} {...m} />)}
          </ul>
          {d.strongest?.length > 0 && <details className="mastery-more">
            <summary>Your strongest skills</summary>
            <ul className="mastery-list">{d.strongest.map(m => <MasteryRow key={m.skill} {...m} />)}</ul>
          </details>}
          {d.openMistakes > 0 && <p className="section-note section-note--flag">
            <Target /> {d.openMistakes} missed question{d.openMistakes === 1 ? '' : 's'} are queued for your next unit to teach against.
          </p>}
        </> : <div className="chart-empty"><Brain /><p>Finish a lesson or practice step and your per-skill mastery appears here.</p></div>}

        {d.subjects?.length > 0 && <div className="subject-split">
          {d.subjects.map(s => <div key={s.subject}>
            <small>{s.subject}</small>
            <div className="mastery-track"><i style={{ width: `${Math.max(4, s.accuracy)}%` }} /></div>
            <b>{s.accuracy}%</b>
          </div>)}
        </div>}
      </div>

      <div className="stat-col">
        <h2 className="section-title">Your paths</h2>
        <PathProgressCard title="Test Prep" snapshot={d.testPath} href="/dashboard/test-path-view" accent="violet" />
        <PathProgressCard title="College Planning" snapshot={d.collegePath} href="/dashboard/college-path-view" accent="teal" />

        <h2 className="section-title">Application progress</h2>
        <div className="app-progress">
          <span><small>Colleges researched</small><b>{d.collegesResearched}</b></span>
          <span><small>Applications submitted</small><b>{d.applicationsSubmitted}</b></span>
          <span><small>Personal statement</small><b>{d.essayProgress === 2 ? 'Final' : d.essayProgress === 1 ? 'Drafted' : 'Not started'}</b></span>
        </div>
        <div className="app-progress">
          <span><small>Test prep steps done</small><b>{d.totalTestPrepCompleted}</b></span>
          <span><small>College steps done</small><b>{d.totalCollegePlanningCompleted}</b></span>
        </div>
      </div>
    </section>
  </main></AppShell>
}

const metricLabels = {
  sat_total: 'SAT total', sat_math: 'SAT math', sat_ebrw: 'SAT reading & writing',
  act_composite: 'ACT composite', act_math: 'ACT math', act_reading: 'ACT reading',
  act_science: 'ACT science', gpa: 'GPA', colleges_researched: 'Colleges researched',
  applications_submitted: 'Applications submitted', essay_progress: 'Essay progress',
}

function TrackerPage() {
  const d = boot.data
  const metricKeys = Object.keys(d.statHistory || {}).filter(key => d.statHistory[key]?.length)
  const preferred = d.statHistory?.sat_total?.length ? 'sat_total' : d.statHistory?.gpa?.length ? 'gpa' : metricKeys[0]
  const [metric, setMetric] = useState(preferred)
  const [historyTab, setHistoryTab] = useState('test')
  const [analysis, setAnalysis] = useState(''); const [loading, setLoading] = useState(false)
  const analyze = async () => { setLoading(true); try { setAnalysis((await api('/api/tracker-analysis')).analysis) } catch (e) { setAnalysis(e.message) } finally { setLoading(false) } }
  const records = d.statHistory?.[metric] || []
  const history = historyTab === 'test' ? d.testPrepHistory : d.collegePlanningHistory
  const kpi = d.kpis?.[metric]

  return <AppShell name={d.name}><main className="app-main">
    <PageIntro kicker="PROGRESS TRACKER" title="See the shape of your effort."
      copy="Every score you have logged, and every path you have worked through."
      actions={<button className="button button--primary" onClick={analyze} disabled={loading}><Brain /> {loading ? 'Analyzing…' : 'Analyze my progress'}</button>} />

    {analysis && <article className="analysis-panel"><div><Sparkles /><small>MENTICS ANALYSIS</small></div><Markdown>{analysis}</Markdown></article>}

    <section className="tracker-panel">
      {metricKeys.length > 0 ? <>
        <div className="metric-switch" role="tablist" aria-label="Choose a metric">
          {metricKeys.map(key => <button key={key} role="tab" aria-selected={metric === key}
            className={metric === key ? 'active' : ''} onClick={() => setMetric(key)}>
            {metricLabels[key] || key.replace(/_/g, ' ')}
          </button>)}
        </div>
        {kpi && <div className="kpi-row">
          <span><small>LATEST</small><b>{kpi.latest}</b></span>
          <span><small>BEST</small><b>{kpi.best}</b></span>
          <span className={kpi.improvement > 0 ? 'up' : kpi.improvement < 0 ? 'down' : ''}>
            <small>CHANGE</small><b>{kpi.improvement > 0 ? '+' : ''}{Math.round(kpi.improvement * 100) / 100}</b>
          </span>
        </div>}
        <TrendChart records={records} label={metricLabels[metric] || metric} />
        <details className="chart-table">
          <summary>View as a table</summary>
          <table><thead><tr><th>Date</th><th>{metricLabels[metric] || metric}</th></tr></thead>
            <tbody>{records.slice().reverse().map((r, i) => <tr key={`${r.date}-${i}`}><td>{r.date}</td><td>{r.value}</td></tr>)}</tbody></table>
        </details>
      </> : <div className="chart-empty"><BarChart3 /><p>No scores logged yet. Finish a boss battle or update your scores and your trend line starts here.</p></div>}
    </section>

    <section className="tracker-panel">
      <div className="metric-switch" role="tablist" aria-label="Choose a path">
        <button role="tab" aria-selected={historyTab === 'test'} className={historyTab === 'test' ? 'active' : ''} onClick={() => setHistoryTab('test')}>Test prep</button>
        <button role="tab" aria-selected={historyTab === 'college'} className={historyTab === 'college' ? 'active' : ''} onClick={() => setHistoryTab('college')}>College planning</button>
      </div>
      {history?.length ? <ol className="unit-history">
        {history.slice(0, 8).map((gen, i) => {
          const done = gen.tasks.filter(t => t.is_completed).length
          return <li key={`${gen.date}-${i}`}>
            <header><b>{gen.tasks[0]?.unit_title || 'Unit'}</b><span>{done}/{gen.tasks.length} complete</span><em>{String(gen.date).slice(0, 10)}</em></header>
            <ul>{gen.tasks.map(t => <li key={t.id} className={t.is_completed ? 'done' : ''}>
              <i>{t.is_completed ? <Check /> : t.task_order}</i>
              <span>{t.skill_label || String(t.description).replace(/\[([^\]]+)\]\([^)]+\)/g, '$1').slice(0, 70)}</span>
            </li>)}</ul>
          </li>
        })}
      </ol> : <div className="chart-empty"><Target /><p>No {historyTab === 'test' ? 'test prep' : 'college planning'} units yet.</p></div>}
    </section>
  </main></AppShell>
}

const scoreFields = [['gpa', 'GPA', '0', '5', '0.01'], ['sat_ebrw', 'SAT reading & writing', '200', '800', '10'], ['sat_math', 'SAT math', '200', '800', '10'], ['act_math', 'ACT math', '1', '36', '1'], ['act_reading', 'ACT reading', '1', '36', '1'], ['act_science', 'ACT science', '1', '36', '1']]
function EditStats() { const d = boot.data; const values = { gpa: d.gpa, sat_ebrw: d.satEbrw, sat_math: d.satMath, act_math: d.actMath, act_reading: d.actReading, act_science: d.actScience }; return <AppShell name={d.name}><main className="app-main form-page"><PageIntro kicker="UPDATE PROGRESS" title="Keep your snapshot honest." copy="New numbers help every future path respond to your real progress." /><form method="POST" className="settings-form"><div className="form-field-grid">{scoreFields.map(([name, label, min, max, step]) => <label key={name}>{label}<small>{min}–{max}</small><input type="number" name={name} min={min} max={max} step={step} defaultValue={values[name] || ''} /></label>)}</div><div className="form-actions"><a className="button button--quiet" href="/dashboard/stats">Cancel</a><button className="button button--primary" type="submit">Save progress <Check /></button></div></form></main></AppShell> }

function Field({ name, label, textarea = false, value, ...props }) { return <label>{label}{textarea ? <textarea name={name} rows="4" defaultValue={value || ''} {...props} /> : <input name={name} defaultValue={value || ''} {...props} />}</label> }
function BuilderPage({ kind }) { const d = boot.data; const test = kind === 'test'; const [focus, setFocus] = useState(d.test_focus || ''); return <AppShell name={d.name}><main className="app-main form-page"><PageIntro kicker={test ? 'TEST PREPARATION' : 'COLLEGE PLANNING'} title={test ? 'Design your next five steps.' : 'Build a college plan that fits.'} copy={test ? 'Tell Mentics what the score alone cannot show.' : 'Turn a wide-open process into focused, personal action.'} /><form method="POST" className="settings-form builder-form">{test ? <><fieldset><legend>Which test are you preparing for?</legend><div className="choice-grid choice-grid--three">{[['sat', 'SAT only'], ['act', 'ACT only'], ['both', 'SAT + ACT']].map(([value, label]) => <label className={focus === value ? 'selected' : ''} key={value}><input type="radio" name="test_focus" value={value} required checked={focus === value} onChange={() => setFocus(value)} /><BookOpen /><b>{label}</b></label>)}</div></fieldset><div className="form-field-grid"><Field name="desired_sat" label="Desired SAT" type="number" min="400" max="1600" step="10" value={d.desired_sat} /><Field name="desired_act" label="Desired ACT" type="number" min="1" max="36" value={d.desired_act} /><Field name="current_sat_ebrw" label="Current SAT reading & writing" type="number" min="200" max="800" value={d.current_sat_ebrw} /><Field name="current_sat_math" label="Current SAT math" type="number" min="200" max="800" value={d.current_sat_math} /><Field name="current_act_composite" label="Current ACT composite" type="number" min="1" max="36" value={d.current_act_composite} /><Field name="current_act_math" label="Current ACT math" type="number" min="1" max="36" value={d.current_act_math} /><Field name="current_act_reading" label="Current ACT reading" type="number" min="1" max="36" value={d.current_act_reading} /><Field name="current_act_science" label="Current ACT science" type="number" min="1" max="36" value={d.current_act_science} /><Field name="hours_per_week" label="Hours available each week" type="number" min="1" max="40" value={d.hours_per_week} /></div><Field name="strengths" label="Your strengths" textarea value={d.strengths} /><Field name="weaknesses" label="Where you need the most help" textarea required value={d.weaknesses} /><Field name="test_date" label="Test date" type="date" value={d.test_date} /></> : <><div className="form-field-grid"><label>Current grade<select name="current_grade" required defaultValue={d.grade || ''}><option value="">Choose grade</option>{['9', '10', '11', '12'].map(v => <option value={v} key={v}>{v}th grade</option>)}</select></label><label>Planning stage<select name="planning_stage" required defaultValue={d.planning_stage || ''}><option value="">Choose stage</option><option value="exploring">Exploring options</option><option value="researching">Researching colleges</option><option value="applying">Ready to apply</option></select></label></div><Field name="interested_majors" label="Interested majors" textarea value={d.majors} /><Field name="target_colleges" label="Target colleges" textarea value={d.target_colleges} /></>}<div className="form-actions"><a className="button button--quiet" href="/dashboard">Cancel</a><button className="button button--primary" type="submit">Build my five-step path <ArrowRight /></button></div></form></main></AppShell> }

function BattleArena() {
  const d = boot.data
  const [battle, setBattle] = useState(d.currentBattle)
  const [answers, setAnswers] = useState({})
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [secondsLeft, setSecondsLeft] = useState(null)
  const refresh = async id => { try { setBattle(await api(`/api/sat-battles/${id}`)) } catch (x) { setError(x.message) } }
  useEffect(() => {
    if (!battle?.id || !['waiting', 'active'].includes(battle.status)) return undefined
    const poll = window.setInterval(() => refresh(battle.id), 1800)
    return () => window.clearInterval(poll)
  }, [battle?.id, battle?.status])
  useEffect(() => {
    if (battle?.status !== 'active' || !battle.startedAt) return undefined
    const tick = () => setSecondsLeft(Math.max(0, battle.durationSeconds - Math.floor((Date.now() - Date.parse(battle.startedAt)) / 1000)))
    tick(); const timer = window.setInterval(tick, 250)
    return () => window.clearInterval(timer)
  }, [battle?.status, battle?.startedAt, battle?.durationSeconds])
  const join = async () => { setBusy(true); setError(''); try { setBattle(await api('/api/sat-battles/queue', { method: 'POST' })) } catch (x) { setError(x.message) } finally { setBusy(false) } }
  const train = async () => { setBusy(true); setError(''); try { setBattle(await api('/api/sat-battles/train', { method: 'POST' })); setAnswers({}) } catch (x) { setError(x.message) } finally { setBusy(false) } }
  const cancelQueue = async () => { if (!battle) return; setBusy(true); setError(''); try { await api(`/api/sat-battles/${battle.id}/cancel`, { method: 'POST' }); setBattle(null) } catch (x) { setError(x.message) } finally { setBusy(false) } }
  const select = (questionIndex, selectedOption) => setAnswers(current => ({ ...current, [questionIndex]: selectedOption }))
  const submit = async () => { if (!battle || Object.keys(answers).length !== battle.questions.length) return; setBusy(true); setError(''); try { setBattle(await api(`/api/sat-battles/${battle.id}/submit`, { method: 'POST', body: JSON.stringify({ answers: Object.entries(answers).map(([question_index, selected_option]) => ({ question_index: Number(question_index), selected_option })) }) })) } catch (x) { setError(x.message) } finally { setBusy(false) } }
  const active = battle?.status === 'active'
  const waiting = battle?.status === 'waiting'
  const complete = battle?.status === 'complete'
  const idle = !battle || battle.status === 'expired'
  const clock = secondsLeft == null ? '2:00' : `${Math.floor(secondsLeft / 60)}:${String(secondsLeft % 60).padStart(2, '0')}`
  const spotlight = d.spotlight
  return <AppShell name={d.name}><main className="app-main battle-page">
    <section className="battle-hero"><div><div className="eyebrow"><span /> LIVE SAT ARENA</div><h1>Fast thinking.<br /><em>Real pressure.</em></h1><p>Race a matched student through five original SAT-style questions. Accuracy wins; speed breaks a tie.</p>{idle && <div className="battle-hero-actions"><button className="button button--primary battle-join" onClick={join} disabled={busy}><Swords /> {busy ? 'Finding a challenger…' : 'Find a challenger'} <ArrowRight /></button><button className="button battle-train-button" onClick={train} disabled={busy}><Brain /> Train with bot</button></div>}</div><div className="battle-hero-mark"><i><Swords /></i><span>1:1</span><small>HEAD-TO-HEAD</small></div></section>
    {error && <div className="error-banner">{error}<button onClick={() => setError('')}>Dismiss</button></div>}
    {idle && <section className="battle-training"><div><small>TRAINING GROUND</small><h2>Build speed before you put rating on the line.</h2><p>Start a private two-minute round with Mentics Arena Bot. Same five-question format, instant result, and zero leaderboard impact.</p></div><button className="button button--primary" onClick={train} disabled={busy}><Brain /> Start a bot drill <ArrowRight /></button></section>}
    {waiting && <section className="battle-stage battle-stage--waiting" aria-live="polite"><span className="battle-search-orbit"><Swords /></span><div><small>MATCHMAKING</small><h2>Finding your challenger</h2><p>Your question set is locked. If nobody joins within 30 seconds, Mentics Arena Bot steps in automatically.</p></div><div className="battle-wait-actions"><button className="text-button" onClick={() => refresh(battle.id)}>Check match status <RotateCcw /></button><button className="text-button" disabled={busy} onClick={cancelQueue}>Leave queue</button></div></section>}
    {active && <section className="battle-stage" aria-label="Active SAT battle"><header className="battle-status"><span><i /><b>{battle.mode === 'training' ? 'PRIVATE BOT DRILL' : 'LIVE BATTLE'}</b><small>vs {battle.opponentName || 'your challenger'}</small></span><strong className={secondsLeft < 20 ? 'urgent' : ''}><Clock3 /> {clock}</strong></header>{battle.submitted ? <div className="battle-locked"><span className="battle-search-orbit"><Check /></span><h2>Answers locked.</h2><p>{battle.mode === 'training' ? 'Mentics Arena Bot is scoring your round now.' : `Waiting for ${battle.opponentName || 'your challenger'} to finish. The arena will reveal the result automatically.`}</p></div> : <><div className="battle-question-progress">{battle.questions.map((_, index) => <i key={index} className={answers[index] != null ? 'done' : ''}>{index + 1}</i>)}</div><div className="battle-questions">{battle.questions.map((question, index) => <article className="battle-question" key={index}><header><small>QUESTION {index + 1} · {question.skill}</small><span>{answers[index] != null ? 'ANSWERED' : 'UNANSWERED'}</span></header><h2>{question.question_text}</h2><div>{question.options.map((option, optionIndex) => <button key={optionIndex} className={answers[index] === optionIndex ? 'selected' : ''} onClick={() => select(index, optionIndex)}><i>{String.fromCharCode(65 + optionIndex)}</i><span>{option}</span></button>)}</div></article>)}</div><button className="button button--primary battle-lock" disabled={busy || Object.keys(answers).length !== battle.questions.length} onClick={submit}>{busy ? 'Locking answers…' : `Lock in ${Object.keys(answers).length}/${battle.questions.length} answers`} <ArrowRight /></button></>}</section>}
    {complete && <section className={`battle-result ${battle.youWon ? 'won' : battle.draw ? 'draw' : 'lost'}`}><div className="battle-result-mark">{battle.youWon ? <Trophy /> : battle.draw ? <Target /> : <Swords />}</div><small>{battle.mode === 'training' ? 'BOT DRILL COMPLETE' : battle.youWon ? 'VICTORY' : battle.draw ? 'DRAW' : 'BATTLE COMPLETE'}</small><h2>{battle.mode === 'training' ? 'A sharper round in the bank.' : battle.youWon ? 'You won the race.' : battle.draw ? 'A dead-even finish.' : 'A strong round. Run it back.'}</h2><p><b>{battle.yourScore}</b> correct <span>vs</span> <b>{battle.opponentScore}</b> correct</p>{battle.mode === 'training' && <em className="battle-training-note">This private drill did not affect your rating.</em>}<button className="button button--primary" onClick={() => { setBattle(null); setAnswers({}) }}>{battle.mode === 'training' ? 'Train again' : 'Find another battle'} <Swords /></button></section>}
    <section className="battle-lower"><div className="battle-rules"><small>HOW IT WORKS</small><h2>One clean round. No fluff.</h2><div><article><b>01</b><span><strong>Match</strong><p>We pair you with one student and serve the same question set.</p></span></article><article><b>02</b><span><strong>Race</strong><p>Answer all five in two minutes. Your clock starts together.</p></span></article><article><b>03</b><span><strong>Climb</strong><p>Accuracy takes it. Faster completion breaks a tied score.</p></span></article></div></div><aside className="battle-leaderboard"><header><span><Trophy /> BATTLE LEADERBOARD</span><a href="#battle-rankings">View rankings</a></header>{d.leaderboard?.length ? d.leaderboard.slice(0, 5).map((row, index) => <div key={row.user_id}><i>{index + 1}</i><span>{String(row.user_name || 'M').slice(0, 1)}</span><b>{row.user_name}</b><strong>{row.rating}</strong></div>) : <p>The first completed battle earns a place here.</p>}</aside></section>
    <section className="battle-spotlight" id="battle-rankings"><div><small>ARENA SPOTLIGHT</small><h2>{spotlight ? `${spotlight.challenger_name} vs ${spotlight.opponent_name}` : 'The next great battle starts with you.'}</h2><p>{spotlight ? 'The latest completed head-to-head round in the Mentics arena.' : 'Enter the arena to set the first battle on the board.'}</p></div><div>{spotlight ? <><strong>{spotlight.winner_id ? 'WINNER DECIDED' : 'DRAW'}</strong><span>Latest completed battle</span></> : <><strong>OPEN</strong><span>Matchmaking is ready</span></>}</div></section>
  </main></AppShell>
}

function ForumPage() {
  const d = boot.data
  const [creating, setCreating] = useState(false)
  const [busy, setBusy] = useState(false)
  const [editing, setEditing] = useState(null)
  const [error, setError] = useState('')
  const submitPost = async e => { e.preventDefault(); setBusy(true); setError(''); const form = new FormData(e.currentTarget); try { await api('/api/posts', { method: 'POST', body: JSON.stringify({ title: form.get('title'), content: form.get('content') }) }); window.location.reload() } catch (x) { setError(x.message) } finally { setBusy(false) } }
  const reply = async (postId, e) => { e.preventDefault(); setBusy(true); setError(''); const form = new FormData(e.currentTarget); try { await api('/api/replies', { method: 'POST', body: JSON.stringify({ post_id: postId, content: form.get('content') }) }); window.location.reload() } catch (x) { setError(x.message) } finally { setBusy(false) } }
  const saveEdit = async (kind, id, e) => { e.preventDefault(); setBusy(true); setError(''); const form = new FormData(e.currentTarget); const payload = kind === 'post' ? { title: form.get('title'), content: form.get('content') } : { content: form.get('content') }; try { await api(`/api/${kind === 'post' ? 'posts' : 'replies'}/${id}`, { method: 'PATCH', body: JSON.stringify(payload) }); window.location.reload() } catch (x) { setError(x.message) } finally { setBusy(false) } }
  const editingItem = (kind, id) => editing?.kind === kind && editing?.id === id
  const editButton = (kind, item) => <button type="button" className="forum-edit" onClick={() => setEditing({ kind, id: item.id })}><PenLine size={14} /> Edit</button>
  return <AppShell name={d.name}><main className="app-main"><PageIntro kicker="MENTICS COMMUNITY" title="Students helping students." copy="Compare approaches, ask better questions, and move forward together." actions={<button className="button button--primary" onClick={() => setCreating(!creating)}><Plus /> New discussion</button>} />{error && <p className="form-error">{error}</p>}{creating && <form className="new-post-panel" onSubmit={submitPost}><Field name="title" label="Discussion title" required /><Field name="content" label="What do you want to share or ask?" textarea required /><button className="button button--primary" disabled={busy}>Publish discussion</button></form>}<form className="forum-search" method="GET"><Search /><input name="search" defaultValue={d.searchQuery || ''} placeholder="Search discussions" /><button>Search</button></form><section className="forum-layout"><div className="thread-list">{d.posts?.length ? d.posts.map(post => <article className="thread" key={post.id}><header><span>{String(post.user_name || 'M').slice(0, 1)}</span><div><b>{post.title}</b><small>{post.user_name} · {String(post.created_at).slice(0, 10)}</small></div>{post.user_id === d.viewerId && !editingItem('post', post.id) && editButton('post', post)}</header>{editingItem('post', post.id) ? <form className="forum-edit-form" onSubmit={e => saveEdit('post', post.id, e)}><input name="title" defaultValue={post.title} maxLength="200" required /><textarea name="content" defaultValue={post.content} maxLength="5000" required /><div><button className="button button--primary" disabled={busy}>Save changes</button><button type="button" className="button button--quiet" onClick={() => setEditing(null)}>Cancel</button></div></form> : <p>{post.content}</p>}{post.replies?.length > 0 && <div className="replies">{post.replies.map(r => <div key={r.id}>{editingItem('reply', r.id) ? <form className="forum-edit-form" onSubmit={e => saveEdit('reply', r.id, e)}><textarea name="content" defaultValue={r.content} maxLength="5000" required /><div><button className="button button--primary" disabled={busy}>Save</button><button type="button" className="button button--quiet" onClick={() => setEditing(null)}>Cancel</button></div></form> : <><div className="reply-meta"><b>{r.user_name}</b>{r.user_id === d.viewerId && editButton('reply', r)}</div><p>{r.content}</p></>}</div>)}</div>}<form onSubmit={e => reply(post.id, e)}><input name="content" required placeholder="Add a thoughtful reply" /><button disabled={busy}><Send /></button></form></article>) : <div className="empty-state"><MessageCircle /><p>No discussions match this search yet.</p></div>}</div><aside className="community-aside"><UsersRound /><h3>Today in Mentics</h3><strong>{d.todaysThreads?.length || 0}</strong><span>new discussions</span><p>Keep posts specific, respectful, and useful to the next student.</p></aside></section></main></AppShell> }

function LeaderboardPage() { const d = boot.data; return <AppShell name={d.name}><main className="app-main"><PageIntro kicker="COMMUNITY MOMENTUM" title="Consistency deserves the spotlight." copy="Points celebrate completed work—not comparison for its own sake." /><section className="leaderboard-list">{d.leaderboard?.map((row, index) => <article className={index < 3 ? 'top' : ''} key={`${row.name}-${index}`}><span>{index + 1}</span><div>{String(row.name || 'M').slice(0, 1).toUpperCase()}</div><b>{row.name}</b><strong>{row.points} pts</strong>{index === 0 && <Trophy />}</article>)}</section></main></AppShell> }

function AccountPage() { const d = boot.data; return <AppShell name={d.name}><main className="app-main form-page"><PageIntro kicker="YOUR ACCOUNT" title="Make Mentics yours." copy="Keep your identity and sign-in details current." />{d.updated && <div className="success-banner"><Check /> Your account was updated.</div>}{d.error && <div className="form-error">{d.error}</div>}<section className="account-sections"><form method="POST"><input type="hidden" name="form_type" value="name" /><div><UserRound /><span><h2>Your name</h2><p>How Mentics addresses you.</p></span></div><Field name="name" label="Full name" value={d.name} required maxLength="100" /><button className="button button--primary">Save name</button></form><form method="POST"><input type="hidden" name="form_type" value="email" /><div><Mail /><span><h2>Email address</h2><p>Where you sign in.</p></span></div><Field name="email" label="Email" type="email" value={d.email} required maxLength="254" /><button className="button button--primary">Save email</button></form><form method="POST"><input type="hidden" name="form_type" value="password" /><div><ShieldCheck /><span><h2>Password</h2><p>Use at least eight characters.</p></span></div><Field name="current_password" label="Current password" type="password" required maxLength="128" /><Field name="new_password" label="New password" type="password" minLength="8" maxLength="128" required /><Field name="confirm_password" label="Confirm new password" type="password" minLength="8" maxLength="128" required /><button className="button button--primary">Change password</button></form></section><form className="logout-link" method="POST" action="/logout"><CsrfField /><button type="submit">Sign out of Mentics <ArrowRight /></button></form></main></AppShell> }

const legalCopy = {
  privacy: {
    title: 'Privacy Policy', date: 'August 23, 2026',
    intro: 'Welcome to Mentics. This policy explains how Mentics collects, uses, discloses, and safeguards information when you use our website and services.',
    sections: [
      ['1. Information we collect', 'We collect account information such as your name, email, and securely hashed password or Google profile details. Educational data can include goals, learning style, anxieties, GPA, SAT/ACT scores, strengths, weaknesses, test dates, grade level, majors, and target colleges. We also collect content you choose to submit, including forum posts and replies, AI-assistant conversations, essays and prompts, plus activity data such as completed tasks, generated paths, and stat updates. Our servers may also receive technical information such as IP address, browser, operating system, access times, and viewed pages.'],
      ['2. How we use information', 'We use this information to create and manage accounts; generate personalized test-prep and college-planning paths; provide contextual chat and essay feedback; operate the forum and leaderboard; display progress; analyze and improve Mentics; and administer points, streaks, and achievements.'],
      ['3. Disclosure of information', 'Mentics does not sell personal information. We may disclose information when required by law or needed to protect rights, property, and safety. We share inputs such as chat messages and essay text with Google Gemini only to provide the AI features you request, subject to Google’s privacy policies. We do not currently share user information with third-party advertisers.'],
      ["4. Children's privacy", 'Mentics is intended for high school students generally over age 13. We do not knowingly collect personally identifiable information from children under 13. If we learn that a user is under 13, we will require verifiable parental consent; parents or guardians may contact us to request appropriate action.'],
      ['5. Your rights and choices', 'You may review or change account information from account settings and may contact us to opt out of communications or ask about your information.'],
      ['6. Security', 'We use administrative, technical, and physical safeguards designed to protect personal information. No security measure or method of transmission can be guaranteed against every interception or misuse.'],
      ['7. Cookies and authentication', 'Mentics uses essential cookies and similar technologies to maintain sessions, remember security state, prevent abuse, and operate the service. Google sign-in uses the openid, email, and profile scopes; we do not request access to Gmail, Google Drive, Calendar, or other Google content.'],
      ['8. AI processing', 'When you request AI chat, path generation, assignment feedback, or essay feedback, the relevant input and necessary path context may be sent to an AI service provider to produce that feature. AI outputs may be inaccurate or incomplete and are not professional, admissions, legal, medical, financial, or mental-health advice. Do not submit content you do not want processed for the feature you requested.'],
      ['9. Public community content', 'Forum posts, replies, display name, and other content you choose to make public may be visible to other users and may be copied by them. Do not publish private contact details, account credentials, educational records, or another person’s information without permission.'],
      ['10. Retention', 'We retain information for as long as reasonably necessary to operate Mentics, maintain security, resolve disputes, enforce agreements, and meet legal obligations. Retention varies by purpose. We may retain aggregated or de-identified information that does not reasonably identify you.'],
      ['11. Your privacy choices and rights', 'You may update certain account and academic information in Mentics. Subject to applicable law, you may request access, correction, deletion, or a copy of personal information by emailing us. We may verify requests and may retain limited information where needed for security, fraud prevention, legal compliance, or legitimate operations.'],
      ['12. California and other regional rights', 'Mentics does not sell personal information or share it for cross-context behavioral advertising. California residents and residents of other jurisdictions may have additional rights under applicable law, including rights to know, correct, delete, or limit certain uses. Contact us to make a request.'],
      ['13. International transfers', 'Mentics is operated from the United States. If you access it from elsewhere, your information may be processed in the United States or other places where our service providers operate, which may have different privacy laws.'],
      ['14. Changes to this policy', 'We may update this policy as the service or law changes. We will post the revised version and update the Last updated date; where required, we will provide additional notice or obtain consent.'],
      ['15. Contact us', 'Questions, privacy requests, or complaints can be sent to thementicsapp@gmail.com.']
    ]
  },
  terms: {
    title: 'Terms of Service', date: 'August 23, 2026',
    intro: 'Please read these terms carefully before using the Mentics website and services. Creating an account, accessing, or using Mentics means you agree to these Terms and our Privacy Policy.',
    sections: [
      ['1. Agreement to terms', 'If you disagree with any part of these terms, you may not access the service.'],
      ['2. Description of service', 'Mentics provides personalized AI-generated SAT/ACT and college-planning paths, contextual guidance, academic progress tracking, points, streaks and achievements, a community forum, and AI-driven essay analysis.'],
      ['3. Accounts and eligibility', 'You must be at least 13 years old. You are responsible for accurate and complete account information, safeguarding your password, and activity under your credentials.'],
      ['4. User-generated content', 'You are responsible for the legality, reliability, and appropriateness of content you submit. By posting content, you grant Mentics a non-exclusive, worldwide, royalty-free, perpetual, transferable license to use, reproduce, modify, display, and distribute it in connection with providing and improving the service. You represent that you have the required rights. Mentics may monitor or remove content that violates these terms or is harmful or objectionable.'],
      ['5. AI and API usage', 'Mentics uses third-party AI services including Google Gemini and is committed to responsible use. AI-generated paths, chat responses, and essay feedback are educational information only and may be inaccurate. You are responsible for verification and judgment.'],
      ['6. Prohibited activities', 'Do not use Mentics illegally, harass or defraud users, post obscene, defamatory, hateful, infringing, or harmful content, compromise system security, decipher server transmissions, or submit false or misleading information.'],
      ['7. Copyright policy and DMCA', 'We respect intellectual-property rights. Send a detailed claim that meets DMCA requirements to thementicsapp@gmail.com with the subject “Copyright Infringement.”'],
      ['8. Disclaimers and trademark notice', 'Mentics is independent and is not affiliated with, endorsed by, or sponsored by the College Board®, owner of the SAT®, or ACT®, Inc., owner of the ACT®. AI content and the service are provided “as is” and “as available,” without express or implied warranties.'],
      ['9. Independence from tests and institutions', 'MENTICS IS INDEPENDENT. Mentics is not affiliated with, endorsed by, sponsored by, approved by, or acting on behalf of the College Board, SAT, ACT, ACT, Inc., any school, university, college, admissions office, scholarship provider, or government agency. References to tests, schools, trademarks, or third-party resources are for identification and educational purposes only.'],
      ['10. Educational and AI disclaimer', 'Mentics, including AI-generated paths, lessons, coaching, and essay feedback, provides general educational information only. It does not guarantee scores, admission, scholarships, financial aid, or any outcome. AI may be inaccurate, incomplete, biased, or out of date. Verify deadlines, requirements, score policies, and admissions information directly with the relevant official source before acting.'],
      ['11. Third-party services', 'Mentics may link to or use third-party services, including Google sign-in, AI providers, official test resources, and college websites. Their content, availability, privacy practices, and terms are outside our control and your use is governed by their policies.'],
      ['12. Termination', 'Mentics may terminate or suspend an account immediately and without prior notice or liability, including for a breach of these terms.'],
      ['13. Governing law and disputes', 'These terms are governed by the laws of Georgia, United States. Before filing a claim, contact us and attempt to resolve the issue informally for 30 days. Nothing in these Terms limits non-waivable consumer rights or a claim properly brought in small-claims court.'],
      ['14. Limitation of liability', 'TO THE MAXIMUM EXTENT PERMITTED BY LAW, Mentics and its directors, employees, agents, and providers are not liable for indirect, incidental, special, consequential, exemplary, or punitive damages, including loss of data, goodwill, profits, scores, admissions opportunities, or other intangible losses arising from the service or its content.'],
      ['15. Changes', 'Mentics may modify these Terms by posting an updated version and changing the Last updated date. Continued use after the effective date means you accept the updated Terms, except where applicable law requires a different form of notice or consent.'],
      ['16. Contact us', 'Questions about these terms can be sent to thementicsapp@gmail.com.']
    ]
  }
}
function LegalPage({ type }) { const d = legalCopy[type]; return <div className="legal-page"><header><Brand /><a href="/"><ArrowLeft /> Back to Mentics</a></header><main><div className="legal-title"><small>MENTICS LEGAL</small><h1>{d.title}</h1><p>Last updated {d.date}</p></div><p className="legal-intro">{d.intro}</p>{d.sections.map(([title, copy]) => <section key={title}><h2>{title}</h2><p>{copy}</p></section>)}</main></div> }
function ArticlePage() { const d = boot.data; return <AppShell name={d.name}><main className="app-main article-page"><a href="/dashboard/test-path-view" className="text-button"><ArrowLeft /> Back to path</a><article><div className="eyebrow"><span /> STRATEGY GUIDE</div><h1>{d.article?.title}</h1><Markdown>{d.article?.content || 'This article is not available yet.'}</Markdown></article></main></AppShell> }

function App() {
  useEffect(() => {
    document.documentElement.dataset.menticsPage = boot.page
    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    const nodes = [...document.querySelectorAll('.app-main > :not(.chat-panel),.onboarding-page main > form > section.active,.auth-panel > *')]
    if (!reduced) {
      nodes.slice(0, 8).forEach((node, index) => {
        node.classList.add('mx-app-enter')
        node.style.setProperty('--mx-enter-delay', `${Math.min(index, 5) * 35}ms`)
      })
      requestAnimationFrame(() => requestAnimationFrame(() => nodes.forEach(node => node.classList.add('is-present'))))
    }
    return () => { delete document.documentElement.dataset.menticsPage }
  }, [])

  let page
  switch (boot.page) {
    case 'dashboard': page = <Dashboard />; break
    case 'path': page = <PathPage />; break
    case 'battles': page = <BattleArena />; break
    case 'login': page = <AuthPage mode="login" />; break
    case 'signup': page = <AuthPage mode="signup" />; break
    case 'onboarding': page = <Onboarding />; break
    case 'stats': page = <StatsPage />; break
    case 'edit-stats': page = <EditStats />; break
    case 'test-builder': page = <BuilderPage kind="test" />; break
    case 'college-builder': page = <BuilderPage kind="college" />; break
    case 'tracker': page = <TrackerPage />; break
    case 'forum': page = <ForumPage />; break
    case 'leaderboard': page = <LeaderboardPage />; break
    case 'account': page = <AccountPage />; break
    case 'privacy': page = <LegalPage type="privacy" />; break
    case 'terms': page = <LegalPage type="terms" />; break
    case 'article': page = <ArticlePage />; break
    default: page = <Landing />
  }
  return <><Toaster position="bottom-right" mobileOffset={16} offset={24} closeButton theme="light" toastOptions={{ duration: 4200 }} />{page}</>
}

export { App, CsrfBootstrap }
