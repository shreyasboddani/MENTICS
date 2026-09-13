# SAT Battles implementation and verification

## Preserved contracts

`/battles` still boots from Flask. The existing avatar POST, queue POST,
training POST, battle GET, cancellation and submission endpoints remain.
Five shared questions, server-side grading, stronger-player rank selection, bot
drop-in, Elo, streaks and private training are preserved. The flat two-minute
clock is not: it is now sized to the round.
No migrations or changes to saved cosmetic keys are required.

The server still owns answer keys. Active responses only add the current
player's **submitted** answers, an opponent-submitted boolean, and a preparing
flag. Explanations and keys remain available only after completion.

## Frontend

- `arena-page.jsx` owns the existing lobby, queue, battle and result flows.
- `arena-experience.jsx` contains generation loading, accessible question choices
  and result review. Numeric shortcuts select answers; selection is reversible
  until submission. Review uses graded answers, not unsubmitted local drafts.
- `arena-avatar-preview.jsx` loads `arena-avatar-scene.js` when visible. The
  procedural Three.js wardrobe uses the existing catalog, no remote models or
  textures, shared geometry, bounded DPR and approximately 30 fps idle rendering.
  It stops when hidden, offscreen or behind the locker. Reduced motion uses
  demand rendering. Geometry, materials, observers and WebGL contexts are disposed.
- The existing SVG fighter remains the lightweight HUD/results renderer and
  fallback when 3D cannot initialize. The 3D version is intentionally stylized;
  it is not a rigged, artist-authored character asset library.
- `arena-calculator.jsx` keeps the official cross-origin Desmos calculator and
  its mounted graph during a round. A body portal avoids transformed ancestors.
  Pointer/keyboard sizing, maximizing, viewport bounds and session sizing are
  supported; mobile uses a bottom sheet with full-screen expansion.
- `app-runtime.jsx` contains the shared shell/CSRF/API primitives extracted from
  App. Hashed shared chunks prevent lazy imports from executing Flask's
  query-versioned `app.js` entry twice. Vite's base matches `/static/react/`.

## Round clock

The clock is derived from the questions actually served rather than fixed at two
minutes, which gave five items 24 seconds each — under half the time the
generator is told to write a bronze item for, and a quarter of a grandmaster
one. Official Digital SAT pacing is about 71 seconds per Reading and Writing
question and 95 per Math question; the Arena is a race, so it runs brisker than
that at the low tiers and approaches real pacing at the top. A round costs 78
seconds per Math item and 60 per Reading and Writing item, scaled by tier
(bronze 0.72 through grandmaster 1.20), rounded to a quarter minute and clamped
to 150-600 seconds. A standard three-Math round therefore runs 4:15 at bronze
and 7:00 at grandmaster. The lobby advertises the clock the selected tier earns,
the battle header counts that clock down, and the bot answers at 62 percent of
it so finishing early still wins a tie on time.

## Generation

The original five parallel slots and per-slot retries remain. Prompts are
shorter and aligned with deterministic limits. Invalid shapes are rejected before
an expensive audit. High-tier audits receive the stem/options **without the
draft key or explanation**, independently solve, and must return `verified=true`.
A failed audit cannot fall back to the unaudited draft.

Validation rejects non-string fields/options, boolean/fractional keys, duplicate
or numerically equivalent options, invalid domains, missing completion blanks,
unfinished explanations, escaped TeX, control characters and unbalanced math
parentheses. Existing repetition and tier gates remain. The legacy best-effort
tier allowance is retained for usable, audited items; it does not waive structural
validation or the high-tier audit.

Two gates judge an item and they are not interchangeable. `SAT_BATTLE_TIER_CONTRACT` decides whether an item is the right *hardness* for its tier; missing that band is retryable and a near-miss is eventually accepted rather than failing the round. `SAT_BATTLE_MINIMUM_TEXT` is the *item* contract and is fatal. Repeating the tier's own Math floor in the fatal gate meant a correct Bronze stem such as "If 3x + 7 = 22, what is the value of 6x - 4?" was thrown out for being 44 characters, the slot could never fill, and every Bronze round failed. The fatal gate is now a sanity floor only. A retry is also told why its last attempt was rejected; a blind retry returned the same item with the same fault.

Generation has a 44-second collection deadline and bounded individual HTTP
requests. Executors no longer wait indefinitely on exit. Failed training leaves
no partial battle. Ranked rows are claimed before generation but questions and
the clock publish together, so loading cannot consume round time. Cancellation
cannot resurrect a preparing round; abandoned preparation expires without RP.

Prefetching complete personalized sets, persistent question pools and streamed
partial rounds are deliberately not introduced: they need additional storage and
fairness decisions. The current five-question contract stays intact.

## Verification (local, September 12, 2026)

- Full pytest suite: **87 passed**, including **55 battle cases**.
- `npm run check`, `npm run build` (client, SSR and nine prerendered pages),
  `python -m py_compile app.py`, and `git diff --check` passed.
- This JavaScript repository has no standalone TypeScript checking configuration.
- Chrome checks used a disposable SQLite database and normal authentication:
  lobby, saved/randomized loadout and reload, rotation, locker at 390px,
  lobby at 768/1440px, queue/cancel, timed completion, submitted completion,
  three correct/two incorrect review, math and reading questions, Desmos equation
  entry, maximizing, keyboard width adjustment, pointer dragging and resizing in
  both dimensions, draft recovery after reload, and mobile calculator layout.
- Loading was inspected with a delayed local request. Checked pages had no
  horizontal overflow or application console errors at those viewports.
- Live Gemini testing exposed invalid math in earlier drafts; the final blind
  audit produced five questions in **33.6 seconds**. That sampled set's math and
  keys were manually checked. This is not a latency benchmark or a guarantee that
  arbitrary model output is mathematically correct. Difficulty consistency still
  merits ongoing review, especially when a slot uses the legacy best-effort tier.
- Shared initial JavaScript is approximately **145 KB gzip**, down from the
  original **167 KB** entry. The Arena route is about **27 KB gzip**; its additional
  3D renderer is about **143 KB gzip**, fetched only for visible character previews.
  Vite still reports the renderer exceeding its 500 KB uncompressed chunk warning.
  The pre-existing absolute font URL warning also remains; the font loads in Flask.

Real multiplayer concurrency was covered by backend tests, not two live browser
accounts. No production deployment, data migration or exhaustive device/cosmetic
combination matrix was performed.
