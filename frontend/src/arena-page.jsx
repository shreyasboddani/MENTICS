import { useCallback, useEffect, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import { toast } from 'sonner'
import { ArrowRight, Brain, Check, Clock3, Flame, RotateCcw, Sparkles, Swords, Target, Trophy, Volume2, VolumeX, Zap } from 'lucide-react'
import { AppShell, api as request, Starfield } from './app-runtime'
import { boot } from './boot'
import { ArenaCustomizer, ArenaFighter, normalizeArenaAvatar } from './arena-fighter'
import { ArenaCalculator } from './arena-calculator'
import { ArenaAvatarPreview } from './arena-avatar-preview'
import { BattleLoadingScreen, BattleQuestionPanel, BattleReview } from './arena-experience'
import './arena.css'

async function api(url, options = {}) {
  const controller = new AbortController()
  const timeout = window.setTimeout(() => controller.abort(), 55000)
  try { return await request(url, { ...options, signal: controller.signal }) }
  catch (error) {
    if (error.name === 'AbortError') throw new Error('The Arena took too long to respond. Reload to recover any battle that has already started.', { cause: error })
    throw error
  } finally { window.clearTimeout(timeout) }
}

const BATTLE_TRAINING_RANKS = [
  ['bronze', 'Bronze', 'SAT essentials'],
  ['silver', 'Silver', 'Connected skills'],
  ['gold', 'Gold', 'Timing traps'],
  ['platinum', 'Platinum', 'Dense reasoning'],
  ['diamond', 'Diamond', 'Advanced synthesis'],
  ['master', 'Master', 'Elite pace'],
  ['grandmaster', 'Grandmaster', 'Hardest SAT-style sets'],
]

// Win-streak tiers follow how a real flame actually gets hotter -- deep red,
// orange, gold, white, blue, violet -- so the colour itself tells you the run
// is climbing without needing the number read to you.
const WIN_STREAK_TIERS = [
  { at: 1, key: 'ember', label: 'Ember', hot: '#ffb27a', cool: '#e0361f' },
  { at: 3, key: 'blaze', label: 'Blaze', hot: '#ffd08a', cool: '#ff6b1f' },
  { at: 5, key: 'solar', label: 'Solar', hot: '#fff0a8', cool: '#ffa722' },
  { at: 8, key: 'whitehot', label: 'White hot', hot: '#ffffff', cool: '#ffeeb0' },
  { at: 12, key: 'azure', label: 'Azure', hot: '#dff4ff', cool: '#2f8fff' },
  { at: 20, key: 'void', label: 'Void', hot: '#f0dcff', cool: '#8b3dff' },
]

export function winStreakTier(streak) {
  let tier = null
  for (const candidate of WIN_STREAK_TIERS) if (streak >= candidate.at) tier = candidate
  return tier
}

function WinStreakFlame({ streak = 0, best = 0, compact = false }) {
  const tier = winStreakTier(streak)
  if (!tier) {
    if (compact) return null
    return <div className="win-streak win-streak--cold">
      <Flame aria-hidden="true" />
      <span><b>No win streak</b><small>{best > 0 ? `Best run ${best}` : 'Win a ranked round to light it'}</small></span>
    </div>
  }
  const id = `flame-${tier.key}`
  return <div className={`win-streak win-streak--${tier.key}`} data-tier={tier.key}
    title={`${streak} win streak - ${tier.label}`}>
    <svg viewBox="0 0 24 30" aria-hidden="true" className="win-streak-flame">
      <defs>
        <linearGradient id={id} x1="0" y1="1" x2="0" y2="0">
          <stop offset="0%" stopColor={tier.cool} />
          <stop offset="55%" stopColor={tier.cool} />
          <stop offset="100%" stopColor={tier.hot} />
        </linearGradient>
      </defs>
      <path d="M12 1c4.2 5.1 6.4 8.6 6.4 11.7 0 2.3-1 3.9-2.6 4.6 1-3.1-.6-6-4-8.6-.9 2.8-2.6 4.4-4.6 6.4-2 2-2.7 4.4-1.6 6.9C3.2 20.6 2 18 2 15.1 2 9.6 6.6 6.2 12 1Z"
        fill={`url(#${id})`} />
      <path d="M12 29c-3.6 0-6.4-2.3-6.4-5.6 0-2.6 1.7-4.4 3.5-6.3 1.5-1.6 2.8-3 3.3-5 2.9 2.3 4.2 4.7 3.5 7.2 1.2-.5 2-1.6 2.2-3.1 1.5 1.9 2.3 3.8 2.3 5.6 0 3.6-3 7.2-8.4 7.2Z"
        fill={`url(#${id})`} opacity=".92" />
    </svg>
    <span><b>{streak} win{streak === 1 ? '' : 's'}</b><small>{tier.label}{best > streak ? ` · best ${best}` : ''}</small></span>
  </div>
}

function BattleRatingResult({ rank, previousRank, delta }) {
  if (delta == null || !rank) return null
  const promoted = previousRank && previousRank.key !== rank.key
  const climbed = delta > 0
  const span = rank.nextAt ? rank.nextAt - rank.minimum : 0
  const progress = span > 0 ? Math.min(100, Math.max(0, ((rank.rating - rank.minimum) / span) * 100)) : 100
  return <div className={`battle-rating-result ${climbed ? 'is-up' : 'is-down'}`}>
    <div className="battle-rating-swing">
      <b>{climbed ? '+' : '−'}{Math.abs(delta)}</b>
      <small>RP</small>
    </div>
    <div className="battle-rating-standing">
      {promoted && <em className={climbed ? 'promoted' : 'demoted'}>
        {climbed ? 'RANKED UP' : 'RANKED DOWN'} · {previousRank.label} → {rank.label}
      </em>}
      <strong className={`battle-result-rank--${rank.key}`}>{rank.label} · {rank.rating} RP</strong>
      <i className="battle-rating-track"><b style={{ width: `${progress}%` }} /></i>
      <span>{rank.nextAt
        ? `${Math.max(0, rank.nextAt - rank.rating)} RP to ${rank.nextLabel}`
        : 'Top of the ladder.'}</span>
    </div>
  </div>
}

const clockText = seconds => `${Math.floor(seconds / 60)}:${String(Math.round(seconds) % 60).padStart(2, '0')}`

function BattleClock({ startedAt, durationSeconds = 300 }) {
  const [secondsLeft, setSecondsLeft] = useState(null)
  useEffect(() => {
    if (!startedAt) return undefined
    const tick = () => setSecondsLeft(Math.max(0, durationSeconds - Math.floor((Date.now() - Date.parse(startedAt)) / 1000)))
    tick()
    // One tick per second is all an mm:ss readout can show.
    const timer = window.setInterval(tick, 1000)
    return () => window.clearInterval(timer)
  }, [startedAt, durationSeconds])
  // The round's own clock, never a hard-coded two minutes: a grandmaster set of
  // Math items is not paced like five easy Reading questions.
  const clock = clockText(secondsLeft == null ? durationSeconds : secondsLeft)
  return <strong className={secondsLeft != null && secondsLeft < 30 ? 'urgent' : ''}><Clock3 /> {clock}</strong>
}

function ArenaGameLobby({ paused, name, rank, rankProgress, avatar, openCustomizer, mode, setMode, trainingRank, setTrainingRank, selectedTier, busy, join, train, winStreak, bestWinStreak, clocks }) {
  const ranked = mode === 'ranked'
  const tierClock = clocks?.[ranked ? rank?.key : trainingRank] ?? clocks?.bronze ?? 300
  return <section className="arena-game-shell" data-mode={mode} aria-label="SAT Battle Arena game lobby">
    <div className="arena-game-sky" aria-hidden="true"><i /><i /><i /><i /></div>
    <header className="arena-game-bar"><span><Swords /> SAT BATTLES</span><b>MENTICS / ARENA</b><em><i /> Online</em></header>
    <div className="arena-game-grid">
      <nav className="arena-mode-rail" aria-label="Choose game mode">
        <small>CHOOSE YOUR MODE</small>
        <button type="button" className={ranked ? 'selected' : ''} onClick={() => setMode('ranked')}><i><Swords /></i><span><b>Ranked duel</b><small>Climb the ladder</small></span></button>
        <button type="button" className={!ranked ? 'selected' : ''} onClick={() => setMode('training')}><i><Brain /></i><span><b>Training room</b><small>Choose any tier</small></span></button>
        <div className="arena-season-card"><Trophy /><span><small>CURRENT RANK</small><b>{rank?.label || 'Bronze'}</b><em>{rank?.rating || 1000} RP</em></span><i><b style={{ width: `${rankProgress}%` }} /></i></div>
        <WinStreakFlame streak={winStreak} best={bestWinStreak} />
      </nav>
      <section className="arena-player-stage">
        <div className="arena-stage-wordmark" aria-hidden="true">GAME<br />ON.</div>
        <div className="arena-stage-caption" aria-hidden="true"><span>YOUR NEXT LEVEL</span><b>Starts here.</b></div>
        <div className="arena-stage-rig" aria-hidden="true"><i /><i /><i /></div>
        <div className="arena-spotlight" aria-hidden="true" />
        <ArenaAvatarPreview avatar={avatar} paused={paused} label={`${name || 'Your'} Arena fighter`} />
        <div className="arena-stage-name"><small>PLAYER / 01</small><h1>{name || 'Arena player'}</h1><span><i /> Ready to play</span></div>
        <button type="button" className="arena-locker-button" onClick={openCustomizer}><Sparkles /> Edit loadout</button>
        <div className="arena-stage-platform" aria-hidden="true"><i /><b>MENTICS</b><i /></div>
      </section>
      <aside className="arena-match-console">
        <header><small>{ranked ? 'RANKED PLAY' : 'TRAINING SIM'}</small><span>{ranked ? <Swords /> : <Brain />}</span></header>
        <h2>{ranked ? <>One rival.<br />Your move.</> : <>Practice.<br />Level up.</>}</h2>
        <p>{ranked ? 'Same questions. Same clock. Outthink your opponent and climb the ranks.' : 'Choose your challenge. Build your speed. Keep your rank.'}</p>
        {!ranked && <div className="arena-rank-selector" role="radiogroup" aria-label="Bot question rank">{BATTLE_TRAINING_RANKS.map(([key, label]) => <button type="button" role="radio" aria-checked={trainingRank === key} className={trainingRank === key ? 'selected' : ''} key={key} onClick={() => setTrainingRank(key)}><i data-rank={key} /><span>{label}</span></button>)}</div>}
        <div className="arena-difficulty-callout"><Target /><span><small>QUESTION TIER</small><b>{ranked ? `${rank?.label || 'Bronze'} matchmaking` : `${selectedTier[1]} simulation`}</b></span></div>
        <p className="arena-scale-copy">Every rank gets full-length, original SAT-style questions. Higher ranks add denser passages, tighter traps, multi-constraint math, and dramatically harder reasoning.</p>
        <button type="button" className="arena-deploy-button" onClick={ranked ? join : train} disabled={busy}><span>{busy ? 'INITIALIZING…' : ranked ? 'FIND A MATCH' : 'START TRAINING'}</span><i>{ranked ? <Swords /> : <Zap />}</i></button>
        <footer><span><b>05</b> QUESTIONS</span><span><b>{clockText(tierClock)}</b> CLOCK</span><span><b>{ranked ? 'RP' : '0 RP'}</b> {ranked ? 'AT STAKE' : 'RISK'}</span></footer>
        {ranked && <p className="arena-match-note">An Arena bot joins if no player matches within 30 seconds.</p>}
      </aside>
    </div>
    <footer className="arena-game-ticker"><span>FIVE QUESTIONS. ONE SHARED CHALLENGE.</span><i /><span>ACCURACY WINS · SPEED BREAKS THE TIE</span><i /><span>GRANDMASTER = MAXIMUM SAT DIFFICULTY</span></footer>
  </section>
}

export default function BattleArena() {
  const d = boot.data
  const [battle, setBattle] = useState(d.currentBattle)
  const [answers, setAnswers] = useState(() => {
    if (d.currentBattle?.answers?.length) return Object.fromEntries(d.currentBattle.answers.map(a => [a.question_index, a.selected_option]))
    try { return JSON.parse(sessionStorage.getItem(`mentics:battle:${d.currentBattle?.id}`)) || {} } catch { return {} }
  })
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [activeQuestion, setActiveQuestion] = useState(0)
  const [calculatorOpen, setCalculatorOpen] = useState(false)
  const winStreak = battle?.winStreak ?? d.winStreak ?? 0
  const bestWinStreak = battle?.bestWinStreak ?? d.bestWinStreak ?? 0
  const [cinematic, setCinematic] = useState('')
  const [lobbyMode, setLobbyMode] = useState('ranked')
  const [trainingRank, setTrainingRank] = useState(d.battleRank?.key || 'bronze')
  const [avatar, setAvatar] = useState(() => normalizeArenaAvatar(d.arenaAvatar || d.currentBattle?.playerAvatar))
  // The last loadout the server confirmed. Picking a slot updates the fighter
  // everywhere immediately, so without this a save that fails -- or a locker
  // closed without equipping -- leaves the lobby showing a fighter that only
  // exists on this screen, and it silently reverts on the next page load.
  const savedAvatar = useRef(avatar)
  const [customizing, setCustomizing] = useState(false)
  const [savingAvatar, setSavingAvatar] = useState(false)
  const [musicEnabled, setMusicEnabled] = useState(false)
  const previousStatus = useRef(d.currentBattle?.status)
  const stageRef = useRef(null)
  const cinematicTimers = useRef([])
  const arenaAudio = useRef(null)
  const active = battle?.status === 'active'
  const waiting = battle?.status === 'waiting'
  const complete = battle?.status === 'complete'
  const idle = !battle || battle.status === 'expired'
  const clearCinematic = useCallback(() => { cinematicTimers.current.forEach(window.clearTimeout); cinematicTimers.current = [] }, [])
  const stopArenaMusic = useCallback(() => {
    const audio = arenaAudio.current
    if (!audio) return
    arenaAudio.current = null
    window.clearInterval(audio.timer)
    const now = audio.context.currentTime
    audio.master.gain.cancelScheduledValues(now)
    audio.master.gain.setValueAtTime(Math.max(.0001, audio.master.gain.value), now)
    audio.master.gain.exponentialRampToValueAtTime(.0001, now + .12)
    window.setTimeout(() => {
      audio.oscillators.forEach(oscillator => { try { oscillator.stop() } catch (error) { void error } })
      audio.oscillators.clear()
      audio.context.close().catch(() => undefined)
    }, 150)
  }, [])
  const startArenaMusic = useCallback((force = false) => {
    if ((!musicEnabled && !force) || arenaAudio.current || typeof window === 'undefined') return
    const AudioContext = window.AudioContext || window.webkitAudioContext
    if (!AudioContext) return
    const context = new AudioContext()
    const master = context.createGain()
    master.gain.setValueAtTime(.0001, context.currentTime)
    master.gain.exponentialRampToValueAtTime(.035, context.currentTime + .2)
    master.connect(context.destination)
    // Held only until each note ends; see the onended cleanup below.
    const oscillators = new Set()
    const pattern = [0, 7, 12, 7, 3, 10, 7, 14, 0, 7, 15, 12, 3, 10, 7, 2]
    let step = 0
    const playBeat = () => {
      const now = context.currentTime
      const note = 220 * Math.pow(2, pattern[step % pattern.length] / 12)
      const lead = context.createOscillator()
      const leadGain = context.createGain()
      lead.type = step % 4 === 0 ? 'square' : 'triangle'
      lead.frequency.setValueAtTime(note, now)
      leadGain.gain.setValueAtTime(.0001, now)
      leadGain.gain.exponentialRampToValueAtTime(.19, now + .018)
      leadGain.gain.exponentialRampToValueAtTime(.0001, now + .22)
      lead.connect(leadGain).connect(master)
      lead.start(now); lead.stop(now + .24)
      oscillators.add(lead)
      lead.onended = () => { lead.disconnect(); leadGain.disconnect(); oscillators.delete(lead) }
      if (step % 4 === 0) {
        const bass = context.createOscillator()
        const bassGain = context.createGain()
        bass.type = 'sine'
        bass.frequency.setValueAtTime(note / 2, now)
        bassGain.gain.setValueAtTime(.0001, now)
        bassGain.gain.exponentialRampToValueAtTime(.28, now + .015)
        bassGain.gain.exponentialRampToValueAtTime(.0001, now + .27)
        bass.connect(bassGain).connect(master)
        bass.start(now); bass.stop(now + .29)
        oscillators.add(bass)
        bass.onended = () => { bass.disconnect(); bassGain.disconnect(); oscillators.delete(bass) }
      }
      step += 1
    }
    context.resume().catch(() => {})
    playBeat()
    arenaAudio.current = { context, master, oscillators, timer: window.setInterval(playBeat, 285) }
  }, [musicEnabled])
  const toggleArenaMusic = () => {
    if (musicEnabled) { stopArenaMusic(); setMusicEnabled(false) }
    else { setMusicEnabled(true); startArenaMusic(true) }
  }
  const launchCinematic = useCallback(() => {
    clearCinematic()
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return
    setCinematic('fight')
    ;[['', 650]].forEach(([phase, delay]) => cinematicTimers.current.push(window.setTimeout(() => setCinematic(phase), delay)))
  }, [clearCinematic])
  const requestVersion = useRef(0)
  const polling = useRef(false)
  const refresh = useCallback(async id => {
    if (polling.current) return
    polling.current = true
    const version = requestVersion.current
    try {
      const next = await api(`/api/sat-battles/${id}`)
      if (version === requestVersion.current) { setBattle(next); setError('') }
    } catch { if (version === requestVersion.current) setError('Connection interrupted. Reconnecting automatically; your selections are kept.') }
    finally { polling.current = false }
  }, [])
  useEffect(() => {
    if (!battle?.id || !['waiting', 'active'].includes(battle.status)) return undefined
    const poll = window.setInterval(() => { if (!document.hidden) refresh(battle.id) }, 1800)
    const onVisible = () => {
      if (!document.hidden) refresh(battle.id)
      if (document.hidden) arenaAudio.current?.context.suspend()
      else arenaAudio.current?.context.resume().catch(() => {})
    }
    document.addEventListener('visibilitychange', onVisible)
    return () => { window.clearInterval(poll); requestVersion.current += 1; document.removeEventListener('visibilitychange', onVisible) }
  }, [battle?.id, battle?.status, refresh])
  useEffect(() => {
    if (!battle?.id) return
    try { sessionStorage.setItem(`mentics:battle:${battle.id}`, JSON.stringify(answers)) } catch { /* Optional recovery. */ }
  }, [battle?.id, answers])
  useEffect(() => {
    const previous = previousStatus.current
    previousStatus.current = battle?.status
    if (previous !== 'waiting' || battle?.status !== 'active') return undefined
    launchCinematic()
  }, [battle?.status, launchCinematic])
  useEffect(() => {
    return () => clearCinematic()
  }, [clearCinematic])
  useEffect(() => {
    if (!waiting && !active) stopArenaMusic()
  }, [waiting, active, stopArenaMusic])
  useEffect(() => {
    return () => stopArenaMusic()
  }, [stopArenaMusic])
  useEffect(() => {
    if (!customizing) return undefined
    const previousOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    return () => { document.body.style.overflow = previousOverflow }
  }, [customizing])
  useEffect(() => {
    if (battle?.status !== 'active') return undefined
    const frame = window.requestAnimationFrame(() => stageRef.current?.scrollIntoView({ block: 'start', behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth' }))
    return () => window.cancelAnimationFrame(frame)
  }, [battle?.id, battle?.status])
  useEffect(() => {
    if (battle?.status !== 'complete' || !battle.youWon || window.matchMedia('(prefers-reduced-motion: reduce)').matches) return undefined
    const burst = () => import('canvas-confetti').then(({ default: confetti }) => confetti({ particleCount: 56, spread: 66, startVelocity: 29, origin: { y: .62 }, colors: ['#6f45dc', '#a786ff', '#e2d6ff', '#ffd267'] }))
    burst()
    const timer = window.setTimeout(burst, 240)
    return () => window.clearTimeout(timer)
  }, [battle?.id, battle?.status, battle?.youWon])
  useEffect(() => {
    if (battle?.status !== 'complete') return
    boot.data.battleRank = battle.rank
    boot.data.winStreak = battle.winStreak
    boot.data.bestWinStreak = battle.bestWinStreak
    boot.data.currentBattle = null
  }, [battle])
  const startBattle = nextBattle => { requestVersion.current += 1; setCalculatorOpen(false); setAnswers({}); setActiveQuestion(0); setBattle(nextBattle); if (nextBattle?.status === 'active') launchCinematic() }
  const join = async () => { startArenaMusic(); setBusy(true); setError(''); try { startBattle(await api('/api/sat-battles/queue', { method: 'POST' })) } catch (x) { stopArenaMusic(); setError(x.message) } finally { setBusy(false) } }
  const train = async () => { startArenaMusic(); setBusy(true); setError(''); try { startBattle(await api('/api/sat-battles/train', { method: 'POST', body: JSON.stringify({ rank: trainingRank }) })) } catch (x) { stopArenaMusic(); setError(x.message) } finally { setBusy(false) } }
  const cancelQueue = async () => { if (!battle) return; setBusy(true); setError(''); try { requestVersion.current += 1; await api(`/api/sat-battles/${battle.id}/cancel`, { method: 'POST' }); stopArenaMusic(); setBattle(null) } catch (x) { setError(x.message) } finally { setBusy(false) } }
  const saveAvatar = async () => {
    setSavingAvatar(true); setError('')
    try {
      const saved = await api('/api/sat-battles/avatar', { method: 'POST', body: JSON.stringify(avatar) })
      setAvatar(saved.avatar)
      savedAvatar.current = saved.avatar
      // boot.data is what a remount initialises from; keep it in step with the server.
      boot.data.arenaAvatar = saved.avatar
      setCustomizing(false)
      toast.success('Fighter loadout equipped')
    } catch (x) {
      setAvatar(savedAvatar.current)
      setError(x.message)
      toast.error(x.message)
    } finally { setSavingAvatar(false) }
  }
  const closeCustomizer = useCallback(() => { setAvatar(savedAvatar.current); setCustomizing(false) }, [])
  const select = useCallback((questionIndex, selectedOption) => setAnswers(current => ({ ...current, [questionIndex]: selectedOption })), [])
  const submit = async () => { if (!battle || Object.keys(answers).length !== battle.questions.length) return; setBusy(true); setError(''); try { requestVersion.current += 1; setBattle(await api(`/api/sat-battles/${battle.id}/submit`, { method: 'POST', body: JSON.stringify({ answers: Object.entries(answers).map(([question_index, selected_option]) => ({ question_index: Number(question_index), selected_option })) }) })) } catch (x) { setError(x.message) } finally { setBusy(false) } }
  const spotlight = d.spotlight
  const rank = battle?.rank || d.battleRank
  const battleDifficulty = String(battle?.difficulty || rank?.label || 'Bronze').toUpperCase()
  const rankProgress = rank?.nextAt ? Math.max(0, Math.min(100, (rank.rating - rank.minimum) / (rank.nextAt - rank.minimum) * 100)) : 100
  const questionCount = battle?.questions?.length || 0
  const currentQuestionIndex = Math.min(activeQuestion, Math.max(0, questionCount - 1))
  const currentQuestion = battle?.questions?.[currentQuestionIndex]
  const answeredCount = Object.keys(answers).length
  const remainingCount = questionCount - answeredCount
  const selectedTrainingTier = BATTLE_TRAINING_RANKS.find(([key]) => key === trainingRank) || BATTLE_TRAINING_RANKS[0]
  const advanceQuestion = () => setActiveQuestion(index => Math.min(index + 1, Math.max(0, questionCount - 1)))
  return <AppShell name={d.name}><main className={`app-main battle-page ${active ? 'battle-page--in-match' : waiting ? 'battle-page--queue' : complete ? 'battle-page--complete' : ''}`}>
    {idle && !busy && <ArenaGameLobby paused={customizing} name={d.name} rank={rank} rankProgress={rankProgress} avatar={avatar} openCustomizer={() => setCustomizing(true)} mode={lobbyMode} setMode={setLobbyMode} trainingRank={trainingRank} setTrainingRank={setTrainingRank} selectedTier={selectedTrainingTier} clocks={d.battleClocks} busy={busy} join={join} train={train} winStreak={winStreak} bestWinStreak={bestWinStreak} />}
    {idle && busy && <BattleLoadingScreen rank={selectedTrainingTier[1]} matchmaking={lobbyMode === 'ranked'} />}
    {idle && customizing && typeof document !== 'undefined' && createPortal(<ArenaCustomizer avatar={avatar} onChange={setAvatar} onSave={saveAvatar} onClose={closeCustomizer} saving={savingAvatar} />, document.body)}
    {error && <div className="error-banner" role="alert">{error}<button onClick={() => window.location.reload()}>Reload battle</button><button onClick={() => setError('')}>Dismiss</button></div>}
    {waiting && <section className="battle-stage battle-stage--waiting arena-queue-stage" aria-live="polite"><div className="arena-queue-world"><div className="arena-queue-podium arena-queue-podium--you"><div className="arena-queue-light" /><ArenaFighter avatar={battle.playerAvatar || avatar} label={`${d.name || 'Your'} fighter waiting for a match`} size="medium" /><strong>{d.name || 'YOU'}</strong><span>READY</span></div><div className="arena-queue-core"><span className="battle-search-orbit"><Swords /></span><small>MATCHMAKING</small><h2>{battle.preparing ? 'Building your battle' : 'Searching the Arena'}</h2><p>{battle.preparing ? 'Players connected. Preparing your shared questions.' : 'Scanning for a live challenger'}</p><i><b /></i><em>{battle.preparing ? 'YOUR CLOCK HAS NOT STARTED' : 'BOT DROP-IN AT 0:30'}</em></div><div className="arena-queue-podium arena-queue-podium--rival"><div className="arena-queue-light" /><div className="arena-mystery-fighter">?</div><strong>CHALLENGER</strong><span>SEARCHING</span></div></div><p className="arena-queue-note">Both players receive the same fresh SAT set. If nobody joins within 30 seconds, an Arena bot enters automatically.</p><div className="battle-wait-actions"><button className="text-button" onClick={() => refresh(battle.id)}>Check status <RotateCcw /></button><button className="text-button" onClick={toggleArenaMusic}>{musicEnabled ? <Volume2 /> : <VolumeX />} Music {musicEnabled ? 'on' : 'off'}</button><button className="text-button" disabled={busy} onClick={cancelQueue}>Leave queue</button></div></section>}
    {active && <section ref={stageRef} className={`battle-stage battle-stage--active ${answers[currentQuestionIndex] != null ? 'is-striking' : ''}`} aria-label="Active SAT battle">
      {cinematic && <div className="arena-cinematic" data-phase={cinematic} role="status" aria-live="assertive"><Starfield warp tone="violet" /><div className="arena-cinematic-fighters" aria-hidden="true"><div className="arena-cinematic-fighter arena-cinematic-fighter--you"><ArenaFighter avatar={battle.playerAvatar || avatar} size="medium" state="combat" /><b>{d.name || 'YOU'}</b></div><i>VS</i><div className="arena-cinematic-fighter arena-cinematic-fighter--rival"><ArenaFighter avatar={battle.opponentAvatar} size="medium" facing="left" state="combat" /><b>{battle.opponentName || 'RIVAL'}</b></div></div><div className="arena-cinematic-count"><small>{cinematic === 'fight' ? 'MENTICS ARENA' : 'ARENA LINK ESTABLISHED'}</small><strong>{cinematic === 'fight' ? 'FIGHT' : cinematic}</strong><span>{cinematic === 'fight' ? 'MAKE EVERY SECOND COUNT' : 'PREPARE TO THINK FAST'}</span></div>{cinematic !== 'fight' && <button type="button" onClick={() => { clearCinematic(); setCinematic('') }}>Skip intro</button>}</div>}
      <header className="battle-status"><span><i /><b>{battle.mode === 'training' ? 'PRIVATE BOT DRILL' : `${battleDifficulty} SAT BATTLE`}</b><small>vs {battle.opponentName || 'your challenger'}{battle.questionSource === 'gemini' ? ' · GEMINI LIVE SET' : ''}</small></span><button className="arena-audio-toggle" type="button" onClick={toggleArenaMusic} aria-label={musicEnabled ? 'Mute arena music' : 'Play arena music'}>{musicEnabled ? <Volume2 /> : <VolumeX />} <span>Music {musicEnabled ? 'on' : 'off'}</span></button><BattleClock startedAt={battle.startedAt} durationSeconds={battle.durationSeconds} /></header>
      {battle.submitted ? <div className="battle-locked"><span className="battle-search-orbit"><Check /></span><h2>Answers locked.</h2><p>{battle.mode === 'training' ? 'Mentics Arena Bot is scoring your round now.' : `Waiting for ${battle.opponentName || 'your challenger'} to finish. The arena will reveal the result automatically.`}</p></div> : <>
        <div className="battle-combat-hud" aria-label={`You versus ${battle.opponentName || 'Arena bot'}`}><article className="battle-combatant battle-combatant--you"><ArenaFighter avatar={battle.playerAvatar || avatar} label="Your fighter" size="portrait" state="combat" /><div className="battle-combatant-stats"><small>YOU</small><b>{d.name || 'Challenger'}</b><i><em style={{ width: `${questionCount ? answeredCount / questionCount * 100 : 0}%` }} /></i><strong>FOCUS {answeredCount}/{questionCount}</strong></div></article><div className="battle-clash"><i /><b>VS</b><span>{currentQuestion?.skill || 'SAT ARENA'}</span></div><article className="battle-combatant battle-combatant--rival"><div className="battle-combatant-stats"><small>RIVAL</small><b>{battle.opponentName || 'Arena Bot'}</b><i><em /></i><strong>{battle.opponentSubmitted ? 'ANSWERS LOCKED' : 'IN THE ARENA'}</strong></div><ArenaFighter avatar={battle.opponentAvatar} label={`${battle.opponentName || 'Rival'} fighter`} size="portrait" facing="left" state="combat" /></article></div>
        <div className="battle-question-progress" aria-label={`Question ${currentQuestionIndex + 1} of ${questionCount}`}>{battle.questions.map((_, index) => <button type="button" key={index} className={`${answers[index] != null ? 'done' : ''} ${currentQuestionIndex === index ? 'current' : ''}`} onClick={() => setActiveQuestion(index)} aria-label={`Go to question ${index + 1}${answers[index] != null ? ', answered' : ''}`}>{index + 1}</button>)}</div>
        <div className="battle-round-heading"><span>QUESTION {currentQuestionIndex + 1} OF {questionCount}</span><b>{answeredCount}/{questionCount} SELECTED</b></div>
        {currentQuestion && <BattleQuestionPanel key={currentQuestionIndex} question={currentQuestion} index={currentQuestionIndex} selected={answers[currentQuestionIndex]} onSelect={select} disabled={busy} calculatorOpen={calculatorOpen} onToggleCalculator={() => setCalculatorOpen(value => !value)} />}
        <div className="battle-round-actions"><p role="status">{answers[currentQuestionIndex] != null ? 'Selected. You can change this before submitting.' : 'Choose your answer. Use keys 1-4 or tap a choice.'}</p>{currentQuestionIndex < questionCount - 1 ? <button type="button" className="button button--quiet" onClick={advanceQuestion}>{answers[currentQuestionIndex] != null ? 'Next question' : 'Skip for now'} <ArrowRight /></button> : <button type="button" className="button button--quiet" onClick={() => { const unanswered = battle.questions.findIndex((_, index) => answers[index] == null); if (unanswered >= 0) setActiveQuestion(unanswered); else submit() }}>{remainingCount ? `Answer ${remainingCount} remaining` : 'Submit answers'} <ArrowRight /></button>}</div>
        <button className="button button--primary battle-lock" disabled={busy || answeredCount !== questionCount} onClick={submit}>{busy ? 'Locking answers…' : `Lock in ${answeredCount}/${questionCount} answers`} <ArrowRight /></button>
        <ArenaCalculator open={calculatorOpen} onClose={() => setCalculatorOpen(false)} />
      </>}
    </section>}
    {complete && <section className={`battle-result battle-result--fighters ${battle.youWon ? 'won' : battle.draw ? 'draw' : 'lost'}`}>{(battle.youWon || battle.draw) && <div className="arena-confetti" aria-hidden="true">{Array.from({ length: 12 }, (_, index) => <i key={index} style={{ '--arena-index': index }} />)}</div>}<div className="battle-result-mark">{battle.youWon ? <Trophy /> : battle.draw ? <Target /> : <Swords />}</div><small>{battle.mode === 'training' ? 'BOT DRILL COMPLETE' : battle.youWon ? 'VICTORY' : battle.draw ? 'DRAW' : 'BATTLE COMPLETE'}</small><h2>{battle.mode === 'training' ? 'A sharper round in the bank.' : battle.youWon ? 'You won the race.' : battle.draw ? 'A dead-even finish.' : 'A strong round. Run it back.'}</h2><div className="arena-result-versus"><article className={battle.youWon ? 'winner' : ''}><ArenaFighter avatar={battle.playerAvatar || avatar} label="Your fighter" size="medium" state={battle.youWon ? 'victory' : 'idle'} /><b>{d.name || 'YOU'}</b><strong>{battle.yourScore}</strong><span>CORRECT</span></article><i>VS</i><article className={!battle.youWon && !battle.draw ? 'winner' : ''}><ArenaFighter avatar={battle.opponentAvatar} label={`${battle.opponentName || 'Rival'} fighter`} size="medium" facing="left" state={!battle.youWon && !battle.draw ? 'victory' : 'idle'} /><b>{battle.opponentName || 'RIVAL'}</b><strong>{battle.opponentScore}</strong><span>CORRECT</span></article></div>{battle.mode === 'training'
      ? <em className="battle-training-note">This private drill did not affect your rating.</em>
      : battle.ratingDelta != null
        ? <><BattleRatingResult rank={battle.rank} previousRank={battle.previousRank} delta={battle.ratingDelta} />
          <WinStreakFlame streak={battle.winStreak || 0} best={battle.bestWinStreak || 0} /></>
        : <em className={`battle-result-rank battle-result-rank--${battle.rank?.key}`}>{battle.rank?.label} · {battle.rank?.rating} RP</em>}<button className="button button--primary" onClick={() => { requestVersion.current += 1; setCalculatorOpen(false); setBattle(null); setAnswers({}); setActiveQuestion(0) }}>{battle.mode === 'training' ? 'Train again' : 'Find another battle'} <Swords /></button></section>}
    {complete && <BattleReview battle={battle} answers={answers} />}
    <section className="battle-lower"><div className="battle-rules"><small>HOW IT WORKS</small><h2>One clean round. No fluff.</h2><div><article><b>01</b><span><strong>Match</strong><p>We pair you with one student and serve the same question set.</p></span></article><article><b>02</b><span><strong>Race</strong><p>Answer all five before the clock runs out. It is sized to the tier, and it starts together.</p></span></article><article><b>03</b><span><strong>Climb</strong><p>Accuracy takes it. Faster completion breaks a tied score.</p></span></article></div></div><aside className="battle-leaderboard"><header><span><Trophy /> BATTLE LEADERBOARD</span><a href="#battle-rankings">View rankings</a></header>{d.leaderboard?.length ? d.leaderboard.slice(0, 5).map((row, index) => <div key={row.user_id}><i>{index + 1}</i><span>{String(row.user_name || 'M').slice(0, 1)}</span><b>{row.user_name}<small className={`battle-rank-label battle-rank-label--${row.rank.key}`}>{row.rank.label}</small></b><strong>{row.rating}</strong></div>) : <p>The first completed battle earns a place here.</p>}</aside></section>
    <section className="battle-spotlight" id="battle-rankings"><div><small>ARENA SPOTLIGHT</small><h2>{spotlight ? `${spotlight.challenger_name} vs ${spotlight.opponent_name}` : 'The next great battle starts with you.'}</h2><p>{spotlight ? 'The latest completed head-to-head round in the Mentics arena.' : 'Enter the arena to set the first battle on the board.'}</p></div><div>{spotlight ? <><strong>{spotlight.winner_id ? 'WINNER DECIDED' : 'DRAW'}</strong><span>Latest completed battle</span></> : <><strong>OPEN</strong><span>Matchmaking is ready</span></>}</div></section>
  </main></AppShell>
}

