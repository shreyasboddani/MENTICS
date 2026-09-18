import inspect
import json

import pytest
import app as app_module
import prep_tracks
from dbhelper import DatabaseHandler
from userhelper import User


@pytest.fixture
def learner(tmp_path, monkeypatch):
    database = DatabaseHandler(str(tmp_path / 'tracks.db'))
    monkeypatch.setattr(app_module, 'db', database)
    app_module.init_db()
    database.insert('users', {'email': 'tracks@example.test', 'password': 'unused',
                             'name': 'Track Test', 'stats': '{}', 'onboarding_completed': True})
    user = User(database, 'tracks@example.test')
    monkeypatch.setattr(app_module.learning, 'build_unit', lambda *a, **k: pytest.fail('Setup must not call AI'))
    return user, database


def test_all_tracks_exist_and_setup_preserves_completed_work(learner):
    user, db = learner
    prep = app_module._ensure_prep_tracks(user)
    assert set(prep['tracks']) == set(prep_tracks.TRACKS)
    initial = db.select('paths', where={'user_id': user.data['id']})
    assert len(initial) == 20
    first = initial[0]
    db.update('paths', {'is_completed': True}, where={'id': first['id']})
    with app_module.app.test_request_context('/dashboard/test-path-builder', method='POST', data={
        'test_focus': 'act', 'weaknesses': 'Reading pace', 'current_act_math': '25',
    }):
        response = inspect.unwrap(app_module.test_path_builder)(user)
        assert response.status_code == 302
    app_module._ensure_prep_tracks(user)
    current = db.select('paths', where={'user_id': user.data['id']})
    assert {r['id'] for r in current} == {r['id'] for r in initial}
    assert db.select_one('paths', where={'id': first['id']})['is_completed']
    assert user.get_stats()['test_path']['tracks']['act_ela']['current_act_math'] == '25'
    for key in prep_tracks.TRACKS:
        with app_module.app.test_request_context(f'/api/tasks?category=Test%20Prep&track={key}'):
            result = inspect.unwrap(app_module.api_tasks)(user)
            tasks = result.get_json()
            assert len(tasks) == 5
            assert all(t['track_key'] == key for t in tasks)
    assert len(db.select('paths', where={'is_active': True})) == 20


def test_legacy_content_and_results_remain_in_their_lane(learner):
    user, db = learner
    ids = []
    for skill, subject in [('linear_equations_one', 'Math'), ('boundaries', 'Reading and Writing')]:
        ids.append(db.insert('paths', {'user_id': user.data['id'], 'category': 'Test Prep',
            'skill_key': skill, 'subject': subject, 'description': 'Existing work',
            'task_order': 1, 'is_active': True, 'is_completed': True, 'is_user_added': False}))
    app_module._ensure_prep_tracks(user)
    assert db.select_one('paths', where={'id': ids[0]})['track_key'] == 'sat_math'
    assert db.select_one('paths', where={'id': ids[1]})['track_key'] == 'sat_ela'
    assert all(db.select_one('paths', where={'id': i})['is_completed'] for i in ids)


def test_progress_checks_and_regeneration_are_track_scoped(learner):
    user, db = learner
    app_module._ensure_prep_tracks(user)
    math = db.select('paths', where={'track_key': 'sat_math'}, order_by='task_order')
    db.update('paths', {'is_completed': True}, where={'id': math[0]['id']})
    assert not app_module._has_incomplete_earlier_task(user.data['id'], math[1])
    assert app_module._has_incomplete_earlier_task(user.data['id'], math[2])
    with app_module.app.test_request_context('/api/skip_task', method='POST', json={'taskId': math[1]['id']}):
        assert inspect.unwrap(app_module.api_skip_task)(user).get_json()['success']
    others = [r['id'] for r in db.select('paths', where={'is_active': True}) if r['track_key'] != 'sat_math']
    app_module._persist_unit(user.data['id'], prep_tracks.starter_unit('sat_math'), track_key='sat_math')
    assert all(db.select_one('paths', where={'id': i})['is_active'] for i in others)


def test_chat_receives_selected_track_and_keeps_separate_history(learner, monkeypatch):
    user, db = learner
    app_module._ensure_prep_tracks(user)
    def coach(history, stats, *args):
        assert stats['test_path']['active_track'] == 'act_ela'
        assert stats['test_path']['subject_focus'] == 'ela'
        assert len(stats['test_path']['tracks']) == 4
        return 'Active English and Reading advice'
    monkeypatch.setattr(app_module, '_get_test_prep_ai_chat_response', coach)
    with app_module.app.test_request_context('/api/chat?track=act_ela', method='POST', json={'history': [{'role': 'user', 'content': 'Explain punctuation'}]}):
        assert inspect.unwrap(app_module.api_chat)(user).get_json()['reply']
    row = db.select_one('chat_conversations', where={'user_id': user.data['id'], 'category': 'Test Prep:act_ela'})
    assert json.loads(row['history'])[-1]['content'] == 'Active English and Reading advice'


def test_builder_renders_with_empty_or_null_profile(learner):
    user, db = learner
    for profile in ({}, {'test_path': None}, {'test_path': {'test_focus': 'sat'}}):
        user.set_stats(profile)
        with app_module.app.test_request_context('/dashboard/test-path-builder?test_focus=sat&subject_focus=math'):
            response, status = inspect.unwrap(app_module.test_path_builder)(user)
            assert status == 200
            assert 'test-builder' in response


def test_first_visit_opens_exam_questionnaire(learner):
    user, _ = learner
    with app_module.app.test_request_context('/dashboard/test-path-view'):
        response = inspect.unwrap(app_module.test_path_view)(user)
        assert response.status_code == 302
        assert response.location.endswith('/dashboard/test-path-builder')


def test_quick_practice_is_graded_on_server_and_available_to_coach(learner):
    user, db = learner
    q = prep_tracks.BANK['sat']['math'][0]
    with app_module.app.test_request_context('/api/quick-practice', method='POST', json={
        'track': 'sat_math', 'answers': [{'id': 0, 'selected': q['options'][q['answer']], 'correct': False}],
    }):
        assert inspect.unwrap(app_module.save_quick_practice)(user).get_json()['saved']
    context = json.loads(app_module._prep_context(user.data['id'], {}))
    assert context['quick_practice'][0]['track'] == 'sat_math'
    assert context['quick_practice'][0]['results'][0]['correct'] is True
    with app_module.app.test_request_context('/api/quick-practice', method='POST', json={
        'track': 'sat_math', 'answers': [{'id': 999, 'selected': 'x'}],
    }):
        assert inspect.unwrap(app_module.save_quick_practice)(user)[1] == 400


def test_planner_context_focus_and_shape_are_limited_to_selected_section(learner, monkeypatch):
    user, db = learner
    app_module._ensure_prep_tracks(user)
    def build(profile, **kwargs):
        assert profile['focus'] == 'act'
        assert profile['subject_focus'] == 'ela'
        assert all(key.startswith('act_english') or key.startswith('act_reading') for key in profile['skill_options'])
        assert 'boss_battle' not in kwargs['shape']
        assert 'sat_math' in profile['cross_track_context']
        return prep_tracks.starter_unit('act_ela')
    monkeypatch.setattr(app_module.learning, 'build_unit', build)
    with app_module.app.test_request_context('/'):
        tasks = app_module._generate_and_save_new_test_path(user.data['id'], user.get_stats()['test_path'], track_key='act_ela')
    assert len(tasks) == 5
    assert all(t['track_key'] == 'act_ela' for t in tasks)


def test_persisted_assessment_uses_its_own_track_for_order(learner):
    user, db = learner
    app_module._ensure_prep_tracks(user)
    first = db.select_one('paths', where={'track_key': 'act_math', 'task_order': 1})
    db.update('paths', {'is_completed': True}, where={'id': first['id']})
    second = db.select_one('paths', where={'track_key': 'act_math', 'task_order': 2})
    question = db.select_one('sprint_questions', where={'sprint_id': second['task_content_id']})
    sql, _ = app_module._ASSESSMENT_SOURCES['sprint']
    assessment = db.execute_for_one(sql, (question['id'], user.data['id']))
    assert assessment['track_key'] == 'act_math'
    assert not app_module._has_incomplete_earlier_task(user.data['id'], assessment)
