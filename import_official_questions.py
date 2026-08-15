#!/usr/bin/env python3
"""
Script to import official SAT/ACT questions from JSON file into the database.
Usage: python import_official_questions.py sample_official_questions.json
"""

import json
import sys
from pathlib import Path
from dbhelper import DatabaseHandler

def initialize_db(db):
    """Initialize the official_questions table if it doesn't exist."""
    db.create_table("official_questions", {
        "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
        "test_type": "TEXT NOT NULL",
        "subject": "TEXT NOT NULL",
        "topic": "TEXT NOT NULL",
        "difficulty": "TEXT",
        "question_text": "TEXT NOT NULL",
        "options": "TEXT NOT NULL",
        "correct_option": "INTEGER NOT NULL",
        "explanation": "TEXT",
        "source_url": "TEXT",
        "source_or_prompt": "TEXT",
        "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
    })
    db.execute("CREATE INDEX IF NOT EXISTS idx_official_questions_subject_topic ON official_questions (test_type, subject, topic)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_official_questions_difficulty ON official_questions (difficulty)")
    print("✓ Database tables initialized")

def load_json_file(filepath):
    """Load questions from JSON file."""
    with open(filepath, 'r') as f:
        return json.load(f)

def import_questions(db_path, json_file):
    """Import questions from JSON file to database."""
    db = DatabaseHandler(db_path)
    
    # Initialize tables
    initialize_db(db)
    
    # Load questions from file
    data = load_json_file(json_file)
    questions = data.get('questions', [])
    
    print(f"Found {len(questions)} questions to import...")
    
    imported = 0
    errors = []
    
    for idx, q in enumerate(questions):
        try:
            # Validate required fields
            required_fields = ['test_type', 'subject', 'topic', 'question_text', 'options', 'correct_option']
            if not all(field in q for field in required_fields):
                missing = [f for f in required_fields if f not in q]
                errors.append(f"Question {idx}: Missing fields: {missing}")
                continue
            
            # Ensure options is JSON string
            options_json = json.dumps(q['options']) if isinstance(q['options'], list) else q['options']
            
            db.insert("official_questions", {
                "test_type": q.get('test_type', 'SAT'),
                "subject": q.get('subject', 'Math'),
                "topic": q.get('topic', 'General'),
                "difficulty": q.get('difficulty', 'medium'),
                "question_text": q['question_text'],
                "options": options_json,
                "correct_option": int(q['correct_option']),
                "explanation": q.get('explanation', ''),
                "source_url": q.get('source_url', ''),
                "source_or_prompt": q.get('source_or_prompt', ''),
            })
            imported += 1
            print(f"✓ Imported: {q['subject']} - {q['topic']}")
            
        except Exception as e:
            errors.append(f"Question {idx}: {str(e)}")
            print(f"✗ Error: {str(e)}")
    
    print(f"\n{'='*50}")
    print(f"Import Complete!")
    print(f"Successfully imported: {imported}/{len(questions)}")
    if errors:
        print(f"\nErrors ({len(errors)}):")
        for error in errors:
            print(f"  - {error}")
    
    return imported, len(questions), errors

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python import_official_questions.py <json_file> [database_path]")
        print("Example: python import_official_questions.py sample_official_questions.json instance/mentics.db")
        sys.exit(1)
    
    json_file = sys.argv[1]
    db_path = sys.argv[2] if len(sys.argv) > 2 else "instance/mentics.db"
    
    if not Path(json_file).exists():
        print(f"Error: File not found: {json_file}")
        sys.exit(1)
    
    imported, total, errors = import_questions(db_path, json_file)
    
    if imported == 0:
        sys.exit(1)
