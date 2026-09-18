# Test prep and SAT / ACT Battles

## Student flows

- Quick Practice lives at `/dashboard/quick-practice`, linked from navigation, the path, and the builder.
- Students choose one exam, Math or ELA, and either a speed round (a five-minute target, not a hard cutoff) or untimed strategy practice.
- Five original micro-drills provide optional hints, locked answer feedback, round points, accuracy, streaks, complete answer review, and retries of missed questions. Round points do not change account points or mastery. Reloading leaves the round.
- SAT ELA means Reading & Writing. ACT ELA practice covers English and Reading. ACT Science remains in the broader study path.
- Long paths preserve the five-step loop and full official-test checkpoint. `subject_focus` filters lessons and drills server-side; normalization rejects skills from another subject or exam. Old saved plans remain intact until rebuilt.

## ACT Battles

The existing `/battles` route and `/api/sat-battles/*` URLs now serve both exams. The legacy URL names remain for compatibility. Queue and training POST bodies accept `exam: "SAT" | "ACT"`; omitted exam defaults to SAT. The response includes `exam` in waiting, active, and complete states.

`exam_type` is stored on the battle, never accepted during submission. Matchmaking's atomic claim filters by exam. Recovery resumes the stored exam even if the browser requests a different exam. Bot drop-in and training use the stored exam. Rating, streaks, avatars, and the leaderboard remain shared across both exams, explicitly labeled in the lobby.

ACT rounds contain three Math, one Reading, and one English question. Generation uses ACT section prompts, checks section identity, and retains the existing shape validation and independent high-tier audit. Original ACT reserve items support offline operation; a configured training generator that fails validation returns an error instead of substituting a reserve round. No official questions are copied. The round clock is an Arena game target, not official ACT timing.

The current four-choice Math format and online calculator availability were checked against [ACT's examinee information](https://www.act.org/content/act/en/products-and-services/state-and-district-solutions/act-info-for-examinees.html) and [calculator policy](https://www.act.org/content/act/en/products-and-services/the-act/test-day/calculator-policy.html). Existing Desmos practice tooling remains available for Math.

## Deployment

Run `migrations/002_act_battles.sql` before deploying to PostgreSQL where `INIT_DB_ON_STARTUP` is disabled. Local `init_db()` also adds the column and queue index. Existing rows default to SAT. No existing battle or rating is deleted. Changes have not been deployed to production.

## Verification

- Full Python suite: 118 passed, including ACT queue isolation, recovery, bot drop-in, grading, training at every rank, invalid exam values, section-specific generation prompts, reserve choice uniqueness, and subject filtering.
- Node practice-bank check verifies all answer-choice sets and 200 shuffled rounds.
- ESLint and client / SSR / prerender builds pass.
- Browser review uses both development fixtures and the production build against a disposable SQLite account with live AI disabled. Covered ACT lobby switching, training, Math/Reading/English labels, submission, and responsive prep screens. Live Gemini generation was mocked in tests, not called against the provider.
