// Original micro-drills. These teach tactics, not full-length exam endurance.
const item = (skill, tip, prompt, options, answer, explanation) => ({ skill, tip, prompt, options, answer, explanation })
const satEla = [
  item('Transitions', 'Name the relationship before reading the choices: contrast, cause, or continuation.', 'The first prototype used less energy than expected. Its battery life, _____, exceeded the team’s target. Which transition best completes the text?', ['however', 'therefore', 'instead', 'nevertheless'], 1, 'Lower energy use causes longer battery life. “Therefore” signals that result; the other choices suggest a contrast.'),
  item('Sentence boundaries', 'Check both sides of a punctuation mark for complete sentences.', 'The archive opened in June _____ researchers can now consult its letters online. Which choice creates a complete, correctly punctuated sentence?', [',', ';', 'and', 'with'], 1, 'Both sides can stand alone. A semicolon joins two independent clauses. A comma alone creates a comma splice, and “and” would need a comma here.'),
  item('Words in context', 'Predict a simple replacement, then check it against the whole sentence.', 'Although early observations seemed to support the hypothesis, later trials undermined it. As used here, “undermined” most nearly means:', ['concealed', 'expanded', 'weakened', 'established'], 2, '“Although” sets up a contrast with support. The later trials weakened the hypothesis.'),
  item('Evidence', 'Reject answers that go beyond the evidence, even if they sound plausible.', 'In a study of 120 seedlings, plants receiving six hours of light grew taller on average than plants receiving two hours. Which conclusion is best supported?', ['All plants need six hours of light.', 'More light always causes faster growth.', 'Two hours of light prevents growth.', 'The six-hour group was taller on average in this study.'], 3, 'The finding applies to these groups. It does not establish a universal rule or show that the two-hour group did not grow.'),
  item('Subject–verb agreement', 'Find the grammatical subject; ignore nouns inside interrupting phrases.', 'The collection of letters from several explorers _____ a detailed record of the voyage. Which choice completes the sentence correctly?', ['provides', 'provide', 'have provided', 'are providing'], 0, 'The subject is the singular “collection,” not the plural “letters” or “explorers,” so “provides” agrees.'),
  item('Rhetorical synthesis', 'Read the requested goal first; use only notes that serve it.', 'Notes: Lake A is 40 meters deep. Lake B is 65 meters deep. Both lakes contain freshwater. The student wants to emphasize a difference in depth. Which sentence best achieves that goal?', ['Both lakes contain freshwater.', 'Lake B is 25 meters deeper than Lake A.', 'Lake A and Lake B are both lakes.', 'Lake B is a freshwater lake 65 meters deep.'], 1, '65 − 40 = 25. Only this choice directly compares the lakes’ depths.'),
  item('Inference', 'Prefer the narrow conclusion the text supports over an absolute claim.', 'A museum moved a fragile manuscript into a dimmer gallery after conservators observed fading on its pages. What does the text most strongly suggest?', ['The manuscript will never fade again.', 'All other galleries were closed.', 'The move was intended to limit further damage.', 'The museum planned to stop displaying manuscripts.'], 2, 'The sequence connects observed fading with a protective change. It supports the intention to reduce damage, not a guarantee or a broader museum policy.'),
]
const actEla = [
  item('English · Concision', 'Choose the shortest option that preserves the full meaning and correct grammar.', 'Choose the most concise replacement for “returned back again” in: After lunch, Maya returned back again to the laboratory.', ['returned', 'returned back', 'went and returned back', 'returned again back'], 0, '“Returned” already expresses going back. The other choices repeat the same idea.'),
  item('English · Agreement', 'Cross out the phrase between the subject and verb in your head.', 'Choose the correct verb: The results of the experiment _____ consistent across three trials.', ['was', 'is', 'were', 'has been'], 2, '“Results” is plural. “Of the experiment” does not change the subject, so “were” is correct.'),
  item('Reading · Detail', 'Locate the exact evidence before relying on what you remember.', 'Lena had planned to photograph the harbor at dawn. Thick fog concealed the boats, so she spent the morning sketching the nearby market instead. Why did Lena change her plan?', ['The market opened early.', 'Fog blocked her view of the boats.', 'Her camera was broken.', 'The harbor was closed.'], 1, 'The passage explicitly states that thick fog concealed the boats. The other explanations are not given.'),
  item('English · Organization', 'Use pronouns and time markers to find the sentence’s anchor.', 'A paragraph begins: (1) Noor collected water samples from three ponds. (2) She then compared their acidity. (3) The results revealed a clear difference. Where should “Each sample was placed in a labeled container” go?', ['Before sentence 1', 'After sentence 3', 'After sentence 2', 'After sentence 1'], 3, 'The samples must first be collected; labeling them logically precedes comparing their acidity. “Each sample” refers back to sentence 1.'),
  item('Reading · Purpose', 'Ask what a detail does for the passage, not just what it says.', 'The old station once handled hundreds of travelers each day. Now, weeds push through its platform, and the ticket windows stand empty. The details about weeds and empty windows primarily:', ['explain train schedules', 'suggest the station’s decline', 'describe a recent renovation', 'criticize travelers'], 1, 'The details contrast former activity with present disuse and emphasize decline.'),
  item('English · Punctuation', 'An introductory dependent clause needs a comma before the main clause.', 'Choose the correct punctuation: Although the trail was steep _____ the hikers reached the summit before noon.', [',', ';', ':', '.'], 0, '“Although the trail was steep” is a dependent clause. A comma separates it from the independent main clause.'),
  item('Reading · Inference', 'Separate a reasonable inference from a claim the passage cannot prove.', 'At rehearsal, Eli paused before a difficult passage. After practicing it slowly several times, he played the entire piece without stopping. What is best supported?', ['Eli had never played the instrument.', 'The piece had no difficult passages.', 'Focused practice helped Eli perform more fluently.', 'Eli will never make another mistake.'], 2, 'His performance became continuous after targeted practice. The passage supports that improvement without sweeping claims.'),
]
function mathBank(exam) {
  const offset = exam === 'act' ? 3 : 0
  return Array.from({ length: 4 }, (_, index) => {
    const n = index + offset + 2
    return [
      item('Backsolve', 'Substitute a promising answer into the original equation; check both sides.', `If 3x + ${n} = ${7 * n}, what is x?`, [String(n), String(2 * n), String(3 * n), String(6 * n)], 1, `Subtract ${n}: 3x = ${6 * n}. Divide by 3: x = ${2 * n}. Substitution gives ${6 * n} + ${n} = ${7 * n}.`),
      item('Percent multipliers', 'A percent decrease multiplies by 1 minus the decimal rate. Do not subtract the rate itself.', `A jacket costs $${20 * n}. Its price is reduced by 25%. What is the sale price?`, [`$${5 * n}`, `$${19 * n}`, `$${25 * n}`, `$${15 * n}`], 3, `Keep 75% of the price: 0.75 × ${20 * n} = ${15 * n}. The discount itself is $${5 * n}.`),
      item('Read the target', 'Circle what the question actually asks. You may not need to solve for the variable.', `If 4x + ${n} = ${9 * n}, what is the value of 8x?`, [String(16 * n), String(2 * n), String(8 * n), String(18 * n)], 0, `Subtract ${n} to get 4x = ${8 * n}. Double both sides: 8x = ${16 * n}. You do not need to calculate x.`),
      item('Rate setup', 'Write the units with the numbers so they cancel in the right direction.', `A machine produces ${12 * n} parts in 3 minutes at a constant rate. How many parts does it produce in 5 minutes?`, [String(12 * n + 2), String(4 * n), String(20 * n), String(60 * n)], 2, `${12 * n} ÷ 3 = ${4 * n} parts per minute. Multiply by 5 minutes to get ${20 * n} parts.`),
      item(exam === 'sat' ? 'Equivalent expressions' : 'Math · Distribution', 'Distribute to every term, then combine like terms. Check with a simple input if uncertain.', `Which expression is equivalent to ${n}(x + 3) − 2x?`, [`${n - 2}x + 3`, `${n + 2}x + ${3 * n}`, `${n - 2}x + ${3 * n}`, `${n}x + ${3 * n - 2}`], 2, `Distribute ${n}: ${n}x + ${3 * n} − 2x. Combining the x terms gives ${n - 2}x + ${3 * n}.`),
      item('Average shortcut', 'Convert an average to a total before finding the missing value.', `Four numbers have an average of ${5 * n}. Three of the numbers are ${2 * n}, ${4 * n}, and ${6 * n}. What is the fourth?`, [String(5 * n), String(8 * n), String(12 * n), String(20 * n)], 1, `The total is 4 × ${5 * n} = ${20 * n}. The three known numbers total ${12 * n}, leaving ${8 * n}.`),
    ]
  }).flat()
}
export const drillBanks = { sat: { math: mathBank('sat'), ela: satEla }, act: { math: mathBank('act'), ela: actEla } }
export function makeRound(exam, subject) {
  const pool = [...drillBanks[exam][subject]]
  for (let i = pool.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1)); [pool[i], pool[j]] = [pool[j], pool[i]]
  }
  // Prioritize different tactics within a round, not repeated numeric variants.
  const unique = pool.filter((question, index) => pool.findIndex(other => other.skill === question.skill) === index)
  return unique.slice(0, 5).map(question => {
    const choices = question.options.map((text, index) => ({ text, correct: index === question.answer }))
    for (let i = choices.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1)); [choices[i], choices[j]] = [choices[j], choices[i]]
    }
    return { ...question, options: choices.map(choice => choice.text), answer: choices.findIndex(choice => choice.correct) }
  })
}

