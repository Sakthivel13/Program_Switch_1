CREATE OR REPLACE FUNCTION app.cleanup_expired_sessions()
RETURNS INTEGER AS $$
DECLARE
    cleaned INTEGER;
    streams_cleaned INTEGER;
    ecu_cleaned INTEGER;
BEGIN
    -- Update expired sessions and count them
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
    
    -- Delete old stream values and count them
    WITH deleted_streams AS (
        DELETE FROM app.auto_run_stream_values
        WHERE updated_at < NOW() - INTERVAL '1 hour'
        RETURNING id
    )
    SELECT COUNT(*) INTO streams_cleaned FROM deleted_streams;
    
    -- Delete old ECU status and count them
    WITH deleted_ecu AS (
        DELETE FROM app.ecu_active_status
        WHERE session_id IN (
            SELECT session_id FROM app.auto_run_sessions
            WHERE status = 'expired' 
               OR ended_at < NOW() - INTERVAL '2 hours'
        )
        RETURNING id
    )
    SELECT COUNT(*) INTO ecu_cleaned FROM deleted_ecu;
    
    RETURN cleaned + streams_cleaned + ecu_cleaned;
END;
$$ LANGUAGE plpgsql;
