"""Adaptive lesson engine for Digital SAT and ACT prep.

The engine turns a student profile into a five-node learning unit shaped like a
Duolingo unit: teach, drill, teach, review, checkpoint. Nothing here asks the
student to go find a resource on their own -- every node except the final
official-test checkpoint carries the content the student needs.

Generation is deliberately split across several small Gemini calls instead of
one large one. A single call that has to emit a plan plus four sets of teaching
cards plus twenty questions routinely truncates or drifts; five focused calls
each stay well inside the model's reliable window and can run concurrently.

    plan_unit()          one call  -> five nodes with a per-node syllabus
    generate_teaching()  one call  -> concept cards for one lesson node
    generate_exercises() one call  -> practice items for one node

`build_unit()` runs the planner, then fans the content calls out across a
thread pool, so wall-clock cost is roughly two sequential calls.
"""

import json
import re
from concurrent.futures import ThreadPoolExecutor

# --- Dependency injection -------------------------------------------------
# app.py owns the Gemini client. Injecting the generator keeps this module
# import-safe and testable without a configured API key.

_generate_text = None
_logger = None


def configure(generate_text, logger=None):
    global _generate_text, _logger
    _generate_text = generate_text
    _logger = logger


def _log(message, *args):
    if _logger:
        _logger.warning(message, *args)
    else:
        print(message % args if args else message)


def is_configured():
    return _generate_text is not None


# --- Skill taxonomy -------------------------------------------------------
# Stable keys matter: mastery is tracked per key across paths, so the planner
# is constrained to this vocabulary rather than inventing a new label each run.

SKILL_TAXONOMY = {
    # Digital SAT - Reading and Writing
    "central_ideas": ("Central Ideas and Details", "Reading and Writing", "reading", "SAT"),
    "command_of_evidence_text": ("Command of Evidence (Textual)", "Reading and Writing", "reading", "SAT"),
    "command_of_evidence_quant": ("Command of Evidence (Quantitative)", "Reading and Writing", "reading", "SAT"),
    "inferences": ("Inferences", "Reading and Writing", "reading", "SAT"),
    "words_in_context": ("Words in Context", "Reading and Writing", "reading", "SAT"),
    "text_structure_purpose": ("Text Structure and Purpose", "Reading and Writing", "reading", "SAT"),
    "cross_text_connections": ("Cross-Text Connections", "Reading and Writing", "reading", "SAT"),
    "rhetorical_synthesis": ("Rhetorical Synthesis", "Reading and Writing", "writing", "SAT"),
    "transitions": ("Transitions", "Reading and Writing", "writing", "SAT"),
    "boundaries": ("Sentence Boundaries and Punctuation", "Reading and Writing", "grammar", "SAT"),
    "form_structure_sense": ("Form, Structure, and Sense", "Reading and Writing", "grammar", "SAT"),
    "subject_verb_agreement": ("Subject-Verb Agreement", "Reading and Writing", "grammar", "SAT"),
    "pronouns_modifiers": ("Pronouns and Modifiers", "Reading and Writing", "grammar", "SAT"),
    "verb_tense": ("Verb Tense and Form", "Reading and Writing", "grammar", "SAT"),
    # Digital SAT - Math
    "linear_equations_one": ("Linear Equations in One Variable", "Math", "algebra", "SAT"),
    "linear_equations_two": ("Linear Equations in Two Variables", "Math", "algebra", "SAT"),
    "linear_functions": ("Linear Functions", "Math", "algebra", "SAT"),
    "systems_of_equations": ("Systems of Linear Equations", "Math", "algebra", "SAT"),
    "linear_inequalities": ("Linear Inequalities", "Math", "algebra", "SAT"),
    "equivalent_expressions": ("Equivalent Expressions", "Math", "advanced_math", "SAT"),
    "nonlinear_equations": ("Nonlinear Equations and Systems", "Math", "advanced_math", "SAT"),
    "quadratic_functions": ("Quadratic Functions and Graphs", "Math", "advanced_math", "SAT"),
    "exponential_functions": ("Exponential Functions and Growth", "Math", "advanced_math", "SAT"),
    "function_notation": ("Function Notation and Transformations", "Math", "advanced_math", "SAT"),
    "ratios_rates": ("Ratios, Rates, and Proportions", "Math", "data_analysis", "SAT"),
    "percentages": ("Percentages", "Math", "data_analysis", "SAT"),
    "one_variable_data": ("One-Variable Data and Statistics", "Math", "data_analysis", "SAT"),
    "two_variable_data": ("Two-Variable Data and Models", "Math", "data_analysis", "SAT"),
    "probability": ("Probability and Conditional Probability", "Math", "data_analysis", "SAT"),
    "sample_inference": ("Inference from Samples and Margin of Error", "Math", "data_analysis", "SAT"),
    "statistical_claims": ("Evaluating Statistical Claims", "Math", "data_analysis", "SAT"),
    "area_volume": ("Area and Volume", "Math", "geometry", "SAT"),
    "lines_angles_triangles": ("Lines, Angles, and Triangles", "Math", "geometry", "SAT"),
    "right_triangles_trig": ("Right Triangles and Trigonometry", "Math", "geometry", "SAT"),
    "circles": ("Circles", "Math", "geometry", "SAT"),
    "desmos_strategy": ("Desmos Graphing and Regression Strategy", "Math", "algebra", "SAT"),
    # ACT-specific
    "act_english_usage": ("ACT English: Usage and Mechanics", "English", "grammar", "ACT"),
    "act_english_rhetoric": ("ACT English: Rhetorical Skills", "English", "writing", "ACT"),
    "act_reading_detail": ("ACT Reading: Detail and Inference", "Reading", "reading", "ACT"),
    "act_science_data": ("ACT Science: Data Representation", "Science", "science", "ACT"),
    "act_science_experiment": ("ACT Science: Research Summaries", "Science", "science", "ACT"),
    "act_science_viewpoints": ("ACT Science: Conflicting Viewpoints", "Science", "science", "ACT"),
    "act_math_prealgebra": ("ACT Math: Pre-Algebra and Number Sense", "Math", "algebra", "ACT"),
    "act_math_coordinate": ("ACT Math: Coordinate Geometry", "Math", "geometry", "ACT"),
    "act_math_plane_geometry": ("ACT Math: Plane Geometry", "Math", "geometry", "ACT"),
    "act_math_trig": ("ACT Math: Trigonometry", "Math", "geometry", "ACT"),
    # Generic fallback
    "pacing_and_timing": ("Pacing and Test-Day Timing", "Test Strategy", "strategy", "BOTH"),
}

_MATH_SUBJECTS = {"Math"}


def skill_catalog(test_focus="sat"):
    """Skill keys the planner may choose from, filtered to the student's test."""
    focus = (test_focus or "sat").lower()
    allowed = []
    for key, (_, _, _, test) in SKILL_TAXONOMY.items():
        if test == "BOTH":
            allowed.append(key)
        elif focus == "both":
            allowed.append(key)
        elif focus == "act" and test == "ACT":
            allowed.append(key)
        elif focus not in ("act",) and test == "SAT":
            allowed.append(key)
    return allowed


# Students and the model both describe skills in everyday words. Without these,
# "vocabulary" matches nothing in the taxonomy and falls through to a generic
# pacing lesson, which is exactly the vague output this engine exists to avoid.
SKILL_ALIASES = {
    "words_in_context": ["vocabulary", "vocab", "word choice", "diction", "word meaning"],
    "command_of_evidence_text": ["evidence", "supporting detail", "which choice most"],
    "command_of_evidence_quant": ["graph question", "data evidence", "table evidence"],
    "central_ideas": ["main idea", "central idea", "summarize", "gist"],
    "inferences": ["inference", "infer", "logical completion", "conclusion"],
    "text_structure_purpose": ["purpose", "structure", "function of", "author's intent"],
    "cross_text_connections": ["paired passage", "two texts", "compare texts"],
    "rhetorical_synthesis": ["notes question", "synthesis", "bullet points goal"],
    "transitions": ["transition", "however", "furthermore", "connective"],
    "boundaries": ["punctuation", "comma", "semicolon", "colon", "run on", "fragment", "dash"],
    "form_structure_sense": ["sentence structure", "syntax", "parallel"],
    "subject_verb_agreement": ["subject verb", "agreement", "plural verb"],
    "pronouns_modifiers": ["pronoun", "modifier", "dangling", "antecedent", "possessive"],
    "verb_tense": ["tense", "verb form", "conjugation"],
    "linear_equations_one": ["one variable equation", "solve for x", "linear equation"],
    "linear_equations_two": ["two variable", "slope intercept", "standard form"],
    "linear_functions": ["linear function", "rate of change", "slope"],
    "systems_of_equations": ["system of equations", "simultaneous", "substitution", "elimination"],
    "linear_inequalities": ["inequality", "inequalities", "number line"],
    "equivalent_expressions": ["factoring", "simplify", "expand", "polynomial", "rational expression"],
    "nonlinear_equations": ["nonlinear", "radical equation", "absolute value"],
    "quadratic_functions": ["quadratic", "parabola", "vertex", "discriminant", "completing the square"],
    "exponential_functions": ["exponential", "growth and decay", "compound interest", "half life"],
    "function_notation": ["function notation", "transformation", "composition", "f of x"],
    "ratios_rates": ["ratio", "rate", "proportion", "unit conversion", "scale"],
    "percentages": ["percent", "percentage", "markup", "discount"],
    "one_variable_data": ["mean", "median", "mode", "standard deviation", "box plot", "histogram"],
    "two_variable_data": ["scatterplot", "line of best fit", "regression", "correlation"],
    "probability": ["probability", "odds", "two way table"],
    "sample_inference": ["margin of error", "sample", "confidence interval", "survey"],
    "statistical_claims": ["statistical claim", "study design", "causation", "generalize"],
    "area_volume": ["area", "volume", "surface area", "perimeter"],
    "lines_angles_triangles": ["angle", "triangle", "parallel lines", "similar triangles"],
    "right_triangles_trig": ["pythagorean", "sine", "cosine", "tangent", "trig", "sohcahtoa"],
    "circles": ["circle", "radius", "arc", "sector", "chord"],
    "desmos_strategy": ["desmos", "graphing calculator", "table regression", "tilde"],
    "act_science_data": ["chart reading", "figure interpretation"],
    "pacing_and_timing": ["pacing", "timing", "time management", "test anxiety", "guessing"],
}

# Broad subject words a student is likely to type. Each points at the most
# common entry point for that area so a vague weakness still lands somewhere real.
SKILL_ALIASES["lines_angles_triangles"].append("geometry")
SKILL_ALIASES["linear_equations_one"].append("algebra")
SKILL_ALIASES["one_variable_data"].extend(["statistics", "data analysis"])
SKILL_ALIASES["boundaries"].append("grammar")
SKILL_ALIASES["central_ideas"].extend(["reading comprehension", "comprehension"])

# Broad words that should only break ties, never decide a match on their own.
_WEAK_MATCH_WORDS = {"math", "reading", "writing", "english", "science", "test", "question", "questions"}


def resolve_skill(skill_key, fallback_label=""):
    """Map a possibly-invented key onto the taxonomy, never returning None.

    Scoring favours longer and more specific matches so that "quadratic
    equations" lands on quadratic_functions rather than on the first taxonomy
    entry that happens to contain the word "equations".
    """
    key = re.sub(r"[^a-z0-9_]+", "_", str(skill_key or "").strip().lower()).strip("_")
    if key in SKILL_TAXONOMY:
        label, subject, domain, test = SKILL_TAXONOMY[key]
        return {"skill_key": key, "skill_label": label, "subject": subject, "domain": domain, "test": test}

    haystack = re.sub(r"[^a-z ]+", " ", f"{key.replace('_', ' ')} {fallback_label}".lower())
    haystack = re.sub(r"\s+", " ", haystack).strip()
    if not haystack:
        return _entry("pacing_and_timing")

    best_key, best_score = None, 0.0
    for candidate, (label, _, _, _) in SKILL_TAXONOMY.items():
        score = 0.0
        for word in re.split(r"[^a-z]+", label.lower()):
            if len(word) > 3 and re.search(rf"\b{word}", haystack):
                score += 1.0 if word in _WEAK_MATCH_WORDS else len(word)
        for alias in SKILL_ALIASES.get(candidate, []):
            if alias in haystack:
                # Aliases are what the student actually typed, so weight them above
                # incidental label-word overlap.
                score += 2 * len(alias)
        if score > best_score:
            best_key, best_score = candidate, score

    if best_key and best_score >= 5:
        return _entry(best_key)

    label = (str(fallback_label) or "Test Strategy").strip()[:80] or "Test Strategy"
    subject = "Math" if re.search(r"algebra|equation|geometr|function|math|number|graph", haystack) \
        else "Reading and Writing"
    return {
        "skill_key": "pacing_and_timing", "skill_label": label, "subject": subject,
        "domain": "algebra" if subject == "Math" else "reading", "test": "BOTH",
    }


def _entry(key):
    label, subject, domain, test = SKILL_TAXONOMY[key]
    return {"skill_key": key, "skill_label": label, "subject": subject, "domain": domain, "test": test}


# --- Unit shape -----------------------------------------------------------
# The server owns the shape of the unit. The model chooses *what* to teach, not
# how many steps exist or what order they come in, which is what kept the old
# single-call generator producing five near-identical "go read something" rows.

CANONICAL_SHAPE = ["lesson", "practice_sprint", "lesson", "quiz", "boss_battle"]
REINFORCE_SHAPE = ["lesson", "practice_sprint", "practice_sprint", "quiz", "boss_battle"]
DRILL_SHAPE = ["practice_sprint", "lesson", "practice_sprint", "quiz", "boss_battle"]

NODE_LABELS = {
    "lesson": "Lesson",
    "practice_sprint": "Practice",
    "quiz": "Review",
    "boss_battle": "Checkpoint",
}

XP_BY_NODE = {"lesson": 30, "practice_sprint": 20, "quiz": 40, "boss_battle": 100}
EXERCISE_COUNT = {"practice_sprint": 6, "quiz": 8}
TEACH_CARD_COUNT = 5
LESSON_CHECK_COUNT = 5


def choose_shape(mastery_rows, completed_lessons):
    """Pick a unit shape from how much teaching the student already has.

    A student with no lesson history needs instruction first; one with several
    weak-but-taught skills needs reps more than new material.
    """
    if not completed_lessons:
        return CANONICAL_SHAPE
    weak_taught = [
        row for row in mastery_rows
        if row.get("attempts", 0) >= 4 and row.get("accuracy", 1.0) < 0.7
    ]
    if len(weak_taught) >= 2:
        return REINFORCE_SHAPE
    if completed_lessons >= 4 and not weak_taught:
        return DRILL_SHAPE
    return CANONICAL_SHAPE


# --- JSON helpers ---------------------------------------------------------

def _parse_json(raw, expect_key=None):
    """Parse model JSON tolerantly; raise ValueError when nothing usable."""
    if not raw:
        raise ValueError("empty response")
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]", "", str(raw)).strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.I | re.M).strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            raise ValueError(f"no JSON object found in: {text[:300]}")
        try:
            data = json.loads(match.group(0))
        except json.JSONDecodeError as error:
            # A truncated array is the common failure. Salvage whole elements.
            salvaged = _salvage_truncated_array(match.group(0), expect_key)
            if salvaged is not None:
                return salvaged
            raise ValueError(f"unparseable JSON: {error}") from error
    if expect_key and isinstance(data, dict) and expect_key not in data:
        for value in data.values():
            if isinstance(value, list):
                return {expect_key: value}
        raise ValueError(f"missing key '{expect_key}'")
    return data


def _salvage_truncated_array(text, expect_key):
    """Recover the complete objects from an array cut off mid-element."""
    if not expect_key:
        return None
    start = text.find(f'"{expect_key}"')
    if start == -1:
        return None
    bracket = text.find("[", start)
    if bracket == -1:
        return None
    items, depth, buffer, in_string, escaped = [], 0, "", False, False
    for char in text[bracket + 1:]:
        if escaped:
            escaped = False
        elif char == "\\":
            escaped = True
        elif char == '"':
            in_string = not in_string
        if not in_string:
            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    buffer += char
                    try:
                        items.append(json.loads(buffer))
                    except json.JSONDecodeError:
                        pass
                    buffer = ""
                    continue
            elif depth == 0:
                continue
        if depth > 0:
            buffer += char
    return {expect_key: items} if items else None


def _clean(value, limit=2000):
    text = str(value or "").strip()
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", text)
    return text[:limit]


def _call(prompt, *, tokens, system, retries=1, expect_key=None, thinking="low"):
    """Run a generation with one retry, returning parsed JSON or raising."""
    last_error = None
    for attempt in range(retries + 1):
        try:
            raw = _generate_text(
                prompt,
                max_output_tokens=tokens,
                json_output=True,
                thinking_level=thinking,
                system_instruction=system,
            )
            return _parse_json(raw, expect_key=expect_key)
        except Exception as error:  # noqa: BLE001 - retry on any generation fault
            last_error = error
            _log("learning: generation attempt %s failed: %s", attempt + 1, error)
    raise ValueError(str(last_error))


# --- Question validation --------------------------------------------------

def _valid_question(item, *, needs_prompt):
    """Reject anything a student could not actually answer."""
    if not isinstance(item, dict):
        return None
    question = _clean(item.get("question_text") or item.get("question"), 1200)
    options = item.get("options")
    if not question or len(question) < 15:
        return None
    if not isinstance(options, list) or len(options) != 4:
        return None
    options = [_clean(o, 400) for o in options]
    if any(not o for o in options):
        return None
    if len({o.lower() for o in options}) != 4:
        return None
    # The old generator emitted literal placeholders. Never persist those again.
    if any(re.fullmatch(r"[a-d]|option [a-d]|choice [a-d]", o.strip().lower()) for o in options):
        return None
    if re.search(r"practice (?:question|problem) \d+ on\b", question, re.I):
        return None
    try:
        correct = int(item.get("correct_option", item.get("correct", -1)))
    except (TypeError, ValueError):
        return None
    if not 0 <= correct < 4:
        return None
    explanation = _clean(item.get("explanation"), 1500)
    if len(explanation) < 25:
        return None
    source = _clean(
        item.get("source_or_prompt") or item.get("passage") or item.get("stimulus"), 3000
    )
    if needs_prompt and len(source) < 40:
        return None
    return {
        "question_text": question,
        "options": options,
        "correct_option": correct,
        "explanation": explanation,
        "source_or_prompt": source or "Every detail you need is in the question below.",
        "difficulty": _clean(item.get("difficulty"), 12).lower() or "medium",
    }


def _dedupe(items):
    """Drop repeats, keyed on the stimulus as well as the stem.

    Digital SAT Reading and Writing questions share a fixed stem -- every
    words-in-context item asks "Which choice completes the text with the most
    logical and precise word or phrase?" -- so fingerprinting the stem alone
    collapses a whole valid set down to one question.
    """
    seen, unique = set(), []
    for item in items:
        basis = f"{item.get('source_or_prompt', '')} {item['question_text']}"
        fingerprint = re.sub(r"[^a-z0-9]+", "", basis.lower())[:160]
        if fingerprint in seen:
            continue
        seen.add(fingerprint)
        unique.append(item)
    return unique


# --- Prompt fragments -----------------------------------------------------

SYSTEM_TUTOR = (
    "You are the Mentics tutor: an expert Digital SAT and ACT instructor who writes "
    "the actual teaching material, not instructions telling a student to go find it. "
    "You never say 'read an article about X' or 'watch a video on Y'. You teach X "
    "directly, with concrete worked examples and real numbers or real sentences. "
    "You always reply with a single raw JSON object and nothing else."
)

_DSAT_FACTS = (
    "Digital SAT format facts you must respect: the test is adaptive and section-based. "
    "Reading and Writing uses SHORT standalone passages of 25-150 words, each with exactly "
    "ONE question. There is no long shared passage and no paired long-passage set except for "
    "the two cross-text questions. Math allows Desmos on the whole section. There is no essay "
    "and no separate no-calculator module. Never write questions in the retired paper-SAT style."
)

_ACT_FACTS = (
    "ACT format facts you must respect: English uses a passage with underlined portions; Math is "
    "1-36 with 5 answer choices on the real test, but for this drill use exactly 4 choices; "
    "Reading uses long passages; Science uses figures, tables, and experiment summaries."
)


def _format_facts(test_focus):
    return _ACT_FACTS if (test_focus or "").lower() == "act" else _DSAT_FACTS


def _needs_passage(skill):
    """Reading and Writing items are unanswerable without their stimulus."""
    return skill["subject"] not in _MATH_SUBJECTS and skill["domain"] in {
        "reading", "writing", "grammar", "science"
    }


# --- Call 1: the planner --------------------------------------------------

def plan_unit(profile, shape, *, skill_options):
    """Produce the five-node plan: what to teach, why, and a per-node syllabus.

    The per-node syllabus is what lets the teaching call and the exercise call
    for the same node run in parallel and still line up with each other.
    """
    catalog = "\n".join(
        f"- {key}: {SKILL_TAXONOMY[key][0]} ({SKILL_TAXONOMY[key][1]})"
        for key in skill_options
    )
    shape_lines = "\n".join(
        f"{index + 1}. {node} ({NODE_LABELS[node]})" for index, node in enumerate(shape)
    )

    prompt = f"""# ROLE
Design one adaptive learning unit for a student preparing for the {profile['focus_label']}.

# STUDENT
- Target test: {profile['focus_label']}
- Current scores: {profile['current_scores']}
- Goal scores: {profile['goal_scores']}
- Test date: {profile['test_date']}
- Weekly study time: {profile['hours_per_week']}
- Self-reported strengths: {profile['strengths']}
- Self-reported weaknesses: {profile['weaknesses']}

# MEASURED PERFORMANCE
Per-skill mastery from work already graded inside Mentics:
{profile['mastery_summary']}

Questions this student recently answered incorrectly:
{profile['recent_mistakes']}

Skills already taught in earlier units (do not re-teach unless mastery is below 70%):
{profile['taught_skills']}

# WHAT THE STUDENT HAS ASKED FOR
Standing focus they set (keep honouring this until they change it): {profile.get('standing_focus', 'None stated.')}

Most recent request (highest priority if it asks for a change):
{profile['latest_request']}

Recent conversation:
{profile['chat_history']}

A stated focus outranks what the scores alone would suggest. If the student asked for math,
this unit is a math unit, and you pick the math skills their results say are weakest. Only
ignore a standing focus if they have clearly since asked for something else.

# UNIT SHAPE (FIXED - DO NOT CHANGE)
{shape_lines}

How the nodes relate to each other:
- A `lesson` node introduces a NEW skill and teaches it from scratch.
- A `practice_sprint` node DRILLS the skill from the lesson immediately before it. Give it
  that same skill_key. Its syllabus should be the harder or trickier variants of that skill.
- The `quiz` node REVIEWS the skills already taught in this unit. Give it the skill_key of
  the most important one. Never introduce a new skill at the quiz.
- The final `boss_battle` node is a full official practice test and is handled by the server.

# SKILL CATALOG (use these exact keys)
{catalog}

# YOUR JOB
Choose the skills that will move this student's score the most. Work in this order of
authority:
1. A standing or latest focus the student asked for. Honour it.
2. Measured mastery and the specific questions they got wrong. A skill they are failing at
   40% beats a skill they merely listed as a weakness.
3. Self-reported weaknesses, then score gaps, then high-yield defaults.

Do not re-teach a skill they are already above 85% on unless they asked for it. If their
recent mistakes cluster around one sub-skill, teach that sub-skill specifically rather than
the broad topic it sits in.
The two lesson nodes should teach two DIFFERENT skills.

For each node write a `syllabus`: 4 concrete sub-concepts, written as specific teachable
claims, not topic names. Bad: "understand transitions". Good: "contrast transitions
(however, nevertheless) signal that the second idea limits or reverses the first".

The `reason` must cite this student's own data.

# OUTPUT
Return raw JSON only:
{{
  "unit_title": "short name for this unit, 2-5 words",
  "unit_summary": "one sentence telling the student what they will be able to do after this unit",
  "nodes": [
    {{
      "node_type": "{shape[0]}",
      "skill_key": "exact key from the catalog",
      "title": "student-facing node title, max 8 words",
      "objective": "one sentence: what the student will be able to do",
      "syllabus": ["claim 1", "claim 2", "claim 3", "claim 4"],
      "reason": "why this node, citing the student's data",
      "difficulty": "easy | medium | hard"
    }}
  ]
}}
Return exactly {len(shape)} nodes in the fixed order above."""

    data = _call(
        prompt,
        tokens=2600,
        system=SYSTEM_TUTOR,
        expect_key="nodes",
        retries=1,
    )
    return data


# Ordered by how much a point of improvement is worth on the Digital SAT, used
# only when there is nothing measured and nothing self-reported to go on.
HIGH_YIELD_DEFAULTS = {
    "sat": ["words_in_context", "linear_equations_two", "transitions", "boundaries",
            "quadratic_functions", "central_ideas", "ratios_rates", "systems_of_equations"],
    "act": ["act_english_usage", "act_math_prealgebra", "act_reading_detail",
            "act_science_data", "act_english_rhetoric", "act_math_coordinate"],
}


def _candidate_skills(profile):
    """Rank skills to teach when the planner gives us nothing usable.

    Measured weakness beats self-reported weakness, which beats a generic
    high-yield default.
    """
    ordered = []

    for row in sorted(profile.get("_mastery_rows") or [], key=lambda r: r.get("accuracy", 1.0)):
        if row.get("attempts", 0) >= 3 and row.get("accuracy", 1.0) < 0.8:
            ordered.append(row.get("skill_key"))

    for phrase in re.split(r"[,;/]|\band\b", str(profile.get("weaknesses") or "")):
        phrase = phrase.strip()
        if len(phrase) > 2:
            ordered.append(resolve_skill("", phrase)["skill_key"])

    focus = "act" if (profile.get("focus") or "sat").lower() == "act" else "sat"
    ordered.extend(HIGH_YIELD_DEFAULTS[focus])

    allowed = set(profile.get("skill_options") or SKILL_TAXONOMY)
    seen, ranked = set(), []
    for key in ordered:
        if key and key in SKILL_TAXONOMY and key in allowed and key not in seen \
                and key != "pacing_and_timing":
            seen.add(key)
            ranked.append(key)
    return ranked or HIGH_YIELD_DEFAULTS[focus]


def _normalize_plan(data, shape, profile):
    """Force the plan onto the server-owned shape, filling any gaps."""
    raw_nodes = data.get("nodes") if isinstance(data, dict) else None
    raw_nodes = raw_nodes if isinstance(raw_nodes, list) else []

    candidates = _candidate_skills(profile)
    nodes, used_keys, used_order = [], set(), []

    for index, node_type in enumerate(shape):
        raw = raw_nodes[index] if index < len(raw_nodes) and isinstance(raw_nodes[index], dict) else {}
        if node_type == "boss_battle":
            nodes.append(_boss_battle_node(profile))
            continue

        skill = resolve_skill(raw.get("skill_key"), raw.get("title") or "")
        if skill["skill_key"] == "pacing_and_timing" and not raw.get("skill_key"):
            previous = nodes[-1] if nodes else None
            if node_type == "quiz" and used_order:
                # A review node reviews what this unit already taught. Handing it
                # a brand-new skill would test material the student never saw.
                skill = resolve_skill(used_order[0])
            elif node_type == "practice_sprint" and previous and previous["node_type"] == "lesson":
                # Drill immediately reinforces the lesson it follows.
                skill = dict(previous["skill"])
            else:
                # The planner said nothing usable; fall back to the best-evidenced
                # skill we have not used yet.
                skill = resolve_skill(next(
                    (key for key in candidates if key not in used_keys), candidates[0]
                ))

        # Two nodes teaching the identical skill wastes a slot in a five-node unit.
        if skill["skill_key"] in used_keys and node_type == "lesson":
            replacement = next((key for key in candidates if key not in used_keys), None)
            if replacement:
                skill = resolve_skill(replacement)
        if skill["skill_key"] not in used_keys:
            used_keys.add(skill["skill_key"])
            used_order.append(skill["skill_key"])

        syllabus = [
            _clean(item, 240) for item in (raw.get("syllabus") or [])
            if isinstance(item, str) and len(_clean(item, 240)) > 12
        ][:5]
        if len(syllabus) < 2:
            syllabus = _default_syllabus(skill)

        title = _clean(raw.get("title"), 90) or skill["skill_label"]
        objective = _clean(raw.get("objective"), 300) or (
            f"Recognize and correctly answer {skill['skill_label']} questions under time pressure."
        )
        reason = _clean(raw.get("reason"), 700) or (
            f"Your graded work shows {skill['skill_label']} is costing you points, so this unit targets it directly."
        )
        difficulty = (raw.get("difficulty") or "medium").lower()
        if difficulty not in {"easy", "medium", "hard"}:
            difficulty = "medium"

        nodes.append({
            "node_type": node_type,
            "skill": skill,
            "title": title,
            "objective": objective,
            "syllabus": syllabus,
            "reason": reason,
            "difficulty": difficulty,
        })

    unit_title = _clean(data.get("unit_title"), 80) if isinstance(data, dict) else ""
    unit_summary = _clean(data.get("unit_summary"), 300) if isinstance(data, dict) else ""
    teaching = [n for n in nodes if n["node_type"] != "boss_battle"]
    if not unit_title and teaching:
        unit_title = teaching[0]["skill"]["skill_label"]
    if not unit_summary and teaching:
        unit_summary = teaching[0]["objective"]
    return {"unit_title": unit_title or "Your next unit", "unit_summary": unit_summary, "nodes": nodes}


def _default_syllabus(skill):
    label = skill["skill_label"]
    if skill["subject"] in _MATH_SUBJECTS:
        return [
            f"Recognize the setup that signals a {label} question.",
            f"Translate the wording of a {label} problem into one equation or relationship.",
            f"Run the standard solution method for {label} start to finish.",
            f"Check the answer against the question actually asked, and use Desmos to verify.",
        ]
    return [
        f"Identify what a {label} question is really testing before reading the choices.",
        f"Find the evidence in the text that settles a {label} question.",
        f"Predict the answer in your own words before looking at the options.",
        f"Eliminate the trap choices that {label} questions reliably include.",
    ]


def _boss_battle_node(profile):
    is_act = (profile.get("focus") or "sat").lower() == "act"
    if is_act:
        link = "https://www.act.org/content/act/en/products-and-services/the-act/test-preparation/free-act-test-prep.html"
        platform = "the official ACT practice platform"
        stat = "act_composite"
        test_name = "ACT"
    else:
        link = "https://satsuite.collegeboard.org/sat/practice-preparation/practice-tests"
        platform = "Bluebook"
        stat = "sat_total"
        test_name = "SAT"
    return {
        "node_type": "boss_battle",
        "skill": resolve_skill("pacing_and_timing"),
        "title": f"Boss Battle: full official {test_name}",
        "objective": f"Sit a complete, timed official {test_name} practice test and log the score.",
        "syllabus": [],
        "reason": (
            "Everything in this unit was drilled in short bursts. A full timed test is the only way to "
            "prove the gains survive real pacing and fatigue."
        ),
        "difficulty": "hard",
        "stat_to_update": stat,
        "resource_url": link,
        "platform": platform,
        "test_name": test_name,
    }


# --- Call 2: teaching cards ----------------------------------------------

def generate_teaching(node, profile):
    """Concept cards for one lesson node: the part that actually teaches."""
    skill = node["skill"]
    syllabus = "\n".join(f"- {item}" for item in node["syllabus"])
    is_math = skill["subject"] in _MATH_SUBJECTS

    example_rule = (
        "Every card's `worked_example` must contain real numbers and every algebraic step, "
        "written so a student can follow it without any other resource. Show the arithmetic."
        if is_math else
        "Every card's `worked_example` must quote a real sentence or short passage you write "
        "yourself, then walk through the reasoning on that exact text word by word."
    )

    prompt = f"""# TASK
Write the teaching content for a lesson on **{skill['skill_label']}** ({skill['subject']}) for a
student preparing for the {profile['focus_label']}.

{_format_facts(profile.get('focus'))}

# LESSON OBJECTIVE
{node['objective']}

# SUB-CONCEPTS TO COVER (one card each, in this order)
{syllabus}

# STUDENT CONTEXT
- Level: {profile['level_hint']}
- Why this lesson: {node['reason']}
- Mistakes this student has actually made on related questions:
{profile['recent_mistakes']}

# RULES
1. TEACH. Do not tell the student to read, watch, or look up anything. You are the lesson.
2. {example_rule}
3. `body` is 70-130 words of plain, direct explanation. Use markdown for emphasis and short
   lists. No headings inside the body.
4. `takeaway` is one sentence the student could repeat from memory during the test.
5. `trap` names the specific wrong move students make on this sub-concept and how to catch it.
6. Never use bracketed placeholders like [concept] or [insert example]. Write the real thing.
7. Write to a motivated high-school student. Warm, direct, no filler, no hype.

# OUTPUT
Raw JSON only:
{{
  "intro": "2-3 sentences telling the student what this lesson fixes and why it is worth their time",
  "cards": [
    {{
      "title": "short card title, max 7 words",
      "body": "70-130 words that teach the sub-concept",
      "worked_example": "a complete worked example with real content",
      "takeaway": "one memorable sentence",
      "trap": "the specific mistake to avoid"
    }}
  ],
  "recap": "3-5 sentence summary the student can review before the practice"
}}
Return exactly {len(node['syllabus'])} cards, one per sub-concept, in order."""

    data = _call(prompt, tokens=4200, system=SYSTEM_TUTOR, expect_key="cards", retries=1)
    cards = []
    for raw in data.get("cards", []) if isinstance(data, dict) else []:
        if not isinstance(raw, dict):
            continue
        body = _clean(raw.get("body"), 2200)
        if len(body) < 80:
            continue
        if re.search(r"\[(?:core|insert|concept|example|topic|your)\b[^\]]*\]", body, re.I):
            continue  # the old template's placeholder disease
        cards.append({
            "title": _clean(raw.get("title"), 90) or skill["skill_label"],
            "body": body,
            "worked_example": _clean(raw.get("worked_example"), 2500),
            "takeaway": _clean(raw.get("takeaway"), 400),
            "trap": _clean(raw.get("trap"), 600),
        })
    if not cards:
        raise ValueError("no usable teaching cards")
    return {
        "intro": _clean(data.get("intro"), 900),
        "cards": cards[:TEACH_CARD_COUNT],
        "recap": _clean(data.get("recap"), 1200),
    }


# --- Call 3: exercises ----------------------------------------------------

def generate_exercises(node, profile, count, *, cumulative_skills=None):
    """Real practice items for a node. Never placeholders."""
    skill = node["skill"]
    needs_prompt = _needs_passage(skill)
    syllabus = "\n".join(f"- {item}" for item in node["syllabus"]) or f"- Core {skill['skill_label']} technique"

    if cumulative_skills:
        catalog = "\n".join(
            f"- {key}: {SKILL_TAXONOMY[key][0]}" for key in cumulative_skills if key in SKILL_TAXONOMY
        )
        coverage = (
            "This is a cumulative review. Spread the questions roughly evenly across these skills, "
            "and tag each question with the key of the skill it actually tests:\n" + catalog
        )
        skill_field = '      "skill_key": "which skill from the list above this question tests",\n'
    else:
        coverage = f"Every question tests {skill['skill_label']} specifically."
        skill_field = ""

    if needs_prompt:
        stimulus_rule = (
            "`source_or_prompt` MUST contain the passage, sentence, or data description the question "
            "refers to. Write it yourself, 25-150 words, in the short standalone Digital SAT style. "
            "The student sees only what you put in these fields, so a question that references a text "
            "you did not include is worthless."
        )
    else:
        stimulus_rule = (
            "`source_or_prompt` should carry any table, scenario, or setup the question needs, or a "
            "one-line note that the question is self-contained. Never reference a figure you did not describe."
        )

    difficulty_mix = {
        "easy": "3 easy, 2 medium, 1 hard",
        "medium": "2 easy, 3 medium, 1 hard",
        "hard": "1 easy, 3 medium, 2 hard",
    }.get(node["difficulty"], "2 easy, 3 medium, 1 hard")

    prompt = f"""# TASK
Write {count} original multiple-choice practice questions on **{skill['skill_label']}**
({skill['subject']}) for the {profile['focus_label']}.

{_format_facts(profile.get('focus'))}

# COVERAGE
{coverage}

# SUB-CONCEPTS THE STUDENT JUST STUDIED
{syllabus}

# THIS STUDENT'S KNOWN MISTAKES
{profile['recent_mistakes']}
Where it fits naturally, include one question that targets a mistake above.

{profile['official_examples']}

# RULES
1. {stimulus_rule}
2. Exactly 4 answer choices. Exactly one is correct. All four must be plausible to a student
   who half-understands the concept.
3. Every distractor must encode a specific misconception, not noise.
4. `explanation` states why the correct answer is right AND names the misconception behind
   each wrong choice. 40-120 words.
5. Difficulty mix across the set: {difficulty_mix}.
6. Vary `correct_option` across the set. Do not make it 0 every time.
7. Never emit placeholder text. Every question must be fully answerable as written.

# OUTPUT
Raw JSON only:
{{
  "questions": [
    {{
{skill_field}      "source_or_prompt": "the passage, data, or setup the question depends on",
      "question_text": "the question itself",
      "options": ["choice A", "choice B", "choice C", "choice D"],
      "correct_option": 0,
      "explanation": "why the right answer is right and each wrong one is wrong",
      "difficulty": "easy | medium | hard"
    }}
  ]
}}
Return exactly {count} questions."""

    data = _call(
        prompt,
        tokens=900 * count + 800,
        system=SYSTEM_TUTOR,
        expect_key="questions",
        retries=1,
    )
    allowed_keys = set(cumulative_skills or ())
    items = []
    for raw in data.get("questions", []) if isinstance(data, dict) else []:
        valid = _valid_question(raw, needs_prompt=needs_prompt)
        if not valid:
            continue
        # Mastery is tracked per skill, so a cumulative review must attribute each
        # answer to the skill it actually tested rather than to the node's headline skill.
        tagged = str(raw.get("skill_key") or "").strip()
        valid["skill_key"] = tagged if tagged in allowed_keys else skill["skill_key"]
        items.append(valid)
    items = _dedupe(items)
    if len(items) < max(2, count // 2):
        raise ValueError(f"only {len(items)} of {count} questions were usable")
    return items[:count]


def generate_lesson_checks(node, profile, count=LESSON_CHECK_COUNT):
    """In-lesson comprehension checks, phrased as coaching rather than testing."""
    return generate_exercises(node, profile, count)


# --- Orchestration --------------------------------------------------------

def build_unit(profile, *, shape=None, official_examples_fn=None, max_workers=6):
    """Plan a unit, then generate every node's content concurrently.

    Returns a dict with `unit_title`, `unit_summary`, and `nodes`, where each
    node carries the content the student needs. Content failures degrade the
    node rather than the unit: a lesson that loses its checks is still a lesson.
    """
    shape = shape or CANONICAL_SHAPE
    profile = dict(profile)
    profile.setdefault("skill_options", skill_catalog(profile.get("focus")))

    try:
        raw_plan = plan_unit(profile, shape, skill_options=profile["skill_options"])
    except Exception as error:  # noqa: BLE001
        _log("learning: planner failed (%s); using weakness-seeded fallback plan", error)
        raw_plan = {}
    plan = _normalize_plan(raw_plan, shape, profile)

    taught_keys, taught_labels = [], []
    for node in plan["nodes"]:
        if node["node_type"] in ("lesson", "practice_sprint") and node["skill"]["skill_key"] not in taught_keys:
            taught_keys.append(node["skill"]["skill_key"])
            taught_labels.append(node["skill"]["skill_label"])

    jobs = []
    for index, node in enumerate(plan["nodes"]):
        if node["node_type"] == "boss_battle":
            continue
        node_profile = dict(profile)
        if official_examples_fn:
            try:
                node_profile["official_examples"] = official_examples_fn(node["skill"])
            except Exception:  # noqa: BLE001
                node_profile["official_examples"] = ""
        node_profile.setdefault("official_examples", "")

        if node["node_type"] == "lesson":
            jobs.append((index, "teaching", node, node_profile, None))
            jobs.append((index, "checks", node, node_profile, LESSON_CHECK_COUNT))
        elif node["node_type"] == "practice_sprint":
            jobs.append((index, "exercises", node, node_profile, EXERCISE_COUNT["practice_sprint"]))
        elif node["node_type"] == "quiz":
            jobs.append((index, "exercises", node, node_profile, EXERCISE_COUNT["quiz"]))

    def run(job):
        index, kind, node, node_profile, count = job
        try:
            if kind == "teaching":
                return index, kind, generate_teaching(node, node_profile)
            if kind == "checks":
                return index, kind, generate_lesson_checks(node, node_profile, count)
            cumulative = taught_keys if node["node_type"] == "quiz" else None
            return index, kind, generate_exercises(
                node, node_profile, count, cumulative_skills=cumulative
            )
        except Exception as error:  # noqa: BLE001
            _log(
                "learning: %s generation failed for node %s (%s): %s",
                kind, index + 1, node["skill"]["skill_key"], error,
            )
            return index, kind, None

    results = {}
    if jobs:
        with ThreadPoolExecutor(max_workers=min(max_workers, len(jobs))) as pool:
            for index, kind, payload in pool.map(run, jobs):
                results[(index, kind)] = payload

    for index, node in enumerate(plan["nodes"]):
        node["xp_reward"] = XP_BY_NODE[node["node_type"]]
        if node["node_type"] == "lesson":
            teaching = results.get((index, "teaching"))
            checks = results.get((index, "checks")) or []
            if not teaching:
                teaching = _fallback_teaching(node)
            node["teaching"] = teaching
            node["checks"] = checks
            node["steps"] = _interleave_lesson(teaching, checks)
        elif node["node_type"] in ("practice_sprint", "quiz"):
            questions = results.get((index, "exercises")) or []
            node["questions"] = questions
            node["content_ok"] = bool(questions)

    plan["taught_labels"] = taught_labels
    plan["taught_keys"] = taught_keys
    return plan


def _interleave_lesson(teaching, checks):
    """Alternate teach and check the way a Duolingo lesson alternates.

    Teaching first, then a check on what was just taught, so the student is
    never asked about material they have not seen.
    """
    steps = []
    cards = teaching.get("cards", [])
    for position, card in enumerate(cards):
        steps.append({
            "step_type": "teach",
            "title": card["title"],
            "body": card["body"],
            "worked_example": card.get("worked_example", ""),
            "takeaway": card.get("takeaway", ""),
            "trap": card.get("trap", ""),
        })
        if position < len(checks):
            check = checks[position]
            steps.append({
                "step_type": "check",
                "title": "Quick check",
                "source_or_prompt": check["source_or_prompt"],
                "question_text": check["question_text"],
                "options": check["options"],
                "correct_option": check["correct_option"],
                "explanation": check["explanation"],
            })
    # Any checks past the last card become a short closing drill.
    for check in checks[len(cards):]:
        steps.append({
            "step_type": "check",
            "title": "Quick check",
            "source_or_prompt": check["source_or_prompt"],
            "question_text": check["question_text"],
            "options": check["options"],
            "correct_option": check["correct_option"],
            "explanation": check["explanation"],
        })
    if teaching.get("recap"):
        steps.append({
            "step_type": "recap",
            "title": "What you just learned",
            "body": teaching["recap"],
        })
    return steps


def _fallback_teaching(node):
    """A real, usable lesson when generation fails outright.

    This is deliberately concrete. The previous implementation shipped a
    template full of bracketed placeholders, which is worse than nothing
    because it looks like content while teaching the student nothing.
    """
    skill = node["skill"]
    label = skill["skill_label"]
    is_math = skill["subject"] in _MATH_SUBJECTS
    cards = []
    for item in node["syllabus"][:4]:
        if is_math:
            body = (
                f"**{item}**\n\nOn the {label} questions you will see, the work is almost always the same "
                "three moves: name the quantity the question wants, write one equation that connects what "
                "you were given to that quantity, then solve and check the result against the wording of "
                "the question. Most lost points here are not algebra errors. They come from solving for the "
                "wrong thing, or from stopping one step early. Write the target quantity down before you "
                "start solving, and circle it when you are done."
            )
            example = (
                "Worked example: if 3x + 7 = 25, then 3x = 18 and x = 6. If the question asked for x + 2, "
                "the answer is 8, not 6. Substitute back: 3(6) + 7 = 25 confirms the solve, and reading the "
                "question again confirms which number to report."
            )
            trap = "Solving correctly for x when the question asked for something built from x."
        else:
            body = (
                f"**{item}**\n\nFor {label}, the choices are designed so that more than one will look "
                "acceptable if you read only the words near the question. Read the full sentence or short "
                "passage first and decide, in your own words, what the answer has to do. Then find the "
                "choice that matches your prediction. Choosing before you predict is how students end up "
                "picking an answer that is true about the passage but does not answer the question asked."
            )
            example = (
                "Worked example: in 'The results were surprising; the researchers had expected no change at "
                "all,' the second clause explains the first. A transition here must signal explanation, so "
                "'in fact' fits and 'however' does not, even though 'however' feels natural after a "
                "surprising claim."
            )
            trap = "Picking a choice that is true about the text but does not answer the question asked."
        cards.append({
            "title": item[:80],
            "body": body,
            "worked_example": example,
            "takeaway": f"Name what the question wants before you evaluate any choice on {label}.",
            "trap": trap,
        })
    if not cards:
        cards = [{
            "title": label,
            "body": (
                f"{label} rewards a repeatable process over cleverness. Classify the question, apply the "
                "one method that fits that classification, then verify against the exact wording before "
                "you move on."
            ),
            "worked_example": "",
            "takeaway": f"Classify first, then solve, then verify on every {label} question.",
            "trap": "Improvising a method instead of recognizing the question type.",
        }]
    return {
        "intro": (
            f"This lesson is about {label}. {node['objective']} Work through each card, then the checks "
            "will tell you whether it stuck."
        ),
        "cards": cards,
        "recap": (
            f"On {label}: classify the question, decide what the answer must do before reading the choices, "
            "apply one method rather than improvising, and verify against the exact wording. The practice "
            "step next will show you which of those four you are actually skipping."
        ),
    }


# --- Mastery --------------------------------------------------------------

def mastery_level(accuracy, attempts):
    """Duolingo-style crown level, 0-5, from measured accuracy."""
    if attempts < 3:
        return 0
    if accuracy >= 0.95 and attempts >= 12:
        return 5
    if accuracy >= 0.9 and attempts >= 8:
        return 4
    if accuracy >= 0.8 and attempts >= 6:
        return 3
    if accuracy >= 0.65:
        return 2
    return 1


def format_mastery_summary(rows):
    if not rows:
        return "No graded work yet -- this is the student's first measured unit."
    lines = []
    for row in sorted(rows, key=lambda r: r.get("accuracy", 1.0))[:12]:
        attempts = row.get("attempts", 0)
        accuracy = row.get("accuracy", 0.0)
        lines.append(
            f"- {row.get('skill_label', row.get('skill_key'))}: "
            f"{int(round(accuracy * 100))}% correct over {attempts} question(s), "
            f"mastery level {row.get('level', 0)}/5"
        )
    return "\n".join(lines)


# ==========================================================================
# College planning
# ==========================================================================
# College prep is taught the same way as test prep, because the failure mode is
# the same: a student told to "research colleges" does not know what good looks
# like. So the unit teaches the judgement first -- what separates a strong
# activities entry from a weak one, what a balanced list actually means -- and
# checks it with comparison questions, which is the form this material grades
# well in. The unit then ends in a real deliverable rather than a practice test.

COLLEGE_TAXONOMY = {
    # Foundation and self-knowledge
    "narrative_core": ("Your Application Narrative", "Applying", "narrative"),
    "fit_criteria": ("Defining College Fit", "Research", "research"),
    "college_list": ("Building a Balanced List", "Research", "research"),
    "affordability": ("Cost, Aid, and Net Price", "Money", "money"),
    "financial_aid_forms": ("FAFSA and CSS Profile", "Money", "money"),
    "scholarships": ("Finding and Winning Scholarships", "Money", "money"),
    # Profile building
    "course_rigor": ("Course Rigor and Schedule Planning", "Profile", "profile"),
    "activity_depth": ("Building Depth in Activities", "Profile", "profile"),
    "activities_list": ("Writing the Activities List", "Applying", "writing"),
    "honors_awards": ("Presenting Honors and Awards", "Applying", "writing"),
    "summer_planning": ("Making Summers Count", "Profile", "profile"),
    # Testing strategy
    "testing_strategy": ("Test Strategy and Test-Optional Decisions", "Testing", "testing"),
    # Essays
    "essay_topic": ("Finding Your Personal Statement Topic", "Essays", "writing"),
    "essay_structure": ("Structuring the Personal Statement", "Essays", "writing"),
    "essay_revision": ("Revising for Voice and Specificity", "Essays", "writing"),
    "why_us_essay": ("Writing the 'Why Us' Essay", "Essays", "writing"),
    "why_major_essay": ("Writing the 'Why This Major' Essay", "Essays", "writing"),
    "community_essay": ("Community and Identity Essays", "Essays", "writing"),
    "supplement_strategy": ("Managing Supplemental Essays", "Essays", "writing"),
    # Mechanics and people
    "recommendations": ("Requesting Strong Recommendations", "Applying", "people"),
    "common_app_mechanics": ("Common App Mechanics", "Applying", "mechanics"),
    "deadline_strategy": ("ED, EA, and Deadline Strategy", "Applying", "mechanics"),
    "demonstrated_interest": ("Demonstrated Interest", "Research", "research"),
    "interviews": ("College Interviews", "Applying", "people"),
    # Endgame
    "comparing_offers": ("Comparing Offers and Aid Packages", "Money", "money"),
    "waitlist_appeals": ("Waitlists and Aid Appeals", "Applying", "mechanics"),
}

COLLEGE_ALIASES = {
    "essay_topic": ["essay idea", "what to write about", "brainstorm", "personal statement topic"],
    "essay_structure": ["outline", "essay structure", "draft my essay"],
    "essay_revision": ["revise", "edit my essay", "make it better", "feedback"],
    "why_us_essay": ["why us", "why this college", "supplemental"],
    "college_list": ["college list", "school list", "reach", "safety", "target",
                     "balanced list", "where to apply", "my list"],
    "fit_criteria": ["fit", "what i want", "campus", "size", "location"],
    "affordability": ["cost", "tuition", "net price", "afford", "expensive"],
    "financial_aid_forms": ["fafsa", "css profile", "financial aid form"],
    "scholarships": ["scholarship", "merit aid", "grants"],
    "activities_list": ["activities", "extracurriculars list", "common app activities"],
    "activity_depth": ["extracurricular", "clubs", "leadership", "volunteering"],
    "recommendations": ["recommendation", "rec letter", "teacher letter", "counselor"],
    "deadline_strategy": ["early decision", "early action", "deadline", "regular decision", "ed", "ea"],
    "common_app_mechanics": ["common app", "application form", "submit"],
    "testing_strategy": ["test optional", "should i submit my score", "superscore"],
    "interviews": ["interview", "alumni interview"],
    "course_rigor": ["classes", "schedule", "ap", "honors", "course load"],
    "comparing_offers": ["decide", "which college", "compare offers", "award letter"],
}

# What the unit drives toward for each stage. The final node is a real
# deliverable, tracked the way a boss battle tracks a test score.
COLLEGE_MILESTONES = {
    "exploring": {
        "title": "Save five colleges worth exploring",
        "action": "Research five colleges against the fit criteria you just defined, and record one concrete note about each.",
        "stat": "colleges_researched",
        "unit": "colleges",
        "label": "How many colleges did you research?",
    },
    "researching": {
        "title": "Lock in a balanced college list",
        "action": "Finish a list with reach, target, and likely schools, each checked against cost and fit.",
        "stat": "colleges_researched",
        "unit": "colleges",
        "label": "How many colleges are on your list now?",
    },
    "applying": {
        "title": "Move an application to submitted",
        "action": "Complete and submit one full application, essays and activities list included.",
        "stat": "applications_submitted",
        "unit": "applications",
        "label": "How many applications have you submitted?",
    },
}

# Stage drives what a student can usefully act on right now.
COLLEGE_STAGE_FOCUS = {
    "exploring": ["fit_criteria", "activity_depth", "course_rigor", "narrative_core",
                  "affordability", "summer_planning", "testing_strategy"],
    "researching": ["college_list", "fit_criteria", "affordability", "essay_topic",
                    "activity_depth", "recommendations", "testing_strategy", "deadline_strategy"],
    "applying": ["essay_structure", "essay_revision", "activities_list", "why_us_essay",
                 "supplement_strategy", "common_app_mechanics", "deadline_strategy",
                 "recommendations", "why_major_essay", "financial_aid_forms"],
}

COLLEGE_SHAPE = ["lesson", "practice_sprint", "lesson", "quiz", "milestone"]

COLLEGE_XP = {"lesson": 30, "practice_sprint": 20, "quiz": 40, "milestone": 90}


def college_skill_options(stage):
    """Skills to offer the planner, weighted to the student's stage."""
    stage = (stage or "researching").lower()
    focus = COLLEGE_STAGE_FOCUS.get(stage, COLLEGE_STAGE_FOCUS["researching"])
    rest = [k for k in COLLEGE_TAXONOMY if k not in focus]
    return focus + rest


def resolve_college_skill(skill_key, fallback_label=""):
    """Map a key or phrase onto the college taxonomy."""
    key = re.sub(r"[^a-z0-9_]+", "_", str(skill_key or "").strip().lower()).strip("_")
    if key in COLLEGE_TAXONOMY:
        label, subject, domain = COLLEGE_TAXONOMY[key]
        return {"skill_key": key, "skill_label": label, "subject": subject,
                "domain": domain, "test": "COLLEGE"}

    haystack = re.sub(r"[^a-z ]+", " ", f"{key.replace('_', ' ')} {fallback_label}".lower())
    haystack = re.sub(r"\s+", " ", haystack).strip()
    best_key, best_score = None, 0.0
    for candidate, (label, _, _) in COLLEGE_TAXONOMY.items():
        score = 0.0
        for word in re.split(r"[^a-z]+", label.lower()):
            if len(word) > 3 and re.search(rf"\b{word}", haystack):
                score += len(word)
        for alias in COLLEGE_ALIASES.get(candidate, []):
            if alias in haystack:
                score += 2 * len(alias)
        if score > best_score:
            best_key, best_score = candidate, score
    if best_key and best_score >= 5:
        label, subject, domain = COLLEGE_TAXONOMY[best_key]
        return {"skill_key": best_key, "skill_label": label, "subject": subject,
                "domain": domain, "test": "COLLEGE"}
    label, subject, domain = COLLEGE_TAXONOMY["narrative_core"]
    return {"skill_key": "narrative_core", "skill_label": label, "subject": subject,
            "domain": domain, "test": "COLLEGE"}


SYSTEM_COUNSELOR = (
    "You are the Mentics college counselor: an experienced admissions advisor who writes the "
    "actual guidance, not instructions telling a student to go research it. You never say "
    "'look up how to write an essay'. You show them, with real example sentences, real list "
    "entries, and real comparisons between a weak version and a strong one. You are honest "
    "about what admissions officers actually notice and never promise outcomes. You always "
    "reply with a single raw JSON object and nothing else."
)

_COLLEGE_FACTS = (
    "Facts you must respect: the Common App activities list allows 10 activities with a 50-character "
    "position field and a 150-character description. The personal statement is 650 words. Most "
    "supplements are 100-400 words. Early Decision is binding; Early Action is not. FAFSA opens in "
    "the fall of senior year. Many colleges are test-optional, which is a strategic decision, not a "
    "free pass. Never invent a college's specific deadline, requirement, or acceptance rate -- speak "
    "about how to find and evaluate them instead."
)


def plan_college_unit(profile, shape):
    """Plan a college unit: what to teach now, given where the student is."""
    options = profile["skill_options"][:22]
    catalog = "\n".join(
        f"- {key}: {COLLEGE_TAXONOMY[key][0]}" for key in options if key in COLLEGE_TAXONOMY
    )
    shape_lines = "\n".join(
        f"{i + 1}. {node}" for i, node in enumerate(shape)
    )
    milestone = profile["milestone"]

    prompt = f"""# ROLE
Design one college-application learning unit for a high school student.

{_COLLEGE_FACTS}

# STUDENT
- Grade: {profile['grade']}
- Stage of the process: {profile['stage']}
- Intended majors or fields: {profile['majors']}
- Colleges they are considering: {profile['target_colleges']}
- Academic profile: {profile['academics']}
- Application progress so far: {profile['progress']}
- Skills already taught in earlier units (do not repeat): {profile['taught_skills']}

# WHAT THE STUDENT HAS ASKED FOR
Standing focus they set (keep honouring this until they change it): {profile.get('standing_focus', 'None stated.')}

Most recent request (highest priority if it asks for something specific):
{profile['latest_request']}

Recent conversation:
{profile['chat_history']}

A stated focus outranks what their stage alone would suggest. If they asked for help with
essays, this unit is an essay unit.

# UNIT SHAPE (FIXED)
{shape_lines}

How the nodes relate:
- A `lesson` teaches ONE application skill from scratch, with real examples.
- The `practice_sprint` drills judgement on the skill from the lesson before it: give it that
  same skill_key. Its questions compare weak and strong versions so the student learns to tell
  them apart.
- The `quiz` reviews the skills taught in this unit. Use the most important one's key.
- Node 5 is a real deliverable and is handled by the server. Ignore it.

# SKILL CATALOG (use these exact keys)
{catalog}

# YOUR JOB
Pick the skills that unblock this student RIGHT NOW at their stage, working toward this
deliverable: "{milestone['action']}". A senior in October needs essays and mechanics, not a
lecture on choosing activities. A sophomore needs profile building, not supplements.
The two lessons must teach DIFFERENT skills.

Each node needs a `syllabus`: 4 concrete, teachable claims -- not topic names.
Bad: "understand the activities list". Good: "lead the 150-character description with the
outcome you produced, not the role you held".

The `reason` must reference this student's own situation.

# OUTPUT
Raw JSON only:
{{
  "unit_title": "short name for this unit, 2-5 words",
  "unit_summary": "one sentence on what the student will be able to do after this unit",
  "nodes": [
    {{
      "node_type": "{shape[0]}",
      "skill_key": "exact key from the catalog",
      "title": "student-facing title, max 8 words",
      "objective": "one sentence: what they will be able to do",
      "syllabus": ["claim 1", "claim 2", "claim 3", "claim 4"],
      "reason": "why this now, citing their grade, stage, majors, or progress",
      "difficulty": "easy | medium | hard"
    }}
  ]
}}
Return exactly {len(shape) - 1} nodes, for positions 1 through {len(shape) - 1}."""

    return _call(prompt, tokens=2600, system=SYSTEM_COUNSELOR, expect_key="nodes", retries=1)


def generate_college_teaching(node, profile):
    """Teaching cards for a college lesson: show the work, never assign reading."""
    skill = node["skill"]
    syllabus = "\n".join(f"- {item}" for item in node["syllabus"])

    prompt = f"""# TASK
Write the teaching content for a lesson on **{skill['skill_label']}** for a student in
grade {profile['grade']} who is at the "{profile['stage']}" stage of applying to college.

{_COLLEGE_FACTS}

# LESSON OBJECTIVE
{node['objective']}

# SUB-CONCEPTS TO COVER (one card each, in this order)
{syllabus}

# STUDENT CONTEXT
- Intended majors: {profile['majors']}
- Colleges under consideration: {profile['target_colleges']}
- Academic profile: {profile['academics']}
- Progress so far: {profile['progress']}
- Why this lesson: {node['reason']}

# RULES
1. TEACH. Never tell the student to go read, watch, or research something. You are the lesson.
2. `worked_example` must show the real thing: an actual activities-list entry, an actual opening
   paragraph, an actual list of criteria. Where it helps, show a weak version and then the strong
   rewrite, and say exactly what changed and why it matters.
3. `body` is 70-130 words of direct, practical explanation. Markdown emphasis and short lists are
   fine. No headings inside the body.
4. `takeaway` is one sentence the student could act on today.
5. `trap` names the specific mistake students make here and how to catch it.
6. Never use bracketed placeholders. Write the real thing.
7. Be honest and concrete. No hype, no promises about admission, no invented statistics about
   specific colleges.

# OUTPUT
Raw JSON only:
{{
  "intro": "2-3 sentences on what this lesson fixes and why it matters at their stage",
  "cards": [
    {{
      "title": "short card title, max 7 words",
      "body": "70-130 words that teach the sub-concept",
      "worked_example": "a real example, ideally weak version then strong rewrite",
      "takeaway": "one actionable sentence",
      "trap": "the specific mistake to avoid"
    }}
  ],
  "recap": "3-5 sentence summary to review before the practice"
}}
Return exactly {len(node['syllabus'])} cards, one per sub-concept, in order."""

    data = _call(prompt, tokens=4200, system=SYSTEM_COUNSELOR, expect_key="cards", retries=1)
    cards = []
    for raw in data.get("cards", []) if isinstance(data, dict) else []:
        if not isinstance(raw, dict):
            continue
        body = _clean(raw.get("body"), 2200)
        if len(body) < 80 or re.search(r"\[(?:core|insert|concept|example|topic|your)\b[^\]]*\]", body, re.I):
            continue
        cards.append({
            "title": _clean(raw.get("title"), 90) or skill["skill_label"],
            "body": body,
            "worked_example": _clean(raw.get("worked_example"), 2500),
            "takeaway": _clean(raw.get("takeaway"), 400),
            "trap": _clean(raw.get("trap"), 600),
        })
    if not cards:
        raise ValueError("no usable college teaching cards")
    return {
        "intro": _clean(data.get("intro"), 900),
        "cards": cards[:TEACH_CARD_COUNT],
        "recap": _clean(data.get("recap"), 1200),
    }


def generate_college_exercises(node, profile, count, *, cumulative_skills=None):
    """Judgement drills: which version is stronger, and why.

    Application material has no answer key, so the gradeable skill is
    discrimination -- telling a specific, evidenced entry from a vague one.
    """
    skill = node["skill"]
    syllabus = "\n".join(f"- {item}" for item in node["syllabus"]) or f"- Core {skill['skill_label']} judgement"

    if cumulative_skills:
        catalog = "\n".join(
            f"- {key}: {COLLEGE_TAXONOMY[key][0]}" for key in cumulative_skills if key in COLLEGE_TAXONOMY
        )
        coverage = ("This is a cumulative review. Spread questions across these skills and tag each "
                    "question with the key of the skill it tests:\n" + catalog)
        skill_field = '      "skill_key": "which skill from the list above this question tests",\n'
    else:
        coverage = f"Every question tests judgement about {skill['skill_label']}."
        skill_field = ""

    prompt = f"""# TASK
Write {count} multiple-choice judgement questions on **{skill['skill_label']}** for a student in
grade {profile['grade']} at the "{profile['stage']}" stage.

{_COLLEGE_FACTS}

# COVERAGE
{coverage}

# SUB-CONCEPTS THE STUDENT JUST STUDIED
{syllabus}

# STUDENT CONTEXT
- Intended majors: {profile['majors']}
- Colleges under consideration: {profile['target_colleges']}

# QUESTION DESIGN
There is no answer key in college admissions, so test the judgement that separates strong
material from weak. Good question shapes:
- Put a realistic scenario in `source_or_prompt`, then ask which next move is strongest.
- Show four versions of the same activities entry, essay opening, or email, and ask which is
  most effective. Make the wrong ones wrong for DIFFERENT reasons: vague, generic, boastful
  without evidence, or answering a different question than the one asked.
- Give a student profile and ask which choice best fits their situation.

# RULES
1. `source_or_prompt` must contain the scenario, draft, or profile the question depends on.
   Write it yourself, 30-160 words. The student sees only what you put in these fields.
2. Exactly 4 choices, exactly one clearly strongest. Every distractor must be a mistake a real
   student actually makes.
3. `explanation` says why the best answer works AND what is wrong with each other option.
   40-120 words. Be specific about the principle, not just "it's more detailed".
4. Vary `correct_option` across the set. Do not make it 0 every time.
5. Never reference a specific college's real deadline, requirement, or acceptance rate.
6. Never write a question whose answer depends on information you did not include.

# OUTPUT
Raw JSON only:
{{
  "questions": [
    {{
{skill_field}      "source_or_prompt": "the scenario, draft, or profile the question depends on",
      "question_text": "the question itself",
      "options": ["choice A", "choice B", "choice C", "choice D"],
      "correct_option": 0,
      "explanation": "why the best answer works and what is wrong with each other option",
      "difficulty": "easy | medium | hard"
    }}
  ]
}}
Return exactly {count} questions."""

    data = _call(prompt, tokens=950 * count + 800, system=SYSTEM_COUNSELOR,
                 expect_key="questions", retries=1)
    allowed = set(cumulative_skills or ())
    items = []
    for raw in data.get("questions", []) if isinstance(data, dict) else []:
        valid = _valid_question(raw, needs_prompt=True)
        if not valid:
            continue
        tagged = str(raw.get("skill_key") or "").strip()
        valid["skill_key"] = tagged if tagged in allowed else skill["skill_key"]
        items.append(valid)
    items = _dedupe(items)
    if len(items) < max(2, count // 2):
        raise ValueError(f"only {len(items)} of {count} college questions were usable")
    return items[:count]


def _college_milestone_node(profile):
    milestone = profile["milestone"]
    return {
        "node_type": "milestone",
        "skill": resolve_college_skill("narrative_core"),
        "title": milestone["title"],
        "objective": milestone["action"],
        "syllabus": [],
        "reason": (
            "This unit taught the judgement. This step is where you actually produce something, "
            "which is the only part an admissions officer ever sees."
        ),
        "difficulty": "hard",
        "stat_to_update": milestone["stat"],
        "stat_label": milestone["label"],
        "stat_unit": milestone["unit"],
    }


def _normalize_college_plan(data, shape, profile):
    """Force the college plan onto the server-owned shape."""
    raw_nodes = data.get("nodes") if isinstance(data, dict) else None
    raw_nodes = raw_nodes if isinstance(raw_nodes, list) else []
    candidates = [k for k in profile["skill_options"] if k in COLLEGE_TAXONOMY]

    nodes, used_keys, used_order = [], set(), []
    for index, node_type in enumerate(shape):
        if node_type == "milestone":
            nodes.append(_college_milestone_node(profile))
            continue

        raw = raw_nodes[index] if index < len(raw_nodes) and isinstance(raw_nodes[index], dict) else {}
        skill = resolve_college_skill(raw.get("skill_key"), raw.get("title") or "")

        if not raw.get("skill_key"):
            previous = nodes[-1] if nodes else None
            if node_type == "quiz" and used_order:
                skill = resolve_college_skill(used_order[0])
            elif node_type == "practice_sprint" and previous and previous["node_type"] == "lesson":
                skill = dict(previous["skill"])
            else:
                skill = resolve_college_skill(next(
                    (k for k in candidates if k not in used_keys), candidates[0]
                ))
        if skill["skill_key"] in used_keys and node_type == "lesson":
            replacement = next((k for k in candidates if k not in used_keys), None)
            if replacement:
                skill = resolve_college_skill(replacement)
        if skill["skill_key"] not in used_keys:
            used_keys.add(skill["skill_key"])
            used_order.append(skill["skill_key"])

        syllabus = [
            _clean(item, 240) for item in (raw.get("syllabus") or [])
            if isinstance(item, str) and len(_clean(item, 240)) > 12
        ][:5]
        if len(syllabus) < 2:
            syllabus = _default_college_syllabus(skill)

        difficulty = (raw.get("difficulty") or "medium").lower()
        nodes.append({
            "node_type": node_type,
            "skill": skill,
            "title": _clean(raw.get("title"), 90) or skill["skill_label"],
            "objective": _clean(raw.get("objective"), 300) or
                         f"Handle {skill['skill_label']} with judgement instead of guesswork.",
            "syllabus": syllabus,
            "reason": _clean(raw.get("reason"), 700) or
                      f"This is the piece of {skill['skill_label']} that is blocking your next move.",
            "difficulty": difficulty if difficulty in {"easy", "medium", "hard"} else "medium",
        })

    unit_title = _clean(data.get("unit_title"), 80) if isinstance(data, dict) else ""
    unit_summary = _clean(data.get("unit_summary"), 300) if isinstance(data, dict) else ""
    teaching = [n for n in nodes if n["node_type"] != "milestone"]
    if not unit_title and teaching:
        unit_title = teaching[0]["skill"]["skill_label"]
    if not unit_summary and teaching:
        unit_summary = teaching[0]["objective"]
    return {"unit_title": unit_title or "Your next unit", "unit_summary": unit_summary, "nodes": nodes}


def _default_college_syllabus(skill):
    label = skill["skill_label"]
    return [
        f"What admissions readers are actually looking for in {label}.",
        f"The difference between a specific and a generic approach to {label}.",
        f"A repeatable process for producing your own {label} material.",
        f"How to check your own work on {label} before you submit it.",
    ]


def _fallback_college_teaching(node):
    """A real lesson when generation fails, never a placeholder."""
    skill = node["skill"]
    label = skill["skill_label"]
    cards = []
    for item in node["syllabus"][:4]:
        cards.append({
            "title": item[:80],
            "body": (
                f"**{item}**\n\nThe thing that separates strong application material from weak "
                f"material is almost never effort, it is specificity. On {label}, a reader can tell "
                "within one line whether you are describing something that actually happened to you "
                "or something that could be copied onto anyone's application. Name the concrete "
                "detail: the number, the moment, the decision you made, the thing that changed "
                "because you were there. Generic writing is not penalized because it is badly "
                "written; it is penalized because it carries no information."
            ),
            "worked_example": (
                "Weak: 'Participated in debate club and improved my public speaking skills.'\n\n"
                "Strong: 'Ran weekly novice drills; grew the team from 6 to 19 and coached two "
                "first-year debaters to a regional quarterfinal.'\n\n"
                "What changed: the second version reports outcomes only this student could report. "
                "It answers 'what happened because you were there' instead of 'what were you in'."
            ),
            "takeaway": f"On {label}, replace every claim about yourself with the evidence for it.",
            "trap": "Describing the role you held rather than the result you produced.",
        })
    if not cards:
        cards = [{
            "title": label,
            "body": (
                f"{label} rewards specificity and honesty. Decide what you actually want a reader to "
                "know, say it in concrete terms, and cut anything that could appear on someone "
                "else's application unchanged."
            ),
            "worked_example": "",
            "takeaway": f"Be specific and honest on {label}; vagueness reads as having nothing to say.",
            "trap": "Writing what you think admissions wants to hear instead of what is true.",
        }]
    return {
        "intro": f"This lesson is about {label}. {node['objective']}",
        "cards": cards,
        "recap": (
            f"On {label}: lead with evidence, cut anything generic, and check that every line "
            "could only have been written by you."
        ),
    }


def build_college_unit(profile, *, max_workers=6):
    """Plan a college unit, then generate its content concurrently."""
    profile = dict(profile)
    stage = (profile.get("stage") or "researching").lower()
    if stage not in COLLEGE_MILESTONES:
        stage = "researching"
    profile["stage"] = stage
    profile["milestone"] = COLLEGE_MILESTONES[stage]
    profile.setdefault("skill_options", college_skill_options(stage))

    try:
        raw_plan = plan_college_unit(profile, COLLEGE_SHAPE)
    except Exception as error:  # noqa: BLE001
        _log("learning: college planner failed (%s); using stage-ranked fallback", error)
        raw_plan = {}
    plan = _normalize_college_plan(raw_plan, COLLEGE_SHAPE, profile)

    taught_keys, taught_labels = [], []
    for node in plan["nodes"]:
        if node["node_type"] in ("lesson", "practice_sprint") and node["skill"]["skill_key"] not in taught_keys:
            taught_keys.append(node["skill"]["skill_key"])
            taught_labels.append(node["skill"]["skill_label"])

    jobs = []
    for index, node in enumerate(plan["nodes"]):
        if node["node_type"] == "milestone":
            continue
        if node["node_type"] == "lesson":
            jobs.append((index, "teaching", node, None))
            jobs.append((index, "checks", node, LESSON_CHECK_COUNT))
        else:
            jobs.append((index, "exercises", node, EXERCISE_COUNT[node["node_type"]]))

    def run(job):
        index, kind, node, count = job
        try:
            if kind == "teaching":
                return index, kind, generate_college_teaching(node, profile)
            if kind == "checks":
                return index, kind, generate_college_exercises(node, profile, count)
            cumulative = taught_keys if node["node_type"] == "quiz" else None
            return index, kind, generate_college_exercises(
                node, profile, count, cumulative_skills=cumulative
            )
        except Exception as error:  # noqa: BLE001
            _log("learning: college %s failed for node %s (%s): %s",
                 kind, index + 1, node["skill"]["skill_key"], error)
            return index, kind, None

    results = {}
    if jobs:
        with ThreadPoolExecutor(max_workers=min(max_workers, len(jobs))) as pool:
            for index, kind, payload in pool.map(run, jobs):
                results[(index, kind)] = payload

    for index, node in enumerate(plan["nodes"]):
        node["xp_reward"] = COLLEGE_XP[node["node_type"]]
        if node["node_type"] == "lesson":
            teaching = results.get((index, "teaching")) or _fallback_college_teaching(node)
            checks = results.get((index, "checks")) or []
            node["teaching"] = teaching
            node["checks"] = checks
            node["steps"] = _interleave_lesson(teaching, checks)
        elif node["node_type"] in ("practice_sprint", "quiz"):
            node["questions"] = results.get((index, "exercises")) or []

    plan["taught_labels"] = taught_labels
    plan["taught_keys"] = taught_keys
    return plan
