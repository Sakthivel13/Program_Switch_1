============================================================
NIRIX DIAGNOSTICS - Starting...
============================================================

[STARTUP] Syncing tests from filesystem...
[2026-02-21 21:00:16][LOADER][WARN] Schema warnings for D:\Python\PostgreSQL_Nirix_Diagnostics_Web_Application\Test_Programs\TVS_iQube_ST\section_tests.json: ["schema_version: '1.0' does not match '^\\\\d+\\\\.\\\\d+\\\\.\\\\d+$'"]
[2026-02-21 21:00:16][LOADER][WARN] Using non-root ecu_tests.json at: D:\Python\PostgreSQL_Nirix_Diagnostics_Web_Application\Test_Programs\TVS_iQube_ST\Diagnostics\ecu_tests.json
[2026-02-21 21:00:16][LOADER][WARN] Schema warnings for D:\Python\PostgreSQL_Nirix_Diagnostics_Web_Application\Test_Programs\TVS_iQube_ST\Diagnostics\ecu_tests.json: ["schema_version: '1.0' does not match '^\\\\d+\\\\.\\\\d+\\\\.\\\\d+$'"]
[2026-02-21 21:00:16][LOADER][ERROR]   Error syncing ecu_tests.json: (psycopg2.errors.UndefinedColumn) column "updated_at" of relation "vehicle_diagnostic_actions" does not exist
LINE 10:                     updated_at = CURRENT_TIMESTAMP
                             ^

[SQL: 
                UPDATE app.vehicle_diagnostic_actions SET
                    ecu_name    = %(name)s,
                    description = %(desc)s,
                    protocol    = %(proto)s,
                    emission    = %(emission)s,
                    is_active   = %(active)s,
                    sort_order  = %(sort)s,
                    auto_run_programs = %(auto_run)s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %(id)s
            ]
[parameters: {'name': 'BMS', 'desc': 'Battery Management System ECU', 'proto': 'UDS', 'emission': 'OBDII', 'active': True, 'sort': 1, 'auto_run': '[{"program_id": "AUTO_ECU_ACTIVE_CHECK", "program_name": "ECU Active Check", "program_type": "single", "module_name": "ecu_active_check", "function_n ... (275 characters truncated) ... action": "warn_and_continue", "fallback_input": null, "log_as_vin": false, "is_required": true, "timeout_sec": 10, "sort_order": 1, "source": "ecu"}]', 'id': 1}]
(Background on this error at: https://sqlalche.me/e/20/f405)
[2026-02-21 21:00:16][LOADER][WARN] Schema warnings for D:\Python\PostgreSQL_Nirix_Diagnostics_Web_Application\Test_Programs\TVS_iQube_ST\Diagnostics\BMS\LIVE_PARAMETER\tests.json: ["schema_version: '1.0' does not match '^\\\\d+\\\\.\\\\d+\\\\.\\\\d+$'", "tests/1/output_limits/0/signal: 'Light Focus' does not match '^[a-zA-Z0-9_]+$'"]
[2026-02-21 21:00:16][LOADER][WARN] Schema warnings for D:\Python\PostgreSQL_Nirix_Diagnostics_Web_Application\Test_Programs\TVS_iQube_ST\Diagnostics\BMS\WRITE_DATA_IDENTIFIER\tests.json: ["schema_version: '1.0' does not match '^\\\\d+\\\\.\\\\d+\\\\.\\\\d+$'"]
[STARTUP] Test sync complete: {'vehicles_processed': 1, 'vehicles_skipped': 0, 'sections_created': 0, 'sections_updated': 2, 'ecus_created': 0, 'ecus_updated': 1, 'ecu_auto_run_programs_synced': 0, 'parameters_created': 0, 'parameters_updated': 0, 'health_tabs_created': 0, 'health_tabs_updated': 0, 'tests_created': 0, 'tests_updated': 3, 'errors': 1}
[STARTUP] Validating test definitions (schemas)...
[STARTUP] Test validation: {'vehicles_checked': 1, 'section_files_valid': 0, 'section_files_invalid': 1, 'ecu_files_valid': 0, 'ecu_files_invalid': 1, 'test_files_valid': 0, 'test_files_invalid': 2, 'errors': ["TVS_iQube_ST\\section_tests.json: Schema validation failed: schema_version: '1.0' does not match '^\\\\d+\\\\.\\\\d+\\\\.\\\\d+$'", "TVS_iQube_ST\\Diagnostics\\ecu_tests.json: Schema validation failed: schema_version: '1.0' does not match '^\\\\d+\\\\.\\\\d+\\\\.\\\\d+$'", "TVS_iQube_ST\\Diagnostics\\BMS\\LIVE_PARAMETER\\tests.json: Schema validation failed: schema_version: '1.0' does not match '^\\\\d+\\\\.\\\\d+\\\\.\\\\d+$'; tests/1/output_limits/0/signal: 'Light Focus' does not match '^[a-zA-Z0-9_]+$'", "TVS_iQube_ST\\Diagnostics\\BMS\\WRITE_DATA_IDENTIFIER\\tests.json: Schema validation failed: schema_version: '1.0' does not match '^\\\\d+\\\\.\\\\d+\\\\.\\\\d+$'"]}

============================================================
ROUTE AUDIT
============================================================

  admin.admin_add_role                     -> /admin/roles/add
  admin.admin_add_test                     -> /admin/tests/add
  admin.admin_add_user                     -> /admin/users/add
  admin.admin_add_vehicle                  -> /admin/vehicles/add
  admin.admin_approve_user                 -> /admin/users/approve/<int:user_id>
  admin.admin_change_role                  -> /admin/users/role/<int:user_id>
  admin.admin_config                       -> /admin/config
  admin.admin_config_all                   -> /admin/config/all
  admin.admin_config_delete                -> /admin/config/delete/<int:config_id>
  admin.admin_config_save                  -> /admin/config
  admin.admin_config_update                -> /admin/config/update/<int:config_id>
  admin.admin_dashboard                    -> /admin/
  admin.admin_dashboard_data               -> /admin/dashboard/data
  admin.admin_delete_role                  -> /admin/roles/delete/<int:role_id>
  admin.admin_delete_test                  -> /admin/tests/delete/<test_id>
  admin.admin_delete_user                  -> /admin/users/delete/<int:user_id>
  admin.admin_delete_vehicle               -> /admin/vehicles/delete/<int:vehicle_id>
  admin.admin_disable_user                 -> /admin/users/disable/<int:user_id>
  admin.admin_edit_role                    -> /admin/roles/edit/<int:role_id>
  admin.admin_edit_test                    -> /admin/tests/edit/<test_id>
  admin.admin_edit_user                    -> /admin/users/edit/<int:user_id>
  admin.admin_edit_vehicle                 -> /admin/vehicles/edit/<int:vehicle_id>
  admin.admin_enable_user                  -> /admin/users/enable/<int:user_id>
  admin.admin_logs                         -> /admin/logs
  admin.admin_logs_delete                  -> /admin/logs/delete/<int:log_id>
  admin.admin_logs_download                -> /admin/logs/download/<int:log_id>
  admin.admin_logs_purge                   -> /admin/logs/purge
  admin.admin_logs_undo                    -> /admin/logs/undo
  admin.admin_logs_view                    -> /admin/logs/view/<int:log_id>
  admin.admin_reset_pin                    -> /admin/users/reset_pin/<int:user_id>
  admin.admin_roles                        -> /admin/roles
  admin.admin_test_active                  -> /admin/tests/active/<test_id>/<int:state>
  admin.admin_tests                        -> /admin/tests
  admin.admin_tests_purge                  -> /admin/tests/purge
  admin.admin_tests_sync_db                -> /admin/tests/sync_db
  admin.admin_tests_sync_from_json         -> /admin/tests/sync_from_json/<int:vehicle_id>
  admin.admin_tests_sync_preview           -> /admin/tests/sync_preview/<int:vehicle_id>
  admin.admin_undo_test                    -> /admin/tests/undo
  admin.admin_undo_user                    -> /admin/users/undo
  admin.admin_undo_vehicle                 -> /admin/vehicles/undo
  admin.admin_users                        -> /admin/users
  admin.admin_users_purge                  -> /admin/users/purge
  admin.admin_vehicle_active               -> /admin/vehicles/active/<int:vehicle_id>/<int:state>
  admin.admin_vehicles                     -> /admin/vehicles
  admin.admin_vehicles_purge               -> /admin/vehicles/purge
  admin.api_get_user_test_permissions      -> /admin/api/users/<int:user_id>/tests
  admin.api_get_user_vehicle_permissions   -> /admin/api/users/<int:user_id>/vehicles
  admin.api_get_vehicle_users              -> /admin/api/vehicles/<int:vehicle_id>/users
  admin.api_save_user_test_permissions     -> /admin/api/users/<int:user_id>/tests
  admin.api_save_user_vehicle_permissions  -> /admin/api/users/<int:user_id>/vehicles
  admin.api_save_vehicle_users             -> /admin/api/vehicles/<int:vehicle_id>/users
  admin.api_test_exec_get                  -> /admin/api/tests/<test_id>/exec/get
  admin.api_test_exec_save                 -> /admin/api/tests/<test_id>/exec/save
  admin.api_test_flashing_get              -> /admin/api/tests/<test_id>/flashing/get
  admin.api_test_flashing_save             -> /admin/api/tests/<test_id>/flashing/save
  admin.api_test_inputs_get                -> /admin/api/tests/<test_id>/inputs/get
  admin.api_test_inputs_save               -> /admin/api/tests/<test_id>/inputs/save
  admin.api_test_limits_get                -> /admin/api/tests/<test_id>/limits/get
  admin.api_test_limits_save               -> /admin/api/tests/<test_id>/limits/save
  admin.api_test_users                     -> /admin/api/tests/<test_id>/users
  admin.api_tests_filters_ecus             -> /admin/api/tests/filters/ecus
  admin.api_tests_filters_parameters       -> /admin/api/tests/filters/parameters
  admin.api_tests_filters_sections         -> /admin/api/tests/filters/sections
  admin.api_tests_query                    -> /admin/api/tests/query
  admin.api_user_tests_assigned            -> /admin/api/users/<int:user_id>/tests/assigned
  admin.api_user_tests_ecus                -> /admin/api/users/<int:user_id>/tests/ecus
  admin.api_user_tests_list                -> /admin/api/users/<int:user_id>/tests/list
  admin.api_user_tests_parameters          -> /admin/api/users/<int:user_id>/tests/parameters
  admin.api_user_tests_save                -> /admin/api/users/<int:user_id>/tests/save
  admin.api_user_tests_sections            -> /admin/api/users/<int:user_id>/tests/sections
  admin.api_user_vehicles_get              -> /admin/api/users/<int:user_id>/vehicles
  admin.api_user_vehicles_set              -> /admin/api/users/<int:user_id>/vehicles
  admin.static                             -> /admin/static/<path:filename>
  api_append_log                           -> /api/append_log
  api_auto_run_heartbeat                   -> /api/auto_run/<session_id>/heartbeat
  api_auto_run_status                      -> /api/auto_run/<session_id>/status
  api_auto_run_vin                         -> /api/auto_run/vin
  api_batch_cancel                         -> /api/batch/<batch_id>/cancel
  api_batch_status                         -> /api/batch/<batch_id>/status
  api_clear_logs                           -> /api/clear_logs
  api_get_ecu_status                       -> /api/auto_run/<session_id>/ecu_status
  api_get_ecus                             -> /api/ecus/<vehicle_name>
  api_get_health_tabs                      -> /api/health_tabs/<vehicle_name>
  api_get_parameters                       -> /api/parameters/<vehicle_name>/<ecu_code>
  api_get_sections                         -> /api/sections/<vehicle_name>
  api_get_stream_values                    -> /api/auto_run/<session_id>/stream_values
  api_get_test_history                     -> /api/test/<test_id>/history
  api_get_tests                            -> /api/tests
  api_live_logs                            -> /api/live_logs
  api_run_all_for_parameter                -> /api/run_all_for_parameter
  api_run_all_tests                        -> /api/run_all_tests
  api_run_auto_programs                    -> /api/run_auto_programs
  api_run_test                             -> /api/run_test
  api_runner_stats                         -> /api/runner/stats
  api_save_test_log                        -> /api/log/save_test
  api_scan_cancel                          -> /api/scan/<scan_id>/cancel
  api_scan_frame                           -> /api/scan/<scan_id>/frame
  api_scan_start                           -> /api/scan/start
  api_scan_status                          -> /api/scan/<scan_id>/status
  api_set_theme                            -> /api/set_theme
  api_sync_tests                           -> /api/admin/sync_tests
  api_task_cancel                          -> /api/task/<task_id>/cancel
  api_task_logs                            -> /api/task/<task_id>/logs
  api_task_logs_clear                      -> /api/task/<task_id>/logs/clear
  api_task_pause                           -> /api/task/<task_id>/pause
  api_task_resume                          -> /api/task/<task_id>/resume
  api_task_status                          -> /api/task/<task_id>/status
  dashboard                                -> /dashboard
  downloads_page                           -> /downloads
  favicon                                  -> /favicon.ico
  forgot_pin                               -> /forgot-pin
  health_check                             -> /health
  login                                    -> /login
  logout                                   -> /logout
  logs_download                            -> /logs/download/<int:log_id>
  logs_page                                -> /logs
  logs_view                                -> /logs/view/<int:log_id>
  register                                 -> /register
  reset_pin_new                            -> /reset-pin-new
  reset_pin_verify                         -> /reset-pin-verify
  root                                     -> /
  static                                   -> /static/<path:filename>
  tests_page                               -> /tests/<path:model_name>
  tests_root                               -> /tests
  vehicle_image                            -> /vehicle_image/<path:filename>

ROUTE AUDIT PASSED: All 20 required endpoints present


============================================================
NIRIX Diagnostics v3.2.0
URL: http://0.0.0.0:8000
Station ID: HOSNBS8524635
Active Tasks: 0
Scanner Available: True
============================================================

 * Serving Flask app 'website_with_db'
 * Debug mode: off
WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:8000
 * Running on http://172.16.145.116:8000
Press CTRL+C to quit
127.0.0.1 - - [21/Feb/2026 21:00:17] "GET / HTTP/1.1" 302 -
127.0.0.1 - - [21/Feb/2026 21:00:18] "GET /dashboard HTTP/1.1" 200 -
127.0.0.1 - - [21/Feb/2026 21:00:18] "GET /vehicle_image/Nirix_Name_Logo.png HTTP/1.1" 304 -
127.0.0.1 - - [21/Feb/2026 21:00:18] "GET /vehicle_image/TVS_3W_LARGE.png HTTP/1.1" 304 -
127.0.0.1 - - [21/Feb/2026 21:00:19] "GET /vehicle_image/TVS_Apache_160_4V_ABS.png HTTP/1.1" 304 -
127.0.0.1 - - [21/Feb/2026 21:00:19] "GET /vehicle_image/TVS_Apache_RTR_160_2V.png HTTP/1.1" 304 -
127.0.0.1 - - [21/Feb/2026 21:00:19] "GET /vehicle_image/TVS_iQube_S.png HTTP/1.1" 304 -
127.0.0.1 - - [21/Feb/2026 21:00:19] "GET /vehicle_image/TVS_iQube_ST.png HTTP/1.1" 304 -
127.0.0.1 - - [21/Feb/2026 21:00:19] "GET /vehicle_image/TVS_Jupiter_New.png HTTP/1.1" 304 -
127.0.0.1 - - [21/Feb/2026 21:00:19] "GET /vehicle_image/TVS_Jupiter_Old.png HTTP/1.1" 304 -
127.0.0.1 - - [21/Feb/2026 21:00:19] "GET /vehicle_image/TVS_KING_3W_LARGE.png HTTP/1.1" 304 -
127.0.0.1 - - [21/Feb/2026 21:00:19] "GET /vehicle_image/TVS_KING_GD.png HTTP/1.1" 304 -
127.0.0.1 - - [21/Feb/2026 21:00:19] "GET /vehicle_image/TVS_KING_LS+.png HTTP/1.1" 304 -
127.0.0.1 - - [21/Feb/2026 21:00:19] "GET /vehicle_image/TVS_KING_E.png HTTP/1.1" 304 -
127.0.0.1 - - [21/Feb/2026 21:00:19] "GET /vehicle_image/TVS_KING_GS+.png HTTP/1.1" 304 -
127.0.0.1 - - [21/Feb/2026 21:00:19] "GET /vehicle_image/TVS_KING_ZD.png HTTP/1.1" 304 -
127.0.0.1 - - [21/Feb/2026 21:00:20] "GET /vehicle_image/TVS_KING_ZK_LT.png HTTP/1.1" 304 -
127.0.0.1 - - [21/Feb/2026 21:00:20] "GET /vehicle_image/TVS_KING_ZK_PF.png HTTP/1.1" 304 -
127.0.0.1 - - [21/Feb/2026 21:00:20] "GET /vehicle_image/TVS_KING_ZS+.png HTTP/1.1" 304 -
127.0.0.1 - - [21/Feb/2026 21:00:20] "GET /vehicle_image/TVS_Ntorq_125.png HTTP/1.1" 304 -
127.0.0.1 - - [21/Feb/2026 21:00:20] "GET /vehicle_image/TVS_Ntorq_150.png HTTP/1.1" 304 -
127.0.0.1 - - [21/Feb/2026 21:00:20] "GET /vehicle_image/TVS_Radeon.png HTTP/1.1" 304 -
127.0.0.1 - - [21/Feb/2026 21:00:20] "GET /vehicle_image/TVS_Raider_125.png HTTP/1.1" 304 -
127.0.0.1 - - [21/Feb/2026 21:00:20] "GET /vehicle_image/TVS_Raider_IGO.png HTTP/1.1" 304 -
127.0.0.1 - - [21/Feb/2026 21:00:20] "GET /vehicle_image/TVS_Ronin.png HTTP/1.1" 304 -
127.0.0.1 - - [21/Feb/2026 21:00:20] "GET /vehicle_image/TVS_Scooty_Pep_Plus.png HTTP/1.1" 304 -
127.0.0.1 - - [21/Feb/2026 21:00:20] "GET /vehicle_image/TVS_Sport.png HTTP/1.1" 304 -
127.0.0.1 - - [21/Feb/2026 21:00:20] "GET /vehicle_image/TVS_Sport_Kick_Start.png HTTP/1.1" 304 -
127.0.0.1 - - [21/Feb/2026 21:00:20] "GET /vehicle_image/TVS_Star_City_Plus.png HTTP/1.1" 304 -
127.0.0.1 - - [21/Feb/2026 21:00:20] "GET /vehicle_image/TVS_Apache_RTR_180_2V.png HTTP/1.1" 304 -
127.0.0.1 - - [21/Feb/2026 21:00:20] "GET /vehicle_image/TVS_Apache_RR_310.png HTTP/1.1" 304 -
127.0.0.1 - - [21/Feb/2026 21:00:20] "GET /vehicle_image/TVS_XL_100.png HTTP/1.1" 304 -
127.0.0.1 - - [21/Feb/2026 21:00:20] "GET /vehicle_image/TVS_Zest.png HTTP/1.1" 304 -
127.0.0.1 - - [21/Feb/2026 21:00:20] "GET /vehicle_image/TVS_XL_100_HD.png HTTP/1.1" 304 -
127.0.0.1 - - [21/Feb/2026 21:00:20] "GET /vehicle_image/TVS_Apache_RTR_200_4V.png HTTP/1.1" 304 -
127.0.0.1 - - [21/Feb/2026 21:00:20] "GET /vehicle_image/TVS_Apache_RTX.png HTTP/1.1" 304 -
127.0.0.1 - - [21/Feb/2026 21:00:22] "GET /favicon.ico HTTP/1.1" 204 -
127.0.0.1 - - [21/Feb/2026 21:00:26] "GET /tests/TVS%20iQube%20ST HTTP/1.1" 302 -
[2026-02-21 21:00:26][LOADER][WARN] Schema warnings for D:\Python\PostgreSQL_Nirix_Diagnostics_Web_Application\Test_Programs\TVS_iQube_ST\section_tests.json: ["schema_version: '1.0' does not match '^\\\\d+\\\\.\\\\d+\\\\.\\\\d+$'"]
127.0.0.1 - - [21/Feb/2026 21:00:26] "GET /tests?model=TVS+iQube+ST HTTP/1.1" 200 -
127.0.0.1 - - [21/Feb/2026 21:00:26] "GET /static/icons/diagnostics.svg HTTP/1.1" 304 -
127.0.0.1 - - [21/Feb/2026 21:00:26] "GET /static/icons/vehicle_health.svg HTTP/1.1" 304 -
127.0.0.1 - - [21/Feb/2026 21:00:27] "GET /favicon.ico HTTP/1.1" 204 -
[2026-02-21 21:00:28,801] ERROR in app: Exception on /api/run_auto_programs [POST]
Traceback (most recent call last):
  File "C:\Users\sri.sakthivel\AppData\Local\spyder-6\envs\spyder-runtime\Lib\site-packages\flask\app.py", line 1511, in wsgi_app
    response = self.full_dispatch_request()
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\sri.sakthivel\AppData\Local\spyder-6\envs\spyder-runtime\Lib\site-packages\flask\app.py", line 919, in full_dispatch_request
    rv = self.handle_user_exception(e)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\sri.sakthivel\AppData\Local\spyder-6\envs\spyder-runtime\Lib\site-packages\flask\app.py", line 917, in full_dispatch_request
    rv = self.dispatch_request()
         ^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\sri.sakthivel\AppData\Local\spyder-6\envs\spyder-runtime\Lib\site-packages\flask\app.py", line 902, in dispatch_request
    return self.ensure_sync(self.view_functions[rule.endpoint])(**view_args)  # type: ignore[no-any-return]
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "d:\python\postgresql_nirix_diagnostics_web_application\website_with_db.py", line 1456, in api_run_auto_programs
    result = start_auto_run(
             ^^^^^^^^^^^^^^^
  File "D:\Python\PostgreSQL_Nirix_Diagnostics_Web_Application\diagnostics\service.py", line 1586, in start_auto_run
    args = [can_config["can_interface"], can_config["bitrate"]]
            ~~~~~~~~~~^^^^^^^^^^^^^^^^^
KeyError: 'can_interface'
[2026-02-21 21:00:28,817] ERROR in website_with_db: Internal server error
Traceback (most recent call last):
  File "C:\Users\sri.sakthivel\AppData\Local\spyder-6\envs\spyder-runtime\Lib\site-packages\flask\app.py", line 1511, in wsgi_app
    response = self.full_dispatch_request()
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\sri.sakthivel\AppData\Local\spyder-6\envs\spyder-runtime\Lib\site-packages\flask\app.py", line 919, in full_dispatch_request
    rv = self.handle_user_exception(e)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\sri.sakthivel\AppData\Local\spyder-6\envs\spyder-runtime\Lib\site-packages\flask\app.py", line 917, in full_dispatch_request
    rv = self.dispatch_request()
         ^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\sri.sakthivel\AppData\Local\spyder-6\envs\spyder-runtime\Lib\site-packages\flask\app.py", line 902, in dispatch_request
    return self.ensure_sync(self.view_functions[rule.endpoint])(**view_args)  # type: ignore[no-any-return]
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "d:\python\postgresql_nirix_diagnostics_web_application\website_with_db.py", line 1456, in api_run_auto_programs
    result = start_auto_run(
             ^^^^^^^^^^^^^^^
  File "D:\Python\PostgreSQL_Nirix_Diagnostics_Web_Application\diagnostics\service.py", line 1586, in start_auto_run
    args = [can_config["can_interface"], can_config["bitrate"]]
            ~~~~~~~~~~^^^^^^^^^^^^^^^^^
KeyError: 'can_interface'
127.0.0.1 - - [21/Feb/2026 21:00:28] "POST /api/run_auto_programs HTTP/1.1" 500 -
