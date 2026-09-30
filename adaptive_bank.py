"""Full-length diagnostic benchmarks and hard recovery content.

Benchmarks follow real test structure and length:

* SAT Math: 2 modules x 22 questions (44)
* SAT Reading and Writing: 2 modules x 27 questions (54), 50-130 word passages
* ACT Math: 45 questions, easy to hard
* ACT English (50, five passages) and Reading (36, four passages)

Math items are generated from templates with computed answers, so each student
sees different numbers. Reading and writing items are fixed and hand-reviewed.
Results are provisional evidence, never an official scaled-score estimate.
"""
import random
import re

import learning
from bench_act_english import english_items
from bench_act_math import ACT_MATH
from bench_act_reading import reading_items
from bench_common import realize
from bench_sat_math import SAT_EXTRA, SAT_MATH
from bench_sat_rw_extra import EXTRA as SAT_RW_EXTRA
from bench_sat_rw_m1 import M1
from bench_sat_rw_m2 import M2

JAMES_LU = {'name': 'James Lu SAT Prep', 'url': 'https://www.skool.com/sat/about',
            'note': 'Desmos and grammar emphasis informed by James Lu’s public SAT prep. Original Mentics example; not affiliated.'}

ACT_DOMAINS = {'act_math_prealgebra': 'Number, Algebra and Statistics', 'act_math_coordinate': 'Coordinate Geometry and Functions',
               'act_math_plane_geometry': 'Plane Geometry', 'act_math_trig': 'Trigonometry',
               'act_english_usage': 'Usage and Mechanics', 'act_english_rhetoric': 'Rhetorical Skills',
               'act_reading_detail': 'Reading'}

MODULES = {
    'sat_math': {1: 'Module 1', 2: 'Module 2'},
    'sat_ela': {1: 'Module 1', 2: 'Module 2'},
    'act_math': {1: 'Mathematics'},
    'act_ela': {1: 'English', 2: 'Reading'},
}
# Published timing, shown as guidance only (never enforced): minutes per module.
MINUTES = {'sat_math': {1: 35, 2: 35}, 'sat_ela': {1: 32, 2: 32}, 'act_math': {1: 50}, 'act_ela': {1: 35, 2: 40}}


def domain(skill):
    if skill in ACT_DOMAINS:
        return ACT_DOMAINS[skill]
    if skill in {'central_ideas', 'command_of_evidence_text', 'command_of_evidence_quant', 'inferences'}:
        return 'Information and Ideas'
    if skill in {'words_in_context', 'text_structure_purpose', 'cross_text_connections'}:
        return 'Craft and Structure'
    if skill in {'transitions', 'rhetorical_synthesis'}:
        return 'Expression of Ideas'
    resolved = learning.resolve_skill(skill)
    return {'algebra': 'Algebra', 'advanced_math': 'Advanced Math', 'data_analysis': 'Problem Solving and Data Analysis',
            'geometry': 'Geometry and Trigonometry', 'grammar': 'Standard English Conventions',
            'reading': 'Reading'}.get(resolved.get('domain'), resolved.get('subject', 'Test Strategy'))


def credit(track, skill):
    return JAMES_LU if track.startswith('sat') and skill in {'desmos_strategy', 'systems_of_equations', 'nonlinear_equations', 'quadratic_functions', 'boundaries', 'subject_verb_agreement', 'verb_tense', 'form_structure_sense'} else None


def item(skill, difficulty, prompt, options, answer, explanation, hints, *, source='', subskill=None, misconceptions=None):
    return {'skill_key': skill, 'subskill': subskill or skill, 'domain': domain(skill), 'difficulty': difficulty,
            'question_text': prompt, 'source_or_prompt': source, 'options': [str(x) for x in options],
            'correct_option': answer, 'explanation': explanation, 'hints': hints,
            'strategy': hints[1], 'fastest_method': hints[2],
            'misconceptions': misconceptions or ['Recheck the setup and requested quantity.' if i != answer else '' for i in range(4)],
            'validation': 'reviewed_bank'}


def shuffle_options(question, seed):
    # Some explanations name a choice letter. Keep their reviewed order rather
    # than silently making that explanation incorrect. ACT English keeps the
    # test's fixed answer order (NO CHANGE first).
    if question.get('fixed_order'):
        # Keep NO CHANGE first, as on the test, but vary where the right answer
        # sits among the remaining choices so a pattern cannot be guessed.
        options = question['options']
        if options[0] != 'NO CHANGE':
            return dict(question)
        order = [1, 2, 3]
        random.Random(seed).shuffle(order)
        order = [0] + order
        result = dict(question)
        result['options'] = [options[i] for i in order]
        result['correct_option'] = order.index(question['correct_option'])
        result['misconceptions'] = [question['misconceptions'][i] for i in order]
        return result
    text = ' '.join(str(question.get(k, '')) for k in ('explanation', 'fastest_method', 'strategy', 'hints'))
    if re.search(r'\b(?:[Oo]ption|[Cc]hoice|[Aa]nswer)\s+[A-D]\b|\b[A-D]\s+(?:is|would|matches)\b', text):
        return dict(question)
    order = list(range(4))
    random.Random(seed).shuffle(order)
    result = dict(question)
    result['options'] = [question['options'][i] for i in order]
    result['correct_option'] = order.index(question['correct_option'])
    if len(question.get('misconceptions', [])) == 4:
        result['misconceptions'] = [question['misconceptions'][i] for i in order]
    return result


def _copy(q):
    copy = dict(q)
    for key in ('options', 'hints', 'misconceptions'):
        copy[key] = list(q[key])
    return copy


def _finish(track, questions, seed):
    finished = []
    for i, q in enumerate(questions):
        q = _copy(q)
        q.pop('number', None)
        q['domain'] = domain(q['skill_key'])
        q['attribution'] = credit(track, q['skill_key'])
        finished.append(shuffle_options(q, seed * 101 + i * 17))
    return finished


def _templates(track, seed, extras=False):
    if track == 'sat_math':
        return [realize(e, seed) for e in SAT_MATH + (SAT_EXTRA if extras else [])]
    return [realize(e, seed) for e in ACT_MATH]


def _authored(track, extras=False):
    if track == 'sat_ela':
        return M1 + M2 + (SAT_RW_EXTRA if extras else [])
    return english_items() + reading_items()


def benchmark(track, seed=0):
    """The full-length, unaided diagnostic for one section, in test order."""
    questions = _templates(track, seed) if track.endswith('math') else _authored(track)
    return _finish(track, questions, seed)


def bank(track, seed=0):
    """Hard, reviewed recovery content used when generated questions fail checks."""
    questions = _templates(track, seed, extras=True) if track.endswith('math') else _authored(track, extras=True)
    return _finish(track, questions, seed)
