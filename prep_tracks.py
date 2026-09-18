"""Original, immediately usable starter units; no model call during setup."""
import learning
from prep_starter_bank import BANK

TRACKS = ('sat_math', 'sat_ela', 'act_math', 'act_ela')


def starter_unit(track):
    exam, subject = track.split('_')
    questions = BANK[exam][subject]
    # Teach two complementary tactics, practise both, and finish inside this section.
    indexes = [0, 1] if subject == 'math' else ([1, 0] if exam == 'sat' else [1, 2])
    keys = {
        'sat_math': ['linear_equations_one', 'percentages'],
        'sat_ela': ['boundaries', 'transitions'],
        'act_math': ['act_math_prealgebra', 'act_math_prealgebra'],
        'act_ela': ['act_english_usage', 'act_reading_detail'],
    }[track]
    label = f"{exam.upper()} {'Math' if subject == 'math' else 'ELA'}"
    nodes = []
    for pos, idx in enumerate(indexes):
        q = questions[idx]
        skill = learning.resolve_skill(keys[pos])
        def question(item):
            return dict(source_or_prompt='', question_text=item['prompt'], options=item['options'],
                        correct_option=item['answer'], explanation=item['explanation'],
                        skill_key=skill['skill_key'], difficulty='easy')
        teaching = {'intro': q['tip'], 'cards': [{'title': q['skill'], 'body': q['tip'], 'worked_example': q['prompt'] + '\n\n' + q['explanation'], 'takeaway': q['tip'], 'trap': 'Check exactly what the question asks before choosing.'}], 'recap': q['tip']}
        base = dict(skill=skill, objective=q['tip'], reason='A starter skill to establish your baseline. Your results refine the next unit.')
        nodes.append(dict(base, node_type='lesson', xp_reward=learning.XP_BY_NODE['lesson'], title=q['skill'], teaching=teaching, steps=learning._interleave_lesson(teaching, [])))
        practice = [item for item in questions if item['skill'] == q['skill'] and item is not q][:3]
        nodes.append(dict(base, node_type='practice_sprint', xp_reward=learning.XP_BY_NODE['practice_sprint'], title=f"Practise {q['skill'].lower()}", questions=[question(item) for item in practice]))
    review = []
    for node in nodes:
        review.extend(node.get('questions', []))
    nodes.append(dict(nodes[-1], node_type='quiz', xp_reward=learning.XP_BY_NODE['quiz'], title=f'{label} starter checkpoint', questions=review, reason='Review only the skills introduced in this section.'))
    return {'unit_title': f'{label}: your starting point', 'nodes': nodes}
