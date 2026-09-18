"""Durable diagnostics, adaptive selection, and one shared evidence ledger.

No model call holds a database transaction. Generation leases recover after a
worker timeout; answers and benchmark completion commit before path generation.
"""
import json
import re
import time
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from difflib import SequenceMatcher

import adaptive_bank as content
import learning

TRACKS = ('sat_math', 'sat_ela', 'act_math', 'act_ela')
VERSION = 2
LEASE_SECONDS = 90


def unpack(value, default=None):
    if value is None:
        return default
    try:
        return json.loads(value) if isinstance(value, str) else value
    except (TypeError, ValueError):
        return default


def rows(tx, sql, params=()):
    cursor = tx.connection.cursor()
    cursor.execute(tx.database._query(sql), params)
    return [dict(row) for row in cursor.fetchall()]


def lock(tx, user_id):
    tx.execute_write('UPDATE users SET stats=stats WHERE id=?', (user_id,))


def ensure_track(db, user_id, track):
    if track not in TRACKS:
        raise ValueError('Choose SAT or ACT and Math or ELA.')
    with db.transaction() as tx:
        lock(tx, user_id)
        tx.execute_write("UPDATE paths SET is_active=False WHERE user_id=? AND category='Test Prep' AND is_user_added=False AND learning_version<2", (user_id,))
        saved = rows(tx, 'SELECT * FROM adaptive_tracks WHERE user_id=? AND track_key=?', (user_id, track))
        if saved:
            return saved[0]
        now = time.time()
        session_id = tx.insert('adaptive_sessions', {
            'user_id': user_id, 'track_key': track, 'kind': 'benchmark', 'status': 'active',
            'request_key': f'benchmark:{track}:v{VERSION}', 'questions': json.dumps(content.bank(track)),
            'created_at': now, 'updated_at': now,
        })
        row_id = tx.insert('adaptive_tracks', {'user_id': user_id, 'track_key': track, 'benchmark_session_id': session_id})
        tx.insert('paths', {'user_id': user_id, 'track_key': track, 'task_order': 1,
            'description': f"{track.replace('_', ' ').upper()} Benchmark Assessment",
            'reason': 'One diagnostic across the section. Your answers—not a guessed starting level—shape your first path.',
            'category': 'Test Prep', 'is_active': True, 'is_completed': False, 'is_user_added': False,
            'type': 'standard', 'task_format': 'benchmark', 'node_type': 'benchmark',
            'task_content_id': session_id, 'xp_reward': 0, 'learning_version': VERSION,
            'unit_title': 'Find your starting point'})
        return rows(tx, 'SELECT * FROM adaptive_tracks WHERE id=?', (row_id,))[0]


def record_event_tx(tx, user_id, track, source, source_id, question, correct, response_ms=None, hints=0, confidence=None, chosen=None):
    if track not in TRACKS or question.get('skill_key') not in learning.skill_catalog(*track.split('_')):
        return False
    if rows(tx, 'SELECT id FROM learning_events WHERE user_id=? AND source=? AND source_id=?', (user_id, source, str(source_id))):
        return False
    skill = question['skill_key']
    misconceptions = question.get('misconceptions') or []
    misconception = misconceptions[chosen] if not correct and isinstance(chosen, int) and chosen < len(misconceptions) else ''
    tx.insert('learning_events', {'user_id': user_id, 'track_key': track, 'source': source, 'source_id': str(source_id),
        'skill_key': skill, 'subskill': question.get('subskill') or skill, 'domain': question.get('domain') or content.domain(skill),
        'difficulty': question.get('difficulty') if question.get('difficulty') in {'easy','medium','hard'} else 'unknown',
        'is_correct': bool(correct), 'response_ms': response_ms, 'hint_count': hints,
        'confidence': confidence, 'misconception': misconception,
        'evidence': json.dumps({'question': question.get('question_text',''), 'source_or_prompt':question.get('source_or_prompt',''), 'chosen': chosen,
            'rapid_response': response_ms is not None and response_ms < 1500,
            'error_type': 'possible rushed response' if not correct and response_ms is not None and response_ms < 3000 else 'undetermined',
            'strategy': question.get('strategy', '') if hints else '', 'attribution': question.get('attribution')}),
        'created_at': time.time()})
    # Compatibility projection for the existing stats, achievements and coach.
    # The immutable ledger remains the source for the adaptive model.
    existing = rows(tx,'SELECT * FROM skill_mastery WHERE user_id=? AND skill_key=?',(user_id,skill))
    old=existing[0] if existing else {}
    attempts=(old.get('attempts') or 0)+1;correct_count=(old.get('correct') or 0)+int(correct)
    resolved=learning.resolve_skill(skill)
    payload={'user_id':user_id,'skill_key':skill,'skill_label':resolved['skill_label'],'subject':resolved['subject'],
             'attempts':attempts,'correct':correct_count,'level':learning.mastery_level(correct_count/attempts,attempts)}
    if old:
        tx.update('skill_mastery',payload,where={'id':old['id']})
    else:
        tx.insert('skill_mastery',payload)
    options=question.get('options')
    if not correct and source in {'quick','benchmark','battle'} and isinstance(options,list) and type(chosen) is int and 0<=chosen<len(options):
        tx.insert('mistake_bank',{'user_id':user_id,'skill_key':skill,'skill_label':resolved['skill_label'],
            'question_text':question.get('question_text','')[:900],'chosen_text':str(options[chosen])[:400],
            'correct_text':str(options[question['correct_option']])[:400],'explanation':question.get('explanation','')[:900]})
    return True


def record_event(db, *args, **kwargs):
    with db.transaction() as tx:
        lock(tx, args[0])
        return record_event_tx(tx, *args, **kwargs)


def arena_question(question, exam):
    """Translate existing Arena labels without changing battle scoring."""
    skill = learning.resolve_skill(question.get('skill_key') or question.get('skill'))
    section = str(question.get('section') or question.get('domain') or '').lower()
    subject = 'math' if section == 'math' or skill['subject'] == 'Math' else 'ela'
    key = skill['skill_key']
    if exam == 'act' and not key.startswith('act_'):
        if subject == 'math':
            key = {'geometry':'act_math_plane_geometry','advanced_math':'act_math_coordinate'}.get(skill['domain'],'act_math_prealgebra')
            if 'trig' in skill['skill_key']:
                key = 'act_math_trig'
        else:
            key = 'act_english_usage' if skill['domain']=='grammar' else 'act_english_rhetoric' if section=='english' else 'act_reading_detail'
    return f'{exam}_{subject}', {**question,'skill_key':key,'subskill':skill['skill_key'],'domain':content.domain(key)}


def profile(db, user, track):
    user_id = user.data['id']
    prep = user.get_stats().get('test_path') or {}
    prep = prep if isinstance(prep,dict) else {}
    sections = prep.get('tracks') or {}
    sections = sections if isinstance(sections,dict) else {}
    section = sections.get(track) or {}
    questionnaire = {**{k: v for k, v in prep.items() if k != 'tracks'}, **(section if isinstance(section,dict) else {})}
    events = db.execute('SELECT * FROM learning_events WHERE user_id=? AND track_key=? ORDER BY id', (user_id, track))
    grouped = defaultdict(list)
    for event in events:
        grouped[event['skill_key']].append(event)
    legacy = {r['skill_key']: r for r in db.select('skill_mastery', where={'user_id': user_id})}
    skills = {}
    for key in learning.skill_catalog(*track.split('_')):
        samples = grouped[key]
        weights, score = [], 0
        for i, event in enumerate(samples):
            weight = (1.6 if event['source'] == 'benchmark' else 1.0) * (0.97 ** (len(samples)-i-1))
            if event['hint_count']:
                weight *= .6
            if event['response_ms'] is not None and event['response_ms'] < 1500:
                weight *= .2
            weights.append(weight)
            score += weight * int(event['is_correct'])
        prior = legacy.get(key, {})
        # Preserve historical counts as context, but do not double count the
        # current ledger's answers also reflected in the legacy stats view.
        historical_attempts = max(0, (prior.get('attempts') or 0) - len(samples))
        historical_correct = max(0, (prior.get('correct') or 0) - sum(int(s['is_correct']) for s in samples))
        prior_accuracy = historical_correct / max(historical_attempts, 1)
        prior_weight = min(0.5, historical_attempts * .05)
        estimate = (score + prior_accuracy * prior_weight) / (sum(weights) + prior_weight) if weights or prior_weight else None
        recent = samples[-8:]
        difficulty = {}
        for level in ('easy','medium','hard'):
            subset = [s for s in samples if s['difficulty'] == level]
            difficulty[level] = {'attempts': len(subset), 'correct': sum(int(s['is_correct']) for s in subset)}
        times = [s['response_ms'] for s in samples if s['response_ms'] is not None and 1500 <= s['response_ms'] <= 900000]
        subskills = {}
        for sub in {s['subskill'] for s in samples}:
            subevents = [s for s in samples if s['subskill'] == sub]
            subskills[sub] = {'attempts': len(subevents), 'accuracy': round(sum(int(s['is_correct']) for s in subevents)/len(subevents), 3)}
        recent_accuracy = sum(int(s['is_correct']) for s in recent)/len(recent) if recent else None
        early = samples[-16:-8]
        trend = round(recent_accuracy - sum(int(s['is_correct']) for s in early)/len(early), 3) if early else None
        enough = sum(weights) >= 3
        hard_success = any(s['difficulty']=='hard' and s['is_correct'] and not s['hint_count'] and (s['response_ms'] is None or s['response_ms']>=1500) for s in samples)
        readiness = 'hard' if estimate is not None and estimate >= .8 and (enough or hard_success) else 'medium' if estimate is None or estimate >= .55 else 'easy'
        skills[key] = {'label': learning.resolve_skill(key)['skill_label'], 'domain': content.domain(key),
            'attempts': len(samples), 'historical_attempts': prior.get('attempts',0),
            'accuracy': round(sum(int(s['is_correct']) for s in samples)/len(samples),3) if samples else None,
            'mastery_estimate': round(estimate,3) if estimate is not None else None,
            'evidence_confidence': 'developing' if enough else 'limited', 'recent_accuracy': recent_accuracy,
            'trend': trend, 'difficulty': difficulty, 'readiness': readiness,
            'average_response_ms': round(sum(times)/len(times)) if times else None,
            'last_practiced': samples[-1]['created_at'] if samples else None,
            'sources': dict(Counter(s['source'] for s in samples)), 'subskills': subskills,
            'misconceptions': dict(Counter(s['misconception'] for s in recent if s['misconception'] and not s['is_correct'])),
            'hints_used': sum(s['hint_count'] for s in samples),
            'confident_errors': sum(s['confidence']==3 and not s['is_correct'] for s in samples),
            'weekly_attempts': sum(s['created_at'] >= time.time()-604800 for s in samples),
            'rapid_responses': sum(s['response_ms'] is not None and s['response_ms']<1500 for s in samples)}
    track_state = db.select_one('adaptive_tracks', where={'user_id': user_id, 'track_key': track}) or {}
    progress = db.execute("SELECT description, skill_key, is_completed FROM paths WHERE user_id=? AND track_key=? AND is_active=True", (user_id, track))
    recent_questions = []
    for event in events[-40:]:
        evidence = unpack(event['evidence'],{})
        recent_questions.append(re.sub(r'\W+',' ',(evidence.get('source_or_prompt','')+' '+evidence.get('question','')).lower()).strip())
    other_sections = db.execute('''SELECT track_key,skill_key,COUNT(*) AS attempts,
        SUM(CASE WHEN is_correct THEN 1 ELSE 0 END) AS correct
        FROM learning_events WHERE user_id=? AND track_key!=? GROUP BY track_key,skill_key''',(user_id,track))
    old_practice = [unpack(row['details'],{}) for row in db.execute("SELECT details FROM activity_log WHERE user_id=? AND activity_type='quick_practice' ORDER BY id DESC LIMIT 24",(user_id,))]
    return {'track': track, 'questionnaire': questionnaire, 'onboarding': unpack(user.data.get('onboarding_data'), {}),
        'other_sections_background':other_sections,'other_section_goals':prep.get('tracks') or {},
        'legacy_practice_history':[row for row in old_practice if row.get('track')==track][:8],
        'skills': skills, 'benchmark_completed': bool(track_state.get('benchmark_completed_at')),
        'benchmark': unpack(track_state.get('diagnostic'), {}), 'path_progress': progress,
        'recent_questions': recent_questions, 'recent_mistakes': [unpack(e['evidence'], {}) for e in events[-30:] if not e['is_correct']],
        'evidence_policy': 'Demonstrated performance outweighs self-report. A short diagnostic is provisional; do not infer an official SAT score or diagnose carelessness from one miss.'}


def targets(state, count=5):
    skills = state['skills']
    def priority(key):
        s = skills[key]
        estimate = s['mastery_estimate']
        recent = s['recent_accuracy']
        # Measured weakness precedes self-report and unmeasured topics.
        weakness = 3*(1-estimate) if estimate is not None else 1.2
        if recent is not None:
            weakness += 1-recent
        if s['misconceptions']:
            weakness += .35
        if estimate is None:
            weak_text = str(state['questionnaire'].get('weaknesses','')).lower()
            terms = (key+' '+s['label']+' '+learning.resolve_skill(key).get('domain','')).replace('_',' ').lower().split()
            if any(word in weak_text for word in terms if len(word)>3):
                weakness += .35
        if s.get('average_response_ms') and s['average_response_ms'] > (100000 if state['track'].endswith('math') else 80000):
            weakness += .15
        return weakness
    ordered = sorted(skills, key=lambda k: (-priority(k), skills[k]['last_practiced'] or 0, k))
    weak = [k for k in ordered if skills[k]['mastery_estimate'] is not None and skills[k]['mastery_estimate'] < .7]
    pool = weak or ordered
    selected = [pool[i % min(len(pool), 4)] for i in range(max(1,count-1))]
    # One slot for spaced reinforcement or exploring an unmeasured domain.
    other = sorted(ordered, key=lambda k: (k in selected, skills[k]['last_practiced'] or 0))
    selected.append(other[0])
    return selected[:count]


def signature(q):
    return re.sub(r'\W+', ' ', (q.get('source_or_prompt','')+' '+q['question_text']).lower()).strip()


def question_schema(requested):
    properties = {key:{'type':'string'} for key in ('subskill','source_or_prompt','question_text','explanation','strategy','fastest_method')}
    properties.update({
        'skill_key':{'type':'string','enum':list(dict.fromkeys(requested))},
        'difficulty':{'type':'string','enum':['easy','medium','hard']},
        'correct_option':{'type':'integer','minimum':0,'maximum':3},
        'options':{'type':'array','minItems':4,'maxItems':4,'items':{'type':'string'}},
        'hints':{'type':'array','minItems':3,'maxItems':3,'items':{'type':'string'}},
        'misconceptions':{'type':'array','minItems':4,'maxItems':4,'items':{'type':'string'}},
    })
    return {'type':'object','properties':{'questions':{'type':'array','minItems':len(requested),'maxItems':len(requested),
        'items':{'type':'object','properties':properties,'required':list(properties)}}},'required':['questions']}


REVIEW_SCHEMA = {'type':'object','properties':{'reviews':{'type':'array','items':{
    'type':'object','properties':{'index':{'type':'integer'},'answer':{'type':'integer','minimum':0,'maximum':3},
        'valid':{'type':'boolean'},'hints_safe':{'type':'boolean'},'reason':{'type':'string'}},
    'required':['index','answer','valid','hints_safe','reason']}}},'required':['reviews']}


def valid_generated(raw, track):
    if not isinstance(raw, dict) or raw.get('skill_key') not in learning.skill_catalog(*track.split('_')):
        return None
    skill = raw['skill_key']
    q = learning._valid_question(raw, needs_prompt=track.endswith('ela'), requires_blank=learning._skill_requires_blank(skill))
    if q:
        # Choices belong to the separate options field. Embedded lettered
        # choices become contradictory after shuffling and clutter the player.
        for field in ('question_text','source_or_prompt'):
            value=q[field]
            if re.search(r'\n\s*\(?A[).]\s+',value) and re.search(r'\n\s*\(?B[).]\s+',value):
                q[field]=re.split(r'\n\s*\(?A[).]\s+',value,maxsplit=1)[0].strip()
        if track=='act_ela' and ('underlin' in q['question_text'].lower() or any(o.upper()=='NO CHANGE' for o in q['options'])):
            if not re.search(r'\[underlined:[^\]]+\]',q['source_or_prompt'],re.I):
                return None
    hints = raw.get('hints')
    if not q or q['difficulty'] not in {'easy','medium','hard'} or not isinstance(hints,list) or len(hints)!=3 or any(not isinstance(h,str) or len(h)<15 or len(h)>650 for h in hints):
        return None
    if type(raw.get('correct_option')) is not int:
        return None
    if any(re.search(r'(?:correct answer|answer is|choose (?:option )?[ABCD]\b)',h,re.I) for h in hints):
        return None
    misconceptions = raw.get('misconceptions')
    if not isinstance(misconceptions,list) or len(misconceptions)!=4 or any(not isinstance(m,str) or len(m)>500 for m in misconceptions):
        return None
    if not isinstance(raw.get('subskill'),str) or not raw['subskill'].strip():
        return None
    visible = json.dumps({k:raw.get(k) for k in ('question_text','source_or_prompt','options','hints','explanation','fastest_method')})
    if re.search(r'\\\\(?:frac|sqrt|begin|end|left|right|text|cdot|times|leq|geq)\b', visible):
        return None  # These players display plain math, not unevaluated TeX.
    q.update(skill_key=skill, subskill=raw['subskill'][:100], domain=content.domain(skill), hints=hints,
             strategy=str(raw.get('strategy',''))[:700], fastest_method=str(raw.get('fastest_method',''))[:1000],
             misconceptions=misconceptions, attribution=content.credit(track,skill), validation='ai_independent_review')
    return q


def generate_questions(state, requested, generate, *, seed=0):
    """Generate, structurally validate, and independently solve before serving."""
    track = state['track']
    assignments = [{'skill_key':key,'difficulty':state['skills'][key]['readiness']} for key in requested]
    prompt = f'''Create {len(requested)} original {track} practice questions, one per assignment in order.
ASSIGNMENTS: {json.dumps(assignments)}
STUDENT EVIDENCE: {json.dumps(state)}
Use demonstrated weaknesses, misconceptions and prior work; reinforce strong skills at a harder level.
Do not repeat recent questions or just substitute numbers into them. Vary contexts and reasoning.
{learning._format_facts(track.split('_')[0])}
All necessary passages, tables and information must be in source_or_prompt or question_text. No unseen figures.
Use plain text and readable Unicode math (x², ×, √, (a+b)/c). No LaTeX commands, dollar-delimited equations or Markdown tables.
Put answer choices ONLY in options, never repeat lettered choices in question_text or source_or_prompt.
All passages and examples must be original. Do not invent quotations from real authors, novels, studies, or historical documents. Use fictional examples or unattributed original expository text.
For ACT English revision questions, mark the exact replaceable span as [underlined: target words] or use a ____ blank with explicit replacement choices. NO CHANGE requires a marked original span.
Exactly four distinct plausible choices, exactly one correct. Solve each question fully before finalizing.
Write option explanations by their content, never by A/B/C/D or numbered position because choices will be shuffled.
misconceptions MUST have FOUR entries in option order, including an empty string at the correct option's index.
Give three increasingly specific hints: direction, strategy, then setup. NO final value, answer choice, or completed solution in hints.
Explain the correct answer and why each distractor is wrong. Provide the fastest reliable test-specific approach and its limitation.
Only reference James Lu for the supplied public Desmos/grammar emphasis; never invent quotations or claim access to his private course.
Return JSON {{"questions":[{{"skill_key":"...","subskill":"specific stable concept", "difficulty":"easy|medium|hard",
"source_or_prompt":"...", "question_text":"...", "options":["...","...","...","..."],"correct_option":0,
"explanation":"detailed solution and distractor reasoning", "hints":["direction","strategy","setup"],
"strategy":"actionable shortcut with when to use it", "fastest_method":"worked efficient solution",
"misconceptions":["possible misconception for this distractor or empty if correct","...","...","..."]}}]}}.'''
    accepted = []
    note = 'AI-personalized questions, independently checked before practice.'
    try:
        data = learning._parse_json(generate(prompt, max_output_tokens=min(14000, len(requested)*1050+500), json_output=True,json_schema=question_schema(requested),
            thinking_level='low', system_instruction=learning.SYSTEM_TUTOR, timeout_seconds=25), expect_key='questions')
        raw_items = data.get('questions', []) if isinstance(data,dict) else data if isinstance(data,list) else []
        candidates = [valid_generated(q,track) for q in raw_items[:len(requested)]]
        candidates = [q for q in candidates if q and q['skill_key'] in requested]
        candidates = learning._dedupe(candidates)
        if not candidates:
            raise ValueError('No structurally valid questions')
        blind = [{k:v for k,v in q.items() if k not in {'correct_option','explanation','fastest_method','misconceptions'}} for q in candidates]
        audit = learning._parse_json(generate(
            'Independently solve these questions without an answer key. Check ambiguity, missing information, SAT/ACT scope, grammar, difficulty label, and whether any hint reveals the answer. Return JSON {"reviews":[{"index":0,"answer":0,"valid":true,"hints_safe":true,"reason":"your solution and checks"}]}. Reject any doubtful item. Questions: '+json.dumps(blind),
            max_output_tokens=5000, json_output=True,json_schema=REVIEW_SCHEMA, thinking_level='low', system_instruction=learning.SYSTEM_TUTOR, timeout_seconds=18), expect_key='reviews')
        reviews = audit.get('reviews',[]) if isinstance(audit,dict) else audit if isinstance(audit,list) else []
        for review in reviews:
            idx = review.get('index')
            if type(idx) is not int or not 0<=idx<len(candidates):
                continue
            q = candidates[idx]
            if review.get('valid') is True and review.get('hints_safe') is True and type(review.get('answer')) is int and review['answer']==q['correct_option'] and len(str(review.get('reason','')))>30:
                if not any(SequenceMatcher(None,signature(q),str(previous).lower()).ratio()>.88 for previous in state['recent_questions']):
                    accepted.append(q)
    except Exception as error:
        learning._log('Adaptive question generation recovered: %s', type(error).__name__)
    # Fill missing/rejected items with tested content. The fallback is selected
    # from evidence, never silently presented as new AI-generated material.
    result = []
    bank = content.bank(track, seed)
    for key in requested:
        used_signatures = {signature(q) for q in result}
        q = next((q for q in accepted if q['skill_key']==key and signature(q) not in used_signatures),None)
        if q is None:
            options = [q for q in bank if q['skill_key']==key]
            if not options:
                # If there is no reviewed question on this exact skill, never
                # relabel another skill to fake personalization.
                options = sorted(bank, key=lambda q: (q['skill_key'] not in requested, q['question_text'] in state['recent_questions']))
            q = next((q for q in options if signature(q) not in used_signatures), options[0])
            q = dict(q)
            note = 'Some questions use the reviewed recovery bank because AI checks did not pass. Your skill targeting and results are still saved.'
        if signature(q) in {signature(existing) for existing in result}:
            # Math variants are independently computed; ELA can use another
            # reviewed item with its true skill label when the pool is exhausted.
            alternatives = content.bank(track, seed+len(result)+1)
            q = next((a for a in alternatives if a['skill_key']==key and signature(a) not in {signature(e) for e in result}), None) or next((a for a in alternatives if signature(a) not in {signature(e) for e in result}),None)
            if q is None:
                raise ValueError('No distinct reviewed questions available. Try a mixed session.')
        result.append(content.shuffle_options(q,seed*101+len(result)*17))
    return result, note


def start_practice(db, user, track, request_key, generate):
    ensure_track(db,user.data['id'],track)
    if not isinstance(request_key,str) or not re.fullmatch(r'[a-zA-Z0-9_-]{8,80}',request_key):
        raise ValueError('A valid session request ID is required.')
    user_id = user.data['id']
    with db.transaction() as tx:
        lock(tx,user_id)
        saved = rows(tx,"SELECT * FROM adaptive_sessions WHERE user_id=? AND track_key=? AND kind='quick' AND status IN ('active','generating') ORDER BY id DESC",(user_id,track))
        exact = rows(tx,'SELECT * FROM adaptive_sessions WHERE user_id=? AND request_key=?',(user_id,request_key))
        record = exact[0] if exact else saved[0] if saved else None
        if record and record['track_key'] != track:
            raise ValueError('This request ID belongs to another section.')
        if record and (record['status'] in {'active','completed'} or record['status']=='generating' and time.time()-record['updated_at']<LEASE_SECONDS):
            return record['id']
        now=time.time()
        if record:
            session_id=record['id']
            tx.update('adaptive_sessions',{'updated_at':now,'status':'generating'},where={'id':session_id})
        else:
            session_id=tx.insert('adaptive_sessions',{'user_id':user_id,'track_key':track,'kind':'quick',
                'request_key':request_key,'created_at':now,'updated_at':now})
    try:
        state=profile(db,user,track)
        questions,note=generate_questions(state,targets(state),generate,seed=session_id)
        db.update('adaptive_sessions',{'questions':json.dumps(questions),'profile_snapshot':json.dumps(state),
            'status':'active','generation_note':note,'updated_at':time.time()},where={'id':session_id,'user_id':user_id,'updated_at':now,'status':'generating'})
    except Exception:
        db.update('adaptive_sessions',{'status':'failed','generation_note':'Could not prepare a valid session. Start again to retry.','updated_at':time.time()},where={'id':session_id,'user_id':user_id,'updated_at':now,'status':'generating'})
        raise
    return session_id


def session_view(db,user_id,session_id):
    saved=db.select_one('adaptive_sessions',where={'id':session_id,'user_id':user_id})
    if not saved:
        raise ValueError('Session not found.')
    questions=unpack(saved['questions'],[])
    answers=unpack(saved['answers'],{})
    hints=unpack(saved['hint_usage'],{})
    public=[]
    points=streak=best_streak=0
    for i,q in enumerate(questions):
        p={k:q[k] for k in ('question_text','source_or_prompt','options','skill_key','subskill','difficulty','domain','attribution') if k in q}
        p['index']=i
        p['hints']=q['hints'][:hints.get(str(i),0)]
        if str(i) in answers:
            p['answer']=answers[str(i)]
            if saved['kind']=='quick' or saved['status']=='completed':
                p.update({k:q.get(k) for k in ('correct_option','explanation','strategy','fastest_method')})
            right=answers[str(i)]['selected_option']==q['correct_option']
            streak=streak+1 if right else 0
            best_streak=max(best_streak,streak)
            points+=(50 if hints.get(str(i),0) else 100) if right else 0
        public.append(p)
    return {'id':saved['id'],'track':saved['track_key'],'kind':saved['kind'],'status':saved['status'],
        'points':points if saved['kind']=='quick' else None,'streak':streak if saved['kind']=='quick' else None,'best_streak':best_streak if saved['kind']=='quick' else None,
        'questions':public,'answered':len(answers),'total':len(questions),'summary':unpack(saved['summary'],{}),
        'note':saved['generation_note'],'can_retry':saved['status']=='failed' or saved['status']=='generating' and time.time()-saved['updated_at']>=LEASE_SECONDS}


def hint(db,user_id,session_id,index):
    with db.transaction() as tx:
        lock(tx,user_id)
        saved=rows(tx,'SELECT * FROM adaptive_sessions WHERE id=? AND user_id=?',(session_id,user_id))
        if not saved or saved[0]['status']!='active':
            raise ValueError('This session is not active.')
        saved=saved[0];qs=unpack(saved['questions'],[]);answers=unpack(saved['answers'],{})
        if saved['kind']=='benchmark':
            raise ValueError('The benchmark measures unaided work. Hints become available in practice afterward.')
        if type(index) is not int or not 0<=index<len(qs) or str(index) in answers:
            raise ValueError('Choose an unanswered question.')
        usage=unpack(saved['hint_usage'],{}); usage[str(index)]=min(3,usage.get(str(index),0)+1)
        tx.update('adaptive_sessions',{'hint_usage':json.dumps(usage),'updated_at':time.time()},where={'id':session_id})
    return session_view(db,user_id,session_id)


def answer(db,user_id,session_id,data):
    index=data.get('index');selected=data.get('selected_option');elapsed=data.get('response_ms');confidence=data.get('confidence')
    if type(index) is not int or type(selected) is not int or not 0<=selected<4:
        raise ValueError('Choose one answer.')
    if elapsed is not None and (type(elapsed) is not int or not 0<=elapsed<=3600000):
        raise ValueError('Response time is invalid.')
    if confidence is not None and (type(confidence) is not int or not 1<=confidence<=3):
        raise ValueError('Confidence must be between 1 and 3.')
    with db.transaction() as tx:
        lock(tx,user_id)
        saved=rows(tx,'SELECT * FROM adaptive_sessions WHERE id=? AND user_id=?',(session_id,user_id))
        if not saved:
            raise ValueError('Session not found.')
        saved=saved[0];questions=unpack(saved['questions'],[]);answers=unpack(saved['answers'],{})
        if str(index) in answers:
            return session_id
        if saved['status']!='active' or not 0<=index<len(questions):
            raise ValueError('This question is not available.')
        q=questions[index];hint_count=unpack(saved['hint_usage'],{}).get(str(index),0)
        answers[str(index)]={'selected_option':selected,'response_ms':elapsed,'confidence':confidence,'hint_count':hint_count}
        tx.update('adaptive_sessions',{'answers':json.dumps(answers),'updated_at':time.time()},where={'id':session_id})
        record_event_tx(tx,user_id,saved['track_key'],saved['kind'],f'{session_id}:{index}',q,selected==q['correct_option'],elapsed,hint_count,confidence,selected)
    return session_id


def finish(db,user_id,session_id):
    with db.transaction() as tx:
        lock(tx,user_id)
        saved=rows(tx,'SELECT * FROM adaptive_sessions WHERE id=? AND user_id=?',(session_id,user_id))
        if not saved:
            raise ValueError('Session not found.')
        saved=saved[0];questions=unpack(saved['questions'],[]);answers=unpack(saved['answers'],{})
        if saved['status']=='completed':
            return saved['track_key']
        if saved['status']!='active' or not questions or len(answers)!=len(questions):
            raise ValueError('Answer every question before submitting.')
        groups=defaultdict(lambda:{'correct':0,'total':0})
        correct=0;rapid=0
        for i,q in enumerate(questions):
            a=answers[str(i)];right=a['selected_option']==q['correct_option'];correct+=right
            groups[q['domain']]['correct']+=right;groups[q['domain']]['total']+=1
            rapid+=a.get('response_ms') is not None and a['response_ms']<1500
        summary={'correct':correct,'total':len(questions),'accuracy':round(correct/len(questions),3),'domains':dict(groups),
            'rapid_responses':rapid,'message':'This is a starting estimate, not an official score. Your next work will refine it.'}
        tx.update('adaptive_sessions',{'status':'completed','summary':json.dumps(summary),'updated_at':time.time()},where={'id':session_id})
        if saved['kind']=='benchmark':
            tx.update('adaptive_tracks',{'benchmark_completed_at':str(time.time()),'diagnostic':json.dumps(summary)},where={'user_id':user_id,'track_key':saved['track_key']})
            tx.execute_write("UPDATE paths SET is_completed=True WHERE user_id=? AND track_key=? AND task_format='benchmark' AND learning_version=?",(user_id,saved['track_key'],VERSION))
    return saved['track_key']


def build_unit(state, generate, seed=0):
    selected=targets(state,3)[:2]
    if selected[0]==selected[1]:
        selected[1]=targets(state,5)[-1]
    # Two bounded five-question jobs avoid one large, truncation-prone response.
    # They share an immutable profile and perform no database work in threads.
    with ThreadPoolExecutor(max_workers=2) as pool:
        jobs=[pool.submit(generate_questions,state,[key]*5,generate,seed=seed+i*7) for i,key in enumerate(selected)]
        generated=[job.result() for job in jobs]
    questions=[q for group,_ in generated for q in group]
    note=' '.join(dict.fromkeys(message for _,message in generated))
    nodes=[];review=[]
    for idx,key in enumerate(selected):
        group=questions[idx*5:idx*5+5]
        # Recovery content may use a different skill: use its honest taxonomy.
        key=group[0]['skill_key'];skill=learning.resolve_skill(key)
        sample=group[0];measurement=state['skills'][key]
        reason=(f"Your recorded accuracy on {skill['skill_label']} is {round(measurement['accuracy']*100)}%. " if measurement['accuracy'] is not None else 'This skill needs more measured evidence. ')
        reason+='The next focus comes from your recorded performance and goals.'
        if sample['validation']=='reviewed_bank':
            reason+=' This activity uses reviewed recovery content because AI validation was unavailable.'
        attribution = sample.get('attribution')
        credit_text = ('\n\n['+attribution['name']+']('+attribution['url']+'): '+attribution['note']) if attribution else ''
        teaching={'intro':reason,'cards':[{'title':skill['skill_label'],'body':sample['strategy']+credit_text,
            'worked_example':sample['source_or_prompt']+'\n\n'+sample['question_text']+'\n\n'+sample['explanation'],
            'takeaway':sample['hints'][1],'trap':'Verify the requested quantity and the conditions before choosing an answer.'}],
            'recap':sample['fastest_method']}
        taught={key}
        for practice in group[1:4]:
            if practice['skill_key'] in taught:
                continue
            # Recovery may draw an adjacent skill. Teach its rule before the
            # check instead of pretending it belongs to the headline skill.
            taught.add(practice['skill_key'])
            extra_credit=practice.get('attribution')
            attribution_note=('\n\n['+extra_credit['name']+']('+extra_credit['url']+'): '+extra_credit['note']) if extra_credit else ''
            teaching['cards'].append({'title':learning.resolve_skill(practice['skill_key'])['skill_label'],
                'body':practice['strategy']+attribution_note,'takeaway':practice['hints'][0],
                'trap':'Match the rule to the exact question; do not carry over the previous question’s setup.'})
        steps=learning._interleave_lesson({'cards':teaching['cards']},[])
        steps.extend(learning._interleave_lesson({'recap':teaching['recap']},[group[1]]))
        base={'skill':skill,'objective':f"Apply {skill['skill_label']} through worked examples and practice.",'reason':reason}
        nodes.append({**base,'node_type':'lesson','title':skill['skill_label'],'xp_reward':learning.XP_BY_NODE['lesson'],
            'teaching':teaching,'steps':steps})
        nodes.append({**base,'node_type':'practice_sprint','title':'Apply '+skill['skill_label'],'xp_reward':learning.XP_BY_NODE['practice_sprint'],'questions':group[2:4]})
        review.append(group[4])
    nodes.append({**base,'node_type':'quiz','title':'Check your progress','xp_reward':learning.XP_BY_NODE['quiz'],'questions':review})
    return {'unit_title':state['track'].replace('_',' ').upper()+': your next moves','nodes':nodes},note
