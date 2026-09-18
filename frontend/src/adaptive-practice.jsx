import { useEffect, useRef, useState } from 'react'
import { ArrowLeft, ArrowRight, BookOpen, Check, Lightbulb, Target } from 'lucide-react'
import { AppShell, api } from './app-runtime'
import { boot } from './boot'
import { DesmosCalculator, DesmosCalculatorToggle } from './arena-calculator'
import './adaptive-practice.css'

const label = track => `${track.startsWith('act') ? 'ACT' : 'SAT'} · ${track.endsWith('math') ? 'Math' : track.startsWith('act') ? 'English & Reading' : 'Reading & Writing'}`
const requestId = () => crypto.randomUUID()
const post = (url, data) => api(url, { method: 'POST', body: JSON.stringify(data) })

function Credit({ value }) {
  return value ? <p className="adaptive-credit"><a href={value.url} target="_blank" rel="noreferrer">{value.name}</a> · {value.note}</p> : null
}

export function AdaptiveAssessment() {
  return <AppShell name={boot.data.name}><main className="app-main adaptive-page"><AdaptiveSession id={boot.data.sessionId} /></main></AppShell>
}

export default function AdaptivePractice() {
  const [track, setTrack] = useState(() => {
    const query = new URLSearchParams(window.location.search)
    return `${query.get('exam') === 'act' ? 'act' : 'sat'}_${query.get('subject') === 'ela' ? 'ela' : 'math'}`
  })
  const [profile, setProfile] = useState(null)
  const [session, setSession] = useState(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const attempt = useRef(null)
  useEffect(() => {
    let active = true
    api(`/api/adaptive/profile?track=${track}`).then(data => { if (active) setProfile(data) }).catch(e => { if (active) setError(e.message) })
    window.history.replaceState(null, '', `?exam=${track.split('_')[0]}&subject=${track.split('_')[1]}`)
    return () => { active = false }
  }, [track, session])
  const switchTrack = next => { if (next === track) return; setProfile(null); setError(''); attempt.current = null; setTrack(next) }
  const start = async () => {
    setBusy(true); setError('')
    attempt.current ||= requestId()
    try {
      const data = await post('/api/adaptive/practice', { track, request_id: attempt.current })
      setSession(data.id)
    } catch (e) { setError(e.message) } finally { setBusy(false) }
  }
  return <AppShell name={boot.data.name}><main className="app-main adaptive-page">
    {session ? <AdaptiveSession key={session} id={session} onLeave={() => { setSession(null); attempt.current = null }} /> : <>
      <header className="adaptive-heading"><div className="eyebrow">MENTICS / QUICK PRACTICE</div><h1>Make the next rep count.</h1><p>Five questions chosen from your progress. A useful strategy when you need it. Every answer shapes what comes next.</p></header>
      <section className="prep-lanes" aria-label="Practice section"><div className="prep-exams">{['sat', 'act'].map(exam => <button disabled={busy} key={exam} aria-pressed={track.startsWith(exam)} onClick={() => switchTrack(`${exam}_${track.split('_')[1]}`)}>{exam.toUpperCase()}<small>Your progress stays separate</small></button>)}</div><div className="prep-subjects">{['math', 'ela'].map(section => <button key={section} disabled={busy} aria-pressed={track.endsWith(section)} onClick={() => switchTrack(`${track.split('_')[0]}_${section}`)}>{section === 'math' ? <Target size={20} /> : <BookOpen size={20} />}<span><b>{section === 'math' ? 'Math' : 'ELA'}</b><small>{section === 'math' ? 'Reasoning & problem solving' : track.startsWith('act') ? 'English & Reading' : 'Reading & Writing'}</small></span>{track.endsWith(section) && <Check size={18} />}</button>)}</div></section>
      <div className="adaptive-start-grid"><section className="adaptive-card"><div className="eyebrow">YOUR NEXT FOCUS</div><h2>{label(track)}</h2><p>{profile?.benchmark_completed ? 'Your diagnostic and recent answers guide this session.' : 'Your goals and any recorded practice guide this session. Take the benchmark in Learning Paths for a clearer starting point.'}</p>
        {profile ? <ul className="adaptive-focus">{[...new Set(profile.targets || [])].map(key => { const s = profile.skills[key]; return <li key={key}><span>{s.label}</span><small>{s.accuracy == null ? 'Build evidence' : `${Math.round(s.accuracy * 100)}% across ${s.attempts} answers`} · {s.readiness}</small></li> })}</ul> : <p role="status">Reading your learning history…</p>}
        <a className="text-button" href={`/dashboard/test-path-view?track=${track}`}>Continue your learning path <ArrowRight size={16} /></a>
      </section><aside className="adaptive-launch"><span className="eyebrow">A SMALL SESSION. A CLEAR PURPOSE.</span><h2>Find the move.<br />Make it stick.</h2><p>Work through a targeted set with three levels of hints, explanations, and faster test-day approaches.</p><div className="adaptive-launch-facts"><span><b>05</b> questions</span><span><b>03</b> hint levels</span></div><button className="button button--primary" disabled={busy || !profile} onClick={profile?.resume_session ? () => setSession(profile.resume_session) : start}>{busy ? 'Preparing and checking your questions…' : profile?.resume_session ? 'Resume saved practice' : 'Start personalized practice'} {!busy && <ArrowRight size={18} />}</button><small>Answers save as you go. Accuracy comes before speed.</small></aside></div>
      {error && <div role="alert" className="error-banner">{error}<button onClick={() => profile ? start() : window.location.reload()}>Try again</button></div>}
      <p className="adaptive-credit">SAT Desmos and grammar emphasis informed by <a href="https://www.skool.com/sat/about" target="_blank" rel="noreferrer">James Lu’s public SAT prep</a>. Original Mentics questions; not affiliated. Specific influences are credited alongside practice.</p>
    </>}
  </main></AppShell>
}

function AdaptiveSession({ id, onLeave }) {
  const [session, setSession] = useState(null)
  const [activeId, setActiveId] = useState(id)
  const [index, setIndex] = useState(0)
  const [selected, setSelected] = useState(null)
  const [confidence, setConfidence] = useState(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [pathReady, setPathReady] = useState(false)
  const [building, setBuilding] = useState(false)
  const [review, setReview] = useState(false)
  const [calculatorOpen, setCalculatorOpen] = useState(false)
  const clock = useRef({ start: 0, elapsed: 0 })
  const analysisStarted = useRef(false)
  const question = session?.questions[index]
  const answered = !!question?.answer
  const benchmark = session?.kind === 'benchmark'
  const load = async () => {
    try {
      const data = await api(`/api/adaptive/session/${activeId}`)
      setSession(data)
      const next = data.questions.findIndex(q => !q.answer)
      setIndex(next < 0 ? Math.max(0, data.total - 1) : next)
    } catch (e) { setError(e.message) }
  }
  // Load durable session state from the API when its identity changes.
  useEffect(() => { load() }, [activeId]) // eslint-disable-line react-hooks/exhaustive-deps, react-hooks/set-state-in-effect
  useEffect(() => {
    if (session?.status !== 'generating') return
    const timer = setInterval(load, 3000)
    return () => clearInterval(timer)
  }, [session?.status]) // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => {
    clock.current = { start: performance.now(), elapsed: 0 }
    const visibility = () => {
      if (document.hidden) { clock.current.elapsed += performance.now() - clock.current.start; clock.current.start = 0 }
      else clock.current.start = performance.now()
    }
    document.addEventListener('visibilitychange', visibility)
    return () => document.removeEventListener('visibilitychange', visibility)
  }, [id, index])
  const act = async (action, data = {}) => {
    setBusy(true); setError('')
    try {
      const next = await post(`/api/adaptive/session/${activeId}`, { action, ...data })
      setSession(next)
      return next
    } catch (e) { setError(e.message); return null } finally { setBusy(false) }
  }
  const buildPath = async () => {
    setBuilding(true); setError('')
    try { await post(`/api/adaptive/session/${activeId}`, { action: 'next_path' }); setPathReady(true) }
    catch (e) { setError(e.message) } finally { setBuilding(false) }
  }
  useEffect(() => {
    if (benchmark && session?.status === 'completed' && !analysisStarted.current) { analysisStarted.current = true; buildPath() }
  }, [benchmark, session?.status]) // eslint-disable-line react-hooks/exhaustive-deps
  const submit = () => act('answer', { index, selected_option: selected, confidence, response_ms: Math.min(3600000, Math.round(clock.current.elapsed + (clock.current.start ? performance.now() - clock.current.start : 0))) })
  const retryGeneration = async () => {
    setBusy(true); setError('')
    try { const data = await post('/api/adaptive/practice', { track: session.track, request_id: requestId() }); setSession(data); setActiveId(data.id) }
    catch (e) { setError(e.message) } finally { setBusy(false) }
  }
  const leave = onLeave || (() => { window.location.href = `/dashboard/test-path-view?track=${session?.track || 'sat_math'}` })
  return <section className="adaptive-session">
    <div className="adaptive-session-nav"><button className="text-button" onClick={leave}><ArrowLeft size={16} /> Save & leave</button><span>{session ? label(session.track) : 'MENTICS'}</span></div>
    {error && <div className="error-banner" role="alert">{error}{!session && <button onClick={load}>Retry loading</button>}</div>}
    {!session ? <div className="adaptive-card" role="status">Loading your saved session…</div> : session.status === 'generating' || session.status === 'failed' ? <div className="adaptive-card"><h1>Preparing your next questions.</h1><p>Mentics is reading your progress and checking each question before practice.</p>{session.can_retry && <button className="button button--primary" disabled={busy} onClick={retryGeneration}>Retry preparation</button>}</div> : session.status === 'completed' ? <>
      <header className="adaptive-heading"><div className="eyebrow">{benchmark ? 'YOUR STARTING POINT, SAVED' : 'PRACTICE COMPLETE'}</div><h1>{benchmark ? 'Now we have a direction.' : 'One session smarter.'}</h1><p>{session.summary.correct} of {session.summary.total} correct. {benchmark ? session.summary.message : 'These answers now inform your next practice and learning path.'}</p></header>
      <section className="adaptive-card">{!benchmark && <p>{session.points || 0} session points. Best streak: {session.best_streak || 0}. Practice points are separate from account XP.</p>}<div className="adaptive-score"><b>{Math.round(session.summary.accuracy * 100)}<small>%</small></b><span>accuracy<br />in this session</span></div><ul className="adaptive-focus">{Object.entries(session.summary.domains || {}).map(([domain, result]) => <li key={domain}><span>{domain}</span><small>{result.correct} / {result.total} correct</small></li>)}</ul>{session.summary.rapid_responses > 0 && <p>Very fast responses carry less weight in your mastery estimate. Future practice will check that evidence.</p>}
        {benchmark ? <><p role="status">{building ? 'Analyzing your answers and preparing five focused steps…' : pathReady ? 'Your personalized five-step path is ready.' : 'Your benchmark is saved. Continue preparing your path below.'}</p>{pathReady ? <a className="button button--primary" href={`/dashboard/test-path-view?track=${session.track}`}>Open my path <ArrowRight size={18} /></a> : <button className="button button--primary" disabled={building} onClick={buildPath}>{building ? 'Building your path…' : 'Prepare my path'}</button>}</> : <button className="button button--primary" onClick={leave}>Choose the next session <ArrowRight size={18} /></button>}
        <button className="text-button adaptive-review-toggle" onClick={() => setReview(!review)} aria-expanded={review}>{review ? 'Hide' : 'Review'} answers</button>
      </section>{review && session.questions.map(q => <article className="adaptive-card" key={q.index}><div className="eyebrow">QUESTION {q.index + 1} · {q.answer.selected_option === q.correct_option ? 'CORRECT' : 'KEEP PRACTICING'}</div>{q.source_or_prompt && <p className="adaptive-passage">{q.source_or_prompt}</p>}<h3>{q.question_text}</h3><p>Your answer: {q.options[q.answer.selected_option]}</p><b>Correct answer: {q.options[q.correct_option]}</b><p>{q.explanation}</p><p>{q.fastest_method}</p><Credit value={q.attribution} /></article>)}
    </> : question && <>
      <header className="adaptive-heading"><div className="eyebrow">{benchmark ? 'ONE-TIME SECTION BENCHMARK' : 'YOUR TARGETED SESSION'}</div><h1>{benchmark ? 'Show us where you are.' : 'Work the question. Learn the move.'}</h1><p>{benchmark ? '12 original diagnostic questions across this section. Work independently; hints and solutions come after submission. Every answer is saved.' : session.note}</p></header>
      <div className="adaptive-progress"><span>Question {index + 1} of {session.total}</span><span>{session.answered} saved{!benchmark && ` / ${session.points || 0} session points / ${session.streak || 0} streak`}</span><progress aria-label="Saved answers" max={session.total} value={session.answered} /></div>
      <article className="adaptive-card adaptive-question"><div className="eyebrow">{question.domain} · {question.difficulty}</div>{session.track.endsWith('math') && <div className="math-tool-row"><DesmosCalculatorToggle open={calculatorOpen} onToggle={() => setCalculatorOpen(value => !value)} /><span>Embedded graphing calculator</span></div>}{question.source_or_prompt && <div className="adaptive-passage">{question.source_or_prompt}</div>}<h2>{question.question_text}</h2><div className="prep-answers" role="group" aria-label="Answer choices">{question.options.map((option, choice) => <button key={choice} disabled={answered || busy} aria-pressed={(answered ? question.answer.selected_option : selected) === choice} className={`${(answered ? question.answer.selected_option : selected) === choice ? 'is-selected' : ''} ${answered && !benchmark && choice === question.correct_option ? 'is-correct' : ''}`} onClick={() => setSelected(choice)}><span>{'ABCD'[choice]}</span><b>{option}</b></button>)}</div>
        {!answered && <fieldset className="adaptive-confidence"><legend>How confident are you? <small>Optional</small></legend>{['Guessing', 'Somewhat sure', 'Confident'].map((text, i) => <button key={text} disabled={busy} aria-pressed={confidence === i + 1} onClick={() => setConfidence(confidence === i + 1 ? null : i + 1)}>{text}</button>)}</fieldset>}
        {!benchmark && !answered && <button className="text-button" disabled={busy || question.hints.length >= 3} onClick={() => act('hint', { index })}><Lightbulb size={17} />{question.hints.length >= 3 ? 'All hints shown' : `Hint ${question.hints.length + 1} of 3`}</button>}
        {question.hints.map((hint, i) => <div className="adaptive-hint" key={i}><b>Hint {i + 1}</b><p>{hint}</p></div>)}
        <Credit value={question.attribution} />
        {answered && <div className="adaptive-feedback" role="status"><b>{benchmark ? 'Answer saved.' : question.answer.selected_option === question.correct_option ? 'Correct. Keep that approach.' : `The answer is ${'ABCD'[question.correct_option]}. Here’s why.`}</b>{!benchmark && <><p>{question.explanation}</p>{question.fastest_method && <p><b>Test-day approach:</b> {question.fastest_method}</p>}</>}</div>}
        <div className="adaptive-actions"><span>{benchmark ? 'Unsure? Choose your best answer.' : 'Accuracy first. Speed follows.'}</span>{answered ? <button className="button button--primary" disabled={busy} onClick={() => index + 1 < session.total ? (setSelected(null), setConfidence(null), setIndex(index + 1)) : act('finish')}>{busy ? 'Saving…' : index + 1 < session.total ? 'Next question' : benchmark ? 'Submit benchmark' : 'Finish session'}<ArrowRight size={18} /></button> : <button className="button button--primary" disabled={busy || selected === null} onClick={submit}>{busy ? 'Saving…' : benchmark ? 'Save answer' : 'Check answer'}<Check size={18} /></button>}</div>
      </article>
      {session.track.endsWith('math') && <DesmosCalculator open={calculatorOpen} onClose={() => setCalculatorOpen(false)} />}
    </>}
  </section>
}
