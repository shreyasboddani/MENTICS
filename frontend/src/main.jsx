import React, { useEffect, useMemo, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import { createRoot } from 'react-dom/client'
import DOMPurify from 'dompurify'
import { marked } from 'marked'
import {
  ArrowLeft, ArrowRight, Award, BarChart3, BookOpen, Brain, CalendarDays,
  Check, Clock3, Flame,
  GraduationCap, Hand, Headphones, House, LayoutDashboard, LineChart,
  LockKeyhole, LogOut, Mail, Menu, MessageCircle, PenLine, Plus, RotateCcw,
  Search, Send, Settings, ShieldCheck, Sparkles, Target, Trophy, UserRound,
  UsersRound, X, Zap
} from 'lucide-react'
import './styles.css'
import './experience.css'
import './brand-system.css'
import './liquid-glass.css'
import './mentics-redesign.css'

const boot = window.__MENTICS__ || { page: 'landing', data: {} }
const csrfToken = boot.data.csrfToken || ''

function CsrfField() { return <input type="hidden" name="_csrf_token" value={csrfToken} /> }

function CsrfBootstrap() {
  useEffect(() => {
    const attach = event => {
      const form = event.target
      if (!(form instanceof HTMLFormElement) || String(form.method).toLowerCase() !== 'post' || form.querySelector('input[name="_csrf_token"]')) return
      const field = document.createElement('input')
      field.type = 'hidden'; field.name = '_csrf_token'; field.value = csrfToken; form.appendChild(field)
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
  const loggedIn = boot.data.isLoggedIn
  useEffect(() => {
    const nodes = [...document.querySelectorAll('.landing-facts > div,.section-heading,.process-grid article,.journey-showcase-copy,.journey-demo,.platform-copy,.feature-stack > div,.suite-heading,.suite-grid article,.week-heading,.week-flow article,.faq details,.closing')]
    nodes.forEach(node => node.classList.add('mx-reveal'))
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) { nodes.forEach(node => node.classList.add('is-visible')); return }
    const observer = new IntersectionObserver(entries => entries.forEach(entry => { if (entry.isIntersecting) { entry.target.classList.add('is-visible'); observer.unobserve(entry.target) } }), { threshold: .12, rootMargin: '0px 0px -7% 0px' })
    nodes.forEach(node => observer.observe(node))
    return () => observer.disconnect()
  }, [])
  return <div className="landing">
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
          <div className="frame-top"><span /><span /><span /><div>app.mentics</div></div>
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
      </section>

      <section className="trust-strip"><span>A path that adapts</span><span>Focused daily action</span><span>Progress you can see</span><span>Guidance when you need it</span></section>

      <section className="landing-facts" aria-label="Mentics at a glance">
        <div><strong>5</strong><span><b>steps at a time</b><small>Enough direction to move. Never enough noise to freeze.</small></span></div>
        <div><strong>2</strong><span><b>connected tracks</b><small>Test preparation and college planning, finally in one rhythm.</small></span></div>
        <div><strong>1</strong><span><b>place to keep moving</b><small>Your plan, practice, feedback, progress, and people.</small></span></div>
      </section>

      <section className="section process" id="how-it-works">
        <div className="section-heading"><div className="eyebrow"><span /> THE MENTICS METHOD</div><h2>Clarity changes everything.</h2><p>Mentics turns a distant goal into the next right move—then learns from what happens.</p></div>
        <div className="process-grid">
          <article><b>01</b><Target /><h3>Tell us where you are</h3><p>Share your goals, timing, strengths, and the areas that need attention.</p></article>
          <article><b>02</b><Sparkles /><h3>Get a five-step path</h3><p>Receive a focused roadmap built around your actual priorities—not a generic checklist.</p></article>
          <article><b>03</b><BarChart3 /><h3>Improve with evidence</h3><p>Complete work, track results, and let every new path build on real progress.</p></article>
        </div>
      </section>

      <section className="journey-showcase" aria-labelledby="journey-title">
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

      <section className="section platform" id="platform">
        <div className="platform-copy"><div className="eyebrow eyebrow--light"><span /> ONE FOCUSED WORKSPACE</div><h2>Less noise.<br />More momentum.</h2><p>Test prep, college planning, progress, and contextual guidance belong in one calm place.</p><a href={loggedIn ? '/dashboard' : '/signup'}>Explore the platform <ArrowRight size={17} /></a></div>
        <div className="feature-stack">
          <div><Target /><span><b>Adaptive paths</b><small>Five clear steps that respond to your goals and performance.</small></span></div>
          <div><MessageCircle /><span><b>Contextual guidance</b><small>Ask for help without losing the context of what you are working on.</small></span></div>
          <div><GraduationCap /><span><b>College planning</b><small>Turn applications, essays, and deadlines into manageable progress.</small></span></div>
          <div><BarChart3 /><span><b>Visible progress</b><small>Track scores, streaks, milestones, and the work behind them.</small></span></div>
        </div>
      </section>

      <section className="suite-section" id="suite">
        <div className="suite-heading"><div className="eyebrow"><span /> THE COMPLETE MENTICS SUITE</div><h2>Everything your ambition needs.<br />Nothing it doesn’t.</h2><p>The tools already inside Mentics, brought into one expressive workspace.</p></div>
        <div className="suite-grid">
          <article className="suite-path"><Target /><small>ADAPTIVE PATHS</small><h3>Five steps. One clear direction.</h3><p>Personalized SAT, ACT, and college-planning roadmaps that respond to your progress.</p><div className="mini-road"><i>1</i><span /><i>2</i><span /><i>3</i><span /><i>4</i><span /><i>5</i></div></article>
          <article className="suite-sprint"><Zap /><small>FOCUSED SPRINTS</small><h3>Practice with purpose.</h3><p>Short assessments, strategy articles, and immediate explanations make every session count.</p></article>
          <article className="suite-essay"><PenLine /><small>ESSAY FEEDBACK</small><h3>Make every word stronger.</h3><p>Get structured feedback while keeping your voice, story, and ideas unmistakably yours.</p></article>
          <article className="suite-progress"><LineChart /><small>VISIBLE PROGRESS</small><h3>See the work adding up.</h3><p>Scores, milestones, history, points, and streaks reveal the pattern behind improvement.</p></article>
          <article className="suite-community"><UsersRound /><small>COMMUNITY</small><h3>Move forward together.</h3><p>Ask questions, share approaches, and celebrate real consistency on the leaderboard.</p></article>
        </div>
      </section>

      <section className="week-section">
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

      <section className="section faq" id="faq"><div className="section-heading"><h2>Good questions.</h2></div>
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
      <nav className={menu ? 'open' : ''} aria-label="Product navigation">{navItems.map(([href, Icon, label]) => <a key={href} className={active(href) ? 'active' : ''} href={href} aria-current={active(href) ? 'page' : undefined} title={label} onClick={event => travel(event, href, label)}><Icon size={17} /><span>{label}</span></a>)}</nav>
      <div className="product-account"><a href="/account" onClick={event => travel(event, '/account', 'Settings')}><i>{(name || 'M').slice(0, 1).toUpperCase()}</i><span>{name || 'Mentics student'}</span></a><form className="product-logout" method="POST" action="/logout"><CsrfField /><button type="submit" aria-label="Log out"><LogOut size={17} /></button></form></div>
      <button className="product-menu" onClick={() => setMenu(!menu)} aria-label="Toggle navigation">{menu ? <X /> : <Menu />}</button>
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
  const csrfHeader = !['GET', 'HEAD', 'OPTIONS'].includes(method) && csrfToken ? { 'X-CSRF-Token': csrfToken } : {}
  const response = await fetch(url, { headers: { 'Content-Type': 'application/json', ...csrfHeader, ...(options.headers || {}) }, ...options })
  const data = await response.json().catch(() => ({}))
  if (!response.ok) throw new Error(data.error || 'Something went wrong. Please try again.')
  return data
}

function Markdown({ children }) {
  const html = useMemo(() => DOMPurify.sanitize(marked.parse(children || '', { breaks: true })), [children])
  return <div className="markdown" dangerouslySetInnerHTML={{ __html: html }} />
}

function PathPage() {
  const category = boot.data.category
  const isTest = category === 'Test Prep'
  const [tasks, setTasks] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [selected, setSelected] = useState(null)
  const [chatOpen, setChatOpen] = useState(() => window.matchMedia('(min-width: 1050px)').matches)
  const [adding, setAdding] = useState(false)
  const [essayOpen, setEssayOpen] = useState(false)
  const builder = isTest ? '/dashboard/test-path-builder' : '/dashboard/college-path-builder'
  const loadTasks = async (regenerate = false) => {
    setLoading(true); setError('')
    try {
      const data = await api(`/api/tasks?category=${encodeURIComponent(category)}`, regenerate ? { method: 'POST' } : {})
      if (!Array.isArray(data)) throw new Error('Your path could not be loaded.')
      setTasks(data.map(normalizeTask))
    } catch (e) { setError(e.message) } finally { setLoading(false) }
  }
  useEffect(() => {
    let cancelled = false
    api(`/api/tasks?category=${encodeURIComponent(category)}`)
      .then(data => {
        if (!Array.isArray(data)) throw new Error('Your path could not be loaded.')
        if (!cancelled) setTasks(data.map(normalizeTask))
      })
      .catch(e => { if (!cancelled) setError(e.message) })
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
  }, [category])
  const completed = tasks.filter(t => t.is_completed).length
  const activeIndex = tasks.findIndex(t => !t.is_completed)
  const journeyHeight = Math.max(790, 180 + (tasks.length - 1) * 155)
  const journeyXs = [320, 170, 320, 470, 320]
  const journeyPoints = tasks.map((_, index) => ({ x: journeyXs[index % journeyXs.length], y: 90 + index * 155 }))
  const journeyCurve = journeyPoints.reduce((path, point, index) => { if (index === 0) return `M ${point.x} ${point.y}`; const previous = journeyPoints[index - 1]; const mid = (previous.y + point.y) / 2; return `${path} C ${previous.x} ${mid}, ${point.x} ${mid}, ${point.x} ${point.y}` }, '')
  const finishTask = (next) => {
    const updated = tasks.map(t => t.id === next.id ? next : t)
    setTasks(updated)
    setSelected(null)
    if (updated.length === 5 && updated.every(t => t.is_completed)) {
      window.setTimeout(async () => {
        if (window.confirm('You finished all five steps. Build the next five-step path now?')) await loadTasks(true)
      }, 250)
    }
  }
  return <AppShell name={boot.data.name}><main className={`app-main path-page ${chatOpen ? 'chat-docked' : ''}`}>
    <div className="path-header"><div><div className="eyebrow"><span /> {category.toUpperCase()}</div><h1>Your five-step path.</h1><p>Finish what is in front of you. The path adapts from there.</p></div><div className="path-header-actions">{!isTest && <button className="button button--quiet" onClick={() => setEssayOpen(true)}><PenLine size={17} /> Essay feedback</button>}{!chatOpen && <button className="button button--quiet" onClick={() => setChatOpen(true)}><MessageCircle size={17} /> Ask Mentics</button>}<a className="button button--dark" href={builder}>Edit goals <ArrowRight size={16} /></a></div></div>
    <div className="path-progress"><span style={{ width: `${tasks.length ? completed / tasks.length * 100 : 0}%` }} /><p><b><span>{completed}</span><i>/</i><span>{tasks.length || 5}</span></b><span>steps complete</span></p></div>
    {error && <div className="error-banner">{error}<button onClick={() => loadTasks()}>Try again</button></div>}
    {loading ? <PathSkeleton /> : <section className="journey-map" style={{ height: journeyHeight }} aria-label={`${category} learning journey`}>
      <svg className="journey-route" viewBox={`0 0 640 ${journeyHeight}`} preserveAspectRatio="none" aria-hidden="true"><defs><linearGradient id="journey-gradient" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#8b5cf6" /><stop offset="1" stopColor="#4f46e5" /></linearGradient></defs><path className="journey-route-shadow" d={journeyCurve} /><path className="journey-route-progress" d={journeyCurve} pathLength="100" style={{ strokeDasharray: `${tasks.length ? Math.min(100, completed / tasks.length * 100) : 0} 100` }} /></svg>
      {tasks.map((task, index) => {
        const locked = index > activeIndex && activeIndex !== -1; const milestone = task.type === 'milestone' || String(task.description).toLowerCase().includes('boss battle'); const point = journeyPoints[index]; return <button key={task.id || index} disabled={locked} style={{ left: `${point.x / 640 * 100}%`, top: point.y }} className={`journey-step ${task.is_completed ? 'done' : index === activeIndex ? 'current' : 'locked'} ${milestone ? 'milestone' : ''}`} onClick={() => setSelected(task)} aria-label={`Step ${index + 1}: ${task.description}`}>
          {index === activeIndex && !task.is_completed && <span className="journey-next">START</span>}
          <span className="journey-node"><i>{task.is_completed ? <Check /> : locked ? <LockKeyhole /> : milestone ? <Trophy /> : task.task_format === 'quiz' ? <Brain /> : task.task_format === 'practice_sprint' ? <Zap /> : index + 1}</i></span>
          <span className={`journey-label ${point.x < 320 ? 'label-right' : point.x > 320 ? 'label-left' : index % 2 ? 'label-left' : 'label-right'}`}><small>{task.is_completed ? 'COMPLETED' : milestone ? 'MILESTONE' : `STEP ${index + 1}`}</small><b><PlainText value={task.description} /></b>{task.due_date && <em><CalendarDays /> {task.due_date}</em>}</span>
        </button>
      })}
    </section>}
    <div className="path-footer-actions"><button className="button button--quiet" onClick={() => setAdding(true)}><Plus /> Add your own step</button><button className="text-button" onClick={() => loadTasks(true)}><RotateCcw /> Regenerate five steps</button></div>
    {selected && <TaskModal task={selected} category={category} onClose={() => setSelected(null)} onUpdate={(next) => { setTasks(items => items.map(t => t.id === next.id ? next : t)); setSelected(next) }} onCompleted={finishTask} />}
    {adding && <AddTask category={category} onClose={() => setAdding(false)} onAdded={t => { setTasks(items => [...items, normalizeTask(t)]); setAdding(false) }} />}
    {essayOpen && <EssayCoach onClose={() => setEssayOpen(false)} />}
    <ChatPanel open={chatOpen} onClose={() => setChatOpen(false)} category={category} onNewPath={items => setTasks(items.map(normalizeTask))} />
    {!chatOpen && <button className="floating-chat" onClick={() => setChatOpen(true)}><MessageCircle /><span>Ask Mentics</span></button>}
  </main></AppShell>
}

function PlainText({ value }) { return <>{String(value || '').replace(/\[([^\]]+)\]\([^)]+\)/g, '$1').replace(/[*_#`]/g, '')}</> }
function normalizeTask(t) { return { ...t, is_completed: Boolean(t.is_completed), is_skipped: Boolean(t.is_skipped), subtasks: Array.isArray(t.subtasks) ? t.subtasks : [], task_format: t.task_format || 'link' } }

function PathSkeleton() { return <section className="journey-map journey-map--loading">{[0, 1, 2, 3, 4].map(i => <span className="journey-skeleton skeleton" style={{ left: `${[50, 27, 50, 73, 50][i]}%`, top: 90 + i * 155 }} key={i} />)}</section> }

function Modal({ children, onClose, wide = false }) { useEffect(() => { const fn = e => e.key === 'Escape' && onClose(); document.addEventListener('keydown', fn); return () => document.removeEventListener('keydown', fn) }, [onClose]); return createPortal(<div className="modal-wrap" role="dialog" aria-modal="true" onMouseDown={e => e.target === e.currentTarget && onClose()}><div className={`modal ${wide ? 'modal--wide' : ''}`}><button className="modal-close" onClick={onClose} aria-label="Close"><X /></button>{children}</div></div>, document.body) }

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

function TaskModal({ task, category, onClose, onUpdate, onCompleted }) {
  const [note, setNote] = useState(''); const [busy, setBusy] = useState(false); const [assessment, setAssessment] = useState(null); const [dueDate, setDueDate] = useState(task.due_date || ''); const [statPrompt, setStatPrompt] = useState(false); const [statValue, setStatValue] = useState(''); const [error, setError] = useState('')
  const stat = milestoneStats[task.stat_to_update]
  const complete = async () => { setBusy(true); setError(''); try { await api('/api/update_task_status', { method: 'POST', body: JSON.stringify({ taskId: task.id, status: 'complete' }) }); const next = { ...task, is_completed: true }; onUpdate(next); if (stat) setStatPrompt(true); else onCompleted(next) } catch (e) { setError(e.message) } finally { setBusy(false) } }
  const finishMilestone = async (save) => { setBusy(true); setError(''); try { if (save) await api('/api/update_stats', { method: 'POST', body: JSON.stringify({ stat_name: task.stat_to_update, stat_value: statValue }) }); onCompleted({ ...task, is_completed: true }) } catch (e) { setError(e.message) } finally { setBusy(false) } }
  const addNote = async () => { if (!note.trim()) return; const r = await api('/api/add_subtask', { method: 'POST', body: JSON.stringify({ parent_task_id: task.id, description: note }) }); onUpdate({ ...task, subtasks: [...task.subtasks, r.subtask] }); setNote('') }
  const toggleNote = async (s) => { await api('/api/update_subtask', { method: 'POST', body: JSON.stringify({ subtaskId: s.id, is_completed: !s.is_completed }) }); onUpdate({ ...task, subtasks: task.subtasks.map(x => x.id === s.id ? { ...x, is_completed: !x.is_completed } : x) }) }
  const saveDeadline = async () => { await api('/api/update_task_deadline', { method: 'POST', body: JSON.stringify({ taskId: task.id, dueDate: dueDate || null }) }); onUpdate({ ...task, due_date: dueDate || null }) }
  const launch = async () => { setBusy(true); try { const path = task.task_format === 'quiz' ? `/api/quiz/${task.id}` : `/api/practice_sprint/${task.id}`; setAssessment({ ...(await api(path)), kind: task.task_format }) } catch (e) { window.alert(e.message) } finally { setBusy(false) } }
  const skipTask = async () => { setBusy(true); setError(''); try { await api('/api/skip_task', { method: 'POST', body: JSON.stringify({ taskId: task.id }) }); const next = { ...task, is_completed: true, is_skipped: true }; onUpdate(next); onCompleted(next) } catch (e) { setError(e.message) } finally { setBusy(false) } }
  if (assessment) return <Assessment data={assessment} onClose={() => setAssessment(null)} />
  if (statPrompt) return <Modal onClose={() => finishMilestone(false)}><div className="milestone-mark"><Trophy /></div><div className="modal-kicker">MILESTONE COMPLETE</div><h2>Record the progress behind the win.</h2><p className="milestone-copy">This keeps your stats, tracker, and next path grounded in what actually changed.</p><label className="milestone-input">{stat.label}<input autoFocus type="number" value={statValue} onChange={e => setStatValue(e.target.value)} placeholder={stat.placeholder} min={stat.min} max={stat.max} step={stat.step || 1} /></label>{error && <p className="form-error">{error}</p>}<div className="modal-actions"><button className="button button--quiet" onClick={() => finishMilestone(false)} disabled={busy}>Skip for now</button><button className="button button--primary" onClick={() => finishMilestone(true)} disabled={busy || statValue === ''}>Save progress <ArrowRight /></button></div></Modal>
  return <Modal onClose={onClose}><div className="modal-kicker">{category} · {task.type === 'milestone' ? 'Milestone' : 'Action step'}</div><h2><PlainText value={task.description} /></h2><Markdown>{task.reason || ''}</Markdown>
    <div className="task-deadline"><label>Target date<input type="date" value={dueDate} onChange={e => setDueDate(e.target.value)} /></label><button onClick={saveDeadline}>Save date</button></div><div className="task-notes"><label>Notes and sub-steps</label>{task.subtasks.map(s => <button key={s.id} className={s.is_completed ? 'checked' : ''} onClick={() => toggleNote(s)}><span>{s.is_completed && <Check />}</span>{s.description}</button>)}<div><input value={note} onChange={e => setNote(e.target.value)} onKeyDown={e => e.key === 'Enter' && addNote()} placeholder="Add a note or smaller step" /><button onClick={addNote} disabled={!note.trim()}><Plus /></button></div></div>{error && <p className="form-error">{error}</p>}
    <div className="modal-actions">{task.task_format === 'practice_sprint' && <a className="button button--quiet" href={`/strategy_article/${task.id}`} target="_blank" rel="noreferrer"><BookOpen /> Strategy guide</a>}{['quiz', 'practice_sprint'].includes(task.task_format) && <button className="button button--quiet" onClick={launch} disabled={busy}>Start {task.task_format === 'quiz' ? 'quiz' : 'sprint'}</button>}{['quiz', 'practice_sprint'].includes(task.task_format) && !task.is_skipped && <button className="button button--quiet" onClick={skipTask} disabled={busy}>Skip this step</button>}<button className="button button--primary" onClick={complete} disabled={busy || task.is_completed}>{task.is_completed ? 'Completed' : 'Mark complete'} <Check /></button></div>
  </Modal>
}

function AddTask({ category, onClose, onAdded }) { const [description, setDescription] = useState(''); const [date, setDate] = useState(''); const [error, setError] = useState(''); const submit = async e => { e.preventDefault(); setError(''); try { const r = await api('/api/add_task', { method: 'POST', body: JSON.stringify({ description, category, due_date: date || null }) }); onAdded(r.task) } catch (x) { setError(x.message) } }; return <Modal onClose={onClose}><div className="modal-kicker">ADD A PERSONAL STEP</div><h2>Make the path yours.</h2><form className="modal-form" onSubmit={submit}><label>What do you want to do?<textarea autoFocus value={description} onChange={e => setDescription(e.target.value)} placeholder="Write a clear, finishable action" maxLength={500} /></label><label>Due date <span>optional</span><input type="date" value={date} onChange={e => setDate(e.target.value)} /></label>{error && <p className="form-error">{error}</p>}<button className="button button--primary" disabled={!description.trim()}>Add to path <ArrowRight /></button></form></Modal> }

function Assessment({ data, onClose }) {
  const [answers, setAnswers] = useState({}); const [result, setResult] = useState(null); const [busy, setBusy] = useState(false); const [error, setError] = useState(''); const questions = data.questions || []
  const submit = async () => { setBusy(true); setError(''); const rows = questions.map(q => ({ question_id: q.id, selected_option: Number(answers[q.id]) })); try { setResult(await api(data.kind === 'quiz' ? '/api/submit_quiz_results' : '/api/submit_sprint_results', { method: 'POST', body: JSON.stringify({ results: rows }) })) } catch (e) { setError(e.message) } finally { setBusy(false) } }
  return <Modal onClose={onClose} wide><div className="modal-kicker">FOCUSED CHECK</div><h2>{data.title}</h2>{result == null ? <><div className="questions">{questions.map((q, i) => <fieldset key={q.id}><legend>Question {i + 1}</legend>{q.source_or_prompt && <div className="question-source"><small>SOURCE / PROMPT</small><Markdown>{q.source_or_prompt}</Markdown></div>}<p className="question-copy">{q.question_text}</p>{q.options.map((o, oi) => <label key={oi}><input type="radio" name={`q-${q.id}`} checked={Number(answers[q.id]) === oi} onChange={() => setAnswers({ ...answers, [q.id]: oi })} /><span>{o}</span></label>)}</fieldset>)}</div>{error && <p className="form-error">{error}</p>}<button className="button button--primary" disabled={busy || Object.keys(answers).length !== questions.length} onClick={submit}>{busy ? 'Checking…' : 'Check answers'}</button></> : <div className="assessment-result"><Trophy /><h3>{result.correct} of {result.total} correct</h3><p>Review the explanations, then mark this path step complete when you are ready.</p>{questions.map((q, i) => { const detail = result.results?.find(row => row.question_id === q.id); return <details key={q.id}><summary>Question {i + 1} · {detail?.is_correct ? 'Correct' : 'Review'}</summary>{q.source_or_prompt && <div className="question-source"><small>SOURCE / PROMPT</small><Markdown>{q.source_or_prompt}</Markdown></div>}<p className="question-copy">{q.question_text}</p><p>{detail?.explanation || 'Review this concept and try a similar question.'}</p></details> })}<button className="button button--dark" onClick={onClose}>Back to task</button></div>}</Modal>
}

function EssayCoach({ onClose }) { const [prompt, setPrompt] = useState(''); const [essay, setEssay] = useState(''); const [feedback, setFeedback] = useState(''); const [busy, setBusy] = useState(false); const analyze = async () => { if (essay.trim().length < 50) return; setBusy(true); try { setFeedback((await api('/api/analyze_essay', { method: 'POST', body: JSON.stringify({ essay_text: essay, essay_prompt: prompt || 'a general college application essay' }) })).feedback) } catch (e) { setFeedback(e.message) } finally { setBusy(false) } }; return <Modal onClose={onClose} wide><div className="modal-kicker">MENTICS ESSAY COACH</div><h2>Strengthen the essay without losing your voice.</h2><div className="essay-workspace"><label>Essay prompt<input value={prompt} onChange={e => setPrompt(e.target.value)} placeholder="Common App prompt or supplemental question" /></label><label>Essay draft<textarea value={essay} onChange={e => setEssay(e.target.value)} rows="12" maxLength="20000" placeholder="Paste your draft here..." /></label><button className="button button--primary" onClick={analyze} disabled={busy || essay.trim().length < 50}>{busy ? 'Analyzing…' : 'Get structured feedback'} <Sparkles /></button>{feedback && <div className="essay-feedback"><Markdown>{feedback}</Markdown></div>}</div></Modal> }

function ChatPanel({ open, onClose, category, onNewPath }) {
  const [messages, setMessages] = useState([]); const [input, setInput] = useState(''); const [busy, setBusy] = useState(false); const [historyError, setHistoryError] = useState(''); const scroller = useRef(null)
  useEffect(() => { if (open && messages.length === 0) { api(`/api/chat_history?category=${encodeURIComponent(category)}`).then(h => setMessages(Array.isArray(h) && h.length ? h : [{ role: 'assistant', content: `I’m here with your ${category.toLowerCase()} path. Ask about any step, concept, or roadblock.` }])).catch(() => { setHistoryError('I couldn’t restore the earlier conversation, but you can start a new one here.'); setMessages([{ role: 'assistant', content: `I’m ready to help with your ${category.toLowerCase()} path.` }]) }) } }, [open, category, messages.length])
  useEffect(() => { const node = scroller.current; if (node) node.scrollTo({ top: node.scrollHeight, behavior: 'smooth' }) }, [messages, busy])
  const send = async e => { e.preventDefault(); if (!input.trim() || busy) return; const next = [...messages, { role: 'user', content: input.trim() }]; setMessages(next); setInput(''); setBusy(true); try { const r = await api(`/api/chat?category=${encodeURIComponent(category)}`, { method: 'POST', body: JSON.stringify({ history: next }) }); if (Object.prototype.hasOwnProperty.call(r, 'new_path')) { if (!Array.isArray(r.new_path) || r.new_path.length !== 5) throw new Error('Mentics could not build a complete five-step path. Your current path is unchanged.'); onNewPath(r.new_path); setMessages([...next, { role: 'assistant', content: r.reply || 'Your new five-step path is ready. I used our conversation to shape it.' }]) } else setMessages([...next, { role: 'assistant', content: r.reply }]) } catch (x) { setMessages([...next, { role: 'assistant', content: x.message }]) } finally { setBusy(false) } }
  const reset = async () => { try { await api('/api/reset_chat', { method: 'POST', body: JSON.stringify({ category }) }); setHistoryError(''); setMessages([{ role: 'assistant', content: `Fresh start. What would you like help with on your ${category.toLowerCase()} path?` }]) } catch (error) { setHistoryError(error.message) } }
  return <aside className={`chat-panel ${open ? 'chat-panel--open' : ''}`} aria-hidden={!open}><header><span><i><Sparkles /></i><b>Mentics guide</b><small>Present with your current path</small></span><div><button onClick={reset} aria-label="Reset chat"><RotateCcw /></button><button onClick={onClose} aria-label="Close chat"><X /></button></div></header>{historyError && <div className="chat-notice" role="status">{historyError}</div>}<div className="chat-messages" ref={scroller}>{messages.map((m, i) => <div className={`chat-message chat-message--${m.role}`} key={i}>{m.role === 'assistant' ? <Markdown>{m.content}</Markdown> : m.content}</div>)}{busy && <div className="chat-thinking"><i /><i /><i /></div>}</div><form onSubmit={send}><textarea name="message" aria-label="Ask Mentics about your path" value={input} onChange={e => setInput(e.target.value)} onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(e) } }} placeholder="Ask about your path…" rows={1} /><button disabled={!input.trim() || busy} aria-label="Send"><Send /></button></form><p>Mentics can make mistakes. Check important information.</p></aside>
}

function PageIntro({ kicker, title, copy, actions }) {
  return <div className="page-intro page-intro--color"><div><div className="eyebrow"><span /> {kicker}</div><h1>{title}</h1>{copy && <p>{copy}</p>}</div>{actions && <div className="page-actions">{actions}</div>}</div>
}

function AuthPage({ mode }) {
  const signup = mode === 'signup'
  return <div className="auth-page"><div className="auth-brand"><Brand /></div><div className="auth-art"><span className="shape shape--peach" /><span className="shape shape--mint" /><div><small>YOUR NEXT CHAPTER</small><h1>Ambition feels better with a plan.</h1><p>Build momentum across test prep, college planning, and every goal between.</p></div></div><main className="auth-panel"><div className="auth-copy"><small>{signup ? 'START YOUR PATH' : 'WELCOME BACK'}</small><h2>{signup ? 'Join Mentics.' : 'Continue building.'}</h2><p>{signup ? 'Your focused workspace is a minute away.' : 'Your goals and progress are waiting.'}</p></div>{boot.data.error && <div className="form-error" role="alert">{boot.data.error}</div>}<form method="POST" className="react-form"><CsrfField />{signup && <label>Full name<input name="name" autoComplete="name" required maxLength="100" placeholder="Your name" /></label>}<label>Email address<input type="email" name="email" autoComplete="email" required placeholder="you@example.com" /></label><label>Password<input type="password" name="password" autoComplete={signup ? 'new-password' : 'current-password'} minLength={signup ? 8 : undefined} maxLength="128" required placeholder={signup ? 'At least 8 characters' : 'Your password'} /></label><button className="button button--primary" type="submit">{signup ? 'Create my account' : 'Sign in'} <ArrowRight /></button></form><div className="form-divider"><span>or</span></div><a className="google-button" href="/google-login"><span>G</span> Continue with Google</a><p className="auth-switch">{signup ? 'Already have an account?' : 'New to Mentics?'} <a href={signup ? '/login' : '/signup'}>{signup ? 'Sign in' : 'Create an account'}</a></p></main></div>
}

const learningOptions = [['visual', 'Visual', Sparkles, 'I learn by seeing'], ['auditory', 'Auditory', Headphones, 'I learn by hearing'], ['reading_writing', 'Reading / writing', PenLine, 'I learn through words'], ['kinesthetic', 'Hands-on', Hand, 'I learn by doing']]
function Onboarding() {
  const [step, setStep] = useState(0); const [goal, setGoal] = useState(''); const [style, setStyle] = useState(''); const canNext = step === 0 ? goal : style
  return <div className="onboarding-page"><header><Brand /><span>Step {step + 1} of 3</span></header><main><div className="onboarding-progress"><i style={{ width: `${(step + 1) / 3 * 100}%` }} /></div>{boot.data.error && <div className="form-error">{boot.data.error}</div>}<form method="POST"><section className={step === 0 ? 'active' : ''}><div className="eyebrow"><span /> START WITH DIRECTION</div><h1>What are we building toward?</h1><p>This sets the first version of your Mentics workspace.</p><div className="choice-grid choice-grid--two">{[['test_prep', 'Test preparation', BookOpen, 'Build confidence for the SAT or ACT'], ['college_planning', 'College planning', GraduationCap, 'Turn applications into a clear process']].map(([value, label, Icon, copy]) => <label className={goal === value ? 'selected' : ''} key={value}><input type="radio" name="goal" value={value} required checked={goal === value} onChange={() => setGoal(value)} /><Icon /><b>{label}</b><small>{copy}</small></label>)}</div></section><section className={step === 1 ? 'active' : ''}><div className="eyebrow"><span /> MAKE IT YOURS</div><h1>How do you learn best?</h1><p>Your tasks and explanations will use this preference.</p><div className="choice-grid">{learningOptions.map(([value, label, Icon, copy]) => <label className={style === value ? 'selected' : ''} key={value}><input type="radio" name="learning_style" value={value} required checked={style === value} onChange={() => setStyle(value)} /><Icon /><b>{label}</b><small>{copy}</small></label>)}</div></section><section className={step === 2 ? 'active' : ''}><div className="eyebrow"><span /> ONE LAST THING</div><h1>What feels hardest right now?</h1><p>Be honest. This helps Mentics meet you where you are.</p><textarea name="anxieties" rows="6" placeholder="Time management, test anxiety, essays, choosing schools..." /></section><div className="onboarding-actions">{step > 0 ? <button type="button" className="button button--quiet" onClick={() => setStep(step - 1)}><ArrowLeft /> Back</button> : <span />}{step < 2 ? <button type="button" className="button button--primary" disabled={!canNext} onClick={() => setStep(step + 1)}>Continue <ArrowRight /></button> : <button type="submit" className="button button--primary">Build my workspace <ArrowRight /></button>}</div></form></main></div>
}

function StatsPage() {
  const d = boot.data; const value = v => v || '—'
  return <AppShell name={d.name}><main className="app-main"><PageIntro kicker="YOUR PROGRESS" title="The numbers behind the work." copy="A clear snapshot of where you are and how far you have moved." actions={<a className="button button--primary" href="/dashboard/stats/edit">Update scores <ArrowRight /></a>} /><section className="stat-hero-grid"><article className="stat-feature stat-feature--gpa"><small>CURRENT GPA</small><strong>{value(d.gpa)}</strong><p>Your academic foundation</p></article><article className="stat-feature stat-feature--tasks"><small>PATH MILESTONES</small><strong>{(d.totalTestPrepCompleted || 0) + (d.totalCollegePlanningCompleted || 0)}</strong><p>{d.totalTestPrepCompleted || 0} test prep · {d.totalCollegePlanningCompleted || 0} college</p></article></section><section className="score-panels"><article><div><small>SAT SNAPSHOT</small><h2>{value(d.satTotal)}</h2></div><dl><div><dt>Reading & writing</dt><dd>{value(d.satEbrw)}</dd></div><div><dt>Math</dt><dd>{value(d.satMath)}</dd></div></dl></article><article><div><small>ACT SNAPSHOT</small><h2>{value(d.actAverage)}</h2></div><dl><div><dt>Math</dt><dd>{value(d.actMath)}</dd></div><div><dt>Reading</dt><dd>{value(d.actReading)}</dd></div><div><dt>Science</dt><dd>{value(d.actScience)}</dd></div></dl></article></section></main></AppShell>
}

const scoreFields = [['gpa', 'GPA', '0', '5', '0.01'], ['sat_ebrw', 'SAT reading & writing', '200', '800', '10'], ['sat_math', 'SAT math', '200', '800', '10'], ['act_math', 'ACT math', '1', '36', '1'], ['act_reading', 'ACT reading', '1', '36', '1'], ['act_science', 'ACT science', '1', '36', '1']]
function EditStats() { const d = boot.data; const values = { gpa: d.gpa, sat_ebrw: d.satEbrw, sat_math: d.satMath, act_math: d.actMath, act_reading: d.actReading, act_science: d.actScience }; return <AppShell name={d.name}><main className="app-main form-page"><PageIntro kicker="UPDATE PROGRESS" title="Keep your snapshot honest." copy="New numbers help every future path respond to your real progress." /><form method="POST" className="settings-form"><div className="form-field-grid">{scoreFields.map(([name, label, min, max, step]) => <label key={name}>{label}<small>{min}–{max}</small><input type="number" name={name} min={min} max={max} step={step} defaultValue={values[name] || ''} /></label>)}</div><div className="form-actions"><a className="button button--quiet" href="/dashboard/stats">Cancel</a><button className="button button--primary" type="submit">Save progress <Check /></button></div></form></main></AppShell> }

function Field({ name, label, textarea = false, value, ...props }) { return <label>{label}{textarea ? <textarea name={name} rows="4" defaultValue={value || ''} {...props} /> : <input name={name} defaultValue={value || ''} {...props} />}</label> }
function BuilderPage({ kind }) { const d = boot.data; const test = kind === 'test'; const [focus, setFocus] = useState(d.test_focus || ''); return <AppShell name={d.name}><main className="app-main form-page"><PageIntro kicker={test ? 'TEST PREPARATION' : 'COLLEGE PLANNING'} title={test ? 'Design your next five steps.' : 'Build a college plan that fits.'} copy={test ? 'Tell Mentics what the score alone cannot show.' : 'Turn a wide-open process into focused, personal action.'} /><form method="POST" className="settings-form builder-form">{test ? <><fieldset><legend>Which test are you preparing for?</legend><div className="choice-grid choice-grid--three">{[['sat', 'SAT only'], ['act', 'ACT only'], ['both', 'SAT + ACT']].map(([value, label]) => <label className={focus === value ? 'selected' : ''} key={value}><input type="radio" name="test_focus" value={value} required checked={focus === value} onChange={() => setFocus(value)} /><BookOpen /><b>{label}</b></label>)}</div></fieldset><div className="form-field-grid"><Field name="desired_sat" label="Desired SAT" type="number" min="400" max="1600" step="10" value={d.desired_sat} /><Field name="desired_act" label="Desired ACT" type="number" min="1" max="36" value={d.desired_act} /><Field name="current_sat_ebrw" label="Current SAT reading & writing" type="number" min="200" max="800" value={d.current_sat_ebrw} /><Field name="current_sat_math" label="Current SAT math" type="number" min="200" max="800" value={d.current_sat_math} /><Field name="current_act_composite" label="Current ACT composite" type="number" min="1" max="36" value={d.current_act_composite} /><Field name="current_act_math" label="Current ACT math" type="number" min="1" max="36" value={d.current_act_math} /><Field name="current_act_reading" label="Current ACT reading" type="number" min="1" max="36" value={d.current_act_reading} /><Field name="current_act_science" label="Current ACT science" type="number" min="1" max="36" value={d.current_act_science} /><Field name="hours_per_week" label="Hours available each week" type="number" min="1" max="40" value={d.hours_per_week} /></div><Field name="strengths" label="Your strengths" textarea value={d.strengths} /><Field name="weaknesses" label="Where you need the most help" textarea required value={d.weaknesses} /><Field name="test_date" label="Test date" type="date" value={d.test_date} /></> : <><div className="form-field-grid"><label>Current grade<select name="current_grade" required defaultValue={d.grade || ''}><option value="">Choose grade</option>{['9', '10', '11', '12'].map(v => <option value={v} key={v}>{v}th grade</option>)}</select></label><label>Planning stage<select name="planning_stage" required defaultValue={d.planning_stage || ''}><option value="">Choose stage</option><option value="exploring">Exploring options</option><option value="researching">Researching colleges</option><option value="applying">Ready to apply</option></select></label></div><Field name="interested_majors" label="Interested majors" textarea value={d.majors} /><Field name="target_colleges" label="Target colleges" textarea value={d.target_colleges} /></>}<div className="form-actions"><a className="button button--quiet" href="/dashboard">Cancel</a><button className="button button--primary" type="submit">Build my five-step path <ArrowRight /></button></div></form></main></AppShell> }

function HistoryBars({ records = [] }) { const vals = records.map(r => Number(r.value) || 0); const max = Math.max(...vals, 1); return <div className="history-bars">{records.slice(-12).map((r, i) => <div key={`${r.date}-${i}`}><i style={{ height: `${Math.max(8, (Number(r.value) || 0) / max * 100)}%` }} /><small>{String(r.date).slice(5)}</small></div>)}</div> }
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
  return <AppShell name={d.name}><main className="app-main"><PageIntro kicker="PROGRESS TRACKER" title="See the shape of your effort." copy="Scores, paths, and patterns come together here." actions={<button className="button button--primary" onClick={analyze} disabled={loading}><Brain /> {loading ? 'Analyzing…' : 'Analyze my progress'}</button>} />{analysis && <article className="analysis-panel"><div><Sparkles /><small>MENTICS ANALYSIS</small></div><Markdown>{analysis}</Markdown></article>}<section className="tracker-layout"><article className="trend-panel"><div className="tracker-metric-tabs">{metricKeys.length ? metricKeys.slice(0, 7).map(key => <button className={metric === key ? 'active' : ''} onClick={() => setMetric(key)} key={key}>{key.replaceAll('_', ' ')}</button>) : <span>No score history yet</span>}</div><div className="card-top"><div><small>PRIMARY TREND</small><h2>{metric?.replaceAll('_', ' ') || 'No history yet'}</h2></div><LineChart /></div>{records.length ? <HistoryBars records={records} /> : <div className="empty-state"><LineChart /><p>Update your scores to begin a trend line.</p></div>}</article><article className="kpi-panel"><small>KEY METRICS</small>{Object.entries(d.kpis || {}).slice(0, 6).map(([key, v]) => <div key={key}><span>{key.replaceAll('_', ' ')}</span><b>{v.latest}</b><small>{v.improvement > 0 ? `+${v.improvement}` : v.improvement || 'No change'}</small></div>)}</article></section><section className="history-section history-section--tabs"><header><h2>Path history</h2><div><button className={historyTab === 'test' ? 'active' : ''} onClick={() => setHistoryTab('test')}>Test Prep</button><button className={historyTab === 'college' ? 'active' : ''} onClick={() => setHistoryTab('college')}>College Planning</button></div></header><article>{history?.length ? history.slice(0, 8).map((gen, i) => <details key={i}><summary>{String(gen.date).slice(0, 10)} <span>{gen.tasks?.filter(t => t.is_completed).length || 0}/{gen.tasks?.length || 0} complete</span></summary><ol>{gen.tasks?.map(t => <li key={t.id} className={t.is_completed ? 'done' : ''}>{t.description}</li>)}</ol></details>) : <p>No paths yet.</p>}</article></section></main></AppShell>
}

function ForumPage() { const d = boot.data; const [creating, setCreating] = useState(false); const [busy, setBusy] = useState(false); const submitPost = async e => { e.preventDefault(); setBusy(true); const form = new FormData(e.currentTarget); try { await api('/api/posts', { method: 'POST', body: JSON.stringify({ title: form.get('title'), content: form.get('content') }) }); window.location.reload() } finally { setBusy(false) } }; const reply = async (postId, e) => { e.preventDefault(); setBusy(true); const form = new FormData(e.currentTarget); try { await api('/api/replies', { method: 'POST', body: JSON.stringify({ post_id: postId, content: form.get('content') }) }); window.location.reload() } finally { setBusy(false) } }; return <AppShell name={d.name}><main className="app-main"><PageIntro kicker="MENTICS COMMUNITY" title="Students helping students." copy="Compare approaches, ask better questions, and move forward together." actions={<button className="button button--primary" onClick={() => setCreating(!creating)}><Plus /> New discussion</button>} />{creating && <form className="new-post-panel" onSubmit={submitPost}><Field name="title" label="Discussion title" required /><Field name="content" label="What do you want to share or ask?" textarea required /><button className="button button--primary" disabled={busy}>Publish discussion</button></form>}<form className="forum-search" method="GET"><Search /><input name="search" defaultValue={d.searchQuery || ''} placeholder="Search discussions" /><button>Search</button></form><section className="forum-layout"><div className="thread-list">{d.posts?.length ? d.posts.map(post => <article className="thread" key={post.id}><header><span>{String(post.user_name || 'M').slice(0, 1)}</span><div><b>{post.title}</b><small>{post.user_name} · {String(post.created_at).slice(0, 10)}</small></div></header><p>{post.content}</p>{post.replies?.length > 0 && <div className="replies">{post.replies.map(r => <div key={r.id}><b>{r.user_name}</b><p>{r.content}</p></div>)}</div>}<form onSubmit={e => reply(post.id, e)}><input name="content" required placeholder="Add a thoughtful reply" /><button disabled={busy}><Send /></button></form></article>) : <div className="empty-state"><MessageCircle /><p>No discussions match this search yet.</p></div>}</div><aside className="community-aside"><UsersRound /><h3>Today in Mentics</h3><strong>{d.todaysThreads?.length || 0}</strong><span>new discussions</span><p>Keep posts specific, respectful, and useful to the next student.</p></aside></section></main></AppShell> }

function LeaderboardPage() { const d = boot.data; return <AppShell name={d.name}><main className="app-main"><PageIntro kicker="COMMUNITY MOMENTUM" title="Consistency deserves the spotlight." copy="Points celebrate completed work—not comparison for its own sake." /><section className="leaderboard-list">{d.leaderboard?.map((row, index) => <article className={index < 3 ? 'top' : ''} key={`${row.name}-${index}`}><span>{index + 1}</span><div>{String(row.name || 'M').slice(0, 1).toUpperCase()}</div><b>{row.name}</b><strong>{row.points} pts</strong>{index === 0 && <Trophy />}</article>)}</section></main></AppShell> }

function AccountPage() { const d = boot.data; return <AppShell name={d.name}><main className="app-main form-page"><PageIntro kicker="YOUR ACCOUNT" title="Make Mentics yours." copy="Keep your identity and sign-in details current." />{d.updated && <div className="success-banner"><Check /> Your account was updated.</div>}{d.error && <div className="form-error">{d.error}</div>}<section className="account-sections"><form method="POST"><input type="hidden" name="form_type" value="name" /><div><UserRound /><span><h2>Your name</h2><p>How Mentics addresses you.</p></span></div><Field name="name" label="Full name" value={d.name} required maxLength="100" /><button className="button button--primary">Save name</button></form><form method="POST"><input type="hidden" name="form_type" value="email" /><div><Mail /><span><h2>Email address</h2><p>Where you sign in.</p></span></div><Field name="email" label="Email" type="email" value={d.email} required maxLength="254" /><button className="button button--primary">Save email</button></form><form method="POST"><input type="hidden" name="form_type" value="password" /><div><ShieldCheck /><span><h2>Password</h2><p>Use at least eight characters.</p></span></div><Field name="current_password" label="Current password" type="password" required maxLength="128" /><Field name="new_password" label="New password" type="password" minLength="8" maxLength="128" required /><Field name="confirm_password" label="Confirm new password" type="password" minLength="8" maxLength="128" required /><button className="button button--primary">Change password</button></form></section><form className="logout-link" method="POST" action="/logout"><CsrfField /><button type="submit">Sign out of Mentics <ArrowRight /></button></form></main></AppShell> }

const legalCopy = {
  privacy: {
    title: 'Privacy Policy', date: 'October 9, 2025',
    intro: 'Welcome to Mentics. This policy explains how Mentics collects, uses, discloses, and safeguards information when you use our website and services.',
    sections: [
      ['1. Information we collect', 'We collect account information such as your name, email, and securely hashed password or Google profile details. Educational data can include goals, learning style, anxieties, GPA, SAT/ACT scores, strengths, weaknesses, test dates, grade level, majors, and target colleges. We also collect content you choose to submit, including forum posts and replies, AI-assistant conversations, essays and prompts, plus activity data such as completed tasks, generated paths, and stat updates. Our servers may also receive technical information such as IP address, browser, operating system, access times, and viewed pages.'],
      ['2. How we use information', 'We use this information to create and manage accounts; generate personalized test-prep and college-planning paths; provide contextual chat and essay feedback; operate the forum and leaderboard; display progress; analyze and improve Mentics; and administer points, streaks, and achievements.'],
      ['3. Disclosure of information', 'Mentics does not sell personal information. We may disclose information when required by law or needed to protect rights, property, and safety. We share inputs such as chat messages and essay text with Google Gemini only to provide the AI features you request, subject to Google’s privacy policies. We do not currently share user information with third-party advertisers.'],
      ["4. Children's privacy", 'Mentics is intended for high school students generally over age 13. We do not knowingly collect personally identifiable information from children under 13. If we learn that a user is under 13, we will require verifiable parental consent; parents or guardians may contact us to request appropriate action.'],
      ['5. Your rights and choices', 'You may review or change account information from account settings and may contact us to opt out of communications or ask about your information.'],
      ['6. Security', 'We use administrative, technical, and physical safeguards designed to protect personal information. No security measure or method of transmission can be guaranteed against every interception or misuse.'],
      ['7. Contact us', 'Questions or comments about this policy can be sent to thementicsapp@gmail.com.']
    ]
  },
  terms: {
    title: 'Terms of Service', date: 'October 9, 2025',
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
      ['9. Termination', 'Mentics may terminate or suspend an account immediately and without prior notice or liability, including for a breach of these terms.'],
      ['10. Governing law and disputes', 'These terms are governed by the laws of Georgia, United States. Disputes will be resolved through binding arbitration in Cumming, Georgia, except qualifying small-claims matters.'],
      ['11. Limitation of liability', 'Mentics, its directors, employees, and agents are not liable for indirect, incidental, special, consequential, or punitive damages, including loss of profits, data, or goodwill, arising from use of the service or its content.'],
      ['12. Changes', 'Mentics may modify these terms. If a revision is material, we will provide at least 30 days’ notice before the new terms take effect.'],
      ['13. Contact us', 'Questions about these terms can be sent to thementicsapp@gmail.com.']
    ]
  }
}
function LegalPage({ type }) { const d = legalCopy[type]; return <div className="legal-page"><header><Brand /><a href="/"><ArrowLeft /> Back to Mentics</a></header><main><div className="legal-title"><small>MENTICS LEGAL</small><h1>{d.title}</h1><p>Last updated {d.date}</p></div><p className="legal-intro">{d.intro}</p>{d.sections.map(([title, copy]) => <section key={title}><h2>{title}</h2><p>{copy}</p></section>)}</main></div> }
function ArticlePage() { const d = boot.data; return <AppShell name={d.name}><main className="app-main article-page"><a href="/dashboard/test-path-view" className="text-button"><ArrowLeft /> Back to path</a><article><div className="eyebrow"><span /> STRATEGY GUIDE</div><h1>{d.article?.title}</h1><Markdown>{d.article?.content || 'This article is not available yet.'}</Markdown></article></main></AppShell> }

function App() { switch (boot.page) { case 'dashboard': return <Dashboard />; case 'path': return <PathPage />; case 'login': return <AuthPage mode="login" />; case 'signup': return <AuthPage mode="signup" />; case 'onboarding': return <Onboarding />; case 'stats': return <StatsPage />; case 'edit-stats': return <EditStats />; case 'test-builder': return <BuilderPage kind="test" />; case 'college-builder': return <BuilderPage kind="college" />; case 'tracker': return <TrackerPage />; case 'forum': return <ForumPage />; case 'leaderboard': return <LeaderboardPage />; case 'account': return <AccountPage />; case 'privacy': return <LegalPage type="privacy" />; case 'terms': return <LegalPage type="terms" />; case 'article': return <ArticlePage />; default: return <Landing /> } }

createRoot(document.getElementById('root')).render(<React.StrictMode><CsrfBootstrap /><App /></React.StrictMode>)
