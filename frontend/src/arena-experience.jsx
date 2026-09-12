import { useEffect, useRef, useState } from 'react'
import { Check, ChevronRight, Swords, X } from 'lucide-react'
import { ArenaCalculatorToggle } from './arena-calculator'

export function BattleLoadingScreen({ rank, matchmaking = false }) {
  const [elapsed, setElapsed] = useState(0)
  useEffect(() => {
    const started = Date.now()
    const timer = setInterval(() => setElapsed(Math.floor((Date.now() - started) / 1000)), 1000)
    return () => clearInterval(timer)
  }, [])
  return <section className="arena-loading" role="status" aria-live="polite" aria-atomic="true">
    <div className="arena-loading-insignia" aria-hidden="true"><Swords /><i /><i /><i /></div>
    <small>{matchmaking ? 'CONNECTING TO THE ARENA' : `${rank} TRAINING`}</small>
    <h2>{elapsed < 20 ? 'Building your battle.' : 'Good questions take thought.'}</h2>
    <p>{matchmaking ? 'Finding your match and preparing a shared question set.' : 'Creating original questions and checking the set for your chosen difficulty.'}</p>
    <div className="arena-loading-track" aria-hidden="true"><i /></div>
    <ul aria-label="Battle preparation"><li><Check /> Loadout ready</li><li className="working"><span /> {matchmaking ? 'Connecting players' : 'Preparing questions'}</li><li><span /> Battle begins when ready</li></ul>
    <p className="arena-loading-note">{elapsed >= 35 ? 'Still working. If this set cannot be prepared, you can retry from the lobby.' : 'Your round clock starts after the questions are ready.'}</p>
  </section>
}

export function BattleQuestionPanel({ question, index, selected, onSelect, calculatorOpen, onToggleCalculator, disabled }) {
  const root = useRef(null)
  // Only an explicit paragraph boundary separates passage and task. Never guess
  // at sentence boundaries: that can change the meaning of SAT stimuli.
  const paragraphs = question.question_text.split(/\n\s*\n/).filter(Boolean)
  useEffect(() => {
    if (index === 0) return
    root.current?.querySelector('.arena-question-copy')?.focus({ preventScroll: true })
    root.current?.scrollIntoView({ block: 'start', behavior: 'instant' })
  }, [index])
  useEffect(() => {
    const keydown = event => {
      if (event.defaultPrevented || event.altKey || event.ctrlKey || event.metaKey || disabled) return
      if (event.target.closest('input, textarea, select, [contenteditable="true"], .arena-calculator, [role="dialog"]')) return
      const option = /^[1-4]$/.test(event.key) ? Number(event.key) - 1 : -1
      if (option >= 0 && question.options[option] != null) { event.preventDefault(); onSelect(index, option) }
    }
    document.addEventListener('keydown', keydown)
    return () => document.removeEventListener('keydown', keydown)
  }, [index, question.options, onSelect, disabled])
  return <div className="battle-questions" ref={root}>
    <article className="battle-question battle-question--focus" data-domain={question.domain}>
      <header><small>{question.domain === 'math' ? 'MATH' : 'READING & WRITING'} <span> / </span> {question.skill}</small>
        {question.domain === 'math' && <ArenaCalculatorToggle open={calculatorOpen} onToggle={onToggleCalculator} />}
      </header>
      <div className="arena-question-copy" tabIndex={-1} id={`arena-question-${index}`}>
        <span className="arena-question-number">QUESTION {String(index + 1).padStart(2, '0')}</span>
        {paragraphs.map((paragraph, i) => <p key={i}>{paragraph}</p>)}
      </div>
      <fieldset className="arena-answer-choices" aria-describedby={`arena-question-${index}`} disabled={disabled}>
        <legend>Choose your answer <span>Keys 1–4</span></legend>
        {question.options.map((option, optionIndex) => <label key={optionIndex} className={selected === optionIndex ? 'selected' : ''}>
          <input type="radio" name={`question-${index}`} checked={selected === optionIndex} onChange={() => onSelect(index, optionIndex)} />
          <i aria-hidden="true">{String.fromCharCode(65 + optionIndex)}</i><span>{option}</span>
          {selected === optionIndex && <Check aria-hidden="true" />}
        </label>)}
      </fieldset>
    </article>
  </div>
}

export function BattleReview({ battle, answers }) {
  if (!battle.questionReview?.length) return null
  const graded = Array.isArray(battle.answers)
    ? Object.fromEntries(battle.answers.map(answer => [answer.question_index, answer.selected_option]))
    : answers
  return <section className="arena-review" aria-label="Review your answers">
    <header><small>THE NEXT ROUND STARTS HERE</small><h2>Learn from every answer.</h2><p>Review the reasoning, then take it into your next battle.</p></header>
    {battle.questionReview.map((review, i) => {
      const selected = graded[i]
      const correct = selected === battle.answerKey?.[i]
      return <details key={i} className={correct ? 'correct' : 'incorrect'}>
        <summary><i>{correct ? <Check /> : <X />}</i><span><b>Question {i + 1}</b><small>{review.skill}</small></span><em>{correct ? 'Correct' : selected == null ? 'Unanswered' : 'Review'}</em><ChevronRight /></summary>
        <div><p className="arena-review-stem">{review.questionText}</p>
          {!correct && selected != null && <p>Your answer: <strong>{battle.questions?.[i]?.options?.[selected]}</strong></p>}
          <p className="arena-review-key">Correct answer: <strong>{review.correctAnswer}</strong></p><p>{review.explanation}</p></div>
      </details>
    })}
  </section>
}
