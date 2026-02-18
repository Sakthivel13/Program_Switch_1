-- =============================================================================
-- FIX: Add missing auto_run_programs column to vehicle_diagnostic_actions
-- =============================================================================

-- Check if column exists and add if missing
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_schema = 'app' 
        AND table_name = 'vehicle_diagnostic_actions' 
        AND column_name = 'auto_run_programs'
    ) THEN
        ALTER TABLE app.vehicle_diagnostic_actions 
        ADD COLUMN auto_run_programs JSONB;
        
        RAISE NOTICE 'Added auto_run_programs column to vehicle_diagnostic_actions';
    ELSE
        RAISE NOTICE 'auto_run_programs column already exists';
    END IF;
END $$;

-- =============================================================================
-- FIX: Update the schema validation to allow auto_run_programs in ecu_tests.json
-- =============================================================================

-- Note: You need to update your ecu.schema.json file to allow 'auto_run_programs'
-- Add this to your ecu.schema.json in the ecu object properties:
-- "auto_run_programs": {
--   "type": "array",
--   "description": "ECU-specific auto-run programs",
--   "items": {
--     "$ref": "#/definitions/autoRunProgram"
--   }
-- }

-- =============================================================================
-- Create or replace the function to get ECU status for UI
-- =============================================================================

CREATE OR REPLACE FUNCTION app.get_ecu_status_for_session(p_session_id TEXT)
RETURNS TABLE (
    ecu_code TEXT,
    is_active BOOLEAN,
    last_response TIMESTAMP,
    error_count INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        e.ecu_code,
        e.is_active,
        e.last_response,
        e.error_count
    FROM app.ecu_active_status e
    WHERE e.session_id = p_session_id
    ORDER BY e.ecu_code;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- Ensure all indexes exist for performance
-- =============================================================================

CREATE INDEX IF NOT EXISTS idx_vehicle_diagnostic_actions_ecu 
ON app.vehicle_diagnostic_actions(vehicle_id, ecu_code);

CREATE INDEX IF NOT EXISTS idx_vehicle_diagnostic_actions_auto_run 
ON app.vehicle_diagnostic_actions USING gin(auto_run_programs);

CREATE INDEX IF NOT EXISTS idx_ecu_active_status_session_ecu 
ON app.ecu_active_status(session_id, ecu_code);

-- =============================================================================
-- Verify the schema
-- =============================================================================

SELECT 
    column_name, 
    data_type, 
    is_nullable
FROM information_schema.columns 
WHERE table_schema = 'app' 
AND table_name = 'vehicle_diagnostic_actions'
ORDER BY ordinal_position;
