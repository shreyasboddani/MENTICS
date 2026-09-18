# Adaptive learning, version 2

Each student has four independent tracks: SAT Math, SAT Reading & Writing, ACT Math, and ACT English & Reading. Switching tracks preserves the others. Questionnaire answers refine both sections of the selected exam. A section begins with one benchmark task, not a five-task starter unit.

## Durable flow

1. Save exam goals, scores, study time, strengths, weaknesses, and section confidence. Existing onboarding supplies the preferred presentation style and concerns.
2. Provision one 12-question benchmark per section in an atomic transaction. Benchmarks sample domains and difficulty bands; they are original diagnostics, not official tests or scaled-score estimates.
3. Save each answer and its learning evidence together. Benchmark answers cannot be changed or revealed before submission. Refresh and another device read the same saved session.
4. Submit once. Persist completion before generating content. A failed generation never requires another benchmark.
5. Generate a five-step unit: lesson, practice, lesson, practice, review. Each lesson contains an actual worked example and a graded check. The second unit and all future units use the updated profile.

## Shared evidence

`learning_events` is the adaptive evidence ledger. A unique `(user_id, source, source_id)` prevents retry/replay inflation. Sources include benchmarks, Quick Practice, lessons, quizzes, sprints, Battles, and compatible legacy Quick Practice submissions. The existing `skill_mastery` and mistake history remain compatibility projections for stats and the coach.

Evidence includes the actual skill/subskill, difficulty, outcome, response time, confidence, hints, strategy, and possible distractor misconception. Misconceptions are hypotheses, not diagnoses. Unusually fast answers have lower mastery weight; the system does not confidently label a single error careless or conceptual.

The computed profile includes recent and historical accuracy, recency-weighted mastery, difficulty performance, subskills, trends, weekly activity, timing, hints, benchmark results, current path, recent mistakes, and other section summaries. Prior legacy counts contribute a bounded weight without double-counting new ledger entries. Older Quick Practice logs are also available as context. Measured performance outranks self-report. Selection prioritizes weak skills and reserves a slot for reinforcement or an unmeasured skill.

`adaptive_tracks` stores one-time benchmark completion and the current path generation lease. `adaptive_sessions` stores complete question sets, answer checkpoints, hints, profile snapshots, summaries, and request IDs. `path_generations` preserves the evidence used to generate each unit. `learning_hints` persists progressive hints for path activities. Content rows carry `adaptive_meta` so question-level evidence survives a mixed review.

## Question quality and attribution

Generated questions must pass structural validation and a separate blind solving call. The reviewer receives no answer key or worked solution and must agree on the answer, validity, and hint safety. Valid complete questions can be recovered from a truncated response; rejected or missing items use the original reviewed recovery bank, with a visible recovery notice. Question skill labels are never changed to pretend recovery content covers a different skill. Choices are shuffled when explanations do not depend on their letter positions.

Model checks reduce errors; they cannot prove every natural-language question correct. Difficulty labels and mastery estimates are provisional, not psychometric calibration. The small recovery bank is deliberately limited and can repeat across sessions during an AI outage. It is a continuity mechanism, not a claim of unlimited generated content. ACT diagnostics are skill samples, not a full-length ACT simulation.

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

Verification is covered in `tests/test_adaptive_learning.py` and the existing track, completion, account deletion, and Arena suites. Browser checks should include questionnaire → benchmark → refresh → submission → five steps → lesson → Quick Practice → hints → summary, at desktop, tablet, and phone widths. Database checks must also run with `mentics_app`, not only the migration owner.
