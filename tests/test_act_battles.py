import inspect
import json
from datetime import timedelta
from fractions import Fraction

import pytest
import app as app_module
import act_arena
from dbhelper import DatabaseHandler
from userhelper import User


@pytest.fixture
def arena(tmp_path, monkeypatch):
    database = DatabaseHandler(str(tmp_path / 'act-arena.db'))
    monkeypatch.setattr(app_module, 'db', database)
    monkeypatch.setattr(app_module, 'gemini_api_key', None)
    app_module.init_db()
    def user(number):
        email = f'player{number}@example.test'
        database.insert('users', {'email': email, 'password': 'unused', 'stats': '{}', 'name': f'Player {number}', 'onboarding_completed': True})
        return User(database, email)
    def queue(player, exam):
        with app_module.app.test_request_context('/api/sat-battles/queue', method='POST', json={'exam': exam}):
            return inspect.unwrap(app_module.queue_sat_battle)(player).get_json()
    return database, user, queue


def test_matchmaking_never_pairs_different_exams(arena):
    database, user, queue = arena
    sat, act, act_rival, sat_rival = [user(i) for i in range(4)]
    sat_waiting = queue(sat, 'SAT')
    act_waiting = queue(act, 'ACT')
    assert sat_waiting['id'] != act_waiting['id']
    assert act_waiting['status'] == 'waiting'
    assert act_waiting['exam'] == 'ACT'
    act_live = queue(act_rival, 'ACT')
    assert act_live['id'] == act_waiting['id']
    assert act_live['exam'] == 'ACT'
    assert act_live['status'] == 'active'
    assert [q['section'] for q in act_live['questions']] == ['Math'] * 3 + ['Reading', 'English']
    assert all('correct_option' not in q and 'explanation' not in q for q in act_live['questions'])
    sat_live = queue(sat_rival, 'SAT')
    assert sat_live['id'] == sat_waiting['id']
    assert sat_live['exam'] == 'SAT'
    # Recovery cannot silently relabel an existing match when a different exam is requested.
    recovered = queue(act, 'SAT')
    assert recovered['id'] == act_live['id'] and recovered['exam'] == 'ACT'
    stored = database.select_one('sat_battles', where={'id': act_live['id']})
    assert all(q['exam'] == 'ACT' for q in json.loads(stored['questions']))
    for player in (act, act_rival):
        with app_module.app.test_request_context('/api/sat-battles/submit', method='POST', json={'answers': [{'question_index': i, 'selected_option': 0} for i in range(5)]}):
            result = inspect.unwrap(app_module.submit_sat_battle)(player, act_live['id']).get_json()
    assert result['exam'] == 'ACT' and result['status'] == 'complete'
    assert len(result['answerKey']) == 5
    assert len(result['questionReview']) == 5
    assert database.select_one('sat_battle_stats', where={'user_id': act.data['id']})['battles_played'] == 1
    evidence=database.select('learning_events',where={'user_id':act.data['id'],'source':'battle'})
    assert len(evidence)==5
    assert all(row['track_key'].startswith('act_') for row in evidence)


def test_act_bot_drop_in_keeps_exam_and_clock(arena):
    database, user, queue = arena
    player = user(0)
    waiting = queue(player, 'ACT')
    database.update('sat_battles', {'created_at': (app_module._utc_now() - timedelta(seconds=31)).isoformat()}, where={'id': waiting['id']})
    live = app_module._battle_payload(database.select_one('sat_battles', where={'id': waiting['id']}), player.data['id'])
    assert live['exam'] == 'ACT' and live['isBotBattle']
    assert live['durationSeconds'] == app_module._battle_clock_by_tier('ACT')['bronze']
    assert all(q['skill'].startswith('ACT ') for q in live['questions'])


@pytest.mark.parametrize('rank', ['bronze', 'silver', 'gold', 'platinum', 'diamond', 'master', 'grandmaster'])
def test_act_training_supports_each_rank_and_keeps_rating_private(arena, rank):
    database, user, _ = arena
    player = user(0)
    with app_module.app.test_request_context('/api/sat-battles/train', method='POST', json={'exam': 'ACT', 'rank': rank}):
        result = inspect.unwrap(app_module.train_with_sat_battle_bot)(player).get_json()
    assert result['exam'] == 'ACT' and result['difficulty'] == rank and result['mode'] == 'training'
    assert result['durationSeconds'] == app_module._battle_clock_by_tier('ACT')[rank]
    assert not database.select_one('sat_battle_stats', where={'user_id': player.data['id']})


@pytest.mark.parametrize('exam', ['GRE', '', [], 1, None])
@pytest.mark.parametrize('handler', ['queue_sat_battle', 'train_with_sat_battle_bot'])
def test_invalid_exam_is_rejected_without_creating_a_round(arena, exam, handler):
    database, user, _ = arena
    player = user(0)
    with app_module.app.test_request_context('/api/sat-battles/queue', method='POST', json={'exam': exam}):
        response, status = inspect.unwrap(getattr(app_module, handler))(player)
    assert status == 400
    assert 'Choose SAT or ACT' in response.get_json()['error']
    assert not database.select_one('sat_battles')


def test_act_reserve_answer_choices_are_distinct_for_all_parameters(monkeypatch):
    class FixedRandom:
        def __init__(self, n): self.n = n
        def randint(self, *_args): return self.n
        def shuffle(self, _items): pass
    for n in range(3, 10):
        monkeypatch.setattr(act_arena.random, 'SystemRandom', lambda: FixedRandom(n))
        for rank in ['bronze', 'silver', 'gold', 'platinum', 'diamond', 'master', 'grandmaster']:
            questions = act_arena.fallback_questions(rank)
            assert len(questions) == 5
            for q in questions:
                assert len(set(q['options'])) == 4, (rank, n, q)
                numeric = []
                for option in q['options']:
                    try: numeric.append(Fraction(option))
                    except (ValueError, ZeroDivisionError): pass
                assert len(numeric) == len(set(numeric)), (rank, n, q)
                assert q['exam'] == 'ACT'
            if rank in {'diamond', 'master', 'grandmaster'}:
                assert Fraction(questions[1]['options'][0]) == Fraction(n*(n-1), n*(n-1)+2*n*(n+['diamond','master','grandmaster'].index(rank)+2))


def test_act_generator_uses_act_section_prompts(arena, monkeypatch):
    _, _, _ = arena
    calls = []
    reserve = act_arena.fallback_questions('bronze')
    monkeypatch.setattr(app_module, 'gemini_api_key', 'test-only')
    monkeypatch.setattr(app_module, '_get_gemini_client', lambda: None)
    def generate(prompt, **kwargs):
        calls.append((prompt, kwargs))
        import re
        slot = int(re.search(r'Slot: (\d)', prompt).group(1)) - 1
        return json.dumps({'question': reserve[slot]})
    monkeypatch.setattr(app_module, '_generate_arena_text', generate)
    result = app_module._generate_ai_battle_questions('bronze', exam='ACT')
    assert result and len(result) == 5
    assert all('original ACT item' in prompt for prompt, _ in calls)
    assert all('Digital SAT assessment writer' not in options['system_instruction'] for _, options in calls)
    assert result[3]['section'] == 'Reading' and result[4]['section'] == 'English'
    assert all(q['exam'] == 'ACT' and q['source'] == 'gemini' for q in result)
