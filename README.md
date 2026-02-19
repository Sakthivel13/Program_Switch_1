What happens is now it is marking the VIN as none, and it is passing, but it should not be 'None'; instead, it should be the actual output from the aut0 vin-read program or from the manual entry. And also, you can clearly see it is in the wrong order, which means first VIN Read and Battery Voltage, current page auto-run programs and then the ECU active check auto-run program for the next page. And it is keep on giving this as a output in the console,
(Background on this error at: https://sqlalche.me/e/20/gkpj)
[2026-02-19 08:42:38,681] WARNING in website_with_db: Session cleanup failed: (psycopg2.errors.CheckViolation) new row for relation "auto_run_sessions" violates check constraint "auto_run_sessions_status_check"
DETAIL:  Failing row contains (323, ar_1771313452_85447eec, 1, 1, TVS iQube ST, diagnostics, null, none, expired, [{"log_as_vin": false, "program_id": "AUTO_ECU_ACTIVE_CHECK", "s..., 2026-02-17 13:00:52.72749, null, t).

[SQL: 
                        UPDATE app.auto_run_sessions 
                        SET status = 'expired' 
                        WHERE status IN ('running', 'started') 
                        AND started_at < NOW() - INTERVAL '1 hour'
                    ]
(Background on this error at: https://sqlalche.me/e/20/gkpj)
[2026-02-19 08:45:46,421] WARNING in website_with_db: Session cleanup failed: (psycopg2.errors.CheckViolation) new row for relation "auto_run_sessions" violates check constraint "auto_run_sessions_status_check"
DETAIL:  Failing row contains (323, ar_1771313452_85447eec, 1, 1, TVS iQube ST, diagnostics, null, none, expired, [{"log_as_vin": false, "program_id": "AUTO_ECU_ACTIVE_CHECK", "s..., 2026-02-17 13:00:52.72749, null, t).

[SQL: 
                        UPDATE app.auto_run_sessions 
                        SET status = 'expired' 
                        WHERE status IN ('running', 'started') 
                        AND started_at < NOW() - INTERVAL '1 hour'
                    ]
(Background on this error at: https://sqlalche.me/e/20/gkpj)
[2026-02-19 08:47:38,694] WARNING in website_with_db: Session cleanup failed: (psycopg2.errors.CheckViolation) new row for relation "auto_run_sessions" violates check constraint "auto_run_sessions_status_check"
DETAIL:  Failing row contains (323, ar_1771313452_85447eec, 1, 1, TVS iQube ST, diagnostics, null, none, expired, [{"log_as_vin": false, "program_id": "AUTO_ECU_ACTIVE_CHECK", "s..., 2026-02-17 13:00:52.72749, null, t).

[SQL: 
                        UPDATE app.auto_run_sessions 
                        SET status = 'expired' 
                        WHERE status IN ('running', 'started') 
                        AND started_at < NOW() - INTERVAL '1 hour'
                    ]
(Background on this error at: https://sqlalche.me/e/20/gkpj)
[2026-02-19 08:50:46,431] WARNING in website_with_db: Session cleanup failed: (psycopg2.errors.CheckViolation) new row for relation "auto_run_sessions" violates check constraint "auto_run_sessions_status_check"
DETAIL:  Failing row contains (323, ar_1771313452_85447eec, 1, 1, TVS iQube ST, diagnostics, null, none, expired, [{"log_as_vin": false, "program_id": "AUTO_ECU_ACTIVE_CHECK", "s..., 2026-02-17 13:00:52.72749, null, t).

[SQL: 
                        UPDATE app.auto_run_sessions 
                        SET status = 'expired' 
                        WHERE status IN ('running', 'started') 
                        AND started_at < NOW() - INTERVAL '1 hour'
                    ]
(Background on this error at: https://sqlalche.me/e/20/gkpj)
[2026-02-19 08:52:38,899] WARNING in website_with_db: Session cleanup failed: (psycopg2.errors.CheckViolation) new row for relation "auto_run_sessions" violates check constraint "auto_run_sessions_status_check"
DETAIL:  Failing row contains (323, ar_1771313452_85447eec, 1, 1, TVS iQube ST, diagnostics, null, none, expired, [{"log_as_vin": false, "program_id": "AUTO_ECU_ACTIVE_CHECK", "s..., 2026-02-17 13:00:52.72749, null, t).

[SQL: 
                        UPDATE app.auto_run_sessions 
                        SET status = 'expired' 
                        WHERE status IN ('running', 'started') 
                        AND started_at < NOW() - INTERVAL '1 hour'
                    ]
(Background on this error at: https://sqlalche.me/e/20/gkpj)
[2026-02-19 08:55:46,798] WARNING in website_with_db: Session cleanup failed: (psycopg2.errors.CheckViolation) new row for relation "auto_run_sessions" violates check constraint "auto_run_sessions_status_check"
DETAIL:  Failing row contains (323, ar_1771313452_85447eec, 1, 1, TVS iQube ST, diagnostics, null, none, expired, [{"log_as_vin": false, "program_id": "AUTO_ECU_ACTIVE_CHECK", "s..., 2026-02-17 13:00:52.72749, null, t).

[SQL: 
                        UPDATE app.auto_run_sessions 
                        SET status = 'expired' 
                        WHERE status IN ('running', 'started') 
                        AND started_at < NOW() - INTERVAL '1 hour'
                    ]
(Background on this error at: https://sqlalche.me/e/20/gkpj)
[2026-02-19 08:57:38,944] WARNING in website_with_db: Session cleanup failed: (psycopg2.errors.CheckViolation) new row for relation "auto_run_sessions" violates check constraint "auto_run_sessions_status_check"
DETAIL:  Failing row contains (323, ar_1771313452_85447eec, 1, 1, TVS iQube ST, diagnostics, null, none, expired, [{"log_as_vin": false, "program_id": "AUTO_ECU_ACTIVE_CHECK", "s..., 2026-02-17 13:00:52.72749, null, t).

[SQL: 
                        UPDATE app.auto_run_sessions 
                        SET status = 'expired' 
                        WHERE status IN ('running', 'started') 
                        AND started_at < NOW() - INTERVAL '1 hour'
                    ]
(Background on this error at: https://sqlalche.me/e/20/gkpj)
[2026-02-19 09:00:47,125] WARNING in website_with_db: Session cleanup failed: (psycopg2.errors.CheckViolation) new row for relation "auto_run_sessions" violates check constraint "auto_run_sessions_status_check"
DETAIL:  Failing row contains (323, ar_1771313452_85447eec, 1, 1, TVS iQube ST, diagnostics, null, none, expired, [{"log_as_vin": false, "program_id": "AUTO_ECU_ACTIVE_CHECK", "s..., 2026-02-17 13:00:52.72749, null, t).

[SQL: 
                        UPDATE app.auto_run_sessions 
                        SET status = 'expired' 
                        WHERE status IN ('running', 'started') 
                        AND started_at < NOW() - INTERVAL '1 hour'
                    ]
(Background on this error at: https://sqlalche.me/e/20/gkpj)
[2026-02-19 09:02:39,283] WARNING in website_with_db: Session cleanup failed: (psycopg2.errors.CheckViolation) new row for relation "auto_run_sessions" violates check constraint "auto_run_sessions_status_check"
DETAIL:  Failing row contains (323, ar_1771313452_85447eec, 1, 1, TVS iQube ST, diagnostics, null, none, expired, [{"log_as_vin": false, "program_id": "AUTO_ECU_ACTIVE_CHECK", "s..., 2026-02-17 13:00:52.72749, null, t).

[SQL: 
                        UPDATE app.auto_run_sessions 
                        SET status = 'expired' 
                        WHERE status IN ('running', 'started') 
                        AND started_at < NOW() - INTERVAL '1 hour'
                    ]
(Background on this error at: https://sqlalche.me/e/20/gkpj)
[2026-02-19 09:05:47,155] WARNING in website_with_db: Session cleanup failed: (psycopg2.errors.CheckViolation) new row for relation "auto_run_sessions" violates check constraint "auto_run_sessions_status_check"
DETAIL:  Failing row contains (323, ar_1771313452_85447eec, 1, 1, TVS iQube ST, diagnostics, null, none, expired, [{"log_as_vin": false, "program_id": "AUTO_ECU_ACTIVE_CHECK", "s..., 2026-02-17 13:00:52.72749, null, t).

[SQL: 
                        UPDATE app.auto_run_sessions 
                        SET status = 'expired' 
                        WHERE status IN ('running', 'started') 
                        AND started_at < NOW() - INTERVAL '1 hour'
                    ]
(Background on this error at: https://sqlalche.me/e/20/gkpj)

And the auto-run program of the battery voltage stream is showing only in the test pages. But it should not show in there; instead it should show in the display pages mentioned in the table or in the section_tests.json. Kindly fix all the issues correctly. 
