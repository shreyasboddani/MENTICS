import pytest
import learning

@pytest.mark.parametrize('exam', ['sat', 'act', 'both'])
@pytest.mark.parametrize('subject,allowed_subjects', [('math', {'Math'}), ('ela', {'Reading and Writing', 'English', 'Reading'})])
def test_subject_catalog_and_generated_plan_stay_in_selected_lane(exam, subject, allowed_subjects):
    keys = learning.skill_catalog(exam, subject)
    assert keys
    assert all(learning.SKILL_TAXONOMY[key][1] in allowed_subjects for key in keys)
    if exam != 'both':
        assert all(learning.SKILL_TAXONOMY[key][3] == exam.upper() for key in keys)
    profile = {'focus': exam, 'subject_focus': subject, 'skill_options': keys, 'weaknesses': 'science, grammar, quadratics', '_mastery_rows': []}
    # Simulate a planner that ignores both the subject and exam restrictions.
    plan = learning._normalize_plan({'nodes': [{'skill_key': 'act_science_data', 'title': 'Wrong science lesson', 'syllabus': ['Read a graph of the experiment.', 'Compare the experimental treatments.']}] * 5}, learning.CANONICAL_SHAPE, profile)
    for node in plan['nodes']:
        if node['node_type'] == 'boss_battle':
            continue  # Existing full-exam checkpoint remains explicit.
        assert node['skill']['skill_key'] in keys
        assert node['title'] != 'Wrong science lesson'
    fallback = learning._normalize_plan({}, learning.CANONICAL_SHAPE, profile)
    assert all(node['skill']['skill_key'] in keys for node in fallback['nodes'] if node['node_type'] != 'boss_battle')


def test_all_subjects_preserves_original_catalog():
    assert learning.skill_catalog('sat') == learning.skill_catalog('sat', 'all')
    assert 'act_science_data' in learning.skill_catalog('act', 'all')
    assert 'act_science_data' not in learning.skill_catalog('act', 'ela')
