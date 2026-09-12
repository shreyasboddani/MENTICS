import { useEffect, useRef, useState } from 'react'
import { RotateCcw, RotateCw } from 'lucide-react'
import { ArenaFighter } from './arena-fighter'

// The renderer is fetched only for a visible lobby/locker, never for HUD portraits.
export function ArenaAvatarPreview({ avatar, label = 'Your fighter', paused = false, view = 'full' }) {
  const host = useRef(null)
  const scene = useRef(null)
  const latest = useRef(avatar)
  const [ready, setReady] = useState(false)
  const [failed, setFailed] = useState(false)
  useEffect(() => {
    latest.current = avatar
    scene.current?.setAvatar(avatar)
  }, [avatar])
  useEffect(() => {
    let cancelled = false
    const element = host.current
    const observer = new IntersectionObserver(entries => {
      if (!entries[0].isIntersecting) return
      observer.disconnect()
      import('./arena-avatar-scene').then(({ createAvatarScene }) => {
        if (cancelled) return
        scene.current = createAvatarScene(element, latest.current, () => setFailed(true))
        setReady(true)
      }).catch(() => { if (!cancelled) setFailed(true) })
    })
    observer.observe(element)
    return () => { cancelled = true; observer.disconnect(); scene.current?.dispose(); scene.current = null }
  }, [])
  useEffect(() => { scene.current?.setPaused(paused) }, [paused, ready])
  useEffect(() => { scene.current?.setView(view) }, [view, ready])
  return <div className="arena-avatar-preview" data-ready={ready && !failed}>
    <div className="arena-avatar-canvas" ref={host} role="img" aria-label={label} hidden={failed} />
    {(!ready || failed) && <div className="arena-avatar-fallback"><ArenaFighter avatar={avatar} label={label} /></div>}
    {!failed && <div className="arena-avatar-controls" aria-label="Character viewing controls">
      <button type="button" aria-label="Rotate fighter left" onClick={() => scene.current?.turn(-Math.PI / 4)}><RotateCcw /></button>
      <span>{ready ? 'DRAG TO ROTATE' : 'PREPARING FIGHTER'}</span>
      <button type="button" aria-label="Rotate fighter right" onClick={() => scene.current?.turn(Math.PI / 4)}><RotateCw /></button>
    </div>}
  </div>
}
