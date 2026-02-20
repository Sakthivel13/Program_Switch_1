[2026-02-20 11:39:16,316] WARNING in website_with_db: Session cleanup failed: (psycopg2.errors.UndefinedColumn) column "updated_at" does not exist LINE 1: ...pp.auto_run_sessions WHERE status = 'expired' AND updated_at... ^

[SQL: SELECT count(*) as cnt FROM app.auto_run_sessions WHERE status = 'expired' AND updated_at > NOW() - INTERVAL '5 minutes'] (Background on this error at: https://sqlalche.me/e/20/f405)


auto_run_results,

"id"	"session_id"	"vehicle_id"	"program_id"	"program_type"	"status"	"result_value"	"result_data"	"manual_input"	"error_message"	"created_at"	"updated_at"	"user_id"	"log_as_vin"	"program_name"	"passed"	"source"
303	"ar_1771568622_3e513933"	1	"AUTO_VIN_READ"	"single"	"success"	"None"	"{""raw"": null, ""vin"": null, ""message"": ""Timeout waiting for VIN response""}"	false		"2026-02-20 11:53:45.707382"	"2026-02-20 11:53:45.707382"	1	true	"VIN Read"	true	"section"
304	"ar_1771568622_3e513933"	1	"AUTO_ECU_ACTIVE_CHECK"	"single"	"failed"	"inactive"	"{""raw"": {""request"": {""dlc"": 8, ""data"": [""02"", ""3E"", ""80"", ""00"", ""00"", ""00"", ""00"", ""00""], ""timestamp"": 0.0, ""arbitration_id"": ""7F0"", ""is_extended_id"": false}, ""response"": null}, ""message"": ""ECU not responding (timeout)"", ""ecu_code"": ""BMS"", ""is_active"": false, ""last_response"": null}"	false	"LIMIT_VIOLATION"	"2026-02-20 11:53:47.732208"	"2026-02-20 11:53:47.732208"	1	false	"ECU Active Check"	false	"section"

auto_run_sessions,

"id"	"session_id"	"vehicle_id"	"user_id"	"vehicle_name"	"section_type"	"vin"	"vin_source"	"status"	"programs_config"	"started_at"	"ended_at"	"vin_input_needed"
410	"ar_1771568622_3e513933"	1	1	"TVS iQube ST"	"diagnostics"	"MD629120000000000"	"manual"	"running"	"[{""log_as_vin"": true, ""program_id"": ""AUTO_VIN_READ"", ""sort_order"": 1, ""ecu_targets"": [""BMS""], ""is_required"": true, ""module_name"": ""vin_read"", ""timeout_sec"": 15, ""display_type"": ""text"", ""display_unit"": null, ""program_name"": ""VIN Read"", ""program_type"": ""single"", ""display_label"": ""VIN"", ""display_pages"": [""section"", ""ecu"", ""parameter""], ""function_name"": ""read_vin"", ""output_limits"": [], ""execution_mode"": ""single"", ""fallback_input"": {""label"": ""Enter VIN"", ""length"": 17, ""input_type"": ""string"", ""format_hint"": ""17-character VIN (no I, O, Q)"", ""is_required"": true}, ""fallback_action"": ""manual_input""}, {""log_as_vin"": false, ""program_id"": ""AUTO_BATTERY_VOLTAGE"", ""sort_order"": 2, ""ecu_targets"": [""BMS""], ""is_required"": true, ""module_name"": ""battery_voltage"", ""timeout_sec"": 0, ""display_type"": ""value"", ""display_unit"": ""V"", ""program_name"": ""Battery Voltage"", ""program_type"": ""stream"", ""display_label"": ""Battery Voltage"", ""display_pages"": [""section"", ""ecu"", ""parameter""], ""function_name"": ""read_battery_voltage_stream"", ""output_limits"": [{""lsl"": 10.0, ""usl"": 13.6, ""unit"": ""V"", ""signal"": ""battery_voltage""}], ""execution_mode"": ""stream"", ""fallback_input"": null, ""fallback_action"": ""block""}, {""source"": ""ecu"", ""log_as_vin"": false, ""program_id"": ""AUTO_ECU_ACTIVE_CHECK"", ""sort_order"": 1, ""ecu_targets"": [""BMS""], ""is_required"": true, ""module_name"": ""ecu_active_check"", ""timeout_sec"": 10, ""display_type"": ""status"", ""display_unit"": null, ""program_name"": ""ECU Active Check"", ""program_type"": ""single"", ""display_label"": ""ECU Status"", ""display_pages"": [""ecu""], ""function_name"": ""check_ecu_active"", ""output_limits"": [{""lsl"": 1, ""usl"": 1, ""unit"": null, ""signal"": ""is_active""}], ""execution_mode"": ""single"", ""fallback_input"": null, ""fallback_action"": ""warn_and_continue""}]"	"2026-02-20 11:53:42.664113"		true


ecu_active_status,

"id"	"session_id"	"vehicle_id"	"ecu_code"	"is_active"	"last_response"	"error_count"	"updated_at"
97	"ar_1771568622_3e513933"	1	"BMS"	false		1	"2026-02-20 11:53:47.740259"

auto_run_stream_values,



Only table column names are showing; other than that, nothing is visible when we run the program

Basically, auto_run_results ->shows all the auto-run program results

auto_run_sessions ->shows the current VIN and current streaming value

ecu_active_status -> shows the ECU activeness

auto_run_stream_values -> shows the streaming data values 


The current session VIN and the Streaming value of battery voltage should be displayed in the above horizontal grid, where we have the vehicle image, description, VIN_pattern, and these auto-run values should be shown below these. And the ECU active Status (green/red dot) should be shown in the respective ECU horizontal grid.

On the test sequence page for all parameters, it shows the live streaming data, but it shouldn't. 

For each user, the user should log in to open the dashboard page, and based on that, the auto-run programs should run only once per user, meaning that for one user's login, our auto-run program should run.

And when I run the test sequence program, it is giving,
[2026-02-20 12:56:34.867][INFO] Task started: test_id=TVS_iQube_ST_BMS_LP_Photosensor_STREAM, mode=stream
[2026-02-20 12:56:34.867][INFO] Attempt 1/4 test=TVS_iQube_ST_BMS_LP_Photosensor_STREAM mode=stream generator=False
[2026-02-20 12:56:34.873][INFO] Executing Read_Photosensor mode=stream
[2026-02-20 12:56:34.878][INFO] [PROGRESS 5%] Opening CAN bus
[2026-02-20 12:56:34.878][INFO] [PROGRESS 5%] Opening CAN bus
[2026-02-20 12:56:35.019][ERROR] Exception:
Traceback (most recent call last):
  File "D:\Python\PostgreSQL_Nirix_Diagnostics_Web_Application\diagnostics\runner.py", line 749, in _execute_function
    result["output"] = fn(*args, **call_kwargs)
                       ^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Python\PostgreSQL_Nirix_Diagnostics_Web_Application\Test_Programs\TVS_iQube_ST\Diagnostics\BMS\LIVE_PARAMETER\Read_Photosensor.py", line 76, in Read_Photosensor
    bus = open_can_bus(channel=can_interface, bitrate=int(bitrate))
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Python\PostgreSQL_Nirix_Diagnostics_Web_Application\diagnostics\can_utils.py", line 140, in open_can_bus
    return interface.Bus(
           ^^^^^^^^^^^^^^
  File "C:\Users\sri.sakthivel\AppData\Roaming\Python\Python312\site-packages\can\util.py", line 392, in wrapper
    return f(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^
  File "C:\Users\sri.sakthivel\AppData\Roaming\Python\Python312\site-packages\can\interface.py", line 137, in Bus
    bus = cls(channel, **kwargs)
          ^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\sri.sakthivel\AppData\Roaming\Python\Python312\site-packages\can\interfaces\pcan\pcan.py", line 311, in __init__
    raise PcanCanInitializationError(self._get_formatted_error(result))
can.interfaces.pcan.pcan.PcanCanInitializationError: A PCAN Channel has not been initialized yet or the initialization process has failed
[2026-02-20 12:56:35.019][ERROR] Exception: Traceback (most recent call last):
  File "D:\Python\PostgreSQL_Nirix_Diagnostics_Web_Application\diagnostics\runner.py", line 749, in _execute_function
    result["output"] = fn(*args, **call_kwargs)
[2026-02-20 12:56:35.019][INFO] Task completed: passed=False, duration=155ms, status=ERROR
