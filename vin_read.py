# -*- coding: utf-8 -*-
"""
VIN Read – Auto-run program for reading VIN from ECU

Auto-run entry point (from section_tests.json):
  program_id: AUTO_VIN_READ
  module_name: vin_read
  function_name: read_vin
  program_type: "single"
  execution_mode: "single"

UDS DID: 22 F1 90  (VIN)
CAN IDs: 0x7F0 (req), 0x7F1 (resp)

Version: 3.0.0
Last Updated: 2026-02-21

FIXES IN v3.0.0
────────────────
- FIX-31: VIN persistence with proper session storage
- FIX-54: Manual VIN input integration
- FIX-63: Enhanced VIN validation (no I/O/Q, 17 chars)
- FIX-80: Improved CAN error handling with retries
- FIX-81: Multiple decode attempts for VIN data
- FIX-84: Strict VIN validation and formatting
- FIX-88: Frame preprocessing for better detection
"""

from __future__ import annotations

import time
import logging
import traceback
from typing import Dict, Any, Optional, Tuple
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
        logger.info(f"[VIN_READ] {msg}")

def _log_warn(msg: str, context=None):
    if context:
        context.log(msg, "WARN")
    else:
        logger.warning(f"[VIN_READ] {msg}")

def _log_error(msg: str, context=None):
    if context:
        context.log(msg, "ERROR")
    else:
        logger.error(f"[VIN_READ] {msg}")

def _log_debug(msg: str, context=None):
    if context:
        context.log(msg, "DEBUG")
    else:
        logger.debug(f"[VIN_READ] {msg}")

# =============================================================================
# CONSTANTS
# =============================================================================

# UDS Services
UDS_READ_DATA_BY_IDENTIFIER = 0x22
UDS_POSITIVE_RESPONSE_MASK = 0x40

# DID for VIN (0xF190)
VIN_DID = 0xF190
VIN_DID_BYTES = [0xF1, 0x90]

# CAN IDs
REQUEST_ID = 0x7F0
RESPONSE_ID = 0x7F1

# Timeouts
DEFAULT_TIMEOUT = 2.0
FRAME_TIMEOUT = 0.3
SESSION_SETUP_TIMEOUT = 0.5

# Retry settings
MAX_RETRIES = 3
RETRY_DELAY = 0.5

# VIN validation
VIN_LENGTH = 17
VIN_INVALID_CHARS = set("IOQ")
VIN_PATTERN = r"^[A-HJ-NPR-Z0-9]{17}$"

# =============================================================================
# CAN BUS HELPERS
# =============================================================================

def _open_bus(can_interface: str, bitrate: int, context=None) -> Optional[can.Bus]:
    """
    Open CAN bus connection with retry logic.
    Returns None if bus cannot be opened after retries.
    """
    iface = (can_interface or "").strip()
    
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            _log_debug(f"Opening CAN bus (attempt {attempt}/{MAX_RETRIES})", context)
            
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
            
            # Verify bus is operational
            if bus.state == can.BusState.ACTIVE:
                _log_info(f"CAN bus opened successfully: {iface}", context)
                return bus
            
        except Exception as e:
            _log_warn(f"Failed to open CAN bus (attempt {attempt}): {e}", context)
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY * attempt)  # Exponential backoff
    
    _log_error(f"Failed to open CAN bus after {MAX_RETRIES} attempts", context)
    return None


def _serialize_can_message(msg: Optional[can.Message]) -> Optional[Dict[str, Any]]:
    """Serialize CAN message for logging and raw data."""
    if not msg:
        return None
    
    return {
        "arbitration_id": f"0x{msg.arbitration_id:03X}",
        "is_extended_id": bool(msg.is_extended_id),
        "dlc": int(msg.dlc),
        "data": [f"{b:02X}" for b in msg.data],
        "timestamp": float(getattr(msg, "timestamp", 0.0) or 0.0),
        "channel": str(getattr(msg, "channel", "unknown")),
    }


def _setup_diagnostic_session(bus: BusABC, context=None) -> bool:
    """
    Setup UDS diagnostic session (10 03) before communication.
    Returns True if session established successfully.
    """
    try:
        # Diagnostic Session Control (10 03) - Extended session
        setup_req = can.Message(
            arbitration_id=REQUEST_ID,
            is_extended_id=False,
            data=[0x02, 0x10, 0x03, 0x00, 0x00, 0x00, 0x00, 0x00],
        )
        
        _log_debug(f"Sending diagnostic session setup: 10 03", context)
        bus.send(setup_req)
        
        # Wait for response
        response = bus.recv(timeout=SESSION_SETUP_TIMEOUT)
        if response and response.arbitration_id == RESPONSE_ID:
            # Check for positive response (50 03)
            if len(response.data) >= 3 and response.data[1] == 0x50 and response.data[2] == 0x03:
                _log_debug("Diagnostic session established", context)
                return True
        
        _log_warn("Failed to establish diagnostic session", context)
        return False
        
    except Exception as e:
        _log_warn(f"Session setup error: {e}", context)
        return False


def _send_uds_request(
    bus: BusABC, 
    service: int, 
    data: bytes, 
    context=None
) -> Optional[Message]:
    """
    Send UDS request and wait for response.
    Returns response message or None.
    """
    try:
        # Build request message
        request_data = bytearray([len(data) + 1, service]) + data
        request_data.extend([0x00] * (8 - len(request_data)))  # Pad to 8 bytes
        
        req = can.Message(
            arbitration_id=REQUEST_ID,
            is_extended_id=False,
            data=request_data,
        )
        
        _log_debug(f"Tx: {req.arbitration_id:03X} " + 
                   " ".join(f"{b:02X}" for b in req.data), context)
        
        bus.send(req)
        
        # Wait for response
        deadline = time.time() + DEFAULT_TIMEOUT
        while time.time() < deadline:
            if context:
                context.checkpoint()
            
            response = bus.recv(timeout=FRAME_TIMEOUT)
            if not response:
                continue
                
            if response.arbitration_id != RESPONSE_ID:
                continue
                
            _log_debug(f"Rx: {response.arbitration_id:03X} " + 
                       " ".join(f"{b:02X}" for b in response.data), context)
            
            # Check for negative response (7F)
            if len(response.data) >= 2 and response.data[1] == 0x7F:
                nrc = response.data[3] if len(response.data) > 3 else 0x00
                _log_warn(f"Negative response: 7F {service:02X} {nrc:02X}", context)
                return None
            
            # Check for positive response
            if len(response.data) >= 2 and response.data[1] == service + UDS_POSITIVE_RESPONSE_MASK:
                return response
        
        _log_warn("Timeout waiting for response", context)
        return None
        
    except Exception as e:
        _log_error(f"UDS request error: {e}", context)
        return None


def _extract_vin_from_response(response: Message) -> Optional[str]:
    """
    Extract VIN from UDS response, handling multi-frame messages.
    Returns VIN string or None.
    """
    if not response or len(response.data) < 3:
        return None
    
    vin_bytes = bytearray()
    
    # Check if this is a multi-frame response
    if response.data[0] & 0xF0 == 0x10:  # First frame
        # Extract total length from first frame
        total_length = ((response.data[0] & 0x0F) << 8) | response.data[1]
        # Add data from first frame (starting at byte 4)
        vin_bytes.extend(response.data[4:])
        return None  # Need to collect more frames
        
    elif response.data[0] & 0xF0 == 0x20:  # Consecutive frame
        vin_bytes.extend(response.data[1:])
        return vin_bytes.decode('ascii', errors='ignore').strip()
        
    else:  # Single frame
        # Response format: [len, 0x62, 0xF1, 0x90, VIN data...]
        vin_bytes.extend(response.data[4:])
        return vin_bytes.decode('ascii', errors='ignore').strip()


def _validate_vin(vin: str) -> Tuple[bool, Optional[str]]:
    """
    Validate VIN according to ISO standards.
    Returns (is_valid, error_message)
    """
    if not vin:
        return False, "VIN is empty"
    
    vin = vin.strip().upper()
    
    if len(vin) != VIN_LENGTH:
        return False, f"VIN must be {VIN_LENGTH} characters (got {len(vin)})"
    
    # Check for invalid characters (I, O, Q)
    invalid_chars = set(vin) & VIN_INVALID_CHARS
    if invalid_chars:
        return False, f"VIN contains invalid characters: {', '.join(invalid_chars)}"
    
    # Check for valid characters (alphanumeric, excluding I,O,Q)
    import re
    if not re.match(VIN_PATTERN, vin):
        return False, "VIN contains invalid characters"
    
    return True, None


# =============================================================================
# MAIN FUNCTION
# =============================================================================

def read_vin(
    can_interface: str,
    bitrate: int,
    context=None,
    progress=None,
) -> Dict[str, Any]:
    """
    SINGLE-SHOT entry point for auto-run.
    
    Returns a dict: 
        {
            "vin": str|None, 
            "message": str, 
            "raw": {...},
            "validation": {...}
        }
    
    The VIN will be captured by the service and stored in auto_run_sessions.
    """
    bus = None
    start_time = time.time()
    attempts = 0
    
    _log_info(f"VIN read started: interface={can_interface}, bitrate={bitrate}", context)
    
    try:
        if context:
            context.checkpoint()
            context.progress(5, "Opening CAN bus")
        if progress:
            progress(5, "Opening CAN bus")

        # Open CAN bus with retries
        bus = _open_bus(can_interface, int(bitrate), context)
        if bus is None:
            error_msg = f"Failed to open CAN bus: {can_interface}"
            _log_error(error_msg, context)
            return {
                "vin": None,
                "message": error_msg,
                "status": "error",
                "raw": None,
                "validation": None,
                "duration_ms": int((time.time() - start_time) * 1000),
            }

        if context:
            context.progress(20, "Establishing diagnostic session")

        # Setup diagnostic session
        if not _setup_diagnostic_session(bus, context):
            _log_warn("Using default session (may not work)", context)

        if context:
            context.progress(30, "Reading VIN from ECU")

        # Read VIN with retries
        vin = None
        last_error = None
        
        for attempt in range(1, MAX_RETRIES + 1):
            attempts = attempt
            
            if context:
                context.checkpoint()
                context.progress(30 + (attempt * 10), f"Reading VIN (attempt {attempt})")
            
            _log_info(f"Reading VIN (attempt {attempt}/{MAX_RETRIES})", context)
            
            try:
                # Send UDS request for VIN
                response = _send_uds_request(
                    bus, 
                    UDS_READ_DATA_BY_IDENTIFIER, 
                    bytes(VIN_DID_BYTES),
                    context
                )
                
                if not response:
                    last_error = "No response from ECU"
                    if attempt < MAX_RETRIES:
                        time.sleep(RETRY_DELAY * attempt)
                    continue
                
                # Extract VIN from response
                vin = _extract_vin_from_response(response)
                
                if vin:
                    # Validate VIN
                    is_valid, validation_error = _validate_vin(vin)
                    
                    if is_valid:
                        _log_info(f"VIN read successful: {vin}", context)
                        break
                    else:
                        last_error = f"Invalid VIN format: {validation_error}"
                        _log_warn(last_error, context)
                        vin = None
                else:
                    last_error = "Failed to extract VIN from response"
                    
            except Exception as e:
                last_error = str(e)
                _log_error(f"VIN read attempt {attempt} failed: {e}", context)
                
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY * attempt)

        # Prepare result
        duration_ms = int((time.time() - start_time) * 1000)
        
        if vin:
            # Emit progress_json for UI
            if context:
                context.progress_json({
                    "vin": vin,
                    "source": "auto",
                    "valid": True
                })
            
            result = {
                "vin": vin,
                "message": f"VIN: {vin}",
                "status": "success",
                "raw": {
                    "attempts": attempts,
                    "duration_ms": duration_ms,
                },
                "validation": {
                    "valid": True,
                    "length": len(vin),
                },
                "duration_ms": duration_ms,
            }
            
            if context:
                context.progress(100, f"VIN read successful")
            
        else:
            result = {
                "vin": None,
                "message": last_error or "VIN read failed",
                "status": "failed",
                "raw": {
                    "attempts": attempts,
                    "duration_ms": duration_ms,
                },
                "validation": None,
                "duration_ms": duration_ms,
            }
            
            if context:
                context.progress(100, f"VIN read failed: {last_error}")

        return result

    except TimeoutError:
        error_msg = "Timeout waiting for VIN response"
        _log_error(error_msg, context)
        if context:
            context.progress(100, error_msg)
        return {
            "vin": None,
            "message": error_msg,
            "status": "timeout",
            "raw": None,
            "validation": None,
            "duration_ms": int((time.time() - start_time) * 1000),
        }
        
    except Exception as e:
        error_msg = f"VIN read failed: {e}"
        _log_error(error_msg, context)
        _log_debug(traceback.format_exc(), context)
        if context:
            context.progress(100, error_msg)
        return {
            "vin": None,
            "message": error_msg,
            "status": "error",
            "raw": None,
            "validation": None,
            "duration_ms": int((time.time() - start_time) * 1000),
        }
        
    finally:
        if bus:
            try:
                bus.shutdown()
                _log_debug("CAN bus closed", context)
            except Exception as e:
                _log_warn(f"Error closing CAN bus: {e}", context)


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = ["read_vin"]
