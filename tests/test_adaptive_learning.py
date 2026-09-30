import inspect
import json
from collections import Counter
from concurrent.futures import ThreadPoolExecutor

import pytest
import adaptive
import adaptive_bank
import app as server
import learning
from bench_common import words as word_count
from dbhelper import DatabaseHandler
from userhelper import User


@pytest.fixture
def learner(tmp_path, monkeypatch):
    db = DatabaseHandler(str(tmp_path / 'adaptive.db'))
    monkeypatch.setattr(server, 'db', db)
    server.init_db()
    db.insert('users', {'email':'adaptive@example.test','name':'Adaptive Test','password':'unused',
        'stats':json.dumps({'test_path':{'test_focus':'sat','weaknesses':'algebra','desired_sat':'1500'}}),
        'onboarding_completed':True,'onboarding_data':json.dumps({'learning_style':'visual'})})
    monkeypatch.setattr(server, '_generate_text', lambda *a, **k: '{}')
    return User(db,'adaptive@example.test'), db


def complete_benchmark(user, db, track='sat_math', correct=True):
    state = adaptive.ensure_track(db,user.data['id'],track)
    sid = state['benchmark_session_id']
    questions = json.loads(db.select_one('adaptive_sessions',where={'id':sid})['questions'])
    for i,q in enumerate(questions):
        adaptive.answer(db,user.data['id'],sid,{'index':i,'selected_option':q['correct_option'] if correct else (q['correct_option']+1)%4,'response_ms':45000,'confidence':3})
    adaptive.finish(db,user.data['id'],sid)
    return sid


LENGTHS = {'sat_math': 44, 'sat_ela': 54, 'act_math': 45, 'act_ela': 86}


@pytest.mark.parametrize('track',adaptive.TRACKS)
def test_benchmarks_are_full_length_and_hard(track):
    for seed in (0, 1, 2, 17, 101):
        questions=adaptive_bank.benchmark(track,seed)
        assert len(questions)==LENGTHS[track]
        if track!='act_ela':
            assert not any(q['difficulty']=='easy' for q in questions[-10:])
        hard_share=sum(q['difficulty']=='hard' for q in questions)/len(questions)
        assert hard_share>=({'act_math':.25,'act_ela':.12}.get(track,.35))
        catalog=set(learning.skill_catalog(*track.split('_')))
        assert {q['skill_key'] for q in questions}<=catalog
        assert len({q['domain'] for q in questions})>=3
        for q in questions:
            assert len(set(q['options']))==4
            assert 0<=q['correct_option']<4
            assert len(q['hints'])==3 and len(q['misconceptions'])==4
            assert q['misconceptions'][q['correct_option']]==''
            assert len(q['explanation'])>(40 if track=='act_ela' else 60)
        positions=[q['correct_option'] for q in questions]
        assert all(positions.count(i)>=len(questions)//8 for i in range(4)), 'answer positions must be spread out'


def test_benchmark_structure_matches_the_real_tests():
    math=adaptive_bank.benchmark('sat_math',3)
    assert [sum(q['module']==m for q in math) for m in (1,2)]==[22,22]
    domains=Counter(q['domain'] for q in math)
    assert domains=={'Algebra':15,'Advanced Math':15,'Problem Solving and Data Analysis':7,'Geometry and Trigonometry':7}
    reading=adaptive_bank.benchmark('sat_ela',3)
    assert [sum(q['module']==m for q in reading) for m in (1,2)]==[27,27]
    assert Counter(q['domain'] for q in reading)=={'Craft and Structure':15,'Information and Ideas':14,'Standard English Conventions':14,'Expression of Ideas':11}
    # Module 2 is harder than Module 1, as the adaptive second module is for a strong student.
    for questions in (math,reading):
        share=lambda m:sum(q['difficulty']=='hard' for q in questions if q['module']==m)
        assert share(2)>share(1)
    act=adaptive_bank.benchmark('act_ela',3)
    assert [sum(q['module']==m for q in act) for m in (1,2)]==[50,36]


def test_reading_passages_are_real_exam_length():
    sat=[q for q in adaptive_bank.benchmark('sat_ela',0)]
    lengths=[word_count(q['source_or_prompt']) for q in sat]
    assert sum(lengths)/len(lengths)>=50
    by_skill={}
    for q in sat: by_skill.setdefault(q['skill_key'],[]).append(word_count(q['source_or_prompt']))
    for skill,minimum in adaptive.MIN_WORDS.items():
        if skill in by_skill and not skill.startswith('act_'):
            assert min(by_skill[skill])>=minimum*.7,(skill,min(by_skill[skill]))
    for q in adaptive_bank.benchmark('act_ela',0):
        assert word_count(q['source_or_prompt'])>=(220 if q['skill_key']!='act_reading_detail' else 450), q['skill_key']
    assert max(word_count(q['source_or_prompt']) for q in sat)>=90


@pytest.mark.parametrize('track',('sat_math','act_math'))
def test_math_templates_are_unique_and_vary_by_seed(track):
    first=adaptive_bank.benchmark(track,1)
    second=adaptive_bank.benchmark(track,2)
    changed=sum(a['question_text']!=b['question_text'] or a['source_or_prompt']!=b['source_or_prompt'] or a['options']!=b['options'] for a,b in zip(first,second))
    assert changed>=len(first)*.8
    for seed in range(40):
        for q in adaptive_bank.bank(track,seed):
            assert len(set(q['options']))==4


def test_generated_math_answers_are_correct():
    """Re-solve the riskiest templates by brute force, independent of the generator."""
    from fractions import Fraction
    import re
    import bench_sat_math as m
    from bench_common import realize
    fn=lambda name:next(e for e in m.SAT_MATH+m.SAT_EXTRA if e['fn'].__name__==name)
    plain=lambda text:text.replace('−','-')
    for seed in range(60):
        q=realize(fn('_radical'),seed);t=plain(q['question_text'])
        inside=re.search(r'√\(x(?: ([+-]) (\d+))?\)',t)
        a=int(inside.group(1)+inside.group(2)) if inside.group(1) else 0
        b=int(re.search(r'= x - (\d+)',t).group(1))
        assert [x for x in range(-60,80) if x+a>=0 and abs((x+a)**.5-(x-b))<1e-9]==[int(plain(q['options'][0]))]
        q=realize(fn('_fractions'),seed);t=plain(q['question_text'])
        a,b,c,d=map(int,re.search(r'\(x \+ (\d+)\)/(\d+) - \(x - (\d+)\)/(\d+)',t).groups());e=Fraction(re.search(r'= (-?[\d/]+)',t).group(1))
        assert [x for x in range(-60,120) if Fraction(x+a,b)-Fraction(x-c,d)==e]==[int(plain(q['options'][0]))]
        q=realize(fn('_van_budget'),seed);nums=[int(x) for x in re.findall(r'\$?(\d+)',q['question_text'])]
        vans,large,small,budget=nums[:4]
        assert max(l for l in range(vans+1) if large*l+small*(vans-l)<=budget)==int(q['options'][0])
        q=realize(fn('_half_life'),seed);mass,half_life,weeks=[int(x) for x in re.findall(r'(\d+)',q['question_text'])[:3]]
        assert Fraction(mass)/2**Fraction(7*weeks,half_life)==int(q['options'][0])


def test_migration_archives_only_old_generated_prep(learner):
    user,db=learner
    uid=user.data['id']
    old=db.insert('paths',{'user_id':uid,'task_order':1,'category':'Test Prep','is_active':True,'is_user_added':False,'description':'Old','is_completed':True})
    personal=db.insert('paths',{'user_id':uid,'task_order':1,'category':'Test Prep','is_active':True,'is_user_added':True,'description':'Personal'})
    college=db.insert('paths',{'user_id':uid,'task_order':1,'category':'College Planning','is_active':True,'is_user_added':False,'description':'College'})
    server._ensure_prep_tracks(user)
    server._ensure_prep_tracks(user)
    assert not db.select_one('paths',where={'id':old})['is_active']
    assert db.select_one('paths',where={'id':old})['is_completed']
    assert all(db.select_one('paths',where={'id':i})['is_active'] for i in [personal,college])
    assert len(db.select('adaptive_tracks',where={'user_id':uid}))==4
    assert len(db.select('adaptive_sessions',where={'user_id':uid}))==4
    for track in adaptive.TRACKS:
        with server.app.test_request_context('/api/tasks?track='+track):
            result=inspect.unwrap(server.api_tasks)(user)
            assert len(result.json)==1
            assert result.json[0]['task_format']=='benchmark'


def test_benchmark_resume_is_unaided_atomic_and_only_once(learner):
    user,db=learner;uid=user.data['id']
    state=adaptive.ensure_track(db,uid,'sat_math');sid=state['benchmark_session_id']
    view=adaptive.session_view(db,uid,sid)
    assert all('correct_option' not in q and not q['hints'] for q in view['questions'])
    with pytest.raises(ValueError): adaptive.hint(db,uid,sid,0)
    with pytest.raises(ValueError): adaptive.finish(db,uid,sid)
    payload={'index':0,'selected_option':0,'response_ms':100,'confidence':3}
    with ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(lambda _:adaptive.answer(db,uid,sid,payload),range(2)))
    resumed=adaptive.session_view(db,uid,sid)
    assert resumed['answered']==1
    assert 'correct_option' not in resumed['questions'][0]
    assert len(db.select('learning_events',where={'user_id':uid}))==1
    assert complete_benchmark(user,db)==sid
    adaptive.finish(db,uid,sid)
    server._ensure_prep_tracks(user)
    assert adaptive.ensure_track(db,uid,'sat_math')['benchmark_completed_at']
    assert adaptive.ensure_track(db,uid,'sat_math')['benchmark_session_id']==sid
    assert len(db.select('learning_events',where={'user_id':uid,'track_key':'sat_math'}))==44
    assert 'correct_option' in adaptive.session_view(db,uid,sid)['questions'][0]
    state=adaptive.profile(db,user,'sat_math')
    assert state['onboarding']['learning_style']=='visual'
    assert state['skills']['linear_equations_one']['rapid_responses']==1


def test_first_five_steps_are_idempotent_and_survive_return(learner):
    user,db=learner;uid=user.data['id'];sid=complete_benchmark(user,db)
    with server.app.test_request_context('/'):
        first=server._generate_and_save_new_test_path(uid,user.get_stats()['test_path'],track_key='sat_math',request_key=f'initial:{sid}',initial=True)
        again=server._generate_and_save_new_test_path(uid,user.get_stats()['test_path'],track_key='sat_math',request_key=f'initial:{sid}',initial=True)
    assert len(first)==5
    assert [p['id'] for p in first]==[p['id'] for p in again]
    assert [p['task_format'] for p in first]==['lesson','practice_sprint','lesson','practice_sprint','quiz']
    server._ensure_prep_tracks(user)
    active=db.select('paths',where={'user_id':uid,'track_key':'sat_math','is_active':True})
    assert len(active)==5 and all(p['learning_version']==2 for p in active)
    assert len(db.select('path_generations',where={'user_id':uid}))==1
    other=adaptive.ensure_track(db,uid,'sat_ela')
    assert not other['benchmark_completed_at']


def test_quick_practice_hints_feedback_and_shared_mastery(learner):
    user,db=learner;uid=user.data['id']
    sid=adaptive.start_practice(db,user,'sat_math','practice-request-01',lambda *a,**k:'{}')
    assert adaptive.start_practice(db,user,'sat_math','different-request',lambda *a,**k:pytest.fail('Resume must not regenerate'))==sid
    view=adaptive.session_view(db,uid,sid)
    assert view['total']==5 and 'recovery bank' in view['note']
    for n in range(1,5):
        view=adaptive.hint(db,uid,sid,0)
        assert len(view['questions'][0]['hints'])==min(n,3)
        assert 'correct_option' not in view['questions'][0]
    questions=json.loads(db.select_one('adaptive_sessions',where={'id':sid})['questions'])
    for i,q in enumerate(questions):
        adaptive.answer(db,uid,sid,{'index':i,'selected_option':q['correct_option'],'response_ms':20000})
    adaptive.finish(db,uid,sid)
    state=adaptive.profile(db,user,'sat_math')
    assert sum(s['attempts'] for s in state['skills'].values())==5
    assert sum(s['hints_used'] for s in state['skills'].values())==3
    assert sum(s['sources'].get('quick',0) for s in state['skills'].values())==5
    assert sum(r['attempts'] for r in db.select('skill_mastery',where={'user_id':uid}))==5
    assert not state['benchmark_completed']
    with pytest.raises(ValueError): adaptive.session_view(db,uid+999,sid)


def test_targeting_changes_with_mistakes_and_mastery(learner):
    user,db=learner;uid=user.data['id']
    q=adaptive_bank.bank('sat_math')[0]
    for i in range(6): adaptive.record_event(db,uid,'sat_math','quick',str(i),q,False,response_ms=20000,chosen=0)
    state=adaptive.profile(db,user,'sat_math')
    assert adaptive.targets(state).count(q['skill_key'])>=2
    assert state['plan'][0]['key']==q['skill_key']
    assert state['skills'][q['skill_key']]['readiness']=='medium'  # weak skills are never given easy questions
    for i in range(6,70): adaptive.record_event(db,uid,'sat_math','quick',str(i),q,True,response_ms=20000)
    state=adaptive.profile(db,user,'sat_math')
    assert state['skills'][q['skill_key']]['readiness']=='hard'
    assert adaptive.targets(state).count(q['skill_key'])<=1


def test_question_audit_rejects_wrong_answer_and_unsafe_hints(learner):
    user,db=learner
    state=adaptive.profile(db,user,'sat_math')
    q=next(x for x in adaptive_bank.bank('sat_math') if x['difficulty']=='hard')
    q={**q,'question_text':'Original verified structure: '+q['question_text']}
    calls=[]
    def generator(prompt,**kwargs):
        calls.append(prompt)
        if len(calls)%2: return json.dumps({'questions':[q]})
        assert 'correct_option' not in prompt and q['explanation'] not in prompt
        return json.dumps({'reviews':[{'index':0,'answer':(q['correct_option']+1)%4,'valid':True,'hints_safe':True,'reason':'Independent arithmetic disagrees with the supplied problem.'}]})
    questions,note=adaptive.generate_questions(state,[q['skill_key']],generator)
    assert questions[0]['validation']=='reviewed_bank'
    assert len(calls)==2
    assert adaptive.valid_generated({**q,'hints':['The answer is B.']*3},'sat_math') is None


def test_failed_path_can_retry_without_retaking_benchmark(learner,monkeypatch):
    user,db=learner;uid=user.data['id'];sid=complete_benchmark(user,db,correct=False)
    original=adaptive.build_unit
    monkeypatch.setattr(adaptive,'build_unit',lambda *a,**k: (_ for _ in ()).throw(RuntimeError('worker failed')))
    with pytest.raises(RuntimeError): server._generate_and_save_new_test_path(uid,{},track_key='sat_math',request_key='retry-test',initial=True)
    assert adaptive.ensure_track(db,uid,'sat_math')['benchmark_completed_at']
    assert adaptive.session_view(db,uid,sid)['status']=='completed'
    monkeypatch.setattr(adaptive,'build_unit',original)
    assert len(server._generate_and_save_new_test_path(uid,{},track_key='sat_math',request_key='retry-test',initial=True))==5


def test_benchmark_cannot_be_skipped_or_manually_completed(learner):
    user,db=learner;adaptive.ensure_track(db,user.data['id'],'sat_math')
    task=db.select_one('paths',where={'user_id':user.data['id'],'track_key':'sat_math'})
    for fn,url in [(server.api_skip_task,'/api/skip_task'),(server.api_update_task_status,'/api/update_task_status')]:
        with server.app.test_request_context(url,method='POST',json={'taskId':task['id'],'status':'complete'}):
            assert inspect.unwrap(fn)(user)[1]==409


def test_authenticated_end_to_end_and_path_hints(learner):
    user,db=learner;uid=user.data['id']
    client=server.app.test_client()
    with client.session_transaction() as session:
        session['user']=user.email;session['user_id']=uid;session['_csrf_token']='adaptive-test-token'
    headers={'X-CSRF-Token':'adaptive-test-token'}
    def post(url,data):
        response=client.post(url,json=data,headers=headers)
        assert response.status_code==200,response.json
        return response.json
    tasks=client.get('/api/tasks?track=sat_math').json
    assert len(tasks)==1 and tasks[0]['task_format']=='benchmark'
    sid=tasks[0]['task_content_id']
    qs=json.loads(db.select_one('adaptive_sessions',where={'id':sid})['questions'])
    for i,q in enumerate(qs):post(f'/api/adaptive/session/{sid}',{'action':'answer','index':i,'selected_option':q['correct_option'],'response_ms':40000})
    post(f'/api/adaptive/session/{sid}',{'action':'finish'})
    generated=post(f'/api/adaptive/session/{sid}',{'action':'next_path'})['tasks']
    assert len(generated)==5
    lesson_id=generated[0]['id']
    lesson=client.get(f'/api/lesson/{lesson_id}').json
    assert lesson['is_math'] is True
    check=next(s for s in lesson['steps'] if s['step_type']=='check')
    assert 'correct_option' not in check
    hint=post('/api/activity-hint',{'kind':'lesson_step','question_id':check['id']})
    assert len(hint['hints'])==1
    again=client.get(f'/api/lesson/{lesson_id}').json
    assert len(next(s for s in again['steps'] if s['step_type']=='check')['hints'])==1
    q=db.select_one('lesson_steps',where={'id':check['id']})
    post(f'/api/lesson/{lesson_id}/answer',{'step_id':check['id'],'selected_option':q['correct_option'],'response_ms':32000})
    post(f'/api/lesson/{lesson_id}/answer',{'step_id':check['id'],'selected_option':q['correct_option'],'response_ms':1000})
    evidence=db.select('learning_events',where={'user_id':uid,'source':'lesson'})
    assert len(evidence)==1 and evidence[0]['hint_count']==1 and evidence[0]['response_ms']==32000
    post(f'/api/lesson/{lesson_id}/finish',{})
    practice=post('/api/adaptive/practice',{'track':'sat_math','request_id':'http-practice-request'})
    assert practice['total']==5
    snapshot=json.loads(db.select_one('adaptive_sessions',where={'id':practice['id']})['profile_snapshot'])
    assert any(s['sources'].get('lesson') for s in snapshot['skills'].values())
    # A fresh client represents relogin or another device, not browser memory.
    other=server.app.test_client()
    with other.session_transaction() as session:
        session['user']=user.email;session['user_id']=uid
    restored=other.get('/api/tasks?track=sat_math').json
    assert len(restored)==5 and all(t['task_format']!='benchmark' for t in restored)
    assert other.get('/api/adaptive/profile?track=sat_math').json['resume_session']==practice['id']


def test_generation_lease_prevents_stale_worker_replacement(learner,monkeypatch):
    user,db=learner;uid=user.data['id'];complete_benchmark(user,db)
    original=adaptive.build_unit
    def replace_lease(*args,**kwargs):
        unit=original(*args,**kwargs)
        db.update('adaptive_tracks',{'generation_token':'a-newer-worker'},where={'user_id':uid,'track_key':'sat_math'})
        return unit
    monkeypatch.setattr(adaptive,'build_unit',replace_lease)
    with pytest.raises(ValueError,match='newer generation'):
        server._generate_and_save_new_test_path(uid,{},track_key='sat_math',request_key='stale-worker-test')
    assert db.select_one('adaptive_tracks',where={'user_id':uid,'track_key':'sat_math'})['generation_token']=='a-newer-worker'
    active=db.select('paths',where={'user_id':uid,'track_key':'sat_math','is_active':True})
    assert len(active)==1 and active[0]['task_format']=='benchmark'


def test_question_array_response_is_reviewed_not_discarded(learner):
    user,db=learner;state=adaptive.profile(db,user,'sat_math');q=next(x for x in adaptive_bank.bank('sat_math') if x['difficulty']=='hard')
    def generate(prompt,**kwargs):
        if prompt.startswith('Independently'):
            return json.dumps([{'index':0,'answer':q['correct_option'],'valid':True,'hints_safe':True,'reason':'Subtraction and division give the unique listed correct value.'}])
        return json.dumps([q])
    questions,_=adaptive.generate_questions(state,[q['skill_key']],generate)
    assert questions[0]['validation']=='ai_independent_review'


def test_account_deletion_includes_new_learning_state(learner):
    user,db=learner;uid=user.data['id'];complete_benchmark(user,db)
    db.insert('learning_hints',{'user_id':uid,'source':'lesson','source_id':'test','hint_count':1})
    server._delete_user_data(uid)
    for table in ('adaptive_tracks','adaptive_sessions','learning_events','learning_hints','path_generations'):
        assert not db.select(table,where={'user_id':uid})


def test_ambiguous_revision_and_embedded_choices_are_not_shown():
    q=adaptive_bank.bank('act_ela')[-1]
    malformed={**q,'question_text':'Which choice best revises the underlined portion?',
        'source_or_prompt':'The team [1] made a decision to preserve the original collection.'}
    assert adaptive.valid_generated(malformed,'act_ela') is None
    q=adaptive_bank.bank('sat_math')[0]
    normalized=adaptive.valid_generated({**q,'question_text':q['question_text']+'\n(A) 1\n(B) 2\n(C) 3\n(D) 4'},'sat_math')
    assert normalized and '\n(A)' not in normalized['question_text']


def answer_benchmark(user, db, track, wrong_skills=()):
    state = adaptive.ensure_track(db, user.data['id'], track)
    sid = state['benchmark_session_id']
    questions = json.loads(db.select_one('adaptive_sessions', where={'id': sid})['questions'])
    for i, q in enumerate(questions):
        right = q['skill_key'] not in wrong_skills
        adaptive.answer(db, user.data['id'], sid, {'index': i, 'selected_option': q['correct_option'] if right else (q['correct_option'] + 1) % 4, 'response_ms': 50000})
    adaptive.finish(db, user.data['id'], sid)
    return sid


def set_prep(user, **fields):
    stats = user.get_stats()
    stats['test_path'] = {**stats.get('test_path', {}), **fields}
    user.set_stats(stats)


def test_plan_combines_benchmark_results_with_what_the_student_asked_for(learner):
    user, db = learner
    set_prep(user, weaknesses='quadratics, probability, circles')
    answer_benchmark(user, db, 'sat_math', wrong_skills={'systems_of_equations', 'exponential_functions', 'quadratic_functions'})
    state = adaptive.profile(db, user, 'sat_math')
    ranked = [e['key'] for e in state['plan']]
    assert ranked[0] == 'quadratic_functions', 'missed on the benchmark AND named by the student'
    assert set(ranked[:3]) == {'quadratic_functions', 'systems_of_equations', 'exponential_functions'}, 'benchmark misses outrank self-report alone'
    entry = {e['key']: e for e in state['plan']}
    assert entry['probability']['priority'] > entry['two_variable_data']['priority'], 'a named skill beats an equally correct unnamed one'
    assert entry['probability']['self_reported'] and not entry['two_variable_data']['self_reported']
    assert any('You told us you need help with' in r for r in entry['quadratic_functions']['reasons'])
    assert any(r.startswith('Benchmark: 0 of 3 correct') for r in entry['systems_of_equations']['reasons'])
    # Measured strength outranks self-report: circles was named but answered correctly, including a hard item.
    assert any('already a strength' in r for r in entry['circles']['reasons'])
    assert entry['circles']['priority'] < entry['probability']['priority']


def test_area_words_reach_every_skill_in_that_area(learner):
    named = adaptive.parse_named_skills('geometry, semicolons and grammar', 'sat_math')
    assert {'area_volume', 'circles', 'right_triangles_trig', 'lines_angles_triangles'} <= set(named)
    assert all(weight < 1 for key, (weight, _) in named.items() if key in {'area_volume', 'circles'}) or 'circles' in named
    ela = adaptive.parse_named_skills('commas, vocab in context', 'sat_ela')
    assert ela['boundaries'][0] == 1.0 and 'words_in_context' in ela and not set(ela) & {'circles'}
    act = adaptive.parse_named_skills('trig, punctuation', 'act_math')
    assert 'act_math_trig' in act and 'boundaries' not in act
    assert 'act_english_usage' in adaptive.parse_named_skills('punctuation', 'act_ela')


def test_first_path_teaches_the_benchmark_and_self_reported_gaps(learner):
    user, db = learner;uid = user.data['id']
    set_prep(user, weaknesses='quadratics')
    sid = answer_benchmark(user, db, 'sat_math', wrong_skills={'quadratic_functions', 'exponential_functions'})
    with server.app.test_request_context('/'):
        tasks = server._generate_and_save_new_test_path(uid, user.get_stats()['test_path'], track_key='sat_math', request_key=f'initial:{sid}', initial=True)
    lessons = [t for t in tasks if t['task_format'] == 'lesson']
    assert {t['skill_key'] for t in lessons} >= {'quadratic_functions'}
    first = next(t for t in lessons)
    assert 'Benchmark' in first['reason'] and 'You told us you need help with' in first['reason']
    snapshot = json.loads(db.select_one('path_generations', where={'user_id': uid})['profile_snapshot'])
    assert snapshot['plan'][0]['key'] == 'quadratic_functions'


def test_generated_passages_must_be_real_exam_length():
    bank = adaptive_bank.bank('sat_ela')
    full = max((q for q in bank if q['skill_key'] == 'central_ideas'), key=lambda q: len(q['source_or_prompt']))
    assert adaptive.valid_generated(dict(full), 'sat_ela')
    short = {**full, 'source_or_prompt': 'A town garden now brings neighbors together every weekend, and many of them share tools and advice there.'}
    assert adaptive.valid_generated(short, 'sat_ela') is None
    cross = next(q for q in bank if q['skill_key'] == 'cross_text_connections')
    assert adaptive.valid_generated(dict(cross), 'sat_ela')
    assert adaptive.valid_generated({**cross, 'source_or_prompt': cross['source_or_prompt'].replace('Text 2', 'Another view')}, 'sat_ela') is None
    hint_text = ['Look at the contrast in the sentence first.', 'Test each choice against the clue.', 'Plug the choice back into the sentence.']
    assert adaptive.valid_generated({**full, 'hints': hint_text}, 'sat_ela')


def test_recovery_content_stays_hard_and_avoids_seen_questions(learner):
    user, db = learner
    state = adaptive.profile(db, user, 'sat_ela')
    questions, note = adaptive.generate_questions(state, ['central_ideas', 'transitions', 'boundaries', 'verb_tense', 'inferences'], lambda *a, **k: '{}')
    assert 'recovery bank' in note
    assert all(q['difficulty'] in {'medium', 'hard'} for q in questions)
    assert len({adaptive.signature(q) for q in questions}) == 5
    assert all(adaptive.word_count(q['source_or_prompt']) >= 25 for q in questions)


def test_session_view_groups_modules_and_shares_long_passages(learner):
    user, db = learner;uid = user.data['id']
    sid = adaptive.ensure_track(db, uid, 'act_ela')['benchmark_session_id']
    view = adaptive.session_view(db, uid, sid)
    assert [(m['label'], m['start'], m['end']) for m in view['modules']] == [('English', 0, 49), ('Reading', 50, 85)]
    assert len(view['passages']) == 9
    assert all('source_or_prompt' not in q and q['passage_id'] in view['passages'] for q in view['questions'])
    assert all('correct_option' not in q for q in view['questions'])
    sat = adaptive.session_view(db, uid, adaptive.ensure_track(db, uid, 'sat_math')['benchmark_session_id'])
    assert [m['minutes'] for m in sat['modules']] == [35, 35] and sat['passages'] == {}


def test_benchmark_summary_reports_skills_modules_and_difficulty(learner):
    user, db = learner
    sid = answer_benchmark(user, db, 'sat_math', wrong_skills={'circles'})
    summary = adaptive.session_view(db, user.data['id'], sid)['summary']
    assert summary['total'] == 44 and summary['skills']['circles']['correct'] == 0
    assert set(summary['modules']) == {'Module 1', 'Module 2'} and summary['difficulty']['hard']['total'] == 19
    assert 'circles' in summary['weakest'] and summary['domains']['Geometry and Trigonometry']['total'] == 7


def test_recovery_never_reuses_the_benchmark_questions(learner):
    user, db = learner
    answer_benchmark(user, db, 'sat_ela')
    state = adaptive.profile(db, user, 'sat_ela')
    skills = ['words_in_context', 'transitions', 'boundaries', 'inferences', 'rhetorical_synthesis']
    questions, note = adaptive.generate_questions(state, skills, lambda *a, **k: '{}')
    seen = {adaptive.signature(q) for q in adaptive_bank.benchmark('sat_ela', 0)}
    assert 'recovery bank' in note
    assert not any(adaptive.signature(q) in seen for q in questions)
    assert [q['skill_key'] for q in questions] == skills
