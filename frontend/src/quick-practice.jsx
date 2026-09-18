import { useEffect, useRef, useState } from 'react'
import { ArrowRight, BookOpen, Check, Clock3, Flame, RotateCcw, Target, Trophy, Zap } from 'lucide-react'
import { AppShell } from './app-runtime'
import { boot } from './boot'
import { makeRound } from './quick-practice-data'
import './quick-practice.css'

const labels = { sat: { math: 'Math', ela: 'Reading & Writing' }, act: { math: 'Math', ela: 'English & Reading' } }
const formatTime = seconds => `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, '0')}`

export default function QuickPractice() {
  const [exam, setExam] = useState('sat')
  const [subject, setSubject] = useState('math')
  const [mode, setMode] = useState('sprint')
  const [round, setRound] = useState(null)
  const [answers, setAnswers] = useState([])
  const [selected, setSelected] = useState(null)
  const [revealed, setRevealed] = useState(false)
  const [hint, setHint] = useState(false)
  const [seconds, setSeconds] = useState(0)
  const [finished, setFinished] = useState(false)
  const [review, setReview] = useState(false)
  const started = useRef(0)
  const questionHeading = useRef(null)
  const index = answers.length - (revealed ? 1 : 0)
  const question = round?.[index]
  const correct = answers.filter(answer => answer.correct).length
  const streak = answers.reduce((run, answer) => answer.correct ? run + 1 : 0, 0)
  const bestStreak = answers.reduce((state, answer) => { const current = answer.correct ? state.current + 1 : 0; return { current, best: Math.max(state.best, current) } }, { current: 0, best: 0 }).best
  const points = answers.reduce((sum, answer) => sum + (answer.correct ? (answer.hint ? 50 : 100) : 0), 0)

  useEffect(() => {
    if (!round || finished) return
    const timer = window.setInterval(() => setSeconds(Math.floor((Date.now() - started.current) / 1000)), 500)
    return () => window.clearInterval(timer)
  }, [round, finished])
  useEffect(() => { if (round) questionHeading.current?.focus() }, [round, index, finished, review])

  const start = (questions = makeRound(exam, subject)) => {
    setRound(questions); setAnswers([]); setSelected(null); setRevealed(false); setHint(false)
    setFinished(false); setReview(false); setSeconds(0); started.current = Date.now()
  }
  const check = () => {
    if (selected === null || revealed) return
    setAnswers(previous => [...previous, { question, selected, correct: selected === question.answer, hint }])
    setRevealed(true)
  }
  const next = () => {
    if (answers.length === round.length) { setSeconds(Math.floor((Date.now() - started.current) / 1000)); setFinished(true) }
    else { setSelected(null); setRevealed(false); setHint(false) }
  }
  const reset = () => { setRound(null); setFinished(false); setReview(false) }
  const missed = answers.filter(answer => !answer.correct)

  return <AppShell name={boot.data.name}><main className={`app-main quick-prep ${round ? 'prep-in-round' : ''}`}>
    <header className="prep-heading"><div><div className="eyebrow"><span /> TEST PREP / QUICK PRACTICE</div><h1>{round ? 'Make your move.' : 'Get into your rhythm.'}</h1><p>{round ? 'One question. One strategy. A sharper next attempt.' : 'A little focus today. A little more confidence on test day.'}</p></div><a href="/dashboard/test-path-view" className="prep-path-link">My study path <ArrowRight size={16} /></a></header>
    {!round ? <>
      <section className="prep-config" aria-label="Choose your practice">
        <div className="prep-config-title"><span className="prep-step-tag">01</span><div><h2>Make it your session.</h2><p>Pick your exam, your focus, and your pace.</p></div></div><div className="prep-section-heading"><span>EXAM</span></div>
        <div className="prep-exams" role="group" aria-label="Exam">{['sat', 'act'].map(value => <button type="button" key={value} aria-pressed={exam === value} onClick={() => setExam(value)} className={exam === value ? 'is-selected' : ''}><span><b>{value.toUpperCase()}</b><small>{value === 'sat' ? 'Math · Reading & Writing' : 'Math · English & Reading'}</small></span><span className="prep-selection-dot">{exam === value && <Check size={15} />}</span></button>)}</div>
        <div className="prep-section-heading"><span>FOCUS</span></div>
        <div className="prep-subjects" role="group" aria-label="Subject">{[['math', 'Math', Target], ['ela', 'ELA', BookOpen]].map(([value, label, Icon]) => <button type="button" key={value} aria-pressed={subject === value} onClick={() => setSubject(value)} className={subject === value ? 'is-selected' : ''}><Icon /><span><b>{label}</b><small>{value === 'math' ? 'Numbers & problem solving' : labels[exam][value]}</small></span>{subject === value && <Check size={17} />}</button>)}</div>
        <div className="prep-section-heading"><span>PACE</span></div>
        <div className="prep-modes" role="group" aria-label="Practice mode">{[['sprint', 'Speed round', 'Aim for five minutes. Keep going if you need more.', Zap], ['learn', 'Strategy practice', 'No clock on screen. Work through each tactic.', BookOpen]].map(([value, title, copy, Icon]) => <button key={value} type="button" aria-pressed={mode === value} onClick={() => setMode(value)} className={mode === value ? 'is-selected' : ''}><Icon /><b>{title}</b><small>{copy}</small></button>)}</div>
      </section>
      <aside className="prep-launch"><div className="prep-launch-top"><span><i /> READY WHEN YOU ARE</span><Zap size={20} /></div><div className="prep-orbit" aria-hidden="true"><i /><i /><span>05<small>QUESTIONS</small></span><b><Zap size={19} /></b></div><div className="prep-launch-copy"><span className="prep-exam-chip">{exam.toUpperCase()} / {labels[exam][subject]}</span><h2>{mode === 'sprint' ? 'Find your fast.' : 'Learn the move.'}</h2><p>{mode === 'sprint' ? 'Beat the trap. Build your streak. Turn five focused minutes into real practice.' : 'Slow it down. Learn a useful shortcut, then put it to work on the next question.'}</p></div><div className="prep-launch-metrics"><span><Clock3 size={15} />{mode === 'sprint' ? '5-minute target' : 'No timer pressure'}</span><span><Flame size={15} />Streaks + points</span></div><button className="button button--primary" onClick={() => start()}>Start {mode === 'sprint' ? 'speed round' : 'practicing'} <ArrowRight /></button><small>Original strategy drills / Instant explanations</small></aside>
      <section className="prep-bottom" aria-label="Keep building"><a className="prep-long-path" href={`/dashboard/test-path-builder?test_focus=${exam}&subject_focus=${subject}`}><span className="prep-path-icon"><BookOpen /></span><span><small>THE LONG GAME</small><b>Build a stronger foundation.</b><p>Lessons and a study plan shaped around you.</p></span><ArrowRight /></a><div className="prep-how"><span><b>01</b> Try a tactic</span><span><b>02</b> Get feedback</span><span><b>03</b> Retry the miss</span></div></section>
      <p className="prep-fine-print">Round points: 100 per correct answer, or 50 with a hint. Separate from account points. These short drills are not full test simulations.{exam === 'act' ? ' Find Science in the full ACT study path.' : ''}</p>
    </> : <section className="prep-session" aria-label={`${exam.toUpperCase()} ${labels[exam][subject]} practice`}>
      <div className="prep-session-bar"><div><span className="prep-session-kicker">MENTICS PRACTICE / {mode === 'sprint' ? 'SPEED' : 'STRATEGY'}</span><strong><b>{exam.toUpperCase()}</b> {labels[exam][subject]}</strong></div><button className="text-button" onClick={reset}>{finished ? 'Change practice' : 'End round'}</button></div>
      {finished ? <div className="prep-results"><div className="prep-result-mark"><Trophy className="prep-trophy" /><span>ROUND<br />COMPLETE</span></div><div className="eyebrow">YOUR PRACTICE RECEIPT</div><h2 ref={questionHeading} tabIndex={-1}>{correct === round.length ? 'Clean sweep.' : 'The next move is clear.'}</h2><p>{correct} of {round.length} correct{mode === 'sprint' ? ` in ${formatTime(seconds)}` : ''}. {missed.length ? 'Bring the misses back for another rep.' : 'Keep the momentum with another set.'}</p><div className="prep-result-stats"><span><small>ROUND POINTS</small><b>{points}</b></span><span><small>ACCURACY</small><b>{Math.round(correct / round.length * 100)}%</b></span><span><small>BEST STREAK</small><b>{bestStreak}</b></span></div><div className="prep-result-actions"><button className="button button--primary" onClick={() => start()}>New round <ArrowRight /></button>{missed.length > 0 && <button className="button button--quiet" onClick={() => start(missed.map(answer => answer.question))}><RotateCcw /> Retry {missed.length} missed</button>}<button className="text-button" aria-expanded={review} onClick={() => setReview(!review)}>{review ? 'Hide' : 'Review'} answers</button></div>{review && <div className="prep-review">{answers.map((answer, i) => <article key={i}><small>{answer.correct ? 'CORRECT' : 'PRACTICE AGAIN'} · {answer.question.skill}</small><h3>{answer.question.prompt}</h3><p>Your answer: {answer.question.options[answer.selected]}</p><b>Correct answer: {answer.question.options[answer.question.answer]}</b><p>{answer.question.explanation}</p></article>)}</div>}</div> : <>
        <div className="prep-hud"><span className="prep-round-count"><small>QUESTION</small><b>{String(index + 1).padStart(2, '0')}<i>/ {String(round.length).padStart(2, '0')}</i></b></span><span><Flame /> {streak} streak</span><span><Zap /> {points} pts</span>{mode === 'sprint' && <span><Clock3 /> {formatTime(seconds)} <small>/ 5:00 target</small></span>}</div>
        <div className="prep-progress" role="progressbar" aria-label="Questions answered" aria-valuenow={answers.length} aria-valuemin={0} aria-valuemax={round.length}><i style={{ width: `${answers.length / round.length * 100}%` }} /></div>
        <div className="prep-question"><div className="prep-question-meta"><div className="eyebrow">{question.skill}</div><span>{mode === 'sprint' ? 'MAKE THE CALL' : 'WORK THE MOVE'}</span></div><h2 ref={questionHeading} tabIndex={-1}>{question.prompt}</h2><div className="prep-answers" role="group" aria-label="Answer choices">{question.options.map((option, i) => <button type="button" key={i} disabled={revealed} aria-pressed={selected === i} onClick={() => setSelected(i)} className={`${selected === i ? 'is-selected' : ''} ${revealed && i === question.answer ? 'is-correct' : ''} ${revealed && selected === i && i !== question.answer ? 'is-wrong' : ''}`}><span>{'ABCD'[i]}</span><b>{option}</b>{revealed && i === question.answer && <Check aria-label="Correct answer" />}</button>)}</div>
          {!revealed && <button className="text-button prep-hint-button" aria-expanded={hint} onClick={() => setHint(true)} disabled={hint}><Zap size={16} /> Show strategy hint · correct answer earns 50 pts</button>}
          {hint && !revealed && <div className="prep-feedback"><b>The move</b><p>{question.tip}</p></div>}
          {revealed && <div className={`prep-feedback ${selected === question.answer ? 'is-correct' : ''}`} role="status"><b>{selected === question.answer ? 'Correct. Keep that move.' : `The answer is ${'ABCD'[question.answer]}. Here’s why.`}</b><p>{question.explanation}</p><small><strong>Test-day tactic:</strong> {question.tip}</small></div>}
          <div className="prep-question-actions"><span>{mode === 'sprint' ? 'Accuracy first. Speed follows.' : 'Understand the move before moving on.'}</span>{revealed ? <button className="button button--primary" onClick={next}>{answers.length === round.length ? 'See results' : 'Next question'} <ArrowRight /></button> : <button className="button button--primary" disabled={selected === null} onClick={check}>Check answer <Check /></button>}</div>
        </div>
      </>}
    </section>}
  </main></AppShell>
}
