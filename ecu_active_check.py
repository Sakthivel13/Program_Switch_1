# -*- coding: utf-8 -*-
"""
ECU Active Check – Runs when ECU page loads

Auto-run entry point (from ecu_tests.json):
  program_id: AUTO_ECU_ACTIVE_CHECK
  module_name: ecu_active_check
  function_name: check_ecu_active
  program_type: "single"
  execution_mode: "single"

Checks if ECU is responding by sending tester present (3E 80)
Returns status for multiple ECUs with individual results

Version: 3.0.0
Last Updated: 2026-02-21

FIXES IN v3.0.0
────────────────
- FIX-52: ECU status persistence for colored dots in UI
- FIX-61: Enhanced ECU status extraction for multiple ECUs
- FIX-65: Multiple ECU status tracking
- FIX-80: Improved CAN error handling
- FIX-84: Proper status validation and formatting
- FIX-85: Support for multiple ECU targets
"""

from __future__ import annotations

import time
import logging
import traceback
from typing import Dict, Any, Optional, List, Union
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
        logger.info(f"[ECU_CHECK] {msg}")

def _log_warn(msg: str, context=None):
    if context:
        context.log(msg, "WARN")
    else:
        logger.warning(f"[ECU_CHECK] {msg}")

def _log_error(msg: str, context=None):
    if context:
        context.log(msg, "ERROR")
    else:
        logger.error(f"[ECU_CHECK] {msg}")

def _log_debug(msg: str, context=None):
    if context:
        context.log(msg, "DEBUG")
    else:
        logger.debug(f"[ECU_CHECK] {msg}")

# =============================================================================
# CONSTANTS
# =============================================================================

# UDS Services
UDS_TESTER_PRESENT = 0x3E
UDS_POSITIVE_RESPONSE_MASK = 0x40

# CAN IDs
REQUEST_ID = 0x7F0
RESPONSE_ID = 0x7F1

# Timeouts
DEFAULT_TIMEOUT = 1.0  # Quick check for active status
FRAME_TIMEOUT = 0.2
SESSION_SETUP_TIMEOUT = 0.3

# Retry settings
MAX_RETRIES = 2
RETRY_DELAY = 0.1

# ECU status constants
STATUS_ACTIVE = "active"
STATUS_INACTIVE = "inactive"
STATUS_UNKNOWN = "unknown"

# =============================================================================
# CAN BUS HELPERS
# =============================================================================

def _open_bus(can_interface: str, bitrate: int, context=None) -> Optional[can.Bus]:
    """Open CAN bus connection."""
    iface = (can_interface or "").strip()
    
    try:
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
    """Quick diagnostic session setup (optional for tester present)."""
    try:
        setup_req = can.Message(
            arbitration_id=REQUEST_ID,
            is_extended_id=False,
            data=[0x02, 0x10, 0x03, 0x00, 0x00, 0x00, 0x00, 0x00],
        )
        
        bus.send(setup_req)
        response = bus.recv(timeout=SESSION_SETUP_TIMEOUT)
        
        if response and response.arbitration_id == RESPONSE_ID:
            return True
        
    except Exception:
        pass
    
    return False


def _check_single_ecu(
    bus: BusABC,
    ecu_code: str,
    context=None
) -> Dict[str, Any]:
    """
    Check a single ECU's active status.
    Returns status dict for the ECU.
    """
    start_time = time.time()
    attempts = 0
    
    for attempt in range(1, MAX_RETRIES + 1):
        attempts = attempt
        
        try:
            # Send tester present (3E 80)
            req = can.Message(
                arbitration_id=REQUEST_ID,
                is_extended_id=False,
                data=[0x02, 0x3E, 0x80, 0x00, 0x00, 0x00, 0x00, 0x00],
            )
            
            _log_debug(f"Tx: {req.arbitration_id:03X} " + 
                       " ".join(f"{b:02X}" for b in req.data), context)
            
            bus.send(req)
            
            # Wait for response
            deadline = time.time() + DEFAULT_TIMEOUT
            response = None
            
            while time.time() < deadline:
                if context:
                    context.checkpoint()
                
                msg = bus.recv(timeout=FRAME_TIMEOUT)
                if not msg:
                    continue
                    
                if msg.arbitration_id != RESPONSE_ID:
                    continue
                    
                _log_debug(f"Rx: {msg.arbitration_id:03X} " + 
                           " ".join(f"{b:02X}" for b in msg.data), context)
                response = msg
                break
            
            response_time = time.time()
            
            if response:
                # Check for positive response (7E 80)
                if len(response.data) >= 3 and response.data[1] == 0x7E and response.data[2] == 0x80:
                    _log_info(f"ECU {ecu_code} is active", context)
                    
                    return {
                        "ecu_code": ecu_code,
                        "is_active": True,
                        "status": STATUS_ACTIVE,
                        "response_time_ms": int((response_time - start_time) * 1000),
                        "attempts": attempts,
                        "last_response": datetime.fromtimestamp(response_time).isoformat(),
                        "raw": {
                            "request": _serialize_can_message(req),
                            "response": _serialize_can_message(response),
                        }
                    }
                else:
                    # Unexpected response format
                    _log_warn(f"ECU {ecu_code} returned unexpected response", context)
            
            # No response or invalid response
            if attempt < MAX_RETRIES:
                _log_debug(f"Retrying ECU {ecu_code} ({attempt}/{MAX_RETRIES})", context)
                if context:
                    context.sleep(RETRY_DELAY * attempt)
                continue
                
        except Exception as e:
            _log_warn(f"Error checking ECU {ecu_code}: {e}", context)
            if attempt < MAX_RETRIES:
                if context:
                    context.sleep(RETRY_DELAY)
                continue
    
    # No response after all retries
    _log_info(f"ECU {ecu_code} is inactive (no response)", context)
    
    return {
        "ecu_code": ecu_code,
        "is_active": False,
        "status": STATUS_INACTIVE,
        "response_time_ms": int((time.time() - start_time) * 1000),
        "attempts": attempts,
        "last_response": None,
        "error": "No response from ECU",
        "raw": {
            "request": _serialize_can_message(req) if 'req' in locals() else None,
            "response": None,
        }
    }


# =============================================================================
# MAIN FUNCTION
# =============================================================================

def check_ecu_active(
    can_interface: str,
    bitrate: int,
    context=None,
    progress=None,
    ecu_targets: Optional[List[str]] = None,
) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
    """
    Check if ECU(s) are active by sending tester present request.
    
    Args:
        can_interface: CAN interface name
        bitrate: CAN bitrate
        context: Task context for cooperative control
        progress: Progress callback
        ecu_targets: List of ECU codes to check (if None, checks default)
    
    Returns:
        Single ECU result dict or list of ECU status dicts:
        {
            "ecu_code": "BMS",
            "is_active": bool,
            "status": "active"|"inactive"|"unknown",
            "response_time_ms": int,
            "attempts": int,
            "last_response": ISO timestamp or None,
            "error": Optional[str],
            "raw": {...}
        }
    """
    bus = None
    start_time = time.time()
    
    # Default ECU targets if none specified
    if ecu_targets is None:
        ecu_targets = ["BMS"]  # Default to BMS
    
    _log_info(f"ECU active check started for {len(ecu_targets)} ECUs", context)
    _log_debug(f"Targets: {', '.join(ecu_targets)}", context)
    
    try:
        if context:
            context.progress(10, f"Opening CAN bus for ECU check")
        
        # Open CAN bus
        bus = _open_bus(can_interface, bitrate, context)
        if bus is None:
            error_msg = f"Failed to open CAN bus: {can_interface}"
            _log_error(error_msg, context)
            
            # Return error for all targets
            results = []
            for ecu in ecu_targets:
                results.append({
                    "ecu_code": ecu,
                    "is_active": False,
                    "status": STATUS_UNKNOWN,
                    "response_time_ms": 0,
                    "attempts": 0,
                    "last_response": None,
                    "error": error_msg,
                    "raw": None
                })
            
            if len(results) == 1:
                return results[0]
            return results

        # Optional diagnostic session setup
        _setup_diagnostic_session(bus, context)

        if context:
            context.progress(30, f"Checking ECU status")

        # Check each ECU
        results = []
        for idx, ecu in enumerate(ecu_targets):
            if context:
                context.checkpoint()
                context.progress(
                    30 + (idx * 60 // len(ecu_targets)), 
                    f"Checking {ecu}"
                )
            
            _log_info(f"Checking ECU: {ecu}", context)
            
            result = _check_single_ecu(bus, ecu, context)
            results.append(result)
            
            # Emit progress_json for each result
            if context:
                context.progress_json({
                    "ecu_status": {
                        ecu: result["is_active"]
                    },
                    "_type": "ecu_status"
                })

        if context:
            context.progress(100, "ECU check complete")

        # Prepare summary
        active_count = sum(1 for r in results if r["is_active"])
        _log_info(f"ECU check complete: {active_count}/{len(results)} active", context)

        # Return single result or list
        if len(results) == 1:
            return results[0]
        return results

    except Exception as e:
        error_msg = f"ECU check failed: {e}"
        _log_error(error_msg, context)
        _log_debug(traceback.format_exc(), context)
        
        # Return error for all targets
        results = []
        for ecu in ecu_targets:
            results.append({
                "ecu_code": ecu,
                "is_active": False,
                "status": STATUS_UNKNOWN,
                "response_time_ms": int((time.time() - start_time) * 1000),
                "attempts": 0,
                "last_response": None,
                "error": str(e),
                "raw": None
            })
        
        if len(results) == 1:
            return results[0]
        return results
        
    finally:
        if bus:
            try:
                bus.shutdown()
                _log_debug("CAN bus closed", context)
            except Exception as e:
                _log_warn(f"Error closing bus: {e}", context)


# =============================================================================
# COMPATIBILITY WRAPPER (for single ECU calls)
# =============================================================================

def check_single_ecu_active(
    can_interface: str,
    bitrate: int,
    context=None,
    progress=None,
    ecu_code: str = "BMS",
) -> Dict[str, Any]:
    """
    Compatibility wrapper for single ECU check.
    """
    result = check_ecu_active(
        can_interface, 
        bitrate, 
        context, 
        progress, 
        ecu_targets=[ecu_code]
    )
    
    if isinstance(result, list):
        return result[0]
    return result


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "check_ecu_active",
    "check_single_ecu_active",
    "STATUS_ACTIVE",
    "STATUS_INACTIVE", 
    "STATUS_UNKNOWN",
]
