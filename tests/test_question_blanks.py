"""Question contracts for sentence-completion SAT and ACT skills."""

import learning


def _question(source):
    return {
        "source_or_prompt": source,
        "question_text": "Which choice completes the text so that it conforms to the conventions of Standard English?",
        "options": ["is", "are", "were", "have been"],
        "correct_option": 0,
        "explanation": "The singular subject takes the singular verb. The other choices create agreement or tense errors.",
    }


def test_sentence_completion_question_requires_a_visible_blank():
    assert learning._valid_question(
        _question("A collection of maps from the archive displayed in the lobby."),
        needs_prompt=True,
        requires_blank=True,
    ) is None


def test_sentence_completion_question_with_blank_is_usable():
    question = learning._valid_question(
        _question("A collection of maps from the archive _____ displayed in the lobby."),
        needs_prompt=True,
        requires_blank=True,
    )

    assert question is not None
    assert "_____" in question["source_or_prompt"]


def test_vocab_and_grammar_skills_are_marked_as_blank_based():
    assert learning._skill_requires_blank("words_in_context")
    assert learning._skill_requires_blank("boundaries")
    assert not learning._skill_requires_blank("linear_functions")
