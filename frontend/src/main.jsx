import React, { useEffect, useMemo, useRef, useState } from 'react'
import { createRoot } from 'react-dom/client'
import DOMPurify from 'dompurify'
import { marked } from 'marked'
import {
  ArrowRight, BarChart3, BookOpen, CalendarDays, Check, ChevronRight,
  CircleUserRound, Clock3, Compass, FileText, Flame, GraduationCap, House,
  LayoutDashboard, LineChart, ListChecks, LockKeyhole, Menu, MessageCircle,
  Plus, RotateCcw, Send, Settings, Sparkles, Target, Trophy, X, Zap
} from 'lucide-react'
import './styles.css'

const boot = window.__MENTICS__ || { page: 'landing', data: {} }

function Brand({ inverse = false }) {
  return <a className={`brand ${inverse ? 'brand--inverse' : ''}`} href="/" aria-label="Mentics home">MENTICS</a>
}

function Reveal({ as: Tag = 'div', className = '', children, delay = 0, ...props }) {
  const ref = useRef(null)
  useEffect(()=>{
    const node = ref.current
    if (!node) return
    const observer = new IntersectionObserver(([entry])=>{
      if (entry.isIntersecting) {
        node.classList.add('is-visible')
        observer.disconnect()
      }
    }, {threshold:.12, rootMargin:'0px 0px -40px'})
    observer.observe(node)
    return ()=>observer.disconnect()
  },[])
  return <Tag ref={ref} className={`reveal ${className}`} style={{'--reveal-delay':`${delay}ms`}} {...props}>{children}</Tag>
}

function Landing() {
  const loggedIn = boot.data.isLoggedIn
  return <div className="landing">
    <header className="public-nav">
      <Brand />
      <nav aria-label="Main navigation">
        <a href="#how-it-works">How it works</a>
        <a href="#inside-mentics">Inside Mentics</a>
        <a href="#platform">Platform</a>
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
        <div className="eyebrow hero-enter hero-enter--one"><span /> Built for high school ambition</div>
        <h1 className="hero-enter hero-enter--two">MENTICS</h1>
        <p className="hero-tagline hero-enter hero-enter--three">Your high school ambition, clarified.<br />Stop guessing. <strong>Start achieving.</strong></p>
        <div className="hero-actions hero-enter hero-enter--four">
          <a className="button button--primary" href={loggedIn ? '/dashboard' : '/signup'}>
            {loggedIn ? 'Continue your path' : 'Build your free path'} <ArrowRight size={18} />
          </a>
          <a className="button button--quiet" href="#how-it-works">See how it works</a>
        </div>

        <div className="product-frame hero-enter hero-enter--five" aria-label="Mentics product preview">
          <div className="frame-top"><span /><span /><span /><div>app.mentics</div></div>
          <div className="preview-shell">
            <aside className="preview-rail"><Brand /><div className="preview-nav active"><House size={16}/> Home</div><div className="preview-nav"><Target size={16}/> My path</div><div className="preview-nav"><BarChart3 size={16}/> Progress</div></aside>
            <div className="preview-main">
              <div className="preview-heading"><div><small>MONDAY, AUGUST 14</small><h3>Good morning, Alex.</h3><p>One clear step at a time.</p></div><div className="streak-pill"><Flame size={15}/> 6 day focus</div></div>
              <div className="preview-grid">
                <div className="preview-plan">
                  <div className="card-kicker">TODAY'S PATH</div>
                  {[['01','Review linear functions','20 min'],['02','Complete a focused sprint','15 min'],['03','Log missed questions','10 min']].map((item, i) => <div className={`preview-task ${i === 0 ? 'current' : ''}`} key={item[0]}><b>{item[0]}</b><span>{item[1]}</span><small>{item[2]}</small></div>)}
                </div>
                <div className="preview-score"><div className="card-kicker">SAT PROGRESS</div><strong>1420</strong><span>+60 this month</span><div className="mini-chart"><i/><i/><i/><i/><i/><i/></div></div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="trust-strip"><div className="trust-track">{[0,1].map(copy=><React.Fragment key={copy}><span>A path that adapts</span><span>Focused daily action</span><span>Progress you can see</span><span>Guidance when you need it</span></React.Fragment>)}</div></section>

      <Reveal as="section" className="section process" id="how-it-works">
        <div className="section-heading"><div className="eyebrow"><span /> THE MENTICS METHOD</div><h2>Clarity changes everything.</h2><p>Mentics turns a distant goal into the next right move—then learns from what happens.</p></div>
        <div className="process-grid">
          <article><b>01</b><Target/><h3>Tell us where you are</h3><p>Share your goals, timing, strengths, and the areas that need attention.</p></article>
          <article><b>02</b><Sparkles/><h3>Get a five-step path</h3><p>Receive a focused roadmap built around your actual priorities—not a generic checklist.</p></article>
          <article><b>03</b><BarChart3/><h3>Improve with evidence</h3><p>Complete work, track results, and let every new path build on real progress.</p></article>
        </div>
      </Reveal>

      <Reveal as="section" className="section journey" id="inside-mentics">
        <div className="journey-copy">
          <div className="eyebrow"><span /> A PLAN THAT MOVES WITH YOU</div>
          <h2>Five steps.<br/>One clear direction.</h2>
          <p>Your path is short enough to act on and smart enough to evolve. Finish a step, log what happened, and Mentics uses that evidence to shape what comes next.</p>
          <div className="journey-proof"><span><Check/> Specific to your goal</span><span><Check/> Grounded in your progress</span><span><Check/> Built to be finishable</span></div>
          <a className="text-link" href={loggedIn ? '/dashboard/test-path-view' : '/signup'}>See your first five steps <ArrowRight/></a>
        </div>
        <div className="journey-visual">
          <div className="journey-line"/>
          {[
            ['01','Find the signal','Turn your current scores and goals into a focused starting point.'],
            ['02','Build the skill','Work on one specific gap with the right resource or strategy.'],
            ['03','Practice with purpose','Use a targeted sprint to apply the idea under pressure.'],
            ['04','Learn from misses','Capture why mistakes happened instead of simply moving on.'],
            ['05','Measure the change','Use a meaningful checkpoint to decide what comes next.']
          ].map((step,i)=><div className={`journey-step ${i===0?'active':''}`} key={step[0]} style={{'--step-delay':`${i*110}ms`}}><b>{step[0]}</b><span><strong>{step[1]}</strong><small>{step[2]}</small></span></div>)}
        </div>
      </Reveal>

      <Reveal as="section" className="section bento-section">
        <div className="section-heading"><div className="eyebrow"><span /> MORE THAN A CHECKLIST</div><h2>Everything has a reason.</h2><p>Each part of Mentics is designed to turn uncertainty into a decision you can act on today.</p></div>
        <div className="landing-bento">
          <article className="bento-path"><div><Compass/><small>ADAPTIVE PLANNING</small></div><h3>A roadmap that remembers where you have been.</h3><div className="bento-mini-path"><i/><i/><i/><i/><i/></div></article>
          <article className="bento-chat"><div><MessageCircle/><small>CONTEXTUAL GUIDANCE</small></div><div className="mini-conversation"><p>Why is this my next step?</p><p>Because timing—not content—caused most of your recent misses. Let’s fix pacing before adding new material.</p></div></article>
          <article className="bento-essay"><div><FileText/><small>ESSAY FEEDBACK</small></div><h3>Feedback that points to the sentence, not just the problem.</h3><div className="essay-lines"><i/><i/><i/><i/></div></article>
          <article className="bento-data"><div><LineChart/><small>VISIBLE PROGRESS</small></div><strong>+140</strong><span>Projected score movement</span><div className="bento-bars"><i/><i/><i/><i/><i/></div></article>
        </div>
      </Reveal>

      <Reveal as="section" className="momentum-band">
        <div><small>THE REAL ADVANTAGE</small><h2>Momentum you can feel.</h2></div>
        <p>Not more tabs. Not more noise. Just a clear system for deciding, doing, learning, and moving forward.</p>
        <div className="momentum-loop"><span><ListChecks/> Decide</span><i/><span><Target/> Do</span><i/><span><BarChart3/> Learn</span><i/><span><ArrowRight/> Advance</span></div>
      </Reveal>

      <Reveal as="section" className="section platform" id="platform">
        <div className="platform-copy"><div className="eyebrow eyebrow--light"><span /> ONE FOCUSED WORKSPACE</div><h2>Less noise.<br/>More momentum.</h2><p>Test prep, college planning, progress, and contextual guidance belong in one calm place.</p><a href={loggedIn ? '/dashboard' : '/signup'}>Explore the platform <ArrowRight size={17}/></a></div>
        <div className="feature-stack">
          <div><Target/><span><b>Adaptive paths</b><small>Five clear steps that respond to your goals and performance.</small></span></div>
          <div><MessageCircle/><span><b>Contextual guidance</b><small>Ask for help without losing the context of what you are working on.</small></span></div>
          <div><GraduationCap/><span><b>College planning</b><small>Turn applications, essays, and deadlines into manageable progress.</small></span></div>
          <div><BarChart3/><span><b>Visible progress</b><small>Track scores, streaks, milestones, and the work behind them.</small></span></div>
        </div>
      </Reveal>

      <Reveal as="section" className="section faq" id="faq"><div className="section-heading"><h2>Good questions.</h2></div>
        {[['Is Mentics free to use?','Yes. The current early-access product is free and does not require a credit card.'],['Does it support both SAT and ACT?','Yes. Your test-prep path can focus on the SAT, ACT, or both.'],['Can my plan change as I improve?','Yes. Regenerate a path after new scores, completed work, or a change in goals. Mentics uses that context to plan the next five steps.']].map(([q,a])=><details key={q}><summary>{q}<Plus size={18}/></summary><p>{a}</p></details>)}
      </Reveal>

      <Reveal as="section" className="closing"><div><Brand inverse/><h2>Know what to do next.</h2><p>Build a path that makes your ambition feel possible.</p><a className="button button--light" href={loggedIn ? '/dashboard' : '/signup'}>{loggedIn ? 'Open dashboard' : 'Get started free'} <ArrowRight size={18}/></a></div></Reveal>
    </main>
    <footer><Brand/><span>© 2026 Mentics. All rights reserved.</span><div><a href="/terms">Terms</a><a href="/privacy">Privacy</a><a href="mailto:support@mentics.com">Contact</a></div></footer>
  </div>
}

const navItems = [
  ['/dashboard', LayoutDashboard, 'Home'],
  ['/dashboard/test-path-view', Target, 'Test path'],
  ['/dashboard/college-path-view', GraduationCap, 'College path'],
  ['/dashboard/stats', BarChart3, 'Progress'],
  ['/account', Settings, 'Settings']
]

function AppShell({ children, name }) {
  const [menu, setMenu] = useState(false)
  const current = window.location.pathname
  return <div className="app-shell">
    <aside className={`side-nav ${menu ? 'side-nav--open' : ''}`}>
      <div className="side-nav-head"><Brand/><button className="icon-button mobile-only" onClick={()=>setMenu(false)} aria-label="Close menu"><X/></button></div>
      <nav>{navItems.map(([href, Icon, label])=><a key={href} className={current === href ? 'active' : ''} href={href}><Icon size={19}/><span>{label}</span></a>)}</nav>
      <div className="side-account"><div>{(name || 'M').slice(0,1).toUpperCase()}</div><span><b>{name || 'Mentics student'}</b><a href="/account">View account</a></span><a href="/logout" aria-label="Log out"><ChevronRight size={18}/></a></div>
    </aside>
    {menu && <button className="menu-scrim" onClick={()=>setMenu(false)} aria-label="Close menu"/>}
    <div className="app-stage">
      <header className="mobile-header"><button className="icon-button" onClick={()=>setMenu(true)} aria-label="Open menu"><Menu/></button><Brand/><a href="/account"><CircleUserRound/></a></header>
      {children}
    </div>
  </div>
}

function ProgressRing({ value, label }) {
  const pct = Math.min(100, Math.round((value / 5) * 100))
  return <div className="progress-ring" style={{'--progress': `${pct * 3.6}deg`}}><span><b>{value}</b><small>{label}</small></span></div>
}

function Dashboard() {
  const d = boot.data
  const [suggestion, setSuggestion] = useState('Reviewing your latest progress…')
  useEffect(()=>{fetch('/api/get-suggestion').then(r=>r.json()).then(x=>setSuggestion(x.suggestion || 'Your next clear step is waiting.')).catch(()=>setSuggestion('Keep the next step small, specific, and finishable.'))},[])
  const hour = new Date().getHours()
  const greeting = hour < 12 ? 'Good morning' : hour < 18 ? 'Good afternoon' : 'Good evening'
  const chart = d.activityData?.data || [0,0,0,0,0,0,0]
  const max = Math.max(...chart, 1)
  return <AppShell name={d.name}><main className="app-main dashboard-page">
    <div className="page-intro"><div><div className="eyebrow"><span/> YOUR WORKSPACE</div><h1>{greeting}, {String(d.name || 'there').split(' ')[0]}.</h1><p>Keep the momentum. Your next move is ready.</p></div><div className="header-stats"><span><Flame size={17}/><b>{d.gameStats?.streak || 0}</b> day focus</span><span><Zap size={17}/><b>{d.gameStats?.points || 0}</b> points</span></div></div>

    <section className="dashboard-grid">
      <article className="focus-card"><div className="card-top"><div><small>YOUR ACTIVE PATH</small><h2>Make today count.</h2></div><Sparkles/></div><p>{suggestion}</p><div className="path-choices">
        <a href="/dashboard/test-path-view"><ProgressRing value={d.testPrepCompleted || 0} label="of 5"/><span><b>Test preparation</b><small>{d.testPrepCompleted || 0} steps complete</small></span><ArrowRight/></a>
        <a href="/dashboard/college-path-view"><ProgressRing value={d.collegePlanningCompleted || 0} label="of 5"/><span><b>College planning</b><small>{d.collegePlanningCompleted || 0} steps complete</small></span><ArrowRight/></a>
      </div></article>

      <article className="metrics-card"><div className="card-top"><div><small>CURRENT SNAPSHOT</small><h2>Your numbers</h2></div><a href="/dashboard/stats/edit">Update</a></div><div className="metrics-row"><div><span>GPA</span><b>{d.gpa}</b></div><div><span>SAT</span><b>{d.satTotal}</b></div><div><span>ACT</span><b>{d.actAverage}</b></div></div>{d.testDateInfo?.days_left != null && <div className="test-date"><CalendarDays/><span><b>{d.testDateInfo.test_type} in {d.testDateInfo.days_left} days</b><small>{d.testDateInfo.date_str}</small></span></div>}</article>

      <article className="activity-card"><div className="card-top"><div><small>LAST 7 DAYS</small><h2>Consistency</h2></div><BarChart3/></div><div className="bar-chart">{chart.map((v,i)=><div key={i}><i style={{height:`${Math.max(8,(v/max)*100)}%`}}/><small>{d.activityData?.labels?.[i]}</small></div>)}</div></article>

      <article className="recent-card"><div className="card-top"><div><small>LATEST</small><h2>Recent activity</h2></div><Clock3/></div><div className="activity-list">{d.recentActivities?.length ? d.recentActivities.map((a,i)=><div key={i}><span><Check/></span><p><b>{activityTitle(a)}</b><small>{activityDetail(a)}</small></p></div>) : <div className="empty-state"><Target/><p>Your completed work will show up here.</p></div>}</div></article>
    </section>
  </main></AppShell>
}

function activityTitle(a) {
  return ({task_completed:'Task completed', path_generated:'New path created', stat_updated:'Progress updated', task_added:'Task added'})[a.type] || 'Progress recorded'
}
function activityDetail(a) { return a.details?.description || a.details?.stat_name || 'A step forward on your Mentics path' }

async function api(url, options = {}) {
  const response = await fetch(url, {headers:{'Content-Type':'application/json', ...(options.headers || {})}, ...options})
  const data = await response.json().catch(()=>({}))
  if (!response.ok) throw new Error(data.error || 'Something went wrong. Please try again.')
  return data
}

function Markdown({ children }) {
  const html = useMemo(()=>DOMPurify.sanitize(marked.parse(children || '', {breaks:true})), [children])
  return <div className="markdown" dangerouslySetInnerHTML={{__html:html}} />
}

function PathPage() {
  const category = boot.data.category
  const isTest = category === 'Test Prep'
  const [tasks, setTasks] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [selected, setSelected] = useState(null)
  const [chatOpen, setChatOpen] = useState(false)
  const [adding, setAdding] = useState(false)
  const builder = isTest ? '/dashboard/test-path-builder' : '/dashboard/college-path-builder'
  const loadTasks = async (regenerate = false) => {
    setLoading(true); setError('')
    try {
      const data = await api(`/api/tasks?category=${encodeURIComponent(category)}`, regenerate ? {method:'POST'} : {})
      if (!Array.isArray(data)) throw new Error('Your path could not be loaded.')
      setTasks(data.map(normalizeTask))
    } catch(e) { setError(e.message) } finally { setLoading(false) }
  }
  useEffect(()=>{
    let cancelled = false
    api(`/api/tasks?category=${encodeURIComponent(category)}`)
      .then(data=>{
        if (!Array.isArray(data)) throw new Error('Your path could not be loaded.')
        if (!cancelled) setTasks(data.map(normalizeTask))
      })
      .catch(e=>{ if (!cancelled) setError(e.message) })
      .finally(()=>{ if (!cancelled) setLoading(false) })
    return ()=>{ cancelled = true }
  },[category])
  const completed = tasks.filter(t=>t.is_completed).length
  const activeIndex = tasks.findIndex(t=>!t.is_completed)
  return <AppShell name={boot.data.name}><main className="app-main path-page">
    <div className="path-header"><div><div className="eyebrow"><span/> {category.toUpperCase()}</div><h1>Your five-step path.</h1><p>Finish what is in front of you. The path adapts from there.</p></div><div className="path-header-actions"><button className="button button--quiet" onClick={()=>setChatOpen(true)}><MessageCircle size={17}/> Ask Mentics</button><a className="button button--dark" href={builder}>Edit goals <ArrowRight size={16}/></a></div></div>
    <div className="path-progress"><span style={{width:`${tasks.length ? completed/tasks.length*100 : 0}%`}}/><p><b>{completed} of {tasks.length || 5}</b> steps complete</p></div>
    {error && <div className="error-banner">{error}<button onClick={()=>loadTasks()}>Try again</button></div>}
    {loading ? <PathSkeleton/> : <section className="roadmap" aria-label={`${category} roadmap`}>
      <div className="road-line" />
      {tasks.map((task,index)=><button key={task.id || index} className={`road-step ${task.is_completed ? 'done' : index === activeIndex ? 'current' : 'upcoming'} ${index % 2 ? 'road-step--right' : ''}`} onClick={()=>setSelected(task)}>
        <span className="road-node">{task.is_completed ? <Check/> : index > activeIndex && activeIndex !== -1 ? <LockKeyhole/> : String(index+1).padStart(2,'0')}</span>
        <span className="road-card"><span className="road-card-top"><small>{task.is_completed ? 'COMPLETE' : index === activeIndex ? 'UP NEXT' : `STEP ${index+1}`}</small>{task.due_date && <i><CalendarDays/> {task.due_date}</i>}</span><b><PlainText value={task.description}/></b><small>{task.reason || 'A focused step toward your goal.'}</small><span className="road-meta">{task.task_format === 'practice_sprint' ? 'Focused practice' : task.task_format === 'quiz' ? 'Knowledge check' : task.type === 'milestone' ? 'Milestone' : 'Action step'} <ChevronRight/></span></span>
      </button>)}
    </section>}
    <div className="path-footer-actions"><button className="button button--quiet" onClick={()=>setAdding(true)}><Plus/> Add your own step</button><button className="text-button" onClick={()=>loadTasks(true)}><RotateCcw/> Regenerate five steps</button></div>
    {selected && <TaskModal task={selected} category={category} onClose={()=>setSelected(null)} onUpdate={(next)=>{setTasks(items=>items.map(t=>t.id===next.id?next:t));setSelected(next)}}/>}
    {adding && <AddTask category={category} onClose={()=>setAdding(false)} onAdded={t=>{setTasks(items=>[...items,normalizeTask(t)]);setAdding(false)}}/>}
    <ChatPanel open={chatOpen} onClose={()=>setChatOpen(false)} category={category} onNewPath={items=>setTasks(items.map(normalizeTask))}/>
    <button className="floating-chat" onClick={()=>setChatOpen(true)}><MessageCircle/><span>Ask Mentics</span></button>
  </main></AppShell>
}

function PlainText({value}) { return <>{String(value || '').replace(/\[([^\]]+)\]\([^)]+\)/g,'$1').replace(/[*_#`]/g,'')}</> }
function normalizeTask(t){return {...t,is_completed:Boolean(t.is_completed),subtasks:Array.isArray(t.subtasks)?t.subtasks:[],task_format:t.task_format||'link'}}

function PathSkeleton(){return <section className="roadmap roadmap--loading"><div className="road-line"/>{[0,1,2,3,4].map(i=><div className={`road-step ${i%2?'road-step--right':''}`} key={i}><span className="road-node skeleton"/><span className="road-card skeleton"/></div>)}</section>}

function Modal({children,onClose,wide=false}) { useEffect(()=>{const fn=e=>e.key==='Escape'&&onClose();document.addEventListener('keydown',fn);return()=>document.removeEventListener('keydown',fn)},[onClose]); return <div className="modal-wrap" role="dialog" aria-modal="true" onMouseDown={e=>e.target===e.currentTarget&&onClose()}><div className={`modal ${wide?'modal--wide':''}`}><button className="modal-close" onClick={onClose} aria-label="Close"><X/></button>{children}</div></div> }

function TaskModal({task,category,onClose,onUpdate}) {
  const [note,setNote]=useState(''); const [busy,setBusy]=useState(false); const [assessment,setAssessment]=useState(null)
  const complete=async()=>{setBusy(true);try{await api('/api/update_task_status',{method:'POST',body:JSON.stringify({taskId:task.id,status:'complete'})});onUpdate({...task,is_completed:true});onClose()}finally{setBusy(false)}}
  const addNote=async()=>{if(!note.trim())return;const r=await api('/api/add_subtask',{method:'POST',body:JSON.stringify({parent_task_id:task.id,description:note})});onUpdate({...task,subtasks:[...task.subtasks,r.subtask]});setNote('')}
  const toggleNote=async(s)=>{await api('/api/update_subtask',{method:'POST',body:JSON.stringify({subtaskId:s.id,is_completed:!s.is_completed})});onUpdate({...task,subtasks:task.subtasks.map(x=>x.id===s.id?{...x,is_completed:!x.is_completed}:x)})}
  const launch=async()=>{setBusy(true);try{const path=task.task_format==='quiz'?`/api/quiz/${task.id}`:`/api/practice_sprint/${task.id}`;setAssessment({...(await api(path)),kind:task.task_format})}catch(e){window.alert(e.message)}finally{setBusy(false)}}
  if(assessment) return <Assessment data={assessment} onClose={()=>setAssessment(null)}/>
  return <Modal onClose={onClose}><div className="modal-kicker">{category} · {task.type === 'milestone' ? 'Milestone' : 'Action step'}</div><h2><PlainText value={task.description}/></h2><Markdown>{task.reason || ''}</Markdown>
    <div className="task-notes"><label>Notes and sub-steps</label>{task.subtasks.map(s=><button key={s.id} className={s.is_completed?'checked':''} onClick={()=>toggleNote(s)}><span>{s.is_completed&&<Check/>}</span>{s.description}</button>)}<div><input value={note} onChange={e=>setNote(e.target.value)} onKeyDown={e=>e.key==='Enter'&&addNote()} placeholder="Add a note or smaller step"/><button onClick={addNote} disabled={!note.trim()}><Plus/></button></div></div>
    <div className="modal-actions">{task.task_format==='practice_sprint'&&<a className="button button--quiet" href={`/strategy_article/${task.id}`} target="_blank" rel="noreferrer"><BookOpen/> Strategy guide</a>}{['quiz','practice_sprint'].includes(task.task_format)&&<button className="button button--quiet" onClick={launch} disabled={busy}>Start {task.task_format==='quiz'?'quiz':'sprint'}</button>}<button className="button button--primary" onClick={complete} disabled={busy||task.is_completed}>{task.is_completed?'Completed':'Mark complete'} <Check/></button></div>
  </Modal>
}

function AddTask({category,onClose,onAdded}) { const [description,setDescription]=useState('');const [date,setDate]=useState('');const [error,setError]=useState('');const submit=async e=>{e.preventDefault();setError('');try{const r=await api('/api/add_task',{method:'POST',body:JSON.stringify({description,category,due_date:date||null})});onAdded(r.task)}catch(x){setError(x.message)}};return <Modal onClose={onClose}><div className="modal-kicker">ADD A PERSONAL STEP</div><h2>Make the path yours.</h2><form className="modal-form" onSubmit={submit}><label>What do you want to do?<textarea autoFocus value={description} onChange={e=>setDescription(e.target.value)} placeholder="Write a clear, finishable action" maxLength={500}/></label><label>Due date <span>optional</span><input type="date" value={date} onChange={e=>setDate(e.target.value)}/></label>{error&&<p className="form-error">{error}</p>}<button className="button button--primary" disabled={!description.trim()}>Add to path <ArrowRight/></button></form></Modal> }

function Assessment({data,onClose}) { const [answers,setAnswers]=useState({});const [result,setResult]=useState(null);const questions=data.questions||[];const submit=async()=>{const rows=questions.map(q=>({question_id:q.id,is_correct:Number(answers[q.id])===q.correct_option}));await api(data.kind==='quiz'?'/api/submit_quiz_results':'/api/submit_sprint_results',{method:'POST',body:JSON.stringify({results:rows})});setResult(rows.filter(x=>x.is_correct).length)};return <Modal onClose={onClose} wide><div className="modal-kicker">FOCUSED CHECK</div><h2>{data.title}</h2>{result==null?<><div className="questions">{questions.map((q,i)=><fieldset key={q.id}><legend>{i+1}. {q.question_text}</legend>{q.options.map((o,oi)=><label key={oi}><input type="radio" name={`q-${q.id}`} checked={Number(answers[q.id])===oi} onChange={()=>setAnswers({...answers,[q.id]:oi})}/><span>{o}</span></label>)}</fieldset>)}</div><button className="button button--primary" disabled={Object.keys(answers).length!==questions.length} onClick={submit}>Check answers</button></>:<div className="assessment-result"><Trophy/><h3>{result} of {questions.length} correct</h3><p>Review the explanations, then mark this path step complete when you are ready.</p>{questions.map((q,i)=><details key={q.id}><summary>Question {i+1}</summary><p>{q.explanation}</p></details>)}<button className="button button--dark" onClick={onClose}>Back to task</button></div>}</Modal> }

function ChatPanel({open,onClose,category,onNewPath}) {
  const [messages,setMessages]=useState([]);const [input,setInput]=useState('');const [busy,setBusy]=useState(false);const end=useRef(null)
  useEffect(()=>{if(open&&messages.length===0)api(`/api/chat_history?category=${encodeURIComponent(category)}`).then(h=>setMessages(Array.isArray(h)&&h.length?h:[{role:'assistant',content:`I know this ${category.toLowerCase()} path. Ask me about a step, a concept, or what to do when you are stuck.`}])).catch(()=>{})},[open,category,messages.length])
  useEffect(()=>end.current?.scrollIntoView({behavior:'smooth'}),[messages,busy])
  const send=async e=>{e.preventDefault();if(!input.trim()||busy)return;const next=[...messages,{role:'user',content:input.trim()}];setMessages(next);setInput('');setBusy(true);try{const r=await api(`/api/chat?category=${encodeURIComponent(category)}`,{method:'POST',body:JSON.stringify({history:next})});if(r.new_path){onNewPath(r.new_path);setMessages([...next,{role:'assistant',content:'Your new five-step path is ready. I used our conversation to shape it.'}])}else setMessages([...next,{role:'assistant',content:r.reply}])}catch(x){setMessages([...next,{role:'assistant',content:x.message}])}finally{setBusy(false)}}
  const reset=async()=>{await api('/api/reset_chat',{method:'POST',body:JSON.stringify({category})});setMessages([{role:'assistant',content:`Fresh start. What would you like help with on your ${category.toLowerCase()} path?`}])}
  return <aside className={`chat-panel ${open?'chat-panel--open':''}`} aria-hidden={!open}><header><span><i><Sparkles/></i><b>Mentics guide</b><small>Knows your current path</small></span><div><button onClick={reset} aria-label="Reset chat"><RotateCcw/></button><button onClick={onClose} aria-label="Close chat"><X/></button></div></header><div className="chat-messages">{messages.map((m,i)=><div className={`chat-message chat-message--${m.role}`} key={i}>{m.role==='assistant'?<Markdown>{m.content}</Markdown>:m.content}</div>)}{busy&&<div className="chat-thinking"><i/><i/><i/></div>}<div ref={end}/></div><form onSubmit={send}><textarea value={input} onChange={e=>setInput(e.target.value)} onKeyDown={e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();send(e)}}} placeholder="Ask about your path…" rows={1}/><button disabled={!input.trim()||busy} aria-label="Send"><Send/></button></form><p>Mentics can make mistakes. Check important information.</p></aside>
}

function App(){if(boot.page==='dashboard')return <Dashboard/>;if(boot.page==='path')return <PathPage/>;return <Landing/>}

createRoot(document.getElementById('root')).render(<React.StrictMode><App/></React.StrictMode>)
