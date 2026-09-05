import { useEffect, useRef, useState } from 'react'
import { ArrowRight, BookOpen, Check, GraduationCap, Sparkles, Target, LockKeyhole, Flag } from 'lucide-react'
import './home-hero.css'
import './hero-scroll-story.css'

const previews = {
  SAT: { title: 'Make the next point count.', focus: 'Master linear equations', subject: 'Math · Focused practice', steps: ['Find your starting point', 'Learn the strategy', 'Practice with purpose', 'Understand every miss', 'Build your next path'], icon: Target },
  ACT: { title: 'Find your strongest approach.', focus: 'Sharpen your reading strategy', subject: 'Reading · Targeted strategy', steps: ['Set your ACT target', 'Find your section focus', 'Practice with purpose', 'Review your approach', 'Plan your next session'], icon: BookOpen },
  College: { title: 'Make your next chapter yours.', focus: 'Build a balanced college list', subject: 'College planning · Find your fit', steps: ['Define what matters to you', 'Learn what makes a good fit', 'Research your shortlist', 'Bring your findings back', 'Choose your next move'], icon: GraduationCap },
}

/* Scroll drives a camera rig: the sculpture orbits, drops toward eye level, and dollies in. */
const CAMERA = [
  { p: 0, rx: 48, ry: 0, rz: -27, dz: 0, ox: 50, oy: 50, tx: 0, ty: 0, sc: 1 },
  { p: .3, rx: 41, ry: 7, rz: -21, dz: 45, ox: 36, oy: 55, tx: -24, ty: -14, sc: 1.03 },
  { p: .64, rx: 35, ry: 12, rz: -15, dz: 85, ox: 63, oy: 60, tx: -14, ty: -24, sc: 1.05 },
  { p: 1, rx: 30, ry: 9, rz: -8, dz: 112, ox: 71, oy: 66, tx: 4, ty: -12, sc: 1.04 },
]
const CAMERA_VARS = [['--cam-x', 'rx', 'deg'], ['--cam-y', 'ry', 'deg'], ['--cam-z', 'rz', 'deg'], ['--cam-dolly', 'dz', 'px'], ['--cam-origin-x', 'ox', '%'], ['--cam-origin-y', 'oy', '%']]
const PANELS = [{ enter: [0, 0], exit: [.11, .23] }, { enter: [.19, .31], exit: [.53, .63] }, { enter: [.61, .73], exit: [2, 3] }]
const STEP_STOPS = [[.17, 2], [.33, 0], [.49, 1], [.65, 2], [.81, 3], [2, 4]]
const clamp = value => value < 0 ? 0 : value > 1 ? 1 : value
const smooth = value => value * value * (3 - 2 * value)
const cameraAt = progress => {
  let index = 1
  while (index < CAMERA.length - 1 && progress > CAMERA[index].p) index += 1
  const from = CAMERA[index - 1], to = CAMERA[index]
  const eased = smooth(clamp((progress - from.p) / (to.p - from.p)))
  const frame = {}
  for (const key in to) frame[key] = from[key] + (to[key] - from[key]) * eased
  return frame
}

export function HomeHero({ loggedIn }) {
  const [track, setTrack] = useState('SAT')
  const [activeStep, setActiveStep] = useState(2)
  const sceneRef = useRef(null)
  const heroRef = useRef(null)
  const storyRef = useRef(null)
  const visualRef = useRef(null)
  const progressRef = useRef(null)
  const panelsRef = useRef([])
  const [chapter, setChapter] = useState(0)
  useEffect(() => {
    const story = storyRef.current
    const hero = heroRef.current
    const sculpture = sceneRef.current
    const visual = visualRef.current
    const enabled = window.matchMedia('(prefers-reduced-motion: no-preference) and (min-height: 650px)')
    const route = sculpture.querySelector('.path-route-active')
    const parallax = [['.home-hero-grid', 0, -70], ['.home-hero-halo', 54, -46], ['.home-hero-orbit--outer', -34, 26], ['.hero-left-art', -46, -20]].map(([selector, x, y]) => [hero.querySelector(selector), x, y])
    const prompt = hero.querySelector('.hero-scroll-prompt')
    let frame = 0, range = 1, mobile = false
    let lastChapter = -1, lastStep = -1
    const measure = () => { range = Math.max(1, story.offsetHeight - hero.offsetHeight); mobile = window.innerWidth <= 900 }
    const render = () => {
      frame = 0
      if (!enabled.matches) {
        panelsRef.current.forEach(panel => { panel.style.opacity = ''; panel.style.transform = '' })
        CAMERA_VARS.forEach(([name]) => sculpture.style.removeProperty(name))
        parallax.forEach(([node]) => { if (node) node.style.translate = '' })
        if (prompt) prompt.style.opacity = ''
        visual.style.transform = ''
        story.dataset.scroll = 'static'
        setChapter(-1)
        return
      }
      story.dataset.scroll = 'active'
      const progress = clamp(-story.getBoundingClientRect().top / range)
      const current = progress < .17 ? 0 : progress < .58 ? 1 : 2
      if (current !== lastChapter) { lastChapter = current; setChapter(current) }
      const step = STEP_STOPS.find(([edge]) => progress < edge)[1]
      if (step !== lastStep) { lastStep = step; setActiveStep(step) }
      panelsRef.current.forEach((panel, index) => {
        if (!panel) return
        const { enter, exit } = PANELS[index]
        const arriving = enter[1] > enter[0] ? clamp((progress - enter[0]) / (enter[1] - enter[0])) : 1
        const leaving = clamp((progress - exit[0]) / (exit[1] - exit[0]))
        panel.style.opacity = smooth(arriving) * (1 - smooth(leaving))
        panel.style.transform = `translate3d(0, ${(1 - arriving) * 46 - leaving * 54}px, 0) scale(${1 - (1 - arriving) * .045 - leaving * .035})`
      })
      const camera = cameraAt(progress)
      const damp = mobile ? .55 : 1
      const shot = key => CAMERA[0][key] + (camera[key] - CAMERA[0][key]) * damp
      CAMERA_VARS.forEach(([name, key, unit]) => sculpture.style.setProperty(name, `${shot(key).toFixed(2)}${unit}`))
      visual.style.transform = `translate3d(${mobile ? 0 : shot('tx').toFixed(2)}px, ${shot('ty').toFixed(2)}px, 0) scale(${shot('sc').toFixed(4)})`
      parallax.forEach(([node, x, y]) => { if (node) node.style.translate = `${(mobile ? 0 : x) * progress}px ${y * progress}px` })
      if (prompt) prompt.style.opacity = String(1 - clamp(progress / .07))
      progressRef.current.style.transform = `scaleX(${progress})`
      route.style.strokeDashoffset = String(100 - clamp((progress - .05) / .8) * 100)
    }
    const schedule = () => { if (!frame) frame = requestAnimationFrame(render) }
    const remeasure = () => { measure(); schedule() }
    window.addEventListener('scroll', schedule, { passive: true })
    window.addEventListener('resize', remeasure)
    enabled.addEventListener('change', remeasure)
    measure()
    render()
    return () => { cancelAnimationFrame(frame); window.removeEventListener('scroll', schedule); window.removeEventListener('resize', remeasure); enabled.removeEventListener('change', remeasure) }
  }, [])
  const goToChapter = index => {
    const story = storyRef.current
    const range = story.offsetHeight - heroRef.current.offsetHeight
    const top = window.scrollY + story.getBoundingClientRect().top + range * [0, .4, .8][index]
    window.scrollTo({ top, behavior: 'smooth' })
  }
  useEffect(() => {
    const hero = heroRef.current
    let visible = true
    const update = () => { hero.dataset.motion = visible && !document.hidden ? 'running' : 'paused' }
    const observer = new IntersectionObserver(([entry]) => { visible = entry.isIntersecting; update() })
    observer.observe(hero)
    document.addEventListener('visibilitychange', update)
    update()
    return () => { observer.disconnect(); document.removeEventListener('visibilitychange', update) }
  }, [])
  useEffect(() => {
    const scene = sceneRef.current
    const motion = window.matchMedia('(prefers-reduced-motion: no-preference) and (pointer: fine) and (min-width: 901px)')
    let frame = 0
    let x = 0, y = 0, vx = 0, vy = 0, targetX = 0, targetY = 0, last = 0
    const tick = now => {
      const dt = Math.min((now - (last || now - 16)) / 1000, .032)
      last = now
      vx += ((targetX - x) * 100 - vx * 18) * dt
      vy += ((targetY - y) * 100 - vy * 18) * dt
      x += vx * dt; y += vy * dt
      scene.style.rotate = `${-y} ${x} 0 ${Math.hypot(x, y)}deg`
      if (Math.abs(targetX - x) + Math.abs(targetY - y) + Math.abs(vx) + Math.abs(vy) > .01) frame = requestAnimationFrame(tick)
      else { frame = 0; last = 0 }
    }
    const start = () => { if (!frame) frame = requestAnimationFrame(tick) }
    const move = event => {
      if (!motion.matches || event.pointerType === 'touch') return
      const box = scene.parentElement.getBoundingClientRect()
      targetX = ((event.clientX - box.left) / box.width - .5) * 10
      targetY = ((event.clientY - box.top) / box.height - .5) * 8
      start()
    }
    const reset = () => { targetX = 0; targetY = 0; start() }
    const preferenceChanged = () => { cancelAnimationFrame(frame); frame = 0; x = y = vx = vy = targetX = targetY = last = 0; scene.style.rotate = '' }
    const parent = scene.parentElement
    parent.addEventListener('pointermove', move)
    parent.addEventListener('pointerleave', reset)
    motion.addEventListener('change', preferenceChanged)
    return () => { cancelAnimationFrame(frame); parent.removeEventListener('pointermove', move); parent.removeEventListener('pointerleave', reset); motion.removeEventListener('change', preferenceChanged) }
  }, [])
  const preview = previews[track]
  const Icon = preview.icon
  return <div className="hero-scroll-story" ref={storyRef}><section className="home-hero" ref={heroRef} aria-labelledby="home-hero-title">
    <div className="home-hero-atmosphere" aria-hidden="true"><div className="home-hero-grid" /><div className="home-hero-halo" /><div className="home-hero-orbit home-hero-orbit--outer" /><div className="home-hero-orbit home-hero-orbit--inner" /><span className="home-hero-star home-hero-star--one" /><span className="home-hero-star home-hero-star--two" /><span className="home-hero-star home-hero-star--three" /></div>
    <div className="hero-story-copy-stack">
    <div className="hero-left-art" aria-hidden="true"><div className="hero-left-disc" /><div className="hero-left-arc" /><span className="hero-coordinate hero-coordinate--one">YOUR GOAL</span><span className="hero-coordinate hero-coordinate--two">YOUR PACE</span><svg viewBox="0 0 550 400"><path d="M-40 330 C70 330 25 110 130 110 S245 300 345 225 S430 25 570 65" /><circle cx="130" cy="110" r="5" /><circle cx="345" cy="225" r="5" /></svg></div>
    <div className="home-hero-copy hero-story-panel" ref={node => { panelsRef.current[0] = node }} aria-hidden={chapter !== 0 && chapter !== -1} inert={chapter !== 0 && chapter !== -1}>
      <div className="home-hero-eyebrow"><span /> SMALL STEPS. BIG POSSIBILITIES.</div>
      <h1 id="home-hero-title" aria-label="MENTICS">MENTICS<span className="wordmark-sweep" aria-hidden="true">MENTICS</span></h1>
      <p>From your next test to your next chapter.<br className="home-hero-break" /> Personalized SAT, ACT, and college planning that turns <strong>“where do I start?”</strong> into <strong>“I’ve got this.”</strong></p>
      <div className="home-hero-actions"><a className="button home-hero-primary" href={loggedIn ? '/dashboard' : '/signup'}>{loggedIn ? 'Continue your path' : 'Find my starting point'} <ArrowRight size={18} /></a><a className="home-hero-secondary" href="#how-it-works">See how it works <ArrowRight size={16} /></a></div>
      <div className="home-hero-assurance"><span><Check size={14} /> Free to get started</span><span><Check size={14} /> Built around you</span></div>
    </div>
    <div className="hero-story-panel hero-story-panel--chapter" ref={node => { panelsRef.current[1] = node }} aria-hidden={chapter !== 1 && chapter !== -1} inert={chapter !== 1 && chapter !== -1}>
      <div className="home-hero-eyebrow"><span /> 01 / FIND YOUR SIGNAL</div><h2>It starts<br />with <em>you.</em></h2><p>Your goals. Your starting point. The things that feel hard right now. Mentics turns that context into a direction.</p><div className="story-context"><span><Target size={16} /> Your target</span><span><BookOpen size={16} /> Your strengths</span><span><Sparkles size={16} /> Your next opportunity</span></div>
    </div>
    <div className="hero-story-panel hero-story-panel--chapter" ref={node => { panelsRef.current[2] = node }} aria-hidden={chapter !== 2 && chapter !== -1} inert={chapter !== 2 && chapter !== -1}>
      <div className="home-hero-eyebrow"><span /> 02 / TURN CLARITY INTO ACTION</div><h2>One move.<br /><em>Real momentum.</em></h2><p>Five focused steps. One clear place to begin. Learn, practice, and bring back the result. Your next path gets smarter with you.</p><a className="button home-hero-primary" href={loggedIn ? '/dashboard' : '/signup'}>{loggedIn ? 'Continue your path' : 'Build my free path'} <ArrowRight size={18} /></a><a className="story-continue" href="#how-it-works">Keep going. See the method. <ArrowRight size={16} /></a>
    </div>
    </div>
    <div className="hero-story-visual" ref={visualRef}>
    <div className="home-hero-demo">
      <div className="home-hero-track" role="group" aria-label="Choose a sample study path">{Object.keys(previews).map(name => <button type="button" key={name} aria-pressed={track === name} aria-controls="home-path-preview" onClick={() => { setTrack(name); setActiveStep(2) }}>{name}</button>)}</div>
      <div className="home-hero-stage">
        <div className="path-scene" id="home-path-preview" aria-live="polite" aria-atomic="true">
          <div className="path-scene-heading"><span><Sparkles size={14} /> {track} &middot; SAMPLE PATH</span><h2>{preview.title}</h2></div>
          <div className="path-sculpture" ref={sceneRef}>
            <div className="path-plinth path-plinth--bottom" aria-hidden="true" />
            <div className="path-plinth path-plinth--middle" aria-hidden="true" />
            <div className="path-plane">
              <div className="path-plane-grid" aria-hidden="true" />
              <svg className="path-sculpture-route" viewBox="0 0 500 440" aria-hidden="true">
                <path className="path-route-shadow" d="M100 88 C100 15 350 25 350 119 S225 132 225 220 S375 230 375 317 S125 410 125 361" />
                <path className="path-route-base" d="M100 88 C100 15 350 25 350 119 S225 132 225 220 S375 230 375 317 S125 410 125 361" />
                <path className="path-route-active" pathLength="100" strokeDasharray="100" d="M100 88 C100 15 350 25 350 119 S225 132 225 220 S375 230 375 317 S125 410 125 361" />
              </svg>
              <ol className="path-milestones">{preview.steps.map((step, index) => <li key={index} className={`path-milestone path-milestone--${index} ${index === activeStep ? 'is-active' : ''}`}><span className="path-pedestal" aria-hidden="true" /><button type="button" className="path-token" aria-pressed={activeStep === index} aria-label={`Explore step ${index + 1}: ${step}`} onClick={() => setActiveStep(index)}>{index < 2 ? <Check /> : index === 2 ? <Icon /> : index === 4 ? <Flag /> : <LockKeyhole />}</button><span className="path-milestone-label"><small>0{index + 1}{index === activeStep ? ' / EXPLORING' : ''}</small>{step}</span></li>)}</ol>
              <span className="path-plane-signature" aria-hidden="true">MENTICS / YOUR NEXT CHAPTER</span>
            </div>
          </div>
          <div className="path-orbit-badge" aria-hidden="true"><Sparkles size={18} /><span>Made for your<strong>next breakthrough.</strong></span></div>
        </div>
        <div className="home-focus-card"><span className="home-focus-icon"><Icon size={21} /></span><div><small>STEP {String(activeStep + 1).padStart(2, '0')} / YOUR NEXT MOVE</small><strong>{activeStep === 2 ? preview.focus : preview.steps[activeStep]}</strong><span>{preview.subject}</span></div><button type="button" className="home-focus-spark" aria-label="Explore the next sample step" onClick={() => setActiveStep(step => (step + 1) % 5)}><ArrowRight size={18} /></button></div>
      </div>
      <p className="home-hero-caption"><span /> Pick a milestone. See where it takes you.</p>
    </div>
    </div>
    <nav className="hero-story-nav" aria-label="Hero story chapters"><div className="hero-story-nav-track"><i ref={progressRef} /></div>{['Your ambition', 'Your signal', 'Your next move'].map((label, index) => <button key={label} type="button" aria-current={chapter === index ? 'step' : undefined} onClick={() => goToChapter(index)}><span>0{index + 1}</span>{label}</button>)}<a href="#how-it-works">Skip to the method <ArrowRight size={14} /></a></nav>
    <div className="hero-scroll-prompt" aria-hidden="true"><span /> SCROLL TO FIND YOUR PATH</div>
  </section></div>
}
