Python 3.12.11 | packaged by conda-forge | (main, Jun  4 2025, 14:29:09) [MSC v.1943 64 bit (AMD64)]
Type "copyright", "credits" or "license" for more information.

IPython 9.6.0 -- An enhanced Interactive Python. Type '?' for help.

%runfile D:/Python/PostgreSQL_Nirix_Diagnostics_Web_Application/Website_With_DB.py --wdir

============================================================
NIRIX DIAGNOSTICS - Starting...
============================================================

[STARTUP] Syncing tests from filesystem...
[LOADER][WARN] Using non-root ecu_tests.json at: D:\Python\PostgreSQL_Nirix_Diagnostics_Web_Application\Test_Programs\TVS_iQube_ST\Diagnostics\ecu_tests.json
[LOADER][WARN] Schema warnings for D:\Python\PostgreSQL_Nirix_Diagnostics_Web_Application\Test_Programs\TVS_iQube_ST\Diagnostics\ecu_tests.json: ["ecus/0: Additional properties are not allowed ('auto_run_programs' was unexpected)"]
[LOADER][ERROR]   Error syncing ecu_tests.json: (psycopg2.errors.UndefinedColumn) column "auto_run_programs" of relation "vehicle_diagnostic_actions" does not exist
LINE 9:                     auto_run_programs = '[{"program_id": "AU...
                            ^

[SQL: 
                UPDATE app.vehicle_diagnostic_actions SET
                    ecu_name    = %(name)s,
                    description = %(desc)s,
                    protocol    = %(proto)s,
                    emission    = %(emission)s,
                    is_active   = %(active)s,
                    sort_order  = %(sort)s,
                    auto_run_programs = %(auto_run)s  -- FIX-45: Store ECU auto-run programs
                WHERE id = %(id)s
            ]
[parameters: {'name': 'BMS', 'desc': 'Battery Management System ECU', 'proto': 'UDS', 'emission': 'OBDII', 'active': True, 'sort': 1, 'auto_run': '[{"program_id": "AUTO_ECU_ACTIVE_CHECK", "program_name": "ECU Active Check", "program_type": "single", "module_name": "ecu_active_check", "function_n ... (254 characters truncated) ... ull}], "fallback_action": "warn_and_continue", "fallback_input": null, "log_as_vin": false, "is_required": true, "timeout_sec": 10, "sort_order": 1}]', 'id': 1}]
(Background on this error at: https://sqlalche.me/e/20/f405)
[STARTUP] Test sync complete: {'vehicles_processed': 1, 'vehicles_skipped': 0, 'sections_created': 0, 'sections_updated': 2, 'ecus_created': 0, 'ecus_updated': 1, 'ecu_auto_run_programs_synced': 0, 'parameters_created': 0, 'parameters_updated': 0, 'health_tabs_created': 0, 'health_tabs_updated': 0, 'tests_created': 0, 'tests_updated': 3, 'errors': 1}
[STARTUP] Validating test definitions (schemas)...
[STARTUP] Test validation: {'vehicles_checked': 1, 'section_files_valid': 1, 'section_files_invalid': 0, 'ecu_files_valid': 0, 'ecu_files_invalid': 1, 'test_files_valid': 2, 'test_files_invalid': 0, 'errors': ["TVS_iQube_ST\\Diagnostics\\ecu_tests.json: Schema validation failed: ecus/0: Additional properties are not allowed ('auto_run_programs' was unexpected)"]}
[STARTUP] Database indexes verified/created

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

ROUTE AUDIT PASSED: All 24 required endpoints present


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
 * Running on http://10.72.188.116:8000
Press CTRL+C to quit
127.0.0.1 - - [18/Feb/2026 21:08:35] "GET / HTTP/1.1" 302 -
127.0.0.1 - - [18/Feb/2026 21:08:35] "GET /dashboard HTTP/1.1" 200 -
127.0.0.1 - - [18/Feb/2026 21:08:36] "GET /vehicle_image/Nirix_Name_Logo.png HTTP/1.1" 304 -
127.0.0.1 - - [18/Feb/2026 21:08:36] "GET /vehicle_image/TVS_KING_GD.png HTTP/1.1" 304 -
127.0.0.1 - - [18/Feb/2026 21:08:36] "GET /vehicle_image/TVS_KING_3W_LARGE.png HTTP/1.1" 304 -
127.0.0.1 - - [18/Feb/2026 21:08:36] "GET /vehicle_image/TVS_Apache_RTR_200_4V.png HTTP/1.1" 304 -
127.0.0.1 - - [18/Feb/2026 21:08:36] "GET /vehicle_image/TVS_Apache_RTX.png HTTP/1.1" 304 -
127.0.0.1 - - [18/Feb/2026 21:08:36] "GET /vehicle_image/TVS_KING_E.png HTTP/1.1" 304 -
127.0.0.1 - - [18/Feb/2026 21:08:36] "GET /vehicle_image/TVS_Apache_RTR_160_2V.png HTTP/1.1" 304 -
127.0.0.1 - - [18/Feb/2026 21:08:36] "GET /vehicle_image/TVS_KING_ZK_LT.png HTTP/1.1" 304 -
127.0.0.1 - - [18/Feb/2026 21:08:36] "GET /vehicle_image/TVS_KING_LS+.png HTTP/1.1" 304 -
127.0.0.1 - - [18/Feb/2026 21:08:36] "GET /vehicle_image/TVS_iQube_ST.png HTTP/1.1" 304 -
127.0.0.1 - - [18/Feb/2026 21:08:36] "GET /vehicle_image/TVS_iQube_S.png HTTP/1.1" 304 -
127.0.0.1 - - [18/Feb/2026 21:08:37] "GET /vehicle_image/TVS_KING_ZS+.png HTTP/1.1" 304 -
127.0.0.1 - - [18/Feb/2026 21:08:37] "GET /vehicle_image/TVS_Jupiter_New.png HTTP/1.1" 304 -
127.0.0.1 - - [18/Feb/2026 21:08:37] "GET /vehicle_image/TVS_KING_ZD.png HTTP/1.1" 304 -
127.0.0.1 - - [18/Feb/2026 21:08:37] "GET /vehicle_image/TVS_3W_LARGE.png HTTP/1.1" 304 -
127.0.0.1 - - [18/Feb/2026 21:08:37] "GET /vehicle_image/TVS_KING_ZK_PF.png HTTP/1.1" 304 -
127.0.0.1 - - [18/Feb/2026 21:08:37] "GET /vehicle_image/TVS_Jupiter_Old.png HTTP/1.1" 304 -
127.0.0.1 - - [18/Feb/2026 21:08:37] "GET /vehicle_image/TVS_KING_GS+.png HTTP/1.1" 304 -
127.0.0.1 - - [18/Feb/2026 21:08:37] "GET /vehicle_image/TVS_Ntorq_125.png HTTP/1.1" 304 -
127.0.0.1 - - [18/Feb/2026 21:08:37] "GET /vehicle_image/TVS_Ntorq_150.png HTTP/1.1" 304 -
127.0.0.1 - - [18/Feb/2026 21:08:37] "GET /vehicle_image/TVS_Radeon.png HTTP/1.1" 304 -
127.0.0.1 - - [18/Feb/2026 21:08:37] "GET /vehicle_image/TVS_Raider_125.png HTTP/1.1" 304 -
127.0.0.1 - - [18/Feb/2026 21:08:37] "GET /vehicle_image/TVS_Raider_IGO.png HTTP/1.1" 304 -
127.0.0.1 - - [18/Feb/2026 21:08:37] "GET /vehicle_image/TVS_Ronin.png HTTP/1.1" 304 -
127.0.0.1 - - [18/Feb/2026 21:08:37] "GET /vehicle_image/TVS_Scooty_Pep_Plus.png HTTP/1.1" 304 -
127.0.0.1 - - [18/Feb/2026 21:08:37] "GET /vehicle_image/TVS_Sport.png HTTP/1.1" 304 -
127.0.0.1 - - [18/Feb/2026 21:08:37] "GET /vehicle_image/TVS_Sport_Kick_Start.png HTTP/1.1" 304 -
127.0.0.1 - - [18/Feb/2026 21:08:37] "GET /vehicle_image/TVS_Star_City_Plus.png HTTP/1.1" 304 -
127.0.0.1 - - [18/Feb/2026 21:08:37] "GET /vehicle_image/TVS_XL_100.png HTTP/1.1" 304 -
127.0.0.1 - - [18/Feb/2026 21:08:37] "GET /vehicle_image/TVS_XL_100_HD.png HTTP/1.1" 304 -
127.0.0.1 - - [18/Feb/2026 21:08:37] "GET /vehicle_image/TVS_Zest.png HTTP/1.1" 304 -
127.0.0.1 - - [18/Feb/2026 21:08:38] "GET /vehicle_image/TVS_Apache_RTR_180_2V.png HTTP/1.1" 304 -
127.0.0.1 - - [18/Feb/2026 21:08:38] "GET /vehicle_image/TVS_Apache_160_4V_ABS.png HTTP/1.1" 304 -
127.0.0.1 - - [18/Feb/2026 21:08:38] "GET /vehicle_image/TVS_Apache_RR_310.png HTTP/1.1" 304 -
127.0.0.1 - - [18/Feb/2026 21:08:39] "GET /favicon.ico HTTP/1.1" 204 -
127.0.0.1 - - [18/Feb/2026 21:08:57] "GET /tests/TVS%20iQube%20ST HTTP/1.1" 302 -
127.0.0.1 - - [18/Feb/2026 21:08:57] "GET /tests?model=TVS+iQube+ST HTTP/1.1" 200 -
127.0.0.1 - - [18/Feb/2026 21:08:57] "GET /vehicle_image/Nirix_Name_Logo.png HTTP/1.1" 304 -
127.0.0.1 - - [18/Feb/2026 21:08:58] "GET /vehicle_image/TVS_iQube_ST.png HTTP/1.1" 304 -
127.0.0.1 - - [18/Feb/2026 21:08:58] "GET /static/icons/diagnostics.svg HTTP/1.1" 304 -
127.0.0.1 - - [18/Feb/2026 21:08:58] "GET /static/icons/vehicle_health.svg HTTP/1.1" 304 -
127.0.0.1 - - [18/Feb/2026 21:08:59] "GET /favicon.ico HTTP/1.1" 204 -
[SERVICE] Error loading ECUs from DB: (psycopg2.errors.UndefinedColumn) column vda.auto_run_programs does not exist
LINE 5:                     df.icon, vda.auto_run_programs
                                     ^

[SQL: 
                SELECT
                    vda.ecu_code, vda.ecu_name, vda.description,
                    vda.protocol, vda.emission, vda.sort_order,
                    df.icon, vda.auto_run_programs
                FROM app.vehicle_diagnostic_actions vda
                LEFT JOIN app.diagnostic_folders df
                       ON df.id = vda.folder_id
                WHERE vda.vehicle_id = %(vid)s AND vda.is_active = TRUE
                ORDER BY vda.sort_order, vda.ecu_name
            ]
[parameters: {'vid': 1}]
(Background on this error at: https://sqlalche.me/e/20/f405)
127.0.0.1 - - [18/Feb/2026 21:09:00] "POST /api/run_auto_programs HTTP/1.1" 200 -
[LOADER][WARN] Using non-root ecu_tests.json at: D:\Python\PostgreSQL_Nirix_Diagnostics_Web_Application\Test_Programs\TVS_iQube_ST\Diagnostics\ecu_tests.json
[LOADER][WARN] Schema warnings for D:\Python\PostgreSQL_Nirix_Diagnostics_Web_Application\Test_Programs\TVS_iQube_ST\Diagnostics\ecu_tests.json: ["ecus/0: Additional properties are not allowed ('auto_run_programs' was unexpected)"]
[LOADER][ERROR] Error fetching ECU auto-run from DB: (psycopg2.errors.UndefinedColumn) column "auto_run_programs" does not exist
LINE 2:                     SELECT auto_run_programs
                                   ^

[SQL: 
                    SELECT auto_run_programs
                    FROM app.vehicle_diagnostic_actions
                    WHERE vehicle_id = %(vid)s
                      AND ecu_code = %(ecu)s
                      AND is_active = TRUE
                ]
[parameters: {'vid': 1, 'ecu': 'BMS'}]
(Background on this error at: https://sqlalche.me/e/20/f405)
[LOADER][WARN] Using non-root ecu_tests.json at: D:\Python\PostgreSQL_Nirix_Diagnostics_Web_Application\Test_Programs\TVS_iQube_ST\Diagnostics\ecu_tests.json
[LOADER][WARN] Schema warnings for D:\Python\PostgreSQL_Nirix_Diagnostics_Web_Application\Test_Programs\TVS_iQube_ST\Diagnostics\ecu_tests.json: ["ecus/0: Additional properties are not allowed ('auto_run_programs' was unexpected)"]
127.0.0.1 - - [18/Feb/2026 21:09:01] "GET /api/auto_run/ar_1771429140_99206405/status HTTP/1.1" 200 -
127.0.0.1 - - [18/Feb/2026 21:09:01] "GET /api/auto_run/ar_1771429140_99206405/status HTTP/1.1" 200 -
[RUNNER]     FAILED: ECU Active Check
127.0.0.1 - - [18/Feb/2026 21:09:02] "GET /tests?model=TVS+iQube+ST&section=diagnostics&auto_run_session_id=ar_1771429140_99206405 HTTP/1.1" 200 -
127.0.0.1 - - [18/Feb/2026 21:09:02] "GET /vehicle_image/Nirix_Name_Logo.png HTTP/1.1" 304 -
127.0.0.1 - - [18/Feb/2026 21:09:02] "GET /vehicle_image/TVS_iQube_ST.png HTTP/1.1" 304 -
127.0.0.1 - - [18/Feb/2026 21:09:02] "GET /static/icons/microchip.svg HTTP/1.1" 304 -
127.0.0.1 - - [18/Feb/2026 21:09:03] "GET /favicon.ico HTTP/1.1" 204 -

We are having two main issues like one is the above one and the other is like when we click the diagnostics it should show the running of VIN read and Battery Voltage, after running these programs successfully their actual output in the page mentioned in the display page in the section_tests.json. And if the VIN read program fails it should open the pop up UI where we can enter the manual or scanned vin and this should show in that pages. And after opening the next page the auto_run program mentioned in that, that is ECU active check should run like how the other auto-run programs runned and it should show the result in different mannar like it should show the green dot in top right corner in that mentioned ECU horizontal grid and red dot if the ECU is not active this program details is mentioned in ecu_tests.json.
