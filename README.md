-- =============================================================================
-- FIX ALL DATABASE ISSUES
-- =============================================================================

-- 1. Add missing updated_at to vehicle_diagnostic_actions
ALTER TABLE app.vehicle_diagnostic_actions 
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP;

CREATE INDEX IF NOT EXISTS idx_vehicle_diagnostic_actions_updated 
ON app.vehicle_diagnostic_actions(updated_at);

-- 2. Fix cleanup function
CREATE OR REPLACE FUNCTION app.cleanup_expired_sessions()
RETURNS INTEGER AS $$
DECLARE
    cleaned INTEGER;
    streams_cleaned INTEGER;
    ecu_cleaned INTEGER;
BEGIN
    WITH updated AS (
        UPDATE app.auto_run_sessions
        SET status = 'expired',
            ended_at = CURRENT_TIMESTAMP,
            updated_at = CURRENT_TIMESTAMP
        WHERE status IN ('running', 'started')
          AND last_accessed < NOW() - INTERVAL '2 hours'
        RETURNING session_id
    )
    SELECT COUNT(*) INTO cleaned FROM updated;
    
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

-- 3. Ensure config table has required keys
INSERT INTO app.config (key_name, value_text) 
VALUES ('can_interface', 'PCAN_USBBUS1')
ON CONFLICT (key_name) DO NOTHING;

INSERT INTO app.config (key_name, value_text) 
VALUES ('can_bitrate', '500000')
ON CONFLICT (key_name) DO NOTHING;

INSERT INTO app.config (key_name, value_text) 
VALUES ('vci_mode', 'pcan')
ON CONFLICT (key_name) DO NOTHING;

-- 4. Update any NULL values
UPDATE app.auto_run_sessions 
SET updated_at = COALESCE(ended_at, started_at, CURRENT_TIMESTAMP)
WHERE updated_at IS NULL;

UPDATE app.auto_run_stream_values 
SET updated_at = CURRENT_TIMESTAMP
WHERE updated_at IS NULL;

UPDATE app.auto_run_results 
SET source = 'section' 
WHERE source IS NULL;
