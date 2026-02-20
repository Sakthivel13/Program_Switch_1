[2026-02-20 11:39:16,316] WARNING in website_with_db: Session cleanup failed: (psycopg2.errors.UndefinedColumn) column "updated_at" does not exist
LINE 1: ...pp.auto_run_sessions WHERE status = 'expired' AND updated_at...
                                                             ^

[SQL: SELECT count(*) as cnt FROM app.auto_run_sessions WHERE status = 'expired' AND updated_at > NOW() - INTERVAL '5 minutes']
(Background on this error at: https://sqlalche.me/e/20/f405)
