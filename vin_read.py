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

Version: 2.1.0
Last Updated: 2026-02-19

FIXES IN v2.1.0
────────────────
- FIX-140: Enhanced VIN extraction with multi-frame response support
- FIX-141: Added multiple output formats for reliable VIN capture
- FIX-142: Improved error handling and logging
- FIX-143: Added manual input flag support for UI
- FIX-144: Better timeout and retry handling
"""

from __future__ import annotations

import time
import logging
from typing import Dict, Any, Optional, Generator

import can

logging.getLogger("can").setLevel(logging.ERROR)


def _open_bus(can_interface: str, bitrate: int) -> Optional[can.Bus]:
    """
    Open CAN bus connection.
    Returns None if bus cannot be opened.
    """
    iface = (can_interface or "").strip()
    try:
        if iface.upper().startswith("PCAN"):
            return can.Bus(interface="pcan", channel=iface, bitrate=int(bitrate), fd=False)
        if iface.lower().startswith("can"):
            return can.Bus(interface="socketcan", channel=iface, bitrate=int(bitrate))
        raise ValueError(f"Unsupported CAN interface: {iface}")
    except Exception as e:
        print(f"[VIN_READ] Failed to open CAN bus: {e}")
        return None


def _serialize_can_message(msg: can.Message) -> Dict[str, Any]:
    """Serialize CAN message for logging."""
    return {
        "arbitration_id": f"{msg.arbitration_id:03X}",
        "is_extended_id": bool(msg.is_extended_id),
        "dlc": int(msg.dlc),
        "data": [f"{b:02X}" for b in msg.data],
        "timestamp": float(getattr(msg, "timestamp", 0.0) or 0.0),
    }


def _validate_vin(vin: str) -> bool:
    """
    Validate a VIN string.
    
    Rules:
    - Exactly 17 characters
    - No I, O, or Q characters
    - Alphanumeric only (A-Z, 0-9)
    """
    if not vin or len(vin) != 17:
        return False
    
    # Check for invalid characters
    if any(c in vin for c in "IOQ"):
        return False
    
    # Check for valid characters (A-Z, 0-9)
    return all(c.isalnum() for c in vin)


def _read_vin_once(bus: can.BusABC, *, context=None, progress=None) -> Dict[str, Any]:
    """
    Send UDS ReadDataByIdentifier (22 F1 90) once and parse response.
    
    Handles multi-frame responses (ISO-TP) for complete VIN.
    
    Returns dict with vin, message, raw.
    Raises TimeoutError on no response.
    """
    def log(msg: str, level: str = "INFO"):
        if context:
            context.log(msg, level)
        else:
            print(f"[{level}] {msg}")

    if context:
        context.checkpoint()
        context.progress(10, "Sending UDS request (22 F1 90)")
    if progress:
        progress(10, "Sending UDS request (22 F1 90)")

    # UDS ReadDataByIdentifier request for VIN (22 F1 90)
    req = can.Message(
        arbitration_id=0x7F0,
        is_extended_id=False,
        data=[0x03, 0x22, 0xF1, 0x90, 0x00, 0x00, 0x00, 0x00],
    )
    log(f"Tx {req.arbitration_id:03X} " + " ".join(f"{b:02X}" for b in req.data))
    
    try:
        bus.send(req)
    except Exception as e:
        log(f"Failed to send CAN message: {e}", "ERROR")
        raise

    if context:
        context.progress(35, "Waiting for ECU response")

    # Wait for response (VIN response can be multi-frame)
    deadline = time.time() + 3.0  # 3 second timeout for complete VIN
    responses = []
    vin_bytes = bytearray()
    expected_length = 0
    received_frames = 0
    total_frames = 1  # Default to single frame
    
    log("Waiting for VIN response (may be multi-frame)...")
    
    while time.time() < deadline:
        if context:
            context.checkpoint()

        try:
            msg = bus.recv(timeout=0.5)
        except Exception as e:
            log(f"Error receiving CAN message: {e}", "ERROR")
            continue
            
        if not msg:
            continue
        if msg.arbitration_id != 0x7F1:
            continue

        log(f"Rx {msg.arbitration_id:03X} " + " ".join(f"{b:02X}" for b in msg.data))
        responses.append(msg)
        
        # Check if this is a response to 22 F1 90
        if len(msg.data) >= 4 and msg.data[1] == 0x62 and msg.data[2] == 0xF1 and msg.data[3] == 0x90:
            # This is a positive response
            pcidata = msg.data[0]  # PCI (Protocol Control Information)
            
            if (pcidata & 0xF0) == 0x10:
                # First frame of multi-frame response
                expected_length = ((pcidata & 0x0F) << 8) | msg.data[1]
                total_frames = (expected_length + 6) // 7  # Calculate total frames needed
                log(f"Multi-frame response detected: total length={expected_length} bytes, frames={total_frames}")
                
                # Add data from first frame (starts at byte 2)
                # First frame data starts at byte 2 (after PCI bytes)
                data_start = 2
                vin_bytes.extend(msg.data[data_start:])
                received_frames = 1
                
                # Send flow control message to request remaining frames
                flow_control = can.Message(
                    arbitration_id=0x7F0,
                    is_extended_id=False,
                    data=[0x30, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00],  # Flow control (CTS)
                )
                bus.send(flow_control)
                log("Sent flow control (CTS) for remaining frames")
                
            elif (pcidata & 0xF0) == 0x20:
                # Consecutive frame
                frame_index = pcidata & 0x0F
                log(f"Consecutive frame {frame_index} received")
                
                # Add data from consecutive frame (starts at byte 1)
                vin_bytes.extend(msg.data[1:])
                received_frames += 1
                
                if received_frames >= total_frames:
                    log(f"All {total_frames} frames received")
                    break
            else:
                # Single frame response
                length = pcidata & 0x0F
                vin_bytes.extend(msg.data[4:4+length])
                log(f"Single frame response with {length} bytes")
                break
        else:
            log(f"Ignoring non-VIN response", "DEBUG")

    if not responses:
        raise TimeoutError("No response from ECU for VIN request")

    # Extract VIN from collected bytes
    if len(vin_bytes) >= 17:
        try:
            # Try ASCII decode first
            vin_candidate = vin_bytes[:17].decode('ascii', errors='ignore').strip().upper()
            
            # Clean up any non-alphanumeric characters
            vin_clean = ''.join(c for c in vin_candidate if c.isalnum())
            
            if _validate_vin(vin_clean):
                log(f"VIN successfully read: {vin_clean}")
                return {
                    "vin": vin_clean,
                    "value": vin_clean,
                    "result": vin_clean,
                    "data": {"vin": vin_clean},
                    "message": f"VIN: {vin_clean}",
                    "raw": {
                        "request": _serialize_can_message(req),
                        "responses": [_serialize_can_message(r) for r in responses],
                        "frames": received_frames,
                        "total_bytes": len(vin_bytes)
                    }
                }
            else:
                log(f"Invalid VIN format: {vin_clean}", "WARN")
        except Exception as e:
            log(f"Failed to decode VIN: {e}", "ERROR")

    # Return failure with raw data for debugging
    return {
        "vin": None,
        "value": None,
        "result": None,
        "data": {},
        "message": "Invalid or incomplete VIN response",
        "raw": {
            "request": _serialize_can_message(req),
            "responses": [_serialize_can_message(r) for r in responses],
            "bytes_received": len(vin_bytes),
            "hex_bytes": vin_bytes.hex().upper() if vin_bytes else ""
        }
    }


def read_vin(
    can_interface: str,
    bitrate: int,
    context=None,
    progress=None,
) -> Dict[str, Any]:
    """
    SINGLE-SHOT entry point for auto-run.
    
    Returns a dict with VIN in multiple locations to ensure capture:
    - "vin": Primary VIN field
    - "value": Generic value field
    - "result": Result field
    - "data": Nested data object with VIN
    
    The service.py will extract VIN from any of these locations.
    
    Args:
        can_interface: CAN interface name (e.g., "PCAN_USBBUS1", "can0")
        bitrate: CAN bitrate (e.g., 500000)
        context: TaskContext for cooperative cancellation and logging
        progress: Progress callback (legacy)
    
    Returns:
        Dict with VIN information in multiple formats
    """
    bus = None
    start_time = time.time()
    
    try:
        if context:
            context.checkpoint()
            context.progress(5, "Opening CAN bus")
            context.log(f"VIN_READ: Starting with {can_interface} @ {bitrate} bps", "INFO")
        if progress:
            progress(5, "Opening CAN bus")

        bus = _open_bus(can_interface, int(bitrate))
        if bus is None:
            error_msg = f"Failed to open CAN bus: {can_interface}"
            if context:
                context.log(error_msg, "ERROR")
                context.progress(100, error_msg)
            return {
                "vin": None,
                "value": None,
                "result": None,
                "data": {},
                "message": error_msg,
                "raw": None,
                "success": False,
                "duration_ms": int((time.time() - start_time) * 1000)
            }

        if context:
            context.progress(20, "CAN bus opened successfully")
            context.log("VIN_READ: CAN bus opened", "INFO")

        result = _read_vin_once(bus, context=context, progress=progress)
        
        # Add metadata
        result["success"] = result.get("vin") is not None
        result["duration_ms"] = int((time.time() - start_time) * 1000)
        result["timestamp"] = time.time()
        result["source"] = "auto"  # Indicates this was from auto-read

        if context:
            if result.get("vin"):
                vin = result["vin"]
                context.progress(100, f"VIN read successful: {vin}")
                # Emit structured JSON with VIN in multiple places for redundancy
                context.progress_json({
                    "vin": vin,
                    "value": vin,
                    "result": vin,
                    "data": {"vin": vin}
                })
                context.log(f"VIN_READ: Success - {vin}", "INFO")
            else:
                context.progress(100, "VIN read failed: invalid response")
                context.log(f"VIN_READ: Failed - {result.get('message', 'Unknown error')}", "ERROR")

        return result

    except TimeoutError:
        error_msg = "Timeout waiting for VIN response"
        if context:
            context.log(error_msg, "ERROR")
            context.progress(100, error_msg)
        return {
            "vin": None,
            "value": None,
            "result": None,
            "data": {},
            "message": error_msg,
            "raw": None,
            "success": False,
            "duration_ms": int((time.time() - start_time) * 1000),
            "source": "auto"
        }
    except Exception as e:
        error_msg = f"VIN read failed: {str(e)}"
        if context:
            context.log(error_msg, "ERROR")
            context.progress(100, error_msg)
        return {
            "vin": None,
            "value": None,
            "result": None,
            "data": {},
            "message": error_msg,
            "raw": None,
            "success": False,
            "duration_ms": int((time.time() - start_time) * 1000),
            "source": "auto"
        }
    finally:
        if bus:
            try:
                bus.shutdown()
                if context:
                    context.log("VIN_READ: CAN bus closed", "DEBUG")
            except Exception as e:
                if context:
                    context.log(f"VIN_READ: Error closing bus: {e}", "WARN")


# =============================================================================
# SINGLE-SHOT ENTRY POINT (Alias for compatibility)
# =============================================================================

def read_vin_single(
    can_interface: str,
    bitrate: int,
    context=None,
    progress=None,
) -> Dict[str, Any]:
    """
    Alias for read_vin() for backward compatibility.
    """
    return read_vin(can_interface, bitrate, context, progress)


# =============================================================================
# STREAMING ENTRY POINT (Not used for VIN, but kept for interface completeness)
# =============================================================================

def read_vin_stream(
    can_interface: str,
    bitrate: int,
    context=None,
    progress=None,
) -> Generator[Dict[str, Any], None, None]:
    """
    Streaming entry point (not typically used for VIN).
    Included for interface completeness.
    
    Yields:
        VIN reading (single shot then exits)
    """
    result = read_vin(can_interface, bitrate, context, progress)
    yield {
        "status": "completed" if result.get("success") else "error",
        "data": {
            "vin": result.get("vin"),
            "message": result.get("message")
        }
    }


# =============================================================================
# TEST FUNCTION (for standalone testing)
# =============================================================================

if __name__ == "__main__":
    # Simple test when run directly
    import sys
    
    print("VIN Read Test Utility")
    print("=" * 50)
    
    interface = sys.argv[1] if len(sys.argv) > 1 else "PCAN_USBBUS1"
    bitrate = int(sys.argv[2]) if len(sys.argv) > 2 else 500000
    
    print(f"Interface: {interface}")
    print(f"Bitrate: {bitrate}")
    print("-" * 50)
    
    class TestContext:
        def __init__(self):
            self.start = time.time()
        
        def checkpoint(self):
            pass
        
        def progress(self, percent, message):
            print(f"[{percent}%] {message}")
        
        def progress_json(self, data):
            print(f"JSON: {data}")
        
        def log(self, message, level="INFO"):
            print(f"[{level}] {message}")
    
    context = TestContext()
    result = read_vin(interface, bitrate, context=context)
    
    print("-" * 50)
    print(f"Success: {result.get('success', False)}")
    print(f"VIN: {result.get('vin')}")
    print(f"Message: {result.get('message')}")
    print(f"Duration: {result.get('duration_ms')} ms")
    print("=" * 50)
