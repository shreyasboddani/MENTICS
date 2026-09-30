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
from functools import lru_cache

import adaptive_bank as content
import learning
from bench_common import words as word_count

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
            # An unfinished benchmark from before the full-length version is
            # swapped for the current one. Finished benchmarks are never touched.
            if not saved[0].get('benchmark_completed_at'):
                old = rows(tx, "SELECT * FROM adaptive_sessions WHERE id=? AND kind='benchmark' AND status='active'", (saved[0]['benchmark_session_id'],))
                fresh = content.benchmark(track, seed=user_id) if old else None
                if old and len(unpack(old[0]['questions'], [])) != len(fresh):
                    tx.update('adaptive_sessions', {'questions': json.dumps(fresh), 'answers': json.dumps({}), 'updated_at': time.time()}, where={'id': old[0]['id']})
            return saved[0]
        now = time.time()
        session_id = tx.insert('adaptive_sessions', {
            'user_id': user_id, 'track_key': track, 'kind': 'benchmark', 'status': 'active',
            'request_key': f'benchmark:{track}:v{VERSION}', 'questions': json.dumps(content.benchmark(track, seed=user_id)),
            'created_at': now, 'updated_at': now,
        })
        row_id = tx.insert('adaptive_tracks', {'user_id': user_id, 'track_key': track, 'benchmark_session_id': session_id})
        tx.insert('paths', {'user_id': user_id, 'track_key': track, 'task_order': 1,
            'description': f"{track.replace('_', ' ').upper()} Benchmark Assessment",
            'reason': 'A full-length diagnostic with real test structure. Your results, together with what you told us you need help with, shape your first path.',
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


CORRECT_WEIGHT = {'easy': .7, 'medium': 1.0, 'hard': 1.3}
WRONG_WEIGHT = {'easy': 1.3, 'medium': 1.0, 'hard': .7}

# Words students use for a whole area rather than one skill.
DOMAIN_WORDS = {
    'algebra': 'algebra', 'geometry': 'geometry', 'data': 'data_analysis', 'statistics': 'data_analysis',
    'word problems': 'data_analysis', 'advanced': 'advanced_math', 'functions': 'advanced_math',
    'grammar': 'grammar', 'conventions': 'grammar', 'usage': 'grammar', 'writing': 'writing',
    'reading': 'reading', 'comprehension': 'reading', 'passages': 'reading',
}
ACT_DOMAIN_SKILLS = {
    'algebra': ['act_math_prealgebra'], 'data_analysis': ['act_math_prealgebra'],
    'advanced_math': ['act_math_coordinate', 'act_math_prealgebra'],
    'geometry': ['act_math_plane_geometry', 'act_math_coordinate', 'act_math_trig'],
    'grammar': ['act_english_usage'], 'writing': ['act_english_rhetoric'], 'reading': ['act_reading_detail'],
}
ACT_SPECIFIC = {'right_triangles_trig': 'act_math_trig', 'lines_angles_triangles': 'act_math_plane_geometry',
                'area_volume': 'act_math_plane_geometry', 'circles': 'act_math_plane_geometry',
                'linear_functions': 'act_math_coordinate', 'linear_equations_two': 'act_math_coordinate',
                'quadratic_functions': 'act_math_coordinate', 'function_notation': 'act_math_coordinate',
                'transitions': 'act_english_rhetoric', 'rhetorical_synthesis': 'act_english_rhetoric',
                'words_in_context': 'act_reading_detail', 'central_ideas': 'act_reading_detail',
                'inferences': 'act_reading_detail', 'command_of_evidence_text': 'act_reading_detail'}


def act_equivalent(key):
    """The ACT skill that covers a SAT-taxonomy skill the student named."""
    if key in ACT_SPECIFIC:
        return ACT_SPECIFIC[key]
    if key in learning.SKILL_TAXONOMY:
        return (ACT_DOMAIN_SKILLS.get(learning.SKILL_TAXONOMY[key][2]) or [key])[0]
    return key


@lru_cache(maxsize=8)
def known_subskills(track):
    """Sub-skill names present in this section's benchmark, by skill."""
    found = defaultdict(set)
    for q in content.benchmark(track, seed=0):
        found[q['skill_key']].add(q['subskill'])
    return {k: sorted(v) for k, v in found.items()}


def _phrases(text):
    parts = re.split(r'[,;\n/&]|\band\b|\bor\b|\bas well as\b|\bespecially\b', str(text or '').lower())
    return [p.strip(' .:-()"\'') for p in parts if len(p.strip(' .:-()"\'')) >= 3]


def _skills_for_domain(domain_key, track):
    catalog = learning.skill_catalog(*track.split('_'))
    if track.startswith('act'):
        return [k for k in ACT_DOMAIN_SKILLS.get(domain_key, []) if k in catalog]
    return [k for k in catalog if learning.SKILL_TAXONOMY[k][2] == domain_key]


def parse_named_skills(text, track):
    """Map what a student wrote ("quadratics, commas, geometry") onto this section's skills.

    Returns {skill: (weight, phrase)}. A phrase that names one skill weighs 1.0;
    a phrase that names a whole area weighs 0.6 across the skills in that area.
    """
    catalog = set(learning.skill_catalog(*track.split('_')))
    found = {}

    def note(key, weight, phrase):
        if key in catalog and weight > found.get(key, (0, ''))[0]:
            found[key] = (weight, phrase)

    for phrase in _phrases(text):
        key = learning.resolve_skill(phrase)['skill_key']
        if key != 'pacing_and_timing':
            note(act_equivalent(key) if track.startswith('act') else key, 1.0, phrase)
        for word, dom in DOMAIN_WORDS.items():
            if re.search(rf'\b{re.escape(word)}', phrase):
                for k in _skills_for_domain(dom, track):
                    note(k, .6, phrase)
        tokens = [t[:5] for t in re.findall(r'[a-z]{4,}', phrase)]
        for k, subs in known_subskills(track).items():
            if any(tok in sub.lower() for sub in subs for tok in tokens):
                note(k, .8, phrase)
    return found


def goal_gap(questionnaire, track):
    """How far the student's stated target is above their current section score, 0 to 1."""
    def number(name):
        try:
            return float(questionnaire.get(name))
        except (TypeError, ValueError):
            return None
    if track.startswith('sat'):
        target = number('desired_sat')
        current = number('current_sat_math' if track.endswith('math') else 'current_sat_ebrw')
        return None if target is None or current is None else max(0, min(1, (target / 2 - current) / 200))
    target = number('desired_act')
    current = number('current_act_math') if track.endswith('math') else (number('current_act_english') or number('current_act_reading'))
    return None if target is None or current is None else max(0, min(1, (target - current) / 12))


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
    totals = defaultdict(lambda: [0.0, 0.0])  # area -> [weighted correct, weight]
    for key in learning.skill_catalog(*track.split('_')):
        samples = grouped[key]
        weights, score = [], 0
        for i, event in enumerate(samples):
            correct = bool(event['is_correct'])
            weight = (1.6 if event['source'] == 'benchmark' else 1.0) * (0.97 ** (len(samples)-i-1))
            # Missing an easier question says more about a gap than missing a hard one.
            weight *= (CORRECT_WEIGHT if correct else WRONG_WEIGHT).get(event['difficulty'], 1.0)
            if event['hint_count']:
                weight *= .6
            if event['response_ms'] is not None and event['response_ms'] < 1500:
                weight *= .2
            weights.append(weight)
            score += weight * int(correct)
        totals[content.domain(key)][0] += score
        totals[content.domain(key)][1] += sum(weights)
        prior = legacy.get(key, {})
        # Preserve historical counts as context, but do not double count the
        # current ledger's answers also reflected in the legacy stats view.
        historical_attempts = max(0, (prior.get('attempts') or 0) - len(samples))
        historical_correct = max(0, (prior.get('correct') or 0) - sum(int(s['is_correct']) for s in samples))
        prior_accuracy = historical_correct / max(historical_attempts, 1)
        prior_weight = min(0.5, historical_attempts * .05)
        estimate = (score + prior_accuracy * prior_weight) / (sum(weights) + prior_weight) if weights or prior_weight else None
        practice = [s for s in samples if s['source'] != 'benchmark']
        recent = practice[-8:]
        difficulty = {}
        for level in ('easy','medium','hard'):
            subset = [s for s in samples if s['difficulty'] == level]
            difficulty[level] = {'attempts': len(subset), 'correct': sum(int(s['is_correct']) for s in subset)}
        bench = [s for s in samples if s['source'] == 'benchmark']
        benchmark = {'total': len(bench), 'correct': sum(int(s['is_correct']) for s in bench),
            'hard_total': sum(s['difficulty'] == 'hard' for s in bench),
            'hard_correct': sum(s['difficulty'] == 'hard' and bool(s['is_correct']) for s in bench)}
        times = [s['response_ms'] for s in samples if s['response_ms'] is not None and 1500 <= s['response_ms'] <= 900000]
        subskills = {}
        for sub in {s['subskill'] for s in samples}:
            subevents = [s for s in samples if s['subskill'] == sub]
            subskills[sub] = {'attempts': len(subevents), 'correct': sum(int(s['is_correct']) for s in subevents),
                'accuracy': round(sum(int(s['is_correct']) for s in subevents)/len(subevents), 3)}
        recent_accuracy = sum(int(s['is_correct']) for s in recent)/len(recent) if recent else None
        early = practice[-16:-8]
        trend = round(recent_accuracy - sum(int(s['is_correct']) for s in early)/len(early), 3) if early and recent_accuracy is not None else None
        enough = sum(weights) >= 3
        hard_success = any(s['difficulty']=='hard' and s['is_correct'] and not s['hint_count'] and (s['response_ms'] is None or s['response_ms']>=1500) for s in samples)
        # Practice is never easy: weak skills get medium questions with hints
        # available; everything else gets hard, test-level questions.
        readiness = 'hard' if estimate is not None and estimate >= .6 and (enough or hard_success) else 'medium'
        skills[key] = {'label': learning.resolve_skill(key)['skill_label'], 'domain': content.domain(key),
            'attempts': len(samples), 'historical_attempts': prior.get('attempts',0),
            'accuracy': round(sum(int(s['is_correct']) for s in samples)/len(samples),3) if samples else None,
            'mastery_estimate': round(estimate,3) if estimate is not None else None,
            'evidence_confidence': 'developing' if enough else 'limited', 'recent_accuracy': recent_accuracy,
            'trend': trend, 'difficulty': difficulty, 'readiness': readiness, 'benchmark': benchmark,
            'average_response_ms': round(sum(times)/len(times)) if times else None,
            'last_practiced': samples[-1]['created_at'] if samples else None,
            'sources': dict(Counter(s['source'] for s in samples)), 'subskills': subskills,
            'misconceptions': dict(Counter(s['misconception'] for s in recent if s['misconception'] and not s['is_correct'])),
            'hints_used': sum(s['hint_count'] for s in samples),
            'confident_errors': sum(s['confidence']==3 and not s['is_correct'] for s in samples),
            'weekly_attempts': sum(s['created_at'] >= time.time()-604800 for s in samples),
            'rapid_responses': sum(s['response_ms'] is not None and s['response_ms']<1500 for s in samples),
            '_weighted': (score, sum(weights))}
    # An area's results inform skills with little direct evidence: a couple of
    # answers in one skill are blended with how the student did across its area.
    for s in skills.values():
        won, weight = s.pop('_weighted')
        area_won, area_weight = totals[s['domain']]
        if area_weight:
            s['adjusted_estimate'] = round((won + 1.5 * area_won / area_weight) / (weight + 1.5), 3)
        else:
            s['adjusted_estimate'] = s['mastery_estimate']
    track_state = db.select_one('adaptive_tracks', where={'user_id': user_id, 'track_key': track}) or {}
    progress = db.execute("SELECT description, skill_key, is_completed FROM paths WHERE user_id=? AND track_key=? AND is_active=True", (user_id, track))
    recent_questions = []
    for event in events[-80:]:
        evidence = unpack(event['evidence'],{})
        # Openings are enough to recognise a repeat, and keep snapshots small
        # now that passages can be several hundred words.
        recent_questions.append(re.sub(r'\W+',' ',(evidence.get('source_or_prompt','')+' '+evidence.get('question','')).lower()).strip()[:400])
    other_sections = db.execute('''SELECT track_key,skill_key,COUNT(*) AS attempts,
        SUM(CASE WHEN is_correct THEN 1 ELSE 0 END) AS correct
        FROM learning_events WHERE user_id=? AND track_key!=? GROUP BY track_key,skill_key''',(user_id,track))
    old_practice = [unpack(row['details'],{}) for row in db.execute("SELECT details FROM activity_log WHERE user_id=? AND activity_type='quick_practice' ORDER BY id DESC LIMIT 24",(user_id,))]
    state = {'track': track, 'questionnaire': questionnaire, 'onboarding': unpack(user.data.get('onboarding_data'), {}),
        'other_sections_background':other_sections,'other_section_goals':prep.get('tracks') or {},
        'legacy_practice_history':[row for row in old_practice if row.get('track')==track][:8],
        'skills': skills, 'benchmark_completed': bool(track_state.get('benchmark_completed_at')),
        'benchmark': unpack(track_state.get('diagnostic'), {}), 'path_progress': progress,
        'recent_questions': recent_questions, 'recent_mistakes': [unpack(e['evidence'], {}) for e in events[-30:] if not e['is_correct']],
        'goal_gap': goal_gap(questionnaire, track),
        'evidence_policy': 'Demonstrated performance outweighs self-report. A diagnostic is provisional; do not infer an official SAT or ACT score or diagnose carelessness from one miss.'}
    state['plan'] = plan(state)
    return state


def coach_view(state):
    """A compact profile for the coach and the browser: results and plan, without bulky detail."""
    skills = {}
    for key, s in state['skills'].items():
        skills[key] = {k: s[k] for k in ('label', 'domain', 'attempts', 'accuracy', 'mastery_estimate', 'readiness', 'benchmark', 'recent_accuracy', 'trend', 'misconceptions')}
        skills[key]['weakest_subskills'] = {k: v['accuracy'] for k, v in sorted(s['subskills'].items(), key=lambda kv: kv[1]['accuracy'])[:3] if v['accuracy'] < 1}
    benchmark = state.get('benchmark') or {}
    return {'track': state['track'], 'benchmark_completed': state['benchmark_completed'], 'goal_gap': state.get('goal_gap'),
        'benchmark_summary': {k: benchmark[k] for k in ('correct', 'total', 'accuracy', 'domains', 'weakest', 'strongest') if k in benchmark},
        'skills': skills, 'plan': [{k: e[k] for k in ('key', 'label', 'priority', 'reasons', 'focus_subskills')} for e in state['plan'][:6]],
        'targets': state.get('targets')}


def plan(state):
    """Rank skills for the next work, with the evidence behind each choice.

    Measured results carry the most weight: benchmark accuracy (missing easier
    questions counts more than missing hard ones) blended with how the student
    did across the whole area. What the student said they need help with adds
    a real but smaller boost, and is discounted where the benchmark shows it
    is already a strength. Each entry explains itself.
    """
    skills, track = state['skills'], state['track']
    questionnaire = state['questionnaire']
    named = parse_named_skills(questionnaire.get('weaknesses', ''), track)
    strengths = parse_named_skills(questionnaire.get('strengths', ''), track)
    slow_limit = 100000 if track.endswith('math') else 80000
    entries = []
    for key, s in skills.items():
        est = s['adjusted_estimate']
        reasons = []
        score = 3 * (1 - est if est is not None else .45)
        bench, label = s['benchmark'], s['label']
        if bench['total']:
            line = f"Benchmark: {bench['correct']} of {bench['total']} correct on {label}"
            if bench['hard_total']:
                line += f" (hard questions {bench['hard_correct']} of {bench['hard_total']})"
            reasons.append(line)
        elif s['attempts']:
            reasons.append(f"{round(s['accuracy'] * 100)}% across {s['attempts']} recorded answers on {label}")
        elif est is not None:
            reasons.append(f"Your results across {s['domain']} suggest {label} needs checking")
        else:
            reasons.append(f"{label} has not been measured yet")
        if s['recent_accuracy'] is not None:
            score += .8 * (1 - s['recent_accuracy'])
            if s['recent_accuracy'] < .6:
                reasons.append(f"Recent practice accuracy is {round(s['recent_accuracy'] * 100)}%")
        if s['misconceptions']:
            score += .3
            reasons.append('The same kind of wrong answer has repeated: ' + next(iter(s['misconceptions'])))
        if s['average_response_ms'] and s['average_response_ms'] > slow_limit:
            score += .15
            reasons.append('Questions here took much longer than a test allows')
        strong = est is not None and s['attempts'] >= 2 and est >= .85
        if key in named:
            weight, phrase = named[key]
            if strong:
                weight *= .25
                reasons.append(f"You listed “{phrase}”, but your results show it is already a strength")
            else:
                reasons.append(f"You told us you need help with “{phrase}”")
            score += 1.4 * weight
        if key in strengths and strong:
            score -= .4 * strengths[key][0]
        if s['last_practiced'] and time.time() - s['last_practiced'] < 172800 and est is not None and est >= .7:
            score -= .3  # spaced practice: leave a recently mastered skill alone
        missed = sorted((v['accuracy'], k) for k, v in s['subskills'].items() if v['attempts'] and v['correct'] < v['attempts'])
        entries.append({'key': key, 'label': label, 'priority': round(score, 3), 'reasons': reasons,
            'focus_subskills': [k for _, k in missed[:3]], 'self_reported': key in named, 'domain': s['domain']})
    entries.sort(key=lambda e: (-e['priority'], skills[e['key']]['last_practiced'] or 0, e['key']))
    return entries


def targets(state, count=5):
    """Skill keys for a practice set. The weakest area gets most of the slots."""
    ranked = state.get('plan') or plan(state)
    order = [e['key'] for e in ranked]
    skills = state['skills']
    top = order[:3]
    if len(ranked) > 1 and ranked[0]['priority'] > 2 * max(ranked[1]['priority'], .1):
        pattern = [0, 0, 0, 1]
    elif len(top) >= 3:
        pattern = [0, 0, 1, 2]
    else:
        pattern = [0, 0, 1, 1]
    selected = [top[pattern[i % len(pattern)] % len(top)] for i in range(max(1, count - 1))]
    # One slot for spaced reinforcement or exploring an unmeasured area.
    other = sorted(order, key=lambda k: (k in selected, skills[k]['last_practiced'] or 0))
    selected.append(other[0])
    return selected[:count]


def signature(q):
    return re.sub(r'\W+', ' ', (q.get('source_or_prompt','')+' '+q['question_text']).lower()).strip()


def seen_before(sig, recent):
    """Cheap repeat check: long passages compare by opening, short ones by similarity."""
    head = sig[:110]
    for previous in recent:
        if head and previous.startswith(head):
            return True
        if len(sig) < 700 and len(previous) < 700 and SequenceMatcher(None, sig, previous).ratio() > .88:
            return True
    return False


# Minimum stimulus length, in words, for each skill. These follow the real
# digital SAT (about 25-150 words per passage) and the ACT (longer passages).
MIN_WORDS = {
    'central_ideas': 60, 'command_of_evidence_text': 55, 'command_of_evidence_quant': 40, 'inferences': 55,
    'words_in_context': 45, 'text_structure_purpose': 60, 'cross_text_connections': 90,
    'rhetorical_synthesis': 35, 'transitions': 40, 'boundaries': 28, 'form_structure_sense': 28,
    'subject_verb_agreement': 28, 'pronouns_modifiers': 28, 'verb_tense': 28,
    'act_english_usage': 150, 'act_english_rhetoric': 150, 'act_reading_detail': 280,
}

DIFFICULTY_SPEC = {
    'medium': 'MEDIUM = a mid-test item from a real exam: at least two reasoning steps or one subtle distinction, with distractors built from common errors. Never a one-step recall or plug-in problem.',
    'hard': 'HARD = a last-third item from a real exam, the kind only top scorers get right: three or more steps, or an abstract or multi-concept setup, with tempting distractors (partial work, sign or unit traps, plausible-but-unsupported inferences). It should take a strong student over a minute. Never a textbook drill.',
}

LENGTH_RULES = {
    'sat_math': 'SAT Math: use realistic contexts (science, business, sports, data) and multi-step reasoning. Put any system of equations, table or data in source_or_prompt as plain lines; put the actual question in question_text. Use non-trivial numbers and compute every answer carefully.',
    'act_math': 'ACT Math: four choices, ACT content (number and quantity, algebra, functions, geometry, trigonometry, statistics and probability). Use multi-step setups with realistic numbers and compute every answer carefully.',
    'sat_ela': 'SAT Reading and Writing length rules. Every source_or_prompt is ONE self-contained stimulus, never one or two sentences. central_ideas, inferences, command_of_evidence_text and text_structure_purpose: 70-120 words. cross_text_connections: "Text 1" and "Text 2" of about 55-70 words each. command_of_evidence_quant: a 40-70 word setup followed by a small data table written as plain lines. rhetorical_synthesis: a bulleted list of 4-6 notes, each line starting with "•". words_in_context and transitions: 55-90 words with _____ where the choice goes. Conventions skills (boundaries, agreement, tense, pronouns, structure): 40-70 words with _____ where the choice goes. Use the real digital SAT question stems.',
    'act_ela': 'ACT length rules. ACT English: source_or_prompt is a 170-260 word passage excerpt in which the tested portion is marked [underlined: exact words]; the first option may be NO CHANGE (only when an underlined span exists). ACT Reading: source_or_prompt is a 300-450 word passage excerpt (prose fiction, social science, humanities or natural science) and the question tests detail, inference, vocabulary in context, purpose or tone.',
}


def question_schema(requested):
    properties = {key:{'type':'string'} for key in ('subskill','source_or_prompt','question_text','explanation','strategy','fastest_method')}
    properties.update({
        'skill_key':{'type':'string','enum':list(dict.fromkeys(requested))},
        'difficulty':{'type':'string','enum':['medium','hard']},
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
        source = q['source_or_prompt']
        # Real exam stimuli are not one-liners: enforce the minimum length.
        if track.endswith('ela') and word_count(source) < MIN_WORDS.get(skill, 0):
            return None
        if skill == 'cross_text_connections' and not ('Text 1' in source and 'Text 2' in source):
            return None
        if skill == 'rhetorical_synthesis' and len(re.findall(r'(?m)^\s*[•\-*]\s+\S', source)) < 3:
            return None
        if skill == 'transitions' and not re.search(r'_{3,}', source):
            return None
        if track=='act_ela' and skill != 'act_reading_detail' and ('underlin' in q['question_text'].lower() or any(o.upper()=='NO CHANGE' for o in q['options'])):
            if not re.search(r'\[underlined(?: \d+)?:[^\]]+\]',source,re.I):
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


def brief(state, requested):
    """A compact, bounded view of the student's evidence for the question writer."""
    skills = {}
    for key in dict.fromkeys(requested):
        s = state['skills'][key]
        skills[key] = {k: s[k] for k in ('label', 'accuracy', 'mastery_estimate', 'readiness', 'benchmark', 'difficulty', 'misconceptions', 'trend', 'hints_used')}
        skills[key]['weakest_subskills'] = {k: v for k, v in sorted(s['subskills'].items(), key=lambda kv: kv[1]['accuracy'])[:4]}
    q = state['questionnaire']
    return {'track': state['track'], 'goals_and_self_report': {k: q.get(k) for k in ('desired_sat', 'desired_act', 'weaknesses', 'strengths', 'goals', 'test_date', 'hours_per_week') if q.get(k)},
        'goal_gap': state.get('goal_gap'), 'skills': skills,
        'priorities': [{'skill': e['key'], 'why': e['reasons'][:3]} for e in state['plan'][:5]],
        'recent_mistakes': [{k: str(v)[:260] for k, v in m.items() if k in ('question', 'strategy')} for m in state['recent_mistakes'][-4:]],
        'avoid_repeating': [r[:110] for r in state['recent_questions'][-10:]]}


def recovery_pick(pool, readiness, focus, used, recent):
    """Choose reviewed content: hard enough, unseen, and on the focus sub-skill."""
    rank = {'easy': 0, 'medium': 1, 'hard': 2}
    candidates = [q for q in pool if signature(q) not in used]
    candidates.sort(key=lambda q: (seen_before(signature(q), recent), rank[q['difficulty']] < rank[readiness],
        bool(focus) and q.get('subskill') not in focus, rank[q['difficulty']] == 0))
    return candidates[0] if candidates else None


def generate_questions(state, requested, generate, *, seed=0, focus=None):
    """Generate, structurally validate, and independently solve before serving."""
    track = state['track']
    focus = focus or {}
    cycle = defaultdict(int)
    assignments = []
    for key in requested:
        subs = focus.get(key) or []
        assignment = {'skill_key': key, 'difficulty': state['skills'][key]['readiness']}
        if subs:
            assignment['focus_subskill'] = subs[cycle[key] % len(subs)]
            cycle[key] += 1
        assignments.append(assignment)
    specs = '\n'.join(DIFFICULTY_SPEC[level] for level in sorted({a['difficulty'] for a in assignments}))
    prompt = f'''Create {len(requested)} original {track} practice questions at REAL EXAM level, one per assignment in order.
ASSIGNMENTS: {json.dumps(assignments)}
STUDENT EVIDENCE: {json.dumps(brief(state, requested))}
{specs}
These students are preparing for the real test. Questions must be as difficult AND as long as real exam questions; do not write easy or classroom-style items. Practice at medium or hard only.
When an assignment has focus_subskill, test exactly that concept. Use demonstrated weaknesses, repeated misconceptions and what the student said they need help with; reinforce strong skills at their hardest.
Do not repeat recent questions or just substitute numbers into them. Vary contexts and reasoning.
{LENGTH_RULES[track]}
{learning._format_facts(track.split('_')[0])}
All necessary passages, tables and information must be in source_or_prompt or question_text. No unseen figures.
Use plain text and readable Unicode math (x², ×, √, (a+b)/c). No LaTeX commands, dollar-delimited equations or Markdown tables.
Put answer choices ONLY in options, never repeat lettered choices in question_text or source_or_prompt.
All passages and examples must be original. Do not invent quotations from real authors, novels, studies, or historical documents. Use fictional examples or unattributed original expository text.
Exactly four distinct plausible choices, exactly one correct. Solve each question fully before finalizing.
Write option explanations by their content, never by A/B/C/D or numbered position because choices will be shuffled.
misconceptions MUST have FOUR entries in option order, including an empty string at the correct option's index.
Give three increasingly specific hints: direction, strategy, then setup. NO final value, answer choice, or completed solution in hints.
Explain the correct answer and why each distractor is wrong. Provide the fastest reliable test-specific approach and its limitation.
Only reference James Lu for the supplied public Desmos/grammar emphasis; never invent quotations or claim access to his private course.
Return JSON {{"questions":[{{"skill_key":"...","subskill":"specific stable concept", "difficulty":"medium|hard",
"source_or_prompt":"...", "question_text":"...", "options":["...","...","...","..."],"correct_option":0,
"explanation":"detailed solution and distractor reasoning", "hints":["direction","strategy","setup"],
"strategy":"actionable shortcut with when to use it", "fastest_method":"worked efficient solution",
"misconceptions":["possible misconception for this distractor or empty if correct","...","...","..."]}}]}}.'''
    accepted = []
    note = 'AI-personalized, real-exam-level questions, independently checked before practice.'
    recent = state['recent_questions']
    try:
        data = learning._parse_json(generate(prompt, max_output_tokens=min(16000, len(requested)*1500+800), json_output=True,json_schema=question_schema(requested),
            thinking_level='low', system_instruction=learning.SYSTEM_TUTOR, timeout_seconds=33), expect_key='questions')
        raw_items = data.get('questions', []) if isinstance(data,dict) else data if isinstance(data,list) else []
        candidates = [valid_generated(q,track) for q in raw_items[:len(requested)]]
        candidates = [q for q in candidates if q and q['skill_key'] in requested and q['difficulty'] != 'easy']
        candidates = learning._dedupe(candidates)
        if not candidates:
            raise ValueError('No structurally valid questions')
        blind = [{k:v for k,v in q.items() if k not in {'correct_option','explanation','fastest_method','misconceptions'}} for q in candidates]
        audit = learning._parse_json(generate(
            'Independently solve these questions without an answer key. Check ambiguity, missing information, SAT/ACT scope, grammar, difficulty label, and whether any hint reveals the answer. Return JSON {"reviews":[{"index":0,"answer":0,"valid":true,"hints_safe":true,"reason":"your solution and checks"}]}. Reject any doubtful item. Questions: '+json.dumps(blind),
            max_output_tokens=6000, json_output=True,json_schema=REVIEW_SCHEMA, thinking_level='low', system_instruction=learning.SYSTEM_TUTOR, timeout_seconds=15), expect_key='reviews')
        reviews = audit.get('reviews',[]) if isinstance(audit,dict) else audit if isinstance(audit,list) else []
        for review in reviews:
            idx = review.get('index')
            if type(idx) is not int or not 0<=idx<len(candidates):
                continue
            q = candidates[idx]
            if review.get('valid') is True and review.get('hints_safe') is True and type(review.get('answer')) is int and review['answer']==q['correct_option'] and len(str(review.get('reason','')))>30:
                if not seen_before(signature(q), recent):
                    accepted.append(q)
    except Exception as error:
        learning._log('Adaptive question generation recovered: %s', type(error).__name__)
    # Fill missing or rejected items with reviewed content that is still hard
    # and real-length. It is chosen from evidence, never relabelled to another
    # skill, and the student is told when it is used.
    result = []
    bank = content.bank(track, seed)
    for position, key in enumerate(requested):
        used = {signature(q) for q in result}
        q = next((q for q in accepted if q['skill_key']==key and signature(q) not in used),None)
        if q is None:
            wanted = assignments[position]
            pool = [b for b in bank if b['skill_key']==key]
            q = recovery_pick(pool, wanted['difficulty'], [wanted['focus_subskill']] if wanted.get('focus_subskill') else [], used, recent)
            if q is None:
                # If there is no reviewed question on this exact skill, never
                # relabel another skill to fake personalization.
                q = recovery_pick(bank, wanted['difficulty'], [], used, recent)
            if q is None:
                raise ValueError('No distinct reviewed questions available. Try a mixed session.')
            q = dict(q)
            note = 'Some questions use the reviewed recovery bank because AI checks did not pass. Your skill targeting and results are still saved.'
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
        questions,note=generate_questions(state,targets(state),generate,seed=session_id,focus={e['key']:e['focus_subskills'] for e in state['plan']})
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
    passages={}
    passage_ids={}
    points=streak=best_streak=0
    for i,q in enumerate(questions):
        p={k:q[k] for k in ('question_text','options','skill_key','subskill','difficulty','domain','attribution','module') if k in q}
        source=q.get('source_or_prompt','')
        # A long passage shared by several questions is sent once.
        if len(source)>500:
            pid=passage_ids.setdefault(source,str(len(passage_ids)+1))
            passages[pid]=source
            p['passage_id']=pid
        else:
            p['source_or_prompt']=source
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
    modules=[]
    if saved['kind']=='benchmark':
        labels=content.MODULES.get(saved['track_key'],{})
        for module in sorted({q.get('module') for q in questions if q.get('module')}):
            indexes=[i for i,q in enumerate(questions) if q.get('module')==module]
            modules.append({'id':module,'label':labels.get(module,f'Module {module}'),'start':indexes[0],'end':indexes[-1],
                'minutes':content.MINUTES.get(saved['track_key'],{}).get(module)})
    return {'id':saved['id'],'track':saved['track_key'],'kind':saved['kind'],'status':saved['status'],
        'points':points if saved['kind']=='quick' else None,'streak':streak if saved['kind']=='quick' else None,'best_streak':best_streak if saved['kind']=='quick' else None,
        'questions':public,'passages':passages,'modules':modules,'answered':len(answers),'total':len(questions),'summary':unpack(saved['summary'],{}),
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


def summarize(saved, questions, answers):
    """Results by area, skill, difficulty and module, for the student and for path planning."""
    groups=defaultdict(lambda:{'correct':0,'total':0})
    by_skill=defaultdict(lambda:{'correct':0,'total':0,'hard_correct':0,'hard_total':0})
    difficulty=defaultdict(lambda:{'correct':0,'total':0})
    modules=defaultdict(lambda:{'correct':0,'total':0})
    labels=content.MODULES.get(saved['track_key'],{})
    correct=rapid=spent=0
    for i,q in enumerate(questions):
        a=answers[str(i)];right=a['selected_option']==q['correct_option'];correct+=right
        groups[q['domain']]['correct']+=right;groups[q['domain']]['total']+=1
        skill=by_skill[q['skill_key']];skill['correct']+=right;skill['total']+=1
        if q.get('difficulty')=='hard':
            skill['hard_correct']+=right;skill['hard_total']+=1
        difficulty[q.get('difficulty','unknown')]['correct']+=right;difficulty[q.get('difficulty','unknown')]['total']+=1
        if q.get('module'):
            label=labels.get(q['module'],f"Module {q['module']}")
            modules[label]['correct']+=right;modules[label]['total']+=1
        rapid+=a.get('response_ms') is not None and a['response_ms']<1500
        spent+=a.get('response_ms') or 0
    skills={}
    for key,result in by_skill.items():
        skills[key]={**result,'label':learning.resolve_skill(key)['skill_label'],'domain':content.domain(key)}
    ranked=sorted(skills.items(),key=lambda kv:(kv[1]['correct']/kv[1]['total'],-kv[1]['total']))
    return {'correct':correct,'total':len(questions),'accuracy':round(correct/len(questions),3),'domains':dict(groups),
        'skills':skills,'difficulty':dict(difficulty),'modules':dict(modules),
        'weakest':[k for k,v in ranked if v['correct']<v['total']][:5],
        'strongest':[k for k,v in reversed(ranked) if v['correct']==v['total']][:5],
        'minutes':round(spent/60000) if spent else None,'rapid_responses':rapid,
        'message':'This is a starting estimate, not an official score. Your path is built from these results and from what you told us you need help with.'}


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
        summary=summarize(saved,questions,answers)
        tx.update('adaptive_sessions',{'status':'completed','summary':json.dumps(summary),'updated_at':time.time()},where={'id':session_id})
        if saved['kind']=='benchmark':
            tx.update('adaptive_tracks',{'benchmark_completed_at':str(time.time()),'diagnostic':json.dumps(summary)},where={'user_id':user_id,'track_key':saved['track_key']})
            tx.execute_write("UPDATE paths SET is_completed=True WHERE user_id=? AND track_key=? AND task_format='benchmark' AND learning_version=?",(user_id,saved['track_key'],VERSION))
    return saved['track_key']


def lesson_focus(state):
    """Two lesson skills: the top priority, then the next that adds a different area."""
    ranked=state['plan']
    first=ranked[0]
    rest=ranked[1:]
    second=next((e for e in rest if e['domain']!=first['domain'] and e['priority']>=.6*rest[0]['priority']),rest[0])
    return [first,second]


def path_reason(entry, state):
    why='; '.join(entry['reasons'][:3])+'.'
    if entry.get('focus_subskills'):
        why+=' Starting with: '+', '.join(entry['focus_subskills'][:2])+'.'
    if (state.get('goal_gap') or 0)>=.3:
        why+=' Your target is well above your current score, so these questions are at full test difficulty.'
    return why


def build_unit(state, generate, seed=0):
    entries=lesson_focus(state)
    # Two bounded five-question jobs avoid one large, truncation-prone response.
    # They share an immutable profile and perform no database work in threads.
    with ThreadPoolExecutor(max_workers=2) as pool:
        jobs=[pool.submit(generate_questions,state,[e['key']]*5,generate,seed=seed+i*7,focus={e['key']:e['focus_subskills']}) for i,e in enumerate(entries)]
        generated=[job.result() for job in jobs]
    questions=[q for group,_ in generated for q in group]
    note=' '.join(dict.fromkeys(message for _,message in generated))
    nodes=[];review=[]
    for idx,entry in enumerate(entries):
        group=questions[idx*5:idx*5+5]
        # Recovery content may use a different skill: use its honest taxonomy.
        key=group[0]['skill_key'];skill=learning.resolve_skill(key)
        sample=group[0]
        reason=path_reason(entry,state) if key==entry['key'] else 'The next focus comes from your recorded performance and goals.'
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
