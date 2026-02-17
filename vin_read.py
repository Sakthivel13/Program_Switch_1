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

Version: 2.0.0
Last Updated: 2026-02-17
"""

from __future__ import annotations

import time
import logging
from typing import Dict, Any, Optional

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


def _read_vin_once(bus: can.BusABC, *, context=None, progress=None) -> Dict[str, Any]:
    """
    Send UDS ReadDataByIdentifier (22 F1 90) once and parse response.
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
    deadline = time.time() + 2.0
    responses = []
    vin_bytes = bytearray()
    
    while time.time() < deadline:
        if context:
            context.checkpoint()

        try:
            msg = bus.recv(timeout=0.3)
        except Exception as e:
            log(f"Error receiving CAN message: {e}", "ERROR")
            continue
            
        if not msg:
            continue
        if msg.arbitration_id != 0x7F1:
            continue

        log(f"Rx {msg.arbitration_id:03X} " + " ".join(f"{b:02X}" for b in msg.data))
        responses.append(msg)
        
        # Check if this is a positive response to 22 F1 90
        if len(msg.data) >= 4 and msg.data[1] == 0x62 and msg.data[2] == 0xF1 and msg.data[3] == 0x90:
            # First frame of response - add data bytes
            vin_bytes.extend(msg.data[4:])
            
            # Check if more frames expected (first byte indicates multi-frame)
            if len(msg.data) >= 4 and (msg.data[0] & 0xF0) == 0x10:
                # Multi-frame response - wait for consecutive frames
                total_length = ((msg.data[0] & 0x0F) << 8) | msg.data[1]
                log(f"Multi-frame response, total length: {total_length} bytes")
                continue
            else:
                # Single frame response
                break
        elif len(msg.data) >= 1 and (msg.data[0] & 0xF0) == 0x20:
            # Consecutive frame
            vin_bytes.extend(msg.data[1:])
            # Check if we have all data
            if len(vin_bytes) >= 17:  # VIN is 17 characters
                break

    if not responses:
        raise TimeoutError("No response from ECU for VIN request")

    # Extract VIN from response
    if len(vin_bytes) >= 17:
        try:
            vin = vin_bytes[:17].decode('ascii').strip().upper()
            # Validate VIN format
            if len(vin) == 17 and not any(c in vin for c in "IOQ"):
                return {
                    "vin": vin,
                    "message": f"VIN: {vin}",
                    "raw": {
                        "request": _serialize_can_message(req),
                        "responses": [_serialize_can_message(r) for r in responses]
                    }
                }
        except Exception as e:
            log(f"Failed to decode VIN: {e}", "ERROR")

    return {
        "vin": None,
        "message": "Invalid VIN response",
        "raw": {
            "request": _serialize_can_message(req),
            "responses": [_serialize_can_message(r) for r in responses]
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
    
    Returns a dict: 
        {"vin": str|None, "message": str, "raw": {...}}
    
    The VIN will be captured by the service and stored in auto_run_sessions.
    """
    bus = None
    try:
        if context:
            context.checkpoint()
            context.progress(5, "Opening CAN bus")
        if progress:
            progress(5, "Opening CAN bus")

        bus = _open_bus(can_interface, int(bitrate))
        if bus is None:
            error_msg = f"Failed to open CAN bus: {can_interface}"
            if context:
                context.log(error_msg, "ERROR")
            return {
                "vin": None,
                "message": error_msg,
                "raw": None,
            }

        result = _read_vin_once(bus, context=context, progress=progress)

        if context:
            if result.get("vin") is not None:
                context.progress(100, f"VIN read successful: {result['vin']}")
                # Emit structured JSON for UI
                context.progress_json({"vin": result["vin"]})
            else:
                context.progress(100, "VIN read failed: invalid response")

        return result

    except TimeoutError:
        error_msg = "Timeout waiting for VIN response"
        if context:
            context.log(error_msg, "ERROR")
            context.progress(100, error_msg)
        return {
            "vin": None,
            "message": error_msg,
            "raw": None,
        }
    except Exception as e:
        error_msg = f"VIN read failed: {e}"
        if context:
            context.log(error_msg, "ERROR")
            context.progress(100, error_msg)
        return {
            "vin": None,
            "message": error_msg,
            "raw": None,
        }
    finally:
        if bus:
            try:
                bus.shutdown()
            except Exception:
                pass