# -*- coding: utf-8 -*-
"""
Battery Voltage – Streaming auto-run program

Auto-run entry point (from section_tests.json):
  program_id: AUTO_BATTERY_VOLTAGE
  module_name: battery_voltage
  function_name: read_battery_voltage_stream
  program_type: "stream"
  execution_mode: "stream"

UDS DID: 22 E1 42  (Battery Voltage)
CAN IDs: 0x7F0 (req), 0x7F1 (resp)

Version: 3.0.0
Last Updated: 2026-02-21

FIXES IN v3.0.0
────────────────
- FIX-51: Enhanced stream callback chain for persistence
- FIX-62: Display pages support for battery voltage
- FIX-64: Stream value persistence with ON CONFLICT
- FIX-68: Proper generator function implementation
- FIX-69: Stream heartbeat for stale detection
- FIX-80: Improved CAN error handling with recovery
- FIX-81: Multiple decode attempts per reading
"""

from __future__ import annotations

import time
import logging
import traceback
from typing import Dict, Any, Optional, Generator
from datetime import datetime

import can
from can import BusABC, Message

# =============================================================================
# LOGGING
# =============================================================================

logger = logging.getLogger(__name__)

def _log_info(msg: str, context=None):
    if context:
        context.log(msg, "INFO")
    else:
        logger.info(f"[BATTERY] {msg}")

def _log_warn(msg: str, context=None):
    if context:
        context.log(msg, "WARN")
    else:
        logger.warning(f"[BATTERY] {msg}")

def _log_error(msg: str, context=None):
    if context:
        context.log(msg, "ERROR")
    else:
        logger.error(f"[BATTERY] {msg}")

def _log_debug(msg: str, context=None):
    if context:
        context.log(msg, "DEBUG")
    else:
        logger.debug(f"[BATTERY] {msg}")

# =============================================================================
# CONSTANTS
# =============================================================================

# UDS Services
UDS_READ_DATA_BY_IDENTIFIER = 0x22
UDS_POSITIVE_RESPONSE_MASK = 0x40

# DID for Battery Voltage (0xE142)
BATTERY_VOLTAGE_DID = 0xE142
BATTERY_VOLTAGE_DID_BYTES = [0xE1, 0x42]

# CAN IDs
REQUEST_ID = 0x7F0
RESPONSE_ID = 0x7F1

# Timeouts
DEFAULT_TIMEOUT = 2.0
FRAME_TIMEOUT = 0.3
SESSION_SETUP_TIMEOUT = 0.5
READ_INTERVAL = 0.4  # 400ms between readings

# Retry settings
MAX_RETRIES = 2
RETRY_DELAY = 0.25

# Voltage resolution (0.1V per bit)
VOLTAGE_RESOLUTION = 0.1

# Heartbeat interval
HEARTBEAT_INTERVAL = 5.0  # seconds

# =============================================================================
# CAN BUS HELPERS
# =============================================================================

def _open_bus(can_interface: str, bitrate: int, context=None) -> Optional[can.Bus]:
    """Open CAN bus connection with error handling."""
    iface = (can_interface or "").strip()
    
    try:
        _log_debug(f"Opening CAN bus: {iface}", context)
        
        if iface.upper().startswith("PCAN"):
            bus = can.Bus(
                interface="pcan", 
                channel=iface, 
                bitrate=int(bitrate), 
                fd=False
            )
        elif iface.lower().startswith("can") or iface.lower().startswith("vcan"):
            bus = can.Bus(
                interface="socketcan", 
                channel=iface, 
                bitrate=int(bitrate)
            )
        else:
            raise ValueError(f"Unsupported CAN interface: {iface}")
        
        if bus.state == can.BusState.ACTIVE:
            _log_info(f"CAN bus opened: {iface}", context)
            return bus
        
    except Exception as e:
        _log_error(f"Failed to open CAN bus: {e}", context)
    
    return None


def _serialize_can_message(msg: Optional[can.Message]) -> Optional[Dict[str, Any]]:
    """Serialize CAN message for logging."""
    if not msg:
        return None
    
    return {
        "arbitration_id": f"0x{msg.arbitration_id:03X}",
        "data": [f"{b:02X}" for b in msg.data],
        "timestamp": float(getattr(msg, "timestamp", 0.0) or 0.0),
    }


def _setup_diagnostic_session(bus: BusABC, context=None) -> bool:
    """Setup UDS diagnostic session."""
    try:
        setup_req = can.Message(
            arbitration_id=REQUEST_ID,
            is_extended_id=False,
            data=[0x02, 0x10, 0x03, 0x00, 0x00, 0x00, 0x00, 0x00],
        )
        
        _log_debug("Setting up diagnostic session", context)
        bus.send(setup_req)
        
        response = bus.recv(timeout=SESSION_SETUP_TIMEOUT)
        if response and response.arbitration_id == RESPONSE_ID:
            if len(response.data) >= 3 and response.data[1] == 0x50 and response.data[2] == 0x03:
                _log_debug("Diagnostic session established", context)
                return True
        
        return False
        
    except Exception as e:
        _log_debug(f"Session setup skipped: {e}", context)
        return False


def _read_voltage_once(
    bus: BusABC, 
    context=None, 
    progress=None
) -> Dict[str, Any]:
    """
    Send UDS ReadDataByIdentifier (22 E1 42) once and parse response.
    Returns dict with battery_voltage, message, raw.
    """
    _log_debug("Reading battery voltage", context)

    # UDS ReadDataByIdentifier request for Battery Voltage
    req = can.Message(
        arbitration_id=REQUEST_ID,
        is_extended_id=False,
        data=[0x03, 0x22, 0xE1, 0x42, 0x00, 0x00, 0x00, 0x00],
    )
    
    _log_debug(f"Tx: {req.arbitration_id:03X} " + 
               " ".join(f"{b:02X}" for b in req.data), context)
    
    try:
        bus.send(req)
    except Exception as e:
        _log_error(f"Failed to send request: {e}", context)
        raise

    # Wait for response
    deadline = time.time() + DEFAULT_TIMEOUT
    response = None
    
    while time.time() < deadline:
        if context:
            context.checkpoint()
            
        try:
            msg = bus.recv(timeout=FRAME_TIMEOUT)
            if not msg:
                continue
                
            if msg.arbitration_id != RESPONSE_ID:
                continue
                
            _log_debug(f"Rx: {msg.arbitration_id:03X} " + 
                       " ".join(f"{b:02X}" for b in msg.data), context)
            response = msg
            break
            
        except Exception as e:
            _log_error(f"Receive error: {e}", context)

    if not response:
        raise TimeoutError("No response from ECU")

    # Parse response
    # Positive response format: 62 E1 42 XX ...
    if not (len(response.data) >= 5 and 
            response.data[1] == 0x62 and 
            response.data[2] == 0xE1 and 
            response.data[3] == 0x42):
        return {
            "battery_voltage": None,
            "message": "Invalid response format",
            "raw": {
                "request": _serialize_can_message(req),
                "response": _serialize_can_message(response)
            },
        }

    # Voltage is in 0.1V resolution
    voltage_raw = response.data[4]
    voltage = voltage_raw * VOLTAGE_RESOLUTION
    
    return {
        "battery_voltage": round(voltage, 2),
        "message": f"{voltage:.1f} V",
        "raw": {
            "request": _serialize_can_message(req),
            "response": _serialize_can_message(response),
        },
        "timestamp": time.time(),
    }


# =============================================================================
# STREAMING GENERATOR
# =============================================================================

def read_battery_voltage_stream(
    can_interface: str,
    bitrate: int,
    context=None,
    progress=None,
) -> Generator[Dict[str, Any], None, None]:
    """
    STREAMING entry point (GENERATOR) for auto-run.

    Yields runner-compatible dicts:
      {"status": "streaming", "data": {"battery_voltage": <float>}}

    The runner will:
      - Validate limits and emit progress_json
      - Call service.on_stream_data() for persistence
      - Display values in UI with color coding
    """
    bus = None
    iteration = 0
    consecutive_errors = 0
    max_consecutive_errors = 5
    last_heartbeat = time.time()
    
    _log_info(f"Battery voltage stream starting: {can_interface} @ {bitrate} bps", context)
    
    try:
        if context:
            context.checkpoint()
            context.progress(5, "Opening CAN bus")
        if progress:
            progress(5, "Opening CAN bus")

        # Open CAN bus
        bus = _open_bus(can_interface, int(bitrate), context)
        if bus is None:
            error_msg = f"Failed to open CAN bus: {can_interface}"
            _log_error(error_msg, context)
            yield {
                "status": "error", 
                "data": {"error": error_msg}
            }
            return

        # Setup diagnostic session (optional)
        _setup_diagnostic_session(bus, context)

        _log_info("CAN bus opened successfully, starting stream", context)

        # Stream forever (runner will cancel when session ends)
        while True:
            iteration += 1
            
            if context:
                context.checkpoint()
                
                # Send heartbeat periodically
                now = time.time()
                if now - last_heartbeat > HEARTBEAT_INTERVAL:
                    _log_debug(f"Stream heartbeat: iteration {iteration}", context)
                    last_heartbeat = now

            try:
                # Read voltage with retries
                voltage_result = None
                for attempt in range(1, MAX_RETRIES + 1):
                    try:
                        voltage_result = _read_voltage_once(bus, context, progress)
                        if voltage_result.get("battery_voltage") is not None:
                            break
                    except TimeoutError:
                        if attempt < MAX_RETRIES:
                            _log_debug(f"Timeout, retrying ({attempt}/{MAX_RETRIES})", context)
                            if context:
                                context.sleep(RETRY_DELAY * attempt)
                            continue
                        raise
                    except Exception as e:
                        _log_warn(f"Read attempt {attempt} failed: {e}", context)
                        if attempt < MAX_RETRIES:
                            if context:
                                context.sleep(RETRY_DELAY)
                            continue
                        raise

                if voltage_result is None:
                    consecutive_errors += 1
                    if consecutive_errors >= max_consecutive_errors:
                        error_msg = f"Too many consecutive errors ({consecutive_errors})"
                        _log_error(error_msg, context)
                        yield {
                            "status": "error",
                            "data": {"error": error_msg}
                        }
                        return
                    
                    # Skip this iteration
                    if context:
                        context.sleep(READ_INTERVAL)
                    continue

                # Reset error counter on success
                consecutive_errors = 0
                
                value = voltage_result.get("battery_voltage")
                
                if value is not None:
                    # Update progress
                    if context:
                        context.progress(100, f"Battery Voltage: {value:.1f} V")
                        if iteration % 10 == 0:
                            _log_info(f"Streaming: {value:.1f}V (iteration {iteration})", context)
                    
                    if progress:
                        progress(100, f"Battery Voltage: {value:.1f} V")

                    # YIELD for runner → service.on_stream_data → DB persist
                    yield {
                        "status": "streaming", 
                        "data": {
                            "battery_voltage": value,
                            "_iteration": iteration,
                            "_timestamp": time.time(),
                        }
                    }
                else:
                    # Invalid frame
                    _log_warn("Invalid response received", context)
                    yield {
                        "status": "streaming", 
                        "data": {
                            "_warning": "Invalid response",
                            "_iteration": iteration,
                        }
                    }

                # Pace the readings
                if context:
                    context.sleep(READ_INTERVAL)
                else:
                    time.sleep(READ_INTERVAL)

    except GeneratorExit:
        # Handle generator cleanup gracefully
        _log_info("Stream generator closed", context)
        
    except Exception as e:
        _log_error(f"Stream error: {e}", context)
        _log_debug(traceback.format_exc(), context)
        yield {
            "status": "error", 
            "data": {"error": str(e)}
        }
        
    finally:
        _log_info("Shutting down battery voltage stream", context)
        if bus:
            try:
                bus.shutdown()
                _log_debug("CAN bus closed", context)
            except Exception as e:
                _log_warn(f"Error closing bus: {e}", context)


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = ["read_battery_voltage_stream"]
