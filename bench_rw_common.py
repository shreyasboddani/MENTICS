"""Builders for hand-authored Reading and Writing benchmark items.

Authors list the correct choice first; the bank shuffles deterministically.
Passage lengths follow the digital SAT (roughly 25 to 150 words per stimulus).
"""

STEMS = {
    'words_in_context': 'Which choice completes the text with the most logical and precise word or phrase?',
    'transitions': 'Which choice completes the text with the most logical transition?',
    'inferences': 'Which choice most logically completes the text?',
    'central_ideas': 'Which choice best states the main idea of the text?',
    'boundaries': 'Which choice completes the text so that it conforms to the conventions of Standard English?',
    'subject_verb_agreement': 'Which choice completes the text so that it conforms to the conventions of Standard English?',
    'pronouns_modifiers': 'Which choice completes the text so that it conforms to the conventions of Standard English?',
    'verb_tense': 'Which choice completes the text so that it conforms to the conventions of Standard English?',
    'form_structure_sense': 'Which choice completes the text so that it conforms to the conventions of Standard English?',
}

HINTS = {
    'words_in_context': ['Cover the blank and predict a word from the clues in the sentence.',
                         'Look for contrast or cause words, and for the detail that defines the blank.',
                         'Plug each choice back in; the right word fits every clue, not just one.'],
    'transitions': ['Name the relationship between the sentence before the blank and the one after it.',
                    'Decide whether the ideas contrast, continue, give an example, or show a result.',
                    'Match that relationship to the choice and ignore how smooth each one sounds.'],
    'inferences': ['Restate what the passage has already established.',
                   'The right answer follows directly from those facts without adding new claims.',
                   'Eliminate choices that overreach or contradict a stated detail.'],
    'central_ideas': ['Read for what the whole text is doing, not just one detail.',
                      'The main idea must cover every key sentence without adding claims.',
                      'Eliminate choices that are too narrow, too broad, or not stated.'],
    'text_structure_purpose': ['Ask what each part of the text does, not only what it says.',
                               'Notice shifts such as “however”, a turn to evidence, or a change in time.',
                               'Choose the choice that describes the job of the sentence or text within the whole.'],
    'cross_text_connections': ['Summarize each text’s main claim in a few words.',
                               'Decide whether the texts agree, disagree, qualify or explain one another.',
                               'Choose the answer that stays faithful to both authors’ actual statements.'],
    'command_of_evidence_text': ['Identify exactly what claim or hypothesis needs support or weakening.',
                                 'The right choice addresses the claim directly, not something nearby.',
                                 'Eliminate choices that are true but irrelevant, or that reverse the direction asked.'],
    'command_of_evidence_quant': ['Read the claim first, then look only at the data it needs.',
                                  'Check that the choice uses the right rows, columns and units.',
                                  'Eliminate choices that report accurate numbers that do not address the claim.'],
    'boundaries': ['Check whether each side of the blank could stand alone as a sentence.',
                   'Two complete sentences need a period, a semicolon or a comma with a conjunction.',
                   'A list, explanation or pair of commas follows different rules; match the structure.'],
    'subject_verb_agreement': ['Find the grammatical subject and cross out phrases between it and the verb.',
                               'Decide whether the subject is singular or plural.',
                               'Choose the verb form that matches the subject and the sentence’s time frame.'],
    'pronouns_modifiers': ['Ask who or what the pronoun or opening phrase must refer to.',
                           'A modifier must sit next to the word it describes.',
                           'Choose the option that makes the referent unmistakable.'],
    'verb_tense': ['Put the events on a timeline using the clues in the sentence.',
                   'Look for words like “by the time” or “already” that signal which event came first.',
                   'Choose the tense that preserves the order of events.'],
    'form_structure_sense': ['Look at the words before and after the blank for a required form or pattern.',
                             'Check for parallel items, possessives, or a clause that needs a subject and verb.',
                             'Read the sentence aloud with each choice and listen for a structural mismatch.'],
    'rhetorical_synthesis': ['Reread the goal in the question before looking at the notes.',
                             'Use only the notes that accomplish that specific goal.',
                             'Eliminate choices that are true but do not serve the stated purpose.'],
}

MISCONCEPTIONS = {
    'words_in_context': ['Chose a word that fits part of the sentence but contradicts another clue.',
                         'Chose a common meaning of the word that does not fit this context.',
                         'Chose a word that sounds sophisticated without checking the clues.'],
    'transitions': ['Chose a transition that signals the wrong relationship between the ideas.',
                    'Chose a transition that sounds natural but states a relationship the text does not show.',
                    'Picked a transition that would introduce an example or result that is not there.'],
    'inferences': ['Went beyond the evidence and asserted a claim the text does not support.',
                   'Chose an idea that contradicts a stated detail.',
                   'Chose a claim that is plausible in the real world but not supported here.'],
    'central_ideas': ['Chose a detail instead of the overall point.',
                      'Overgeneralized beyond what the text says.',
                      'Chose a claim the text never makes.'],
    'text_structure_purpose': ['Described what the text says rather than what it does.',
                               'Chose a function that does not match the text’s sequence.',
                               'Chose a purpose that is partly true of one sentence but not the whole text.'],
    'cross_text_connections': ['Mischaracterized one author’s position.',
                               'Assumed the authors disagree when one qualifies the other.',
                               'Attributed a claim to the author that the text does not make.'],
    'command_of_evidence_text': ['Chose evidence that is relevant to the topic but not to the specific claim.',
                                 'Chose evidence that supports the opposite direction.',
                                 'Chose a true detail that does not test the claim.'],
    'command_of_evidence_quant': ['Used accurate data that does not address the claim.',
                                  'Compared the wrong rows or left out half of the comparison.',
                                  'Reported a trend that is not what the claim describes.'],
    'boundaries': ['Created a comma splice or fragment.',
                   'Used punctuation that requires a complete clause on one side.',
                   'Used a conjunction or mark that does not fit the sentence structure.'],
    'subject_verb_agreement': ['Matched the verb to the nearest noun instead of the subject.',
                               'Chose the wrong number for the verb.',
                               'Chose a form that disagrees with the subject.'],
    'pronouns_modifiers': ['Left a modifier attached to the wrong noun.',
                           'Used a pronoun that does not agree with its antecedent.',
                           'Left the reference ambiguous.'],
    'verb_tense': ['Used a tense that conflicts with the sequence of events.',
                   'Used a present tense for a past event.',
                   'Used a future form for an event already completed.'],
    'form_structure_sense': ['Broke parallel structure.',
                             'Chose a form that does not fit the grammar around the blank.',
                             'Confused similar-sounding forms.'],
    'rhetorical_synthesis': ['Chose accurate information that does not meet the writer’s goal.',
                             'Left out the information needed for the stated goal.',
                             'Chose a statement not supported by the notes.'],
}


def E(module, skill, difficulty, sub, passage, correct, wrong, why, stem=None, hints=None, notes=None):
    """One hand-authored question, correct choice first."""
    assert len(wrong) == 3, (skill, correct)
    stem = stem or STEMS[skill]
    hints = hints or HINTS[skill]
    misconceptions = [''] + (notes or MISCONCEPTIONS[skill])
    return {'skill_key': skill, 'subskill': sub, 'difficulty': difficulty, 'module': module,
            'question_text': stem, 'source_or_prompt': passage, 'options': [correct] + list(wrong),
            'correct_option': 0, 'explanation': why, 'hints': hints, 'strategy': hints[1],
            'fastest_method': hints[2], 'misconceptions': misconceptions, 'validation': 'reviewed_bank'}
