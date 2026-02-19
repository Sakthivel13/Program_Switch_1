-- Run this SQL command once
ALTER TABLE app.auto_run_sessions DROP CONSTRAINT IF EXISTS auto_run_sessions_status_check;
ALTER TABLE app.auto_run_sessions ADD CONSTRAINT auto_run_sessions_status_check 
CHECK (status IN ('running', 'started', 'completed', 'failed', 'stopped', 'expired'));
