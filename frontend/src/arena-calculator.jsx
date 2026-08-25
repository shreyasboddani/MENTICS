// The Digital SAT ships a Desmos graphing calculator inside the test, so an
// Arena Math item should offer the same tool rather than a reimplementation of
// one that behaves subtly differently under time pressure.
//
// It is embedded as a cross-origin frame, not via the Desmos JS API. The API
// would run Desmos' script inside this origin with the session and CSRF token
// in reach; a frame can only draw graphs. That is also why the CSP in app.py
// grants `frame-src https://www.desmos.com` and leaves `script-src` alone.

import { useEffect, useRef, useState } from 'react'
import { Calculator, GripHorizontal, X } from 'lucide-react'

// `?embed` strips Desmos down to bare graph paper with no expression list, which
// is useless for entering an equation, so the standard calculator URL is used and
// the panel opens wide enough to fit the expression list beside the graph.
const DESMOS_EMBED = 'https://www.desmos.com/calculator'
const DEFAULT_SIZE = { width: 560, height: 480 }
const MIN_SIZE = { width: 340, height: 300 }
const EDGE = 8

function viewport() {
  if (typeof window === 'undefined') return { width: 1280, height: 800 }
  return { width: window.innerWidth, height: window.innerHeight }
}

function clampSize(size) {
  const view = viewport()
  return {
    width: Math.min(Math.max(size.width, MIN_SIZE.width), Math.max(MIN_SIZE.width, view.width - EDGE * 2)),
    height: Math.min(Math.max(size.height, MIN_SIZE.height), Math.max(MIN_SIZE.height, view.height - EDGE * 2)),
  }
}

/** Keep the panel on screen, after a drag, a resize, or a window resize. */
function clampPosition(position, size) {
  const view = viewport()
  return {
    x: Math.min(Math.max(position.x, EDGE), Math.max(EDGE, view.width - size.width - EDGE)),
    y: Math.min(Math.max(position.y, EDGE), Math.max(EDGE, view.height - size.height - EDGE)),
  }
}

function defaultSize() { return clampSize(DEFAULT_SIZE) }

function defaultPosition() {
  const size = defaultSize()
  const view = viewport()
  return clampPosition({ x: view.width - size.width - 24, y: view.height - size.height - 24 }, size)
}

export function ArenaCalculator({ open, onClose }) {
  const [position, setPosition] = useState(defaultPosition)
  const [size, setSize] = useState(defaultSize)
  // The frame is created on first open and then kept mounted, so a graph the
  // student set up on question 2 is still there on question 4.
  const [everOpened, setEverOpened] = useState(open)
  const [loaded, setLoaded] = useState(false)
  const [interacting, setInteracting] = useState(false)
  const gesture = useRef(null)
  const panelRef = useRef(null)
  if (open && !everOpened) setEverOpened(true)

  useEffect(() => {
    if (!open) return undefined
    const onKeyDown = event => { if (event.key === 'Escape') onClose() }
    const onWindowResize = () => {
      const bounds = panelRef.current?.getBoundingClientRect()
      if (!bounds) return
      const next = clampSize({ width: bounds.width, height: bounds.height })
      setSize(next)
      setPosition(current => clampPosition(current, next))
    }
    window.addEventListener('keydown', onKeyDown)
    window.addEventListener('resize', onWindowResize)
    return () => {
      window.removeEventListener('keydown', onKeyDown)
      window.removeEventListener('resize', onWindowResize)
    }
  }, [open, onClose])

  // Pointer capture keeps a gesture on the handle that started it, so releasing
  // over the Desmos frame still ends it instead of stranding the panel.
  const beginGesture = (event, mode) => {
    if (event.button !== 0) return
    // A press on the close button has to stay a click. Capturing the pointer
    // here would retarget the pointerup to this header and swallow it, which is
    // exactly what stopped the X from ever firing.
    if (event.target.closest('button')) return
    const bounds = panelRef.current.getBoundingClientRect()
    gesture.current = {
      mode,
      pointerX: event.clientX,
      pointerY: event.clientY,
      offsetX: event.clientX - bounds.left,
      offsetY: event.clientY - bounds.top,
      width: bounds.width,
      height: bounds.height,
    }
    setInteracting(true)
    event.currentTarget.setPointerCapture(event.pointerId)
    event.preventDefault()
  }

  const onGestureMove = event => {
    const active = gesture.current
    if (!active) return
    if (active.mode === 'move') {
      // Size cannot change during a move, so the gesture's own snapshot is the
      // right thing to clamp against.
      setPosition(clampPosition(
        { x: event.clientX - active.offsetX, y: event.clientY - active.offsetY },
        { width: active.width, height: active.height },
      ))
      return
    }
    const next = clampSize({
      width: active.width + (event.clientX - active.pointerX),
      height: active.height + (event.clientY - active.pointerY),
    })
    setSize(next)
    setPosition(current => clampPosition(current, next))
  }

  const endGesture = () => {
    gesture.current = null
    setInteracting(false)
  }

  const nudge = (event, mode) => {
    const step = event.shiftKey ? 48 : 12
    const moves = { ArrowLeft: [-step, 0], ArrowRight: [step, 0], ArrowUp: [0, -step], ArrowDown: [0, step] }
    const move = moves[event.key]
    if (!move) return
    event.preventDefault()
    if (mode === 'move') {
      setPosition(current => clampPosition({ x: current.x + move[0], y: current.y + move[1] }, size))
      return
    }
    const next = clampSize({ width: size.width + move[0], height: size.height + move[1] })
    setSize(next)
    setPosition(current => clampPosition(current, next))
  }

  if (!everOpened) return null
  return <aside
    ref={panelRef}
    className="arena-calculator"
    hidden={!open}
    data-interacting={interacting ? 'true' : undefined}
    style={{ left: `${position.x}px`, top: `${position.y}px`, width: `${size.width}px`, height: `${size.height}px` }}
    aria-label="Desmos graphing calculator"
  >
    <header
      className="arena-calculator-bar"
      onPointerDown={event => beginGesture(event, 'move')}
      onPointerMove={onGestureMove}
      onPointerUp={endGesture}
      onPointerCancel={endGesture}
    >
      <span
        className="arena-calculator-grip"
        tabIndex={0}
        role="button"
        aria-label="Move the calculator. Use the arrow keys to reposition it."
        onKeyDown={event => nudge(event, 'move')}
      >
        <GripHorizontal aria-hidden="true" />
      </span>
      <b>DESMOS</b>
      <button type="button" onClick={onClose} aria-label="Close the calculator"><X /></button>
    </header>
    <div className="arena-calculator-frame">
      {!loaded && <p className="arena-calculator-loading">Loading Desmos…</p>}
      <iframe
        src={DESMOS_EMBED}
        title="Desmos graphing calculator"
        onLoad={() => setLoaded(true)}
        referrerPolicy="no-referrer"
        sandbox="allow-scripts allow-same-origin allow-popups allow-forms"
      />
    </div>
    <span
      className="arena-calculator-resize"
      onPointerDown={event => beginGesture(event, 'resize')}
      onPointerMove={onGestureMove}
      onPointerUp={endGesture}
      onPointerCancel={endGesture}
      onKeyDown={event => nudge(event, 'resize')}
      tabIndex={0}
      role="button"
      aria-label="Resize the calculator. Use the arrow keys to change its size."
    />
  </aside>
}

export function ArenaCalculatorToggle({ open, onToggle }) {
  return <button
    type="button"
    className={`arena-calculator-toggle ${open ? 'selected' : ''}`}
    onClick={onToggle}
    aria-pressed={open}
  >
    <Calculator aria-hidden="true" /> {open ? 'Hide calculator' : 'Calculator'}
  </button>
}

export default ArenaCalculator
