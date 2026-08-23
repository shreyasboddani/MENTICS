# Official SAT/ACT Questions Integration Guide

## Overview

The MENTICS platform now integrates **official SAT and ACT questions** directly into quiz and sprint generation. Instead of relying solely on AI-generated questions, the system can pull authentic questions from an official question bank and use them for student practice.

## How It Works

### 1. **Official Questions Database**
- Questions are stored in the `official_questions` table
- Each question includes: question text, options, correct answer, explanation, difficulty, subject/topic
- Questions are tagged with test type (SAT or ACT), subject (Math, Reading/Writing), and topic (specific skill)

### 2. **Smart Question Selection**
When generating a quiz or sprint:
1. **First**: System tries to fetch official questions matching the student's target skill/topic
2. **Fallback**: If no official questions available, AI generates new ones
3. **Hybrid**: Mix of official + AI-generated to ensure variety and coverage

### 3. **AI Learning from Official Questions**
- When generating new questions, the AI can reference official examples
- This ensures AI-generated questions match the style, complexity, and format of real official questions
- Results in more authentic practice questions

---

## How to Use

### Option A: Import Questions via Python Script (Recommended for initial setup)

#### 1. Prepare a JSON file with official questions
```json
{
  "questions": [
    {
      "test_type": "SAT",
      "subject": "Math",
      "topic": "Quadratic Functions",
      "difficulty": "medium",
      "question_text": "A quadratic function f(x) = ax² + bx + c has a vertex at (2, -3)...",
      "options": ["a = 2", "a = 1", "a = 0.5", "a = -1"],
      "correct_option": 0,
      "explanation": "Since the vertex is at (2, -3)...",
      "source_or_prompt": "Digital SAT Math Module - Quadratic Functions",
      "source_url": "https://example.com/sat-questions"
    }
  ]
}
```

#### 2. Run the import script
```bash
python import_official_questions.py your_questions.json instance/mentics.db
```

Output:
```
✓ Database tables initialized
✓ Imported: Math - Quadratic Functions
✓ Imported: Math - Linear Equations
...
Successfully imported: 50/50
```

### Option B: Bulk Import via API

#### POST `/api/import_official_questions`
```bash
curl -X POST http://localhost:5000/api/import_official_questions \
  -H "Content-Type: application/json" \
  -d @questions.json
```

Request body:
```json
{
  "questions": [
    {
      "test_type": "SAT",
      "subject": "Math",
      "topic": "Algebra",
      "difficulty": "easy",
      "question_text": "Solve: 3x + 7 = 22",
      "options": ["x = 5", "x = 10", "x = 15"],
      "correct_option": 0,
      "explanation": "Subtract 7, then divide by 3..."
    }
  ]
}
```

Response:
```json
{
  "success": true,
  "imported": 50,
  "total": 50,
  "errors": null
}
```

---

## Database Schema

### `official_questions` table

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key, auto-increment |
| test_type | TEXT | "SAT" or "ACT" |
| subject | TEXT | "Math" or "Reading/Writing" |
| topic | TEXT | Specific skill (e.g., "Quadratic Functions", "Subject-Verb Agreement") |
| difficulty | TEXT | "easy", "medium", "hard" |
| question_text | TEXT | Full question text |
| options | TEXT | JSON array of 4 answer choices |
| correct_option | INTEGER | Index of correct answer (0-3) |
| explanation | TEXT | Detailed explanation of correct answer |
| source_url | TEXT | Link to original official source |
| source_or_prompt | TEXT | Reference material (passage, data, diagram description) |
| created_at | TIMESTAMP | When the question was imported |

### Indexes
- `idx_official_questions_subject_topic` - Fast lookup by test type, subject, and topic
- `idx_official_questions_difficulty` - Fast lookup by difficulty level

---

## Python API Reference

### Fetching Official Questions

```python
from app import _get_official_questions_for_topic

# Get 5 SAT Math questions on "Quadratic Functions"
questions = _get_official_questions_for_topic(
    test_type="SAT",
    subject="Math",
    topic="Quadratic Functions",
    limit=5
)

# Each question has:
# - id, question_text, options, correct_option
# - explanation, source_or_prompt, source_url
# - is_official=True
```

### Auto-Populating Quizzes with Official Questions

```python
from app import _populate_quiz_with_official_questions

# Get 7 questions for a quiz (official + AI fallback)
questions = _populate_quiz_with_official_questions(
    topic="Verb Tense",
    test_type="SAT",
    subject="Reading/Writing",
    needed_count=7
)
```

### Auto-Populating Sprints with Official Questions

```python
from app import _populate_sprint_with_official_questions

# Get 5 questions for a sprint (official + AI fallback)
questions = _populate_sprint_with_official_questions(
    topic="Linear Equations",
    test_type="SAT",
    subject="Math",
    needed_count=5
)
```

---

## Recommended Topics for Questions

### SAT Math
- Quadratic Functions
- Linear Equations
- Systems of Equations
- Function Notation
- Exponential Growth
- Rational Functions
- Polynomials
- Inequalities
- Geometry & Trigonometry

### SAT Reading/Writing
- Subject-Verb Agreement
- Verb Tense Consistency
- Pronoun-Antecedent Agreement
- Parallel Structure
- Word Choice / Vocabulary
- Sentence Boundaries
- Modifiers
- Reading Comprehension

### ACT Math
- Algebra
- Trigonometry
- Coordinate Geometry
- Plane Geometry
- Statistics

### ACT Reading
- Main Idea
- Supporting Details
- Inference
- Author's Purpose
- Tone

---

## Adding More Questions

### Sources for Official Questions

1. **College Board (SAT)**
   - [Official SAT Practice Tests](https://satsuite.collegeboard.org/sat/practice-preparation/practice-tests)
   - [SAT Suite Educator Question Bank](https://satsuiteeducatorquestionbank.collegeboard.org/)
   - Free practice tests and released questions

2. **ACT (ACT Testing)**
   - [ACT Test Prep](https://www.act.org/content/act/en/students/free-test-prep.html)
   - Released questions and practice materials

3. **Khan Academy**
   - Free SAT prep with official College Board content
   - Organized by skill and difficulty

### Creating a JSON file with 50+ questions

Use a spreadsheet tool (Excel/Google Sheets) to organize questions:
- Export as CSV
- Convert to JSON using a script
- Import using the Python script or API

Example conversion script:
```python
import csv
import json

def csv_to_json_questions(csv_file):
    questions = []
    with open(csv_file) as f:
        reader = csv.DictReader(f)
        for row in reader:
            questions.append({
                "test_type": row['test_type'],
                "subject": row['subject'],
                "topic": row['topic'],
                "difficulty": row['difficulty'],
                "question_text": row['question_text'],
                "options": json.loads(row['options']),
                "correct_option": int(row['correct_option']),
                "explanation": row['explanation'],
                "source_url": row.get('source_url', ''),
                "source_or_prompt": row.get('source_or_prompt', '')
            })
    return {"questions": questions}

# Usage
data = csv_to_json_questions("questions.csv")
with open("questions.json", "w") as f:
    json.dump(data, f, indent=2)
```

---

## How Students See This

### In Quizzes
- Questions are pulled automatically from the official database
- If no official questions exist for that topic, AI fills in the gaps
- Each question shows the source/reference material
- Explanations are detailed and match official style

### In Practice Sprints
- 5 focused questions on one skill
- Combination of official (if available) + AI-generated
- Same strategy guide teaching approach
- Results feed back into AI learning

---

## Analytics & Monitoring

To check how many official questions you have:

```sql
SELECT test_type, subject, COUNT(*) as count
FROM official_questions
GROUP BY test_type, subject;
```

To see coverage by topic:

```sql
SELECT test_type, subject, topic, difficulty, COUNT(*) as count
FROM official_questions
GROUP BY test_type, subject, topic, difficulty;
```

---

## Next Steps

1. **Expand Question Bank**: Add 100+ more official questions for comprehensive coverage
2. **Topic Mapping**: Map student weaknesses to specific official questions
3. **Performance Tracking**: Track which official questions students struggle with
4. **Difficulty Progression**: Start easy, gradually increase difficulty
5. **ACT Integration**: Build out ACT question database (currently lighter than SAT)

---

## Troubleshooting

### Import fails: "no such table: official_questions"
- Run the import script which auto-creates the table
- Or call `init_db()` in Flask shell first

### Questions not appearing in quizzes
- Check if official questions exist for that topic: `SELECT * FROM official_questions WHERE topic LIKE '%X%'`
- System will fallback to AI if no official questions found
- Check logs for any import errors

### API endpoint returns error
- Ensure JSON format is correct (required fields: test_type, subject, topic, question_text, options, correct_option)
- Check database connection
- Verify all option strings are present in `options` array

---

## Support

For questions or issues:
1. Check database: `SELECT COUNT(*) FROM official_questions;`
2. Review import logs for errors
3. Ensure JSON format matches schema
4. Test with smaller batches first

