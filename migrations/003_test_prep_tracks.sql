ALTER TABLE paths ADD COLUMN IF NOT EXISTS track_key TEXT;
CREATE INDEX IF NOT EXISTS idx_paths_user_track_active ON paths (user_id, category, track_key, is_active, task_order);
