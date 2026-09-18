// Original Mentics examples. The SAT emphasis is informed by James Lu's public
// Desmos/grammar focus; these are not transcripts or copies of his lessons.
export const strategyGuides = {
  sat: {
    math: [
      { title: 'Graph both sides', skill: 'Desmos intersections', cue: 'An equation or a system asks for a solution.', move: 'Enter each side as a separate y-expression in the test-version graphing calculator. Inspect the intersection and use the coordinate the question asks for.', example: 'For 2x + 3 = 11, graph y = 2x + 3 and y = 11. The intersection is (4, 11), so x = 4.', trap: 'The y-coordinate is not x. Adjust the window and check for additional solutions.' },
      { title: 'Work backward', skill: 'Backsolve', cue: 'Numeric answer choices and a short equation.', move: 'Try a middle answer in the original equation. Use whether it is too high or too low to choose the next candidate when the expression is monotonic.', example: 'For 3x + 2 = 14, testing x = 4 gives 14 immediately.', trap: 'Check the original equation and any restrictions. Backsolving can be slower than one clean algebra step.' },
      { title: 'Solve for the target', skill: 'Read the target', cue: 'The question asks for an expression such as 8x.', move: 'Look for a multiple of the expression you already know before isolating the variable.', example: 'If 4x + 3 = 19, then 4x = 16 and 8x = 32.', trap: 'Answer the requested expression, not the value of x.' },
    ],
    ela: [
      { title: 'Read the punctuation pattern', skill: 'Sentence boundaries', cue: 'The choices keep the words but change punctuation.', move: 'Check whether each side can stand alone. Two complete clauses can use a period or semicolon; a comma alone cannot join them.', example: 'The archive opened; researchers arrived. Both sides contain a subject and a complete verb.', trap: 'A colon needs a complete clause before it and an explanation, example, or list after it. A pause is not a grammar rule.' },
      { title: 'Name the relationship', skill: 'Transitions', cue: 'The choices are linking words.', move: 'Label the connection first: contrast, result, example, or continuation. Then match the meaning.', example: 'Lower energy use leads to longer battery life: therefore signals the result.', trap: 'A transition can sound smooth and still express the wrong logical relationship.' },
      { title: 'Make the answer prove itself', skill: 'Evidence', cue: 'A question asks what the text supports.', move: 'Find the exact detail supporting each part of the answer. Eliminate choices that add a claim the text never establishes.', example: 'One study showing taller seedlings supports a statement about that study, not all plants in every setting.', trap: 'Plausible outside knowledge is not passage evidence.' },
    ],
  },
  act: {
    math: [
      { title: 'Use the choices', skill: 'Backsolve', cue: 'The answer options give possible values.', move: 'Substitute a candidate into the original equation and compare both sides.', example: 'For 3x + 5 = 35, x = 10 makes both sides 35.', trap: 'Check restrictions and the exact requested quantity. Use the tools available in your ACT testing format.' },
      { title: 'Keep the units visible', skill: 'Rate setup', cue: 'A rate, distance, time, or production question.', move: 'Write the rate with its units. Multiply or divide so the unwanted units cancel.', example: '60 parts in 3 minutes is 20 parts/minute; in 5 minutes, 100 parts.', trap: 'Convert hours and minutes before substituting.' },
      { title: 'Turn averages into totals', skill: 'Average shortcut', cue: 'An average and a missing value.', move: 'Multiply average by count, then subtract the known values.', example: 'Four values averaging 10 total 40. If three total 27, the missing value is 13.', trap: 'Use the full count of values, including the missing one.' },
    ],
    ela: [
      { title: 'Cut repetition, keep meaning', skill: 'English · Concision', cue: 'English choices express the same idea at different lengths.', move: 'Remove redundant words while preserving meaning, grammar, and the passage voice.', example: 'Returned already means went back; returned back is redundant.', trap: 'The shortest answer only wins if it is complete and correct.' },
      { title: 'Find the real subject', skill: 'English · Agreement', cue: 'The choices change the verb.', move: 'Ignore intervening phrases and match the verb to the grammatical subject.', example: 'The results of the experiment were consistent. Results is plural.', trap: 'The noun closest to the verb may not be the subject.' },
      { title: 'Return to the evidence', skill: 'Reading · Detail', cue: 'Reading asks why something happened or what was stated.', move: 'Locate the sentence that answers the question before relying on memory.', example: 'If fog concealed the boats, that explains why the photographer changed plans.', trap: 'Reject attractive explanations the passage never gives.' },
    ],
  },
}
