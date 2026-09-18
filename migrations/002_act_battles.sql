-- Run before deploying ACT Battles when startup schema migration is disabled.
-- Existing battles retain SAT identity; queue matching is isolated by exam.
BEGIN;
ALTER TABLE sat_battles ADD COLUMN IF NOT EXISTS exam_type TEXT NOT NULL DEFAULT 'SAT';
CREATE INDEX IF NOT EXISTS idx_sat_battles_exam_queue ON sat_battles (exam_type, status, created_at);
COMMIT;
