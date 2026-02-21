-- =============================================================================
-- NIRIX DIAGNOSTICS - TABLE ALTERATIONS
-- Schema: app
-- Version: 4.4.3
-- Last Updated: 2026-02-20
-- =============================================================================

-- =============================================================================
-- 1. AUTO_RUN_SESSIONS
-- =============================================================================

ALTER TABLE app.auto_run_sessions 
ADD COLUMN IF NOT EXISTS user_login_id UUID;

ALTER TABLE app.auto_run_sessions 
ADD COLUMN IF NOT EXISTS last_accessed TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP;

ALTER TABLE app.auto_run_sessions 
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP;

ALTER TABLE app.auto_run_sessions 
DROP CONSTRAINT IF EXISTS auto_run_sessions_status_check;

ALTER TABLE app.auto_run_sessions 
ADD CONSTRAINT auto_run_sessions_status_check 
CHECK (status IN ('started', 'running', 'completed', 'failed', 'stopped', 'expired'));

CREATE INDEX IF NOT EXISTS idx_auto_run_sessions_user_login 
ON app.auto_run_sessions(user_id, user_login_id) 
WHERE status IN ('running', 'started');

CREATE INDEX IF NOT EXISTS idx_auto_run_sessions_cleanup 
ON app.auto_run_sessions(status, last_accessed) 
WHERE status IN ('running', 'started');

CREATE INDEX IF NOT EXISTS idx_auto_run_sessions_updated 
ON app.auto_run_sessions(updated_at);

-- =============================================================================
-- 2. AUTO_RUN_STREAM_VALUES
-- =============================================================================

ALTER TABLE app.auto_run_stream_values 
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP;

DROP INDEX IF EXISTS app.idx_stream_values_cleanup;

CREATE INDEX IF NOT EXISTS idx_auto_run_stream_values_updated 
ON app.auto_run_stream_values(updated_at);

CREATE INDEX IF NOT EXISTS idx_stream_values_hour_bucket 
ON app.auto_run_stream_values (
    date_trunc('hour', updated_at)
);

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
-- 3. AUTO_RUN_RESULTS  ✅ FIXED LOGIC
-- =============================================================================

ALTER TABLE app.auto_run_results 
ADD COLUMN IF NOT EXISTS source TEXT DEFAULT 'section';

CREATE INDEX IF NOT EXISTS idx_auto_run_results_source 
ON app.auto_run_results(source);

-- 🔥 SAFE UNIQUE CREATION (constraint-first logic)
DO $$
BEGIN
    -- If constraint exists → do nothing
    IF EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'uq_auto_run_results_session_program'
    ) THEN
        -- already correct
        NULL;
    ELSE
        -- If index exists without constraint → drop index
        IF EXISTS (
            SELECT 1 FROM pg_class 
            WHERE relname = 'uq_auto_run_results_session_program'
        ) THEN
            DROP INDEX app.uq_auto_run_results_session_program;
        END IF;

        -- Create constraint
        ALTER TABLE app.auto_run_results 
        ADD CONSTRAINT uq_auto_run_results_session_program 
        UNIQUE (session_id, program_id);
    END IF;
END$$;

-- FK safe creation
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
-- 4. ECU_ACTIVE_STATUS
-- =============================================================================

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'uq_ecu_active_status_session_ecu'
    ) THEN
        ALTER TABLE app.ecu_active_status 
        DROP CONSTRAINT IF EXISTS uq_ecu_status_session,
        DROP CONSTRAINT IF EXISTS uq_ecu_status_session_old;
        
        ALTER TABLE app.ecu_active_status 
        ADD CONSTRAINT uq_ecu_active_status_session_ecu 
        UNIQUE (session_id, ecu_code);
    END IF;
END$$;

CREATE INDEX IF NOT EXISTS idx_ecu_active_status_session 
ON app.ecu_active_status(session_id);

CREATE INDEX IF NOT EXISTS idx_ecu_active_status_session_ecu 
ON app.ecu_active_status(session_id, ecu_code);

-- =============================================================================
-- 5. USER_LOGIN_SESSIONS
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

CREATE INDEX IF NOT EXISTS idx_user_login_sessions_user 
ON app.user_login_sessions(user_id);

CREATE INDEX IF NOT EXISTS idx_user_login_sessions_active 
ON app.user_login_sessions(is_active) 
WHERE is_active = true;

-- =============================================================================
-- 6. TESTS
-- =============================================================================

CREATE INDEX IF NOT EXISTS idx_tests_composite_lookup 
ON app.tests(vehicle_id, section, ecu, parameter) 
WHERE is_active = true;

-- =============================================================================
-- 7. VEHICLE_DIAGNOSTIC_ACTIONS
-- =============================================================================

CREATE INDEX IF NOT EXISTS idx_vehicle_diagnostic_actions_auto_run_gin 
ON app.vehicle_diagnostic_actions USING gin(auto_run_programs);

-- =============================================================================
-- 8. CONFIG
-- =============================================================================

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
-- 9. CLEANUP FUNCTION
-- =============================================================================

CREATE OR REPLACE FUNCTION app.cleanup_expired_sessions()
RETURNS INTEGER AS $$
DECLARE
    cleaned INTEGER;
    streams_cleaned INTEGER;
    ecu_cleaned INTEGER;
BEGIN
    UPDATE app.auto_run_sessions
    SET status = 'expired',
        ended_at = CURRENT_TIMESTAMP,
        updated_at = CURRENT_TIMESTAMP
    WHERE status IN ('running', 'started')
      AND last_accessed < NOW() - INTERVAL '2 hours'
    RETURNING COUNT(*) INTO cleaned;
    
    DELETE FROM app.auto_run_stream_values
    WHERE updated_at < NOW() - INTERVAL '1 hour'
    RETURNING COUNT(*) INTO streams_cleaned;
    
    DELETE FROM app.ecu_active_status
    WHERE session_id IN (
        SELECT session_id FROM app.auto_run_sessions
        WHERE status = 'expired' 
           OR ended_at < NOW() - INTERVAL '2 hours'
    )
    RETURNING COUNT(*) INTO ecu_cleaned;
    
    RETURN cleaned + streams_cleaned + ecu_cleaned;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- 10. DATA NORMALIZATION
-- =============================================================================

UPDATE app.auto_run_sessions 
SET last_accessed = COALESCE(started_at, CURRENT_TIMESTAMP)
WHERE last_accessed IS NULL;

UPDATE app.auto_run_sessions 
SET updated_at = COALESCE(ended_at, started_at, CURRENT_TIMESTAMP)
WHERE updated_at IS NULL;

UPDATE app.auto_run_stream_values 
SET updated_at = CURRENT_TIMESTAMP
WHERE updated_at IS NULL;

UPDATE app.auto_run_results 
SET source = 'section' 
WHERE source IS NULL;


-- Consider adding composite index for cleanup function
CREATE INDEX IF NOT EXISTS idx_auto_run_sessions_cleanup2 
ON app.auto_run_sessions(last_accessed, status) 
WHERE status IN ('running', 'started');

-- Consider index for ECU status cleanup
CREATE INDEX IF NOT EXISTS idx_ecu_active_status_cleanup 
ON app.ecu_active_status(session_id, updated_at);

-- Consider partial index for active login sessions
CREATE INDEX IF NOT EXISTS idx_user_login_sessions_active_only 
ON app.user_login_sessions(last_activity) 
WHERE is_active = true;
