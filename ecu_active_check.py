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
    """Open CAN bus connection."""
    iface = (can_interface or "").strip()
    try:
        if iface.upper().startswith("PCAN"):
            return can.Bus(interface="pcan", channel=iface, bitrate=int(bitrate), fd=False)
        if iface.lower().startswith("can"):
            return can.Bus(interface="socketcan", channel=iface, bitrate=int(bitrate))
        raise ValueError(f"Unsupported CAN interface: {iface}")
    except Exception as e:
        print(f"[ECU_CHECK] Failed to open CAN bus: {e}")
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


def check_ecu_active(
    can_interface: str,
    bitrate: int,
    context=None,
    progress=None,
) -> Dict[str, Any]:
    """
    Check if ECU is active by sending tester present request.
    
    Returns:
        {
            "is_active": bool,
            "ecu_code": "BMS",
            "message": str,
            "last_response": timestamp or None,
            "raw": {...}
        }
    """
    bus = None
    try:
        if context:
            context.progress(10, "Opening CAN bus")
            context.log(f"ECU_CHECK: Starting with {can_interface} @ {bitrate} bps", "INFO")
        
        bus = _open_bus(can_interface, bitrate)
        if bus is None:
            error_msg = f"Failed to open CAN bus: {can_interface}"
            if context:
                context.log(error_msg, "ERROR")
            return {
                "is_active": False,
                "ecu_code": "BMS",
                "message": error_msg,
                "last_response": None,
                "raw": None
            }

        if context:
            context.progress(30, "Sending tester present (3E 80)")

        # Send tester present (3E 80) - UDS service to check if ECU is awake
        req = can.Message(
            arbitration_id=0x7F0,
            is_extended_id=False,
            data=[0x02, 0x3E, 0x80, 0x00, 0x00, 0x00, 0x00, 0x00],
        )
        
        if context:
            context.log(f"Tx {req.arbitration_id:03X} " + " ".join(f"{b:02X}" for b in req.data))
        
        bus.send(req)
        
        # Wait for response
        deadline = time.time() + 1.0
        response_time = None
        
        while time.time() < deadline:
            if context:
                context.checkpoint()
            
            msg = bus.recv(timeout=0.2)
            if not msg:
                continue
                
            if msg.arbitration_id != 0x7F1:
                continue
                
            response_time = time.time()
            if context:
                context.log(f"Rx {msg.arbitration_id:03X} " + " ".join(f"{b:02X}" for b in msg.data))
            
            # Check if response is positive (7E 80)
            if len(msg.data) >= 3 and msg.data[1] == 0x7E and msg.data[2] == 0x80:
                if context:
                    context.progress(100, "ECU is active")
                    context.log("ECU_CHECK: ECU responded positively", "INFO")
                
                return {
                    "is_active": True,
                    "ecu_code": "BMS",
                    "message": "ECU is active and responding",
                    "last_response": response_time,
                    "raw": {
                        "request": _serialize_can_message(req),
                        "response": _serialize_can_message(msg)
                    }
                }
            else:
                # Unexpected response
                if context:
                    context.log(f"ECU_CHECK: Unexpected response format", "WARN")
        
        # No response within timeout
        if context:
            context.progress(100, "ECU not responding")
            context.log("ECU_CHECK: No response within timeout", "WARN")
        
        return {
            "is_active": False,
            "ecu_code": "BMS",
            "message": "ECU not responding (timeout)",
            "last_response": None,
            "raw": {
                "request": _serialize_can_message(req),
                "response": None
            }
        }
        
    except Exception as e:
        if context:
            context.log(f"ECU_CHECK error: {e}", "ERROR")
        return {
            "is_active": False,
            "ecu_code": "BMS",
            "message": str(e),
            "last_response": None,
            "raw": None
        }
    finally:
        if bus:
            try:
                bus.shutdown()
                if context:
                    context.log("ECU_CHECK: CAN bus closed", "INFO")
            except Exception:
                pass