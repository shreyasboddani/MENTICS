-- Mentics production row-level security.
--
-- Prerequisite: create a LOGIN role named mentics_app with no BYPASSRLS.
-- Run this migration as neondb_owner, then use mentics_app for DATABASE_URL.
-- The Flask database helper sets mentics.user_id/auth_email/system on every
-- connection from trusted session state before application queries execute.

BEGIN;

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'mentics_app') THEN
    RAISE EXCEPTION 'Create the mentics_app runtime role before applying RLS';
  END IF;
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'mentics_app' AND rolbypassrls) THEN
    RAISE EXCEPTION 'mentics_app must not have BYPASSRLS';
  END IF;
END
$$;

CREATE OR REPLACE FUNCTION public.mentics_current_user_id()
RETURNS bigint
LANGUAGE sql
STABLE
PARALLEL SAFE
AS $$
  SELECT CASE
    WHEN current_setting('mentics.user_id', true) ~ '^[1-9][0-9]*$'
      THEN current_setting('mentics.user_id', true)::bigint
    ELSE NULL
  END
$$;

CREATE OR REPLACE FUNCTION public.mentics_auth_email()
RETURNS text
LANGUAGE sql
STABLE
PARALLEL SAFE
AS $$
  SELECT NULLIF(lower(current_setting('mentics.auth_email', true)), '')
$$;

CREATE OR REPLACE FUNCTION public.mentics_system_access()
RETURNS boolean
LANGUAGE sql
STABLE
PARALLEL SAFE
AS $$
  SELECT current_setting('mentics.system', true) = 'on'
$$;

REVOKE ALL ON FUNCTION public.mentics_current_user_id() FROM PUBLIC;
REVOKE ALL ON FUNCTION public.mentics_auth_email() FROM PUBLIC;
REVOKE ALL ON FUNCTION public.mentics_system_access() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.mentics_current_user_id() TO mentics_app;
GRANT EXECUTE ON FUNCTION public.mentics_auth_email() TO mentics_app;
GRANT EXECUTE ON FUNCTION public.mentics_system_access() TO mentics_app;

GRANT USAGE ON SCHEMA public TO mentics_app;
REVOKE CREATE ON SCHEMA public FROM mentics_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO mentics_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO mentics_app;
ALTER DEFAULT PRIVILEGES FOR ROLE neondb_owner IN SCHEMA public
  GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO mentics_app;
ALTER DEFAULT PRIVILEGES FOR ROLE neondb_owner IN SCHEMA public
  GRANT USAGE, SELECT ON SEQUENCES TO mentics_app;

-- Drop first so the migration is safely repeatable after policy changes.
DO $$
DECLARE policy_row record;
BEGIN
  FOR policy_row IN
    SELECT schemaname, tablename, policyname
    FROM pg_policies
    WHERE schemaname = 'public' AND policyname LIKE 'mentics_%'
  LOOP
    EXECUTE format(
      'DROP POLICY %I ON %I.%I',
      policy_row.policyname, policy_row.schemaname, policy_row.tablename
    );
  END LOOP;
END
$$;

-- Directly tenant-owned records.
CREATE POLICY mentics_paths_tenant ON paths TO mentics_app
  USING (user_id = mentics_current_user_id() OR mentics_system_access())
  WITH CHECK (user_id = mentics_current_user_id() OR mentics_system_access());
CREATE POLICY mentics_stat_history_tenant ON stat_history TO mentics_app
  USING (user_id = mentics_current_user_id() OR mentics_system_access())
  WITH CHECK (user_id = mentics_current_user_id() OR mentics_system_access());
CREATE POLICY mentics_chat_conversations_tenant ON chat_conversations TO mentics_app
  USING (user_id = mentics_current_user_id() OR mentics_system_access())
  WITH CHECK (user_id = mentics_current_user_id() OR mentics_system_access());
CREATE POLICY mentics_activity_log_tenant ON activity_log TO mentics_app
  USING (user_id = mentics_current_user_id() OR mentics_system_access())
  WITH CHECK (user_id = mentics_current_user_id() OR mentics_system_access());
CREATE POLICY mentics_gamification_stats_tenant ON gamification_stats TO mentics_app
  USING (user_id = mentics_current_user_id() OR mentics_system_access())
  WITH CHECK (user_id = mentics_current_user_id() OR mentics_system_access());
CREATE POLICY mentics_quiz_results_tenant ON quiz_results TO mentics_app
  USING (user_id = mentics_current_user_id() OR mentics_system_access())
  WITH CHECK (user_id = mentics_current_user_id() OR mentics_system_access());
CREATE POLICY mentics_sprint_results_tenant ON sprint_results TO mentics_app
  USING (user_id = mentics_current_user_id() OR mentics_system_access())
  WITH CHECK (user_id = mentics_current_user_id() OR mentics_system_access());
CREATE POLICY mentics_lesson_progress_tenant ON lesson_progress TO mentics_app
  USING (user_id = mentics_current_user_id() OR mentics_system_access())
  WITH CHECK (user_id = mentics_current_user_id() OR mentics_system_access());
CREATE POLICY mentics_lesson_answers_tenant ON lesson_answers TO mentics_app
  USING (user_id = mentics_current_user_id() OR mentics_system_access())
  WITH CHECK (user_id = mentics_current_user_id() OR mentics_system_access());
CREATE POLICY mentics_skill_mastery_tenant ON skill_mastery TO mentics_app
  USING (user_id = mentics_current_user_id() OR mentics_system_access())
  WITH CHECK (user_id = mentics_current_user_id() OR mentics_system_access());
CREATE POLICY mentics_mistake_bank_tenant ON mistake_bank TO mentics_app
  USING (user_id = mentics_current_user_id() OR mentics_system_access())
  WITH CHECK (user_id = mentics_current_user_id() OR mentics_system_access());

-- Account rows: a signed-in user sees only itself. Login/signup receive a
-- narrowly scoped email lookup, and internal bot/profile reads use system mode.
CREATE POLICY mentics_users_select ON users FOR SELECT TO mentics_app
  USING (
    id = mentics_current_user_id()
    OR lower(email) = mentics_auth_email()
    OR mentics_system_access()
  );
CREATE POLICY mentics_users_insert ON users FOR INSERT TO mentics_app
  WITH CHECK (lower(email) = mentics_auth_email() OR mentics_system_access());
CREATE POLICY mentics_users_update ON users FOR UPDATE TO mentics_app
  USING (id = mentics_current_user_id() OR mentics_system_access())
  WITH CHECK (id = mentics_current_user_id() OR mentics_system_access());
CREATE POLICY mentics_users_delete ON users FOR DELETE TO mentics_app
  USING (id = mentics_current_user_id() OR mentics_system_access());

-- Community content is readable by signed-in users but only mutable by its
-- author. The Flask routes still enforce the same ownership checks.
CREATE POLICY mentics_forum_posts_read ON forum_posts FOR SELECT TO mentics_app
  USING (mentics_current_user_id() IS NOT NULL OR mentics_system_access());
CREATE POLICY mentics_forum_posts_insert ON forum_posts FOR INSERT TO mentics_app
  WITH CHECK (user_id = mentics_current_user_id() OR mentics_system_access());
CREATE POLICY mentics_forum_posts_update ON forum_posts FOR UPDATE TO mentics_app
  USING (user_id = mentics_current_user_id() OR mentics_system_access())
  WITH CHECK (user_id = mentics_current_user_id() OR mentics_system_access());
CREATE POLICY mentics_forum_posts_delete ON forum_posts FOR DELETE TO mentics_app
  USING (user_id = mentics_current_user_id() OR mentics_system_access());
CREATE POLICY mentics_forum_replies_read ON forum_replies FOR SELECT TO mentics_app
  USING (mentics_current_user_id() IS NOT NULL OR mentics_system_access());
CREATE POLICY mentics_forum_replies_insert ON forum_replies FOR INSERT TO mentics_app
  WITH CHECK (user_id = mentics_current_user_id() OR mentics_system_access());
CREATE POLICY mentics_forum_replies_update ON forum_replies FOR UPDATE TO mentics_app
  USING (user_id = mentics_current_user_id() OR mentics_system_access())
  WITH CHECK (user_id = mentics_current_user_id() OR mentics_system_access());
CREATE POLICY mentics_forum_replies_delete ON forum_replies FOR DELETE TO mentics_app
  USING (user_id = mentics_current_user_id() OR mentics_system_access());

-- Path-owned content inherits the tenant from its parent path.
CREATE POLICY mentics_subtasks_tenant ON subtasks TO mentics_app
  USING (mentics_system_access() OR EXISTS (
    SELECT 1 FROM paths p WHERE p.id = parent_task_id AND p.user_id = mentics_current_user_id()
  ))
  WITH CHECK (mentics_system_access() OR EXISTS (
    SELECT 1 FROM paths p WHERE p.id = parent_task_id AND p.user_id = mentics_current_user_id()
  ));
CREATE POLICY mentics_quizzes_tenant ON quizzes TO mentics_app
  USING (mentics_system_access() OR EXISTS (
    SELECT 1 FROM paths p WHERE p.id = task_id AND p.user_id = mentics_current_user_id()
  ))
  WITH CHECK (mentics_system_access() OR EXISTS (
    SELECT 1 FROM paths p WHERE p.id = task_id AND p.user_id = mentics_current_user_id()
  ));
CREATE POLICY mentics_quiz_questions_tenant ON quiz_questions TO mentics_app
  USING (mentics_system_access() OR EXISTS (
    SELECT 1 FROM quizzes q JOIN paths p ON p.id = q.task_id
    WHERE q.id = quiz_id AND p.user_id = mentics_current_user_id()
  ))
  WITH CHECK (mentics_system_access() OR EXISTS (
    SELECT 1 FROM quizzes q JOIN paths p ON p.id = q.task_id
    WHERE q.id = quiz_id AND p.user_id = mentics_current_user_id()
  ));
CREATE POLICY mentics_practice_sprints_tenant ON practice_sprints TO mentics_app
  USING (mentics_system_access() OR EXISTS (
    SELECT 1 FROM paths p WHERE p.id = task_id AND p.user_id = mentics_current_user_id()
  ))
  WITH CHECK (mentics_system_access() OR EXISTS (
    SELECT 1 FROM paths p WHERE p.id = task_id AND p.user_id = mentics_current_user_id()
  ));
CREATE POLICY mentics_sprint_questions_tenant ON sprint_questions TO mentics_app
  USING (mentics_system_access() OR EXISTS (
    SELECT 1 FROM practice_sprints s JOIN paths p ON p.id = s.task_id
    WHERE s.id = sprint_id AND p.user_id = mentics_current_user_id()
  ))
  WITH CHECK (mentics_system_access() OR EXISTS (
    SELECT 1 FROM practice_sprints s JOIN paths p ON p.id = s.task_id
    WHERE s.id = sprint_id AND p.user_id = mentics_current_user_id()
  ));
CREATE POLICY mentics_strategy_articles_tenant ON strategy_articles TO mentics_app
  USING (mentics_system_access() OR EXISTS (
    SELECT 1 FROM paths p WHERE p.id = task_id AND p.user_id = mentics_current_user_id()
  ))
  WITH CHECK (mentics_system_access() OR EXISTS (
    SELECT 1 FROM paths p WHERE p.id = task_id AND p.user_id = mentics_current_user_id()
  ));
CREATE POLICY mentics_lessons_tenant ON lessons TO mentics_app
  USING (mentics_system_access() OR EXISTS (
    SELECT 1 FROM paths p WHERE p.id = task_id AND p.user_id = mentics_current_user_id()
  ))
  WITH CHECK (mentics_system_access() OR EXISTS (
    SELECT 1 FROM paths p WHERE p.id = task_id AND p.user_id = mentics_current_user_id()
  ));
CREATE POLICY mentics_lesson_steps_tenant ON lesson_steps TO mentics_app
  USING (mentics_system_access() OR EXISTS (
    SELECT 1 FROM lessons l JOIN paths p ON p.id = l.task_id
    WHERE l.id = lesson_id AND p.user_id = mentics_current_user_id()
  ))
  WITH CHECK (mentics_system_access() OR EXISTS (
    SELECT 1 FROM lessons l JOIN paths p ON p.id = l.task_id
    WHERE l.id = lesson_id AND p.user_id = mentics_current_user_id()
  ));

-- Arena matchmaking intentionally exposes waiting and completed match metadata.
-- Active answer data remains visible only to the two participants.
CREATE POLICY mentics_sat_battles_select ON sat_battles FOR SELECT TO mentics_app
  USING (
    mentics_system_access()
    OR challenger_id = mentics_current_user_id()
    OR opponent_id = mentics_current_user_id()
    OR status IN ('waiting', 'complete')
  );
CREATE POLICY mentics_sat_battles_insert ON sat_battles FOR INSERT TO mentics_app
  WITH CHECK (challenger_id = mentics_current_user_id() OR mentics_system_access());
CREATE POLICY mentics_sat_battles_update ON sat_battles FOR UPDATE TO mentics_app
  USING (
    mentics_system_access()
    OR challenger_id = mentics_current_user_id()
    OR opponent_id = mentics_current_user_id()
    OR status = 'waiting'
  )
  WITH CHECK (
    mentics_system_access()
    OR challenger_id = mentics_current_user_id()
    OR opponent_id = mentics_current_user_id()
    OR status = 'expired'
  );
CREATE POLICY mentics_sat_battles_delete ON sat_battles FOR DELETE TO mentics_app
  USING (
    mentics_system_access()
    OR challenger_id = mentics_current_user_id()
    OR opponent_id = mentics_current_user_id()
  );

-- Arena rankings are public to signed-in players. A participant may update its
-- own record or the opponent's record while finalizing their shared battle.
CREATE POLICY mentics_sat_battle_stats_select ON sat_battle_stats FOR SELECT TO mentics_app
  USING (mentics_current_user_id() IS NOT NULL OR mentics_system_access());
CREATE POLICY mentics_sat_battle_stats_write ON sat_battle_stats FOR ALL TO mentics_app
  USING (
    mentics_system_access()
    OR user_id = mentics_current_user_id()
    OR EXISTS (
      SELECT 1 FROM sat_battles b
      WHERE mentics_current_user_id() IN (b.challenger_id, b.opponent_id)
        AND user_id IN (b.challenger_id, b.opponent_id)
        AND b.status IN ('active', 'complete')
    )
  )
  WITH CHECK (
    mentics_system_access()
    OR user_id = mentics_current_user_id()
    OR EXISTS (
      SELECT 1 FROM sat_battles b
      WHERE mentics_current_user_id() IN (b.challenger_id, b.opponent_id)
        AND user_id IN (b.challenger_id, b.opponent_id)
        AND b.status IN ('active', 'complete')
    )
  );

-- Shared content and infrastructure.
CREATE POLICY mentics_official_questions_read ON official_questions FOR SELECT TO mentics_app
  USING (true);
CREATE POLICY mentics_official_questions_write ON official_questions FOR ALL TO mentics_app
  USING (mentics_system_access())
  WITH CHECK (mentics_system_access());
CREATE POLICY mentics_rate_limits_all ON rate_limits TO mentics_app
  USING (true)
  WITH CHECK (true);

-- Enforce RLS on every application table, including for non-BYPASS table
-- owners. neondb_owner still bypasses by role attribute and remains migration-only.
ALTER TABLE users ENABLE ROW LEVEL SECURITY; ALTER TABLE users FORCE ROW LEVEL SECURITY;
ALTER TABLE paths ENABLE ROW LEVEL SECURITY; ALTER TABLE paths FORCE ROW LEVEL SECURITY;
ALTER TABLE subtasks ENABLE ROW LEVEL SECURITY; ALTER TABLE subtasks FORCE ROW LEVEL SECURITY;
ALTER TABLE stat_history ENABLE ROW LEVEL SECURITY; ALTER TABLE stat_history FORCE ROW LEVEL SECURITY;
ALTER TABLE chat_conversations ENABLE ROW LEVEL SECURITY; ALTER TABLE chat_conversations FORCE ROW LEVEL SECURITY;
ALTER TABLE activity_log ENABLE ROW LEVEL SECURITY; ALTER TABLE activity_log FORCE ROW LEVEL SECURITY;
ALTER TABLE gamification_stats ENABLE ROW LEVEL SECURITY; ALTER TABLE gamification_stats FORCE ROW LEVEL SECURITY;
ALTER TABLE forum_posts ENABLE ROW LEVEL SECURITY; ALTER TABLE forum_posts FORCE ROW LEVEL SECURITY;
ALTER TABLE forum_replies ENABLE ROW LEVEL SECURITY; ALTER TABLE forum_replies FORCE ROW LEVEL SECURITY;
ALTER TABLE sat_battles ENABLE ROW LEVEL SECURITY; ALTER TABLE sat_battles FORCE ROW LEVEL SECURITY;
ALTER TABLE sat_battle_stats ENABLE ROW LEVEL SECURITY; ALTER TABLE sat_battle_stats FORCE ROW LEVEL SECURITY;
ALTER TABLE quizzes ENABLE ROW LEVEL SECURITY; ALTER TABLE quizzes FORCE ROW LEVEL SECURITY;
ALTER TABLE quiz_questions ENABLE ROW LEVEL SECURITY; ALTER TABLE quiz_questions FORCE ROW LEVEL SECURITY;
ALTER TABLE quiz_results ENABLE ROW LEVEL SECURITY; ALTER TABLE quiz_results FORCE ROW LEVEL SECURITY;
ALTER TABLE practice_sprints ENABLE ROW LEVEL SECURITY; ALTER TABLE practice_sprints FORCE ROW LEVEL SECURITY;
ALTER TABLE sprint_questions ENABLE ROW LEVEL SECURITY; ALTER TABLE sprint_questions FORCE ROW LEVEL SECURITY;
ALTER TABLE sprint_results ENABLE ROW LEVEL SECURITY; ALTER TABLE sprint_results FORCE ROW LEVEL SECURITY;
ALTER TABLE official_questions ENABLE ROW LEVEL SECURITY; ALTER TABLE official_questions FORCE ROW LEVEL SECURITY;
ALTER TABLE strategy_articles ENABLE ROW LEVEL SECURITY; ALTER TABLE strategy_articles FORCE ROW LEVEL SECURITY;
ALTER TABLE lessons ENABLE ROW LEVEL SECURITY; ALTER TABLE lessons FORCE ROW LEVEL SECURITY;
ALTER TABLE lesson_steps ENABLE ROW LEVEL SECURITY; ALTER TABLE lesson_steps FORCE ROW LEVEL SECURITY;
ALTER TABLE lesson_progress ENABLE ROW LEVEL SECURITY; ALTER TABLE lesson_progress FORCE ROW LEVEL SECURITY;
ALTER TABLE lesson_answers ENABLE ROW LEVEL SECURITY; ALTER TABLE lesson_answers FORCE ROW LEVEL SECURITY;
ALTER TABLE skill_mastery ENABLE ROW LEVEL SECURITY; ALTER TABLE skill_mastery FORCE ROW LEVEL SECURITY;
ALTER TABLE mistake_bank ENABLE ROW LEVEL SECURITY; ALTER TABLE mistake_bank FORCE ROW LEVEL SECURITY;
ALTER TABLE rate_limits ENABLE ROW LEVEL SECURITY; ALTER TABLE rate_limits FORCE ROW LEVEL SECURITY;

COMMIT;
