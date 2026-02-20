-- =============================================================================
-- NIRIX DIAGNOSTICS - TABLE ALTERATIONS
-- Schema: app
-- Version: 4.4.0
-- Last Updated: 2026-02-20
-- =============================================================================

-- =============================================================================
-- 1. AUTO_RUN_SESSIONS - Add missing columns and constraints
-- =============================================================================

-- Add user_login_id column (for per-login tracking)
ALTER TABLE app.auto_run_sessions 
ADD COLUMN IF NOT EXISTS user_login_id UUID;

-- Add last_accessed column (for timeout detection)
ALTER TABLE app.auto_run_sessions 
ADD COLUMN IF NOT EXISTS last_accessed TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP;

-- Add updated_at column (MISSING - causes cleanup errors)
ALTER TABLE app.auto_run_sessions 
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP;

-- Add status value 'expired' to check constraint
ALTER TABLE app.auto_run_sessions 
DROP CONSTRAINT IF EXISTS auto_run_sessions_status_check;

ALTER TABLE app.auto_run_sessions 
ADD CONSTRAINT auto_run_sessions_status_check 
CHECK (status IN ('started', 'running', 'completed', 'failed', 'stopped', 'expired'));

-- Create index for user login lookups
CREATE INDEX IF NOT EXISTS idx_auto_run_sessions_user_login 
ON app.auto_run_sessions(user_id, user_login_id) 
WHERE status IN ('running', 'started');

-- Create index for cleanup queries
CREATE INDEX IF NOT EXISTS idx_auto_run_sessions_cleanup 
ON app.auto_run_sessions(status, last_accessed) 
WHERE status IN ('running', 'started');

-- Create index on updated_at for cleanup
CREATE INDEX IF NOT EXISTS idx_auto_run_sessions_updated 
ON app.auto_run_sessions(updated_at);

-- =============================================================================
-- 2. AUTO_RUN_STREAM_VALUES - Add missing columns and indexes
-- =============================================================================

-- Add updated_at column (MISSING - causes cleanup errors)
ALTER TABLE app.auto_run_stream_values 
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP;

-- Create index on updated_at for cleanup
CREATE INDEX IF NOT EXISTS idx_auto_run_stream_values_updated 
ON app.auto_run_stream_values(updated_at);

-- Create index for efficient cleanup of old values
CREATE INDEX IF NOT EXISTS idx_stream_values_cleanup 
ON app.auto_run_stream_values(updated_at) 
WHERE updated_at < NOW() - INTERVAL '1 hour';

-- Ensure unique constraint exists for upsert
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'uq_auto_run_stream_values_session_signal'
    ) THEN
        ALTER TABLE app.auto_run_stream_values 
        ADD CONSTRAINT uq_auto_run_stream_values_session_signal 
        UNIQUE (session_id, signal_name);
    END IF;
END$$;

-- =============================================================================
-- 3. AUTO_RUN_RESULTS - Add source column and constraints
-- =============================================================================

-- Add source column (to distinguish section vs ecu programs)
ALTER TABLE app.auto_run_results 
ADD COLUMN IF NOT EXISTS source TEXT DEFAULT 'section';

-- Create index on source for filtering
CREATE INDEX IF NOT EXISTS idx_auto_run_results_source 
ON app.auto_run_results(source);

-- Ensure unique constraint exists
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'uq_auto_run_results_session_program'
    ) THEN
        ALTER TABLE app.auto_run_results 
        ADD CONSTRAINT uq_auto_run_results_session_program 
        UNIQUE (session_id, program_id);
    END IF;
END$$;

-- Add foreign key for user_id if missing
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'auto_run_results_user_id_fkey'
    ) THEN
        ALTER TABLE app.auto_run_results 
        ADD CONSTRAINT auto_run_results_user_id_fkey 
        FOREIGN KEY (user_id) REFERENCES app.users(id) ON DELETE SET NULL;
    END IF;
END$$;

-- =============================================================================
-- 4. ECU_ACTIVE_STATUS - Ensure proper constraints
-- =============================================================================

-- Ensure unique constraint exists
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'uq_ecu_active_status_session_ecu'
    ) THEN
        -- Drop any duplicate constraints first
        ALTER TABLE app.ecu_active_status 
        DROP CONSTRAINT IF EXISTS uq_ecu_status_session,
        DROP CONSTRAINT IF EXISTS uq_ecu_status_session_old;
        
        -- Add single unique constraint
        ALTER TABLE app.ecu_active_status 
        ADD CONSTRAINT uq_ecu_active_status_session_ecu 
        UNIQUE (session_id, ecu_code);
    END IF;
END$$;

-- Add index for session lookups
CREATE INDEX IF NOT EXISTS idx_ecu_active_status_session 
ON app.ecu_active_status(session_id);

-- Add index for session+ecu lookups (for UI polling)
CREATE INDEX IF NOT EXISTS idx_ecu_active_status_session_ecu 
ON app.ecu_active_status(session_id, ecu_code);

-- =============================================================================
-- 5. CREATE USER_LOGIN_SESSIONS TABLE (NEW - needed for per-login tracking)
-- =============================================================================

CREATE TABLE IF NOT EXISTS app.user_login_sessions (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    login_id UUID NOT NULL,
    login_time TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ip_address VARCHAR(45),
    user_agent TEXT,
    last_activity TIMESTAMP WITHOUT TIME ZONE,
    is_active BOOLEAN DEFAULT true,
    
    CONSTRAINT uq_user_login_session UNIQUE (user_id, login_id)
);

-- Add foreign key constraint
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'user_login_sessions_user_id_fkey'
    ) THEN
        ALTER TABLE app.user_login_sessions 
        ADD CONSTRAINT user_login_sessions_user_id_fkey 
        FOREIGN KEY (user_id) REFERENCES app.users(id) ON DELETE CASCADE;
    END IF;
END$$;

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_user_login_sessions_user 
ON app.user_login_sessions(user_id);

CREATE INDEX IF NOT EXISTS idx_user_login_sessions_active 
ON app.user_login_sessions(is_active) 
WHERE is_active = true;

-- =============================================================================
-- 6. TESTS TABLE - Ensure proper indexes
-- =============================================================================

-- Add index for faster lookups by vehicle, section, ecu, parameter
CREATE INDEX IF NOT EXISTS idx_tests_composite_lookup 
ON app.tests(vehicle_id, section, ecu, parameter) 
WHERE is_active = true;

-- =============================================================================
-- 7. VEHICLE_DIAGNOSTIC_ACTIONS - Add GIN index for JSONB queries
-- =============================================================================

CREATE INDEX IF NOT EXISTS idx_vehicle_diagnostic_actions_auto_run_gin 
ON app.vehicle_diagnostic_actions USING gin(auto_run_programs);

-- =============================================================================
-- 8. CONFIG TABLE - Ensure unique constraints
-- =============================================================================

-- Ensure unique constraint on key_name
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'uq_config_key'
    ) THEN
        ALTER TABLE app.config 
        ADD CONSTRAINT uq_config_key UNIQUE (key_name);
    END IF;
END$$;

-- =============================================================================
-- 9. CLEANUP FUNCTION (optional but recommended)
-- =============================================================================

-- Create or replace cleanup function
CREATE OR REPLACE FUNCTION app.cleanup_expired_sessions()
RETURNS INTEGER AS $$
DECLARE
    cleaned INTEGER;
    streams_cleaned INTEGER;
    ecu_cleaned INTEGER;
BEGIN
    -- Mark expired auto-run sessions
    UPDATE app.auto_run_sessions
    SET status = 'expired',
        ended_at = CURRENT_TIMESTAMP,
        updated_at = CURRENT_TIMESTAMP
    WHERE status IN ('running', 'started')
      AND last_accessed < NOW() - INTERVAL '2 hours'
    RETURNING COUNT(*) INTO cleaned;
    
    -- Clean up old stream values (older than 1 hour)
    DELETE FROM app.auto_run_stream_values
    WHERE updated_at < NOW() - INTERVAL '1 hour'
    RETURNING COUNT(*) INTO streams_cleaned;
    
    -- Clean up old ECU status (older than 2 hours)
    DELETE FROM app.ecu_active_status
    WHERE session_id IN (
        SELECT session_id FROM app.auto_run_sessions
        WHERE status = 'expired' OR ended_at < NOW() - INTERVAL '2 hours'
    )
    RETURNING COUNT(*) INTO ecu_cleaned;
    
    RETURN cleaned + streams_cleaned + ecu_cleaned;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- 10. UPDATE EXISTING RECORDS (set defaults for new columns)
-- =============================================================================

-- Set last_accessed for existing running sessions
UPDATE app.auto_run_sessions 
SET last_accessed = COALESCE(started_at, CURRENT_TIMESTAMP)
WHERE last_accessed IS NULL;

-- Set updated_at for existing records
UPDATE app.auto_run_sessions 
SET updated_at = COALESCE(ended_at, started_at, CURRENT_TIMESTAMP)
WHERE updated_at IS NULL;

-- Set updated_at for existing stream values
UPDATE app.auto_run_stream_values 
SET updated_at = CURRENT_TIMESTAMP
WHERE updated_at IS NULL;

-- Set source for existing auto_run_results (default to 'section')
UPDATE app.auto_run_results 
SET source = 'section' 
WHERE source IS NULL;

-- =============================================================================
-- 11. VERIFICATION QUERIES (run these to check your fixes)
-- =============================================================================

/*
-- Check auto_run_sessions columns
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_schema = 'app' 
  AND table_name = 'auto_run_sessions'
ORDER BY ordinal_position;

-- Check auto_run_stream_values columns
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_schema = 'app' 
  AND table_name = 'auto_run_stream_values'
ORDER BY ordinal_position;

-- Check constraints
SELECT conname, contype 
FROM pg_constraint 
WHERE conrelid = 'app.auto_run_sessions'::regclass;

-- Check indexes
SELECT indexname, indexdef 
FROM pg_indexes 
WHERE tablename = 'auto_run_sessions' 
  AND schemaname = 'app';
*/
