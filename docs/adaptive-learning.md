# Adaptive learning, version 2

Each student has four independent tracks: SAT Math, SAT Reading & Writing, ACT Math, and ACT English & Reading. Switching tracks preserves the others. Questionnaire answers refine both sections of the selected exam. A section begins with one benchmark task, not a five-task starter unit.

## Durable flow

1. Save exam goals, scores, study time, strengths, weaknesses, and section confidence. Existing onboarding supplies the preferred presentation style and concerns.
2. Provision one full-length benchmark per section in an atomic transaction. Each follows the real test's structure and length (below); they are original diagnostics, not official tests or scaled-score estimates.
3. Save each answer and its learning evidence together. Benchmark answers cannot be changed or revealed before submission. Refresh and another device read the same saved session.
4. Submit once. Persist completion before generating content. A failed generation never requires another benchmark.
5. Rank skills with the evidence-based plan (below), then generate a five-step unit: lesson, practice, lesson, practice, review. Each lesson contains an actual worked example and a graded check, and its reason says which benchmark result and which self-reported weakness led to it. The second unit and all future units use the updated profile.

## Benchmarks

| Section | Length | Structure |
| --- | --- | --- |
| SAT Math | 44 questions | Module 1 and Module 2 (22 each); Algebra 15, Advanced Math 15, Problem Solving and Data Analysis 7, Geometry and Trigonometry 7. Module 2 is hard-weighted. |
| SAT Reading and Writing | 54 questions | Two modules of 27; Craft and Structure 15, Information and Ideas 14, Conventions 14, Expression of Ideas 11. Each stimulus is a 25-130 word passage, like the digital test. |
| ACT Math | 45 questions | One section ordered easy to hard across number, algebra, functions, geometry, trigonometry, statistics and probability. |
| ACT English and Reading | 86 questions | English: five passages of about 300 words with ten questions each (50). Reading: four passages of about 500-600 words with nine questions each (36). |

The benchmark never calls a model. Math questions are generated from templates with computed answers, so every student sees different numbers (seeded by account) and the suite verifies that each template builds a four-distinct-choice item across many seeds, and brute-force re-solves the riskiest ones. Reading and writing questions are fixed, hand-authored originals with balanced answer positions (ACT English keeps NO CHANGE first, as on the test). Module 2 is fixed rather than adaptive, and suggested times are guidance that is never enforced.

## Path planning

`adaptive.plan()` ranks every skill in the section and explains each choice:

- Measured accuracy carries the most weight. Missing an easy question counts more than missing a hard one, and a skill with few answers is blended with how the student did across its whole area.
- What the student wrote under weaknesses adds a boost. A phrase naming one skill ("quadratics") weighs 1.0; a whole area ("geometry") weighs 0.6 across its skills. It is discounted when the benchmark shows the skill is already strong, because measured performance outranks self-report. Named strengths only reduce priority when the results agree.
- Repeated wrong-answer patterns, unusually slow answers, and falling recent accuracy add priority; a just-mastered skill is left alone for a couple of days.
- The two lessons are the top-ranked skill and the next one from a different area, each starting with its weakest sub-skill. ACT sections have few skill keys, so sub-skill focus matters there.
- The target-score gap is passed to the question writer and noted in the path reason.

## Shared evidence

`learning_events` is the adaptive evidence ledger. A unique `(user_id, source, source_id)` prevents retry/replay inflation. Sources include benchmarks, Quick Practice, lessons, quizzes, sprints, Battles, and compatible legacy Quick Practice submissions. The existing `skill_mastery` and mistake history remain compatibility projections for stats and the coach.

Evidence includes the actual skill/subskill, difficulty, outcome, response time, confidence, hints, strategy, and possible distractor misconception. Misconceptions are hypotheses, not diagnoses. Unusually fast answers have lower mastery weight; the system does not confidently label a single error careless or conceptual.

The computed profile includes recent and historical accuracy, recency-weighted mastery, difficulty performance, subskills, trends, weekly activity, timing, hints, benchmark results, current path, recent mistakes, and other section summaries. Prior legacy counts contribute a bounded weight without double-counting new ledger entries. Older Quick Practice logs are also available as context. Measured performance outranks self-report. Selection prioritizes weak skills and reserves a slot for reinforcement or an unmeasured skill.

`adaptive_tracks` stores one-time benchmark completion and the current path generation lease. `adaptive_sessions` stores complete question sets, answer checkpoints, hints, profile snapshots, summaries, and request IDs. `path_generations` preserves the evidence used to generate each unit. `learning_hints` persists progressive hints for path activities. Content rows carry `adaptive_meta` so question-level evidence survives a mixed review.

## Question quality and attribution

Generated lesson, practice, review and Quick Practice questions are still written fresh by the model for each task. They are asked to match real-exam difficulty and length: practice is never easy (weak skills get medium questions, everything else hard), and validation rejects SAT passages shorter than the per-skill minimum (for example 60 words for main idea, 90 for cross-text, 28 for conventions), ACT English excerpts under 150 words, and ACT Reading excerpts under 280. The model still cannot be forced to write hard questions, so difficulty is requested and length is enforced. They must pass structural validation and a separate blind solving call. The reviewer receives no answer key or worked solution and must agree on the answer, validity, and hint safety. Valid complete questions can be recovered from a truncated response; rejected or missing items use the reviewed recovery bank, with a visible recovery notice. Recovery content is hard and real-length, prefers the focus sub-skill, and avoids questions the student has already seen; Reading and Writing recovery uses a separate pool from the benchmark. Question skill labels are never changed to pretend recovery content covers a different skill. Choices are shuffled when explanations do not depend on their letter positions.

Model checks reduce errors; they cannot prove every natural-language question correct. Difficulty labels and mastery estimates are provisional, not psychometric calibration. The recovery bank is deliberately limited and can repeat across sessions during an AI outage. ACT English and Reading recovery currently reuses the benchmark passages when nothing unseen remains. It is a continuity mechanism, not a claim of unlimited generated content. The ACT benchmark follows the section lengths but omits the Science section and the optional Writing test.

Three progressively stronger hints are available during Quick Practice and new path activities. They are persisted, included in evidence weighting, and followed by a full solution after grading. The benchmark is intentionally unaided. Quick Practice session points are separate from account XP.

James Lu is credited for the publicly documented Desmos and grammar emphasis where applicable. These are original Mentics examples; no private course content, quotations, or claimed affiliation are used. General test strategies are not attributed to him as inventions without evidence.

Sources checked for this work:

- [James Lu public SAT community](https://www.skool.com/sat/about)
- [James Lu public profile](https://www.skool.com/@jameslusat)
- [College Board SAT content domains](https://satsuite.collegeboard.org/practice/content-domains)
- [ACT examinee information](https://www.act.org/content/act/en/products-and-services/state-and-district-solutions/act-info-for-examinees.html)
- [Enhanced ACT format](https://industryinsights.act.org/2025/10/enhanced-act-what-you-need-to-know)

## Reliability and rollout

No AI call holds a database transaction. Each question job has bounded generation/review timeouts. A path uses two independent five-question jobs in parallel to fit the deployment's request budget. Generation leases expire after 90 seconds, and unique lease tokens prevent a stale worker replacing newer work. Initial path requests and completed requests are idempotent. Failed requests can be retried. The old path remains active until all five replacement tasks commit.

Apply `migrations/004_adaptive_learning.sql` using a direct Neon owner connection, first on a production clone. The migration is idempotent and transactional. It adds schema/RLS/grants and archives only generated Test Prep rows with `learning_version < 2`. It does not delete accounts, questionnaire responses, activity history, old content/results, personal steps, college paths, or achievements. Runtime provisioning also archives old generated rows, preventing stale starters from becoming active after an old deployment writes during rollout.

The runtime role has owner-only RLS on all new tables. Account deletion removes the new learning data. Existing lesson/quiz/sprint scoring writes first-attempt evidence atomically under a user lock. Stats include the new sources without counting path answers twice.

RLS identity is reapplied as transaction-local settings for every database operation. A request may reuse its connection, but Neon transaction pooling can assign a different backend after a commit; cached session identity must never be assumed to survive that boundary.

Verification is covered in `tests/test_adaptive_learning.py` and the existing track, completion, account deletion, and Arena suites. Browser checks should include questionnaire → benchmark → refresh → submission → five steps → lesson → Quick Practice → hints → summary, at desktop, tablet, and phone widths. Database checks must also run with `mentics_app`, not only the migration owner.
