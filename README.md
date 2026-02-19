-- =============================================================================
-- FIX-100: Fix auto_run_sessions status constraint
-- =============================================================================
ALTER TABLE app.auto_run_sessions DROP CONSTRAINT IF EXISTS auto_run_sessions_status_check;
ALTER TABLE app.auto_run_sessions ADD CONSTRAINT auto_run_sessions_status_check 
CHECK (status IN ('running', 'started', 'completed', 'failed', 'stopped', 'expired'));

-- =============================================================================
-- FIX-114: Ensure all required columns exist
-- =============================================================================

-- Add source column to auto_run_results if not exists
ALTER TABLE app.auto_run_results ADD COLUMN IF NOT EXISTS source TEXT DEFAULT 'section';

-- Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_auto_run_results_session ON app.auto_run_results(session_id);
CREATE INDEX IF NOT EXISTS idx_auto_run_results_program ON app.auto_run_results(program_id);
CREATE INDEX IF NOT EXISTS idx_auto_run_results_source ON app.auto_run_results(source);

-- Ensure auto_run_stream_values has proper indexes
CREATE INDEX IF NOT EXISTS idx_auto_run_stream_values_session_signal 
ON app.auto_run_stream_values(session_id, signal_name);

-- Ensure ecu_active_status has proper indexes
CREATE INDEX IF NOT EXISTS idx_ecu_active_status_session_ecu 
ON app.ecu_active_status(session_id, ecu_code);
