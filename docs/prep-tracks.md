# Saved prep tracks

SAT Math, SAT ELA, ACT Math, and ACT ELA are independent `paths.track_key`
lanes. Visiting the path page or saving the exam questionnaire provisions any
missing starter units. Setup never makes a model call or replaces existing work.
Questionnaire fields refine both subject profiles for the selected exam. Future
units use its scores, requested focus, measured skills, and completed lessons.

Legacy rows keep their IDs, results, and completion state. Their subject and
skill taxonomy determine the lane; unclassified rows use the previous profile.
Generation only retires core rows in the requested lane. Personal steps remain.
Ordering checks, chat history, and personal steps use the same lane key.

The AI receives the selected lane as its scope and other profiles, active path
progress, recent conversations, and quick-practice results as labelled context.
The server restricts generated skills to the selected exam/section catalog.
Section units end in a section review rather than an unrelated full-test task.

## Quick-practice content

Research checked September 17, 2026:

- [James Lu's public SAT community](https://www.skool.com/sat/about) and
  [profile](https://www.skool.com/@jameslusat) emphasize Desmos and grammar.
  This supports the choice of topics, not a claim that every Mentics strategy
  reproduces his method. All examples and explanations here are original.
- [College Board calculator policy](https://satsuite.collegeboard.org/in-school-assessments/calculator-policy)
  documents the embedded test-version Desmos calculators.
- [College Board Reading and Writing practice](https://satsuite.collegeboard.org/practice/student-question-bank/reading-writing)
  describes recognizing question skills from answer-choice patterns.
- [ACT calculator policy](https://www.act.org/content/act/en/products-and-services/the-act/test-day/calculator-policy.html)
  documents built-in Desmos for online Math and permitted handheld calculators.

The playbook teaches when to use each tactic, an example, and a limitation.
Targeted rounds practise that tactic; mixed rounds vary skills. Round points
are separate from account XP. Completed rounds are checked against the server
bank and saved as coaching context, not claimed as an official score estimate.

`quick-practice-data.js` owns the original drill bank. `npm run build` generates
`prep_starter_bank.py` for serverless packaging and starter-unit construction.
Rebuild it after changing the questions so question IDs agree across clients
and server. Existing IDs must remain stable within each exam/subject bank.

## Database rollout

Apply `migrations/003_test_prep_tracks.sql` before deploying. It is additive and
idempotent. It was verified on Neon branch `prep-tracks-verify-20260917` before
the column and index were applied and directly verified on production.

Tests cover idempotent provisioning, existing progress, legacy rows, per-track
ordering and regeneration, questionnaire rendering, chat scope, and server-side
quick-practice grading. Browser checks exercise questionnaire submission and
switching away from and back to a completed lesson.
