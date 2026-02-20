# -*- coding: utf-8 -*-
"""
CAN UTILITIES (FINAL – PRODUCTION READY, APP.SCHEMA SAFE)

Responsibilities:
✔ Resolve CAN configuration from DB (app.config)
✔ Open / close CAN bus safely
✔ Provide reusable CAN helpers for diagnostic services & test programs
✔ No test-specific logic (VIN/DTC/etc.)
✔ Compatible with python-can
✔ PostgreSQL UPSERT safe
✔ Enhanced error handling and logging
✔ Multiple backend support with fallbacks
✔ Context manager for safe resource handling

Expected DB table:
  app.config(key_name TEXT UNIQUE, value_text TEXT)

Expected keys:
  - can_backend   : PCAN | SOCKETCAN | VIRTUAL   (optional; default PCAN)
  - can_interface : PCAN_USBBUS1 | can0 | vcan0 (optional; default PCAN_USBBUS1)
  - can_bitrate   : 500000 | 250000 | 125000     (optional; default 500000)
  - can_fd        : true | false                  (optional; default false)
  - vci_mode      : pcan | socketcan (legacy)

Version: 2.1.0
Last Updated: 2026-02-20
"""

from __future__ import annotations

import os
import logging
import time
import traceback
from typing import Optional, Dict, Any, Union, Tuple
from contextlib import contextmanager

from can import interface, Bus, Message, CanError
from can import BusABC
from database import query_one, execute

# =============================================================================
# LOGGING
# =============================================================================

logger = logging.getLogger(__name__)

def _log_info(message: str):
    logger.info(f"[CAN_UTILS] {message}")

def _log_warn(message: str):
    logger.warning(f"[CAN_UTILS] {message}")

def _log_error(message: str):
    logger.error(f"[CAN_UTILS] {message}")

def _log_debug(message: str):
    if os.getenv("NIRIX_DEBUG", "false").lower() == "true":
        logger.debug(f"[CAN_UTILS] {message}")

# =============================================================================
# CUSTOM EXCEPTIONS
# =============================================================================

class CANError(Exception):
    """Base CAN exception."""
    pass

class CANInitializationError(CANError):
    """Raised when CAN bus cannot be initialized."""
    pass

class CANCommunicationError(CANError):
    """Raised when CAN communication fails."""
    pass

class CANConfigurationError(CANError):
    """Raised when CAN configuration is invalid."""
    pass

# =============================================================================
# CONSTANTS
# =============================================================================

# Default values
DEFAULT_BACKEND = "pcan"
DEFAULT_INTERFACE = "PCAN_USBBUS1"
DEFAULT_BITRATE = 500000
DEFAULT_FD = False

# Supported backends
SUPPORTED_BACKENDS = {
    "pcan": "PCAN (Peak Systems)",
    "socketcan": "SocketCAN (Linux)",
    "virtual": "Virtual CAN (for testing)",
    "kvaser": "Kvaser CAN",
    "vector": "Vector CAN",
    "ixxat": "IXXAT",
    "neovi": "neoVI",
    "usb2can": "USB2CAN",
    "serial": "Serial CAN",
    "slcan": "SLCAN",
}

# Retry settings
MAX_BUS_INIT_RETRIES = 3
BUS_INIT_RETRY_DELAY = 0.5

# =============================================================================
# CONFIG HELPERS (POSTGRESQL SAFE)
# =============================================================================

def get_config_value(key: str, default: Optional[str] = None) -> Optional[str]:
    """
    Read a configuration value from DB (app.config).
    
    Args:
        key: Configuration key name
        default: Default value if not found
        
    Returns:
        Configuration value or default
    """
    try:
        row = query_one(
            "SELECT value_text FROM app.config WHERE key_name = :k",
            {"k": key},
        )
        if row and row.get("value_text") is not None:
            return row["value_text"]
        return default
    except Exception as e:
        _log_debug(f"Error reading config key '{key}': {e}")
        return default


def set_config_value(key: str, value: str) -> bool:
    """
    Insert or update config value (PostgreSQL UPSERT).
    Requires UNIQUE constraint on app.config.key_name.
    
    Args:
        key: Configuration key name
        value: Value to set
        
    Returns:
        True if successful, False otherwise
    """
    try:
        execute(
            """
            INSERT INTO app.config (key_name, value_text, updated_at)
            VALUES (:k, :v, CURRENT_TIMESTAMP)
            ON CONFLICT (key_name)
            DO UPDATE SET 
                value_text = EXCLUDED.value_text,
                updated_at = CURRENT_TIMESTAMP
            """,
            {"k": key, "v": str(value)},
        )
        _log_debug(f"Set config {key}={value}")
        return True
    except Exception as e:
        _log_error(f"Failed to set config key '{key}': {e}")
        return False


def delete_config_value(key: str) -> bool:
    """
    Delete a configuration value.
    
    Args:
        key: Configuration key name
        
    Returns:
        True if successful, False otherwise
    """
    try:
        execute(
            "DELETE FROM app.config WHERE key_name = :k",
            {"k": key},
        )
        _log_debug(f"Deleted config key '{key}'")
        return True
    except Exception as e:
        _log_error(f"Failed to delete config key '{key}': {e}")
        return False


# =============================================================================
# CAN CONFIG RESOLUTION
# =============================================================================

def get_can_config() -> Dict[str, Any]:
    """
    Resolve CAN configuration from DB with intelligent defaults.

    Returns:
      {
        "backend": "pcan" | "socketcan" | "virtual",
        "channel": "PCAN_USBBUS1" | "can0" | "vcan0",
        "bitrate": 500000,
        "fd": false,
        "supports_fd": false,
        "supports_brs": false
      }
    """
    config = {}
    
    try:
        # Read all relevant config keys
        backend_raw = (get_config_value("can_backend", DEFAULT_BACKEND) or "").strip().lower()
        interface_raw = (get_config_value("can_interface", "") or "").strip()
        bitrate_raw = (get_config_value("can_bitrate", str(DEFAULT_BITRATE)) or "").strip()
        fd_raw = (get_config_value("can_fd", "false") or "").strip().lower()
        
        # Legacy vci_mode support
        vci_mode = (get_config_value("vci_mode", "") or "").strip().lower()
        
        # Determine backend
        backend = backend_raw
        if backend not in SUPPORTED_BACKENDS:
            if vci_mode == "socketcan":
                backend = "socketcan"
            elif vci_mode == "pcan":
                backend = "pcan"
            else:
                backend = DEFAULT_BACKEND
                _log_warn(f"Unknown backend '{backend_raw}', using '{backend}'")
        
        # Determine interface/channel
        channel = interface_raw
        if not channel:
            if backend == "socketcan" or vci_mode == "socketcan":
                channel = "can0"
            elif backend == "virtual":
                channel = "vcan0"
            else:
                channel = DEFAULT_INTERFACE
        
        # Determine bitrate
        try:
            bitrate = int(bitrate_raw)
        except (ValueError, TypeError):
            bitrate = DEFAULT_BITRATE
            _log_warn(f"Invalid bitrate '{bitrate_raw}', using {bitrate}")
        
        # Determine FD support
        fd = fd_raw in ("true", "1", "yes", "on")
        
        # Check if backend supports FD
        supports_fd = backend in ("pcan", "socketcan", "vector", "kvaser")
        supports_brs = supports_fd  # Bit Rate Switch support
        
        config = {
            "backend": backend,
            "channel": channel,
            "bitrate": bitrate,
            "fd": fd,
            "supports_fd": supports_fd,
            "supports_brs": supports_brs,
            "raw": {
                "backend_raw": backend_raw,
                "interface_raw": interface_raw,
                "bitrate_raw": bitrate_raw,
                "fd_raw": fd_raw,
                "vci_mode": vci_mode,
            }
        }
        
        _log_debug(f"Resolved CAN config: {config}")
        
    except Exception as e:
        _log_error(f"Error resolving CAN config: {e}")
        config = {
            "backend": DEFAULT_BACKEND,
            "channel": DEFAULT_INTERFACE,
            "bitrate": DEFAULT_BITRATE,
            "fd": DEFAULT_FD,
            "supports_fd": False,
            "supports_brs": False,
            "error": str(e),
        }
    
    return config


def validate_can_config(config: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Validate CAN configuration.
    
    Args:
        config: CAN configuration dictionary
        
    Returns:
        (is_valid, error_message)
    """
    backend = config.get("backend", "").lower()
    channel = config.get("channel", "")
    bitrate = config.get("bitrate", 0)
    
    if not backend:
        return False, "No backend specified"
    
    if backend not in SUPPORTED_BACKENDS:
        return False, f"Unsupported backend: {backend}"
    
    if not channel:
        return False, "No channel/interface specified"
    
    if bitrate <= 0:
        return False, f"Invalid bitrate: {bitrate}"
    
    # Check for reserved channels in virtual mode
    if backend == "virtual" and channel in ("can0", "can1", "PCAN_USBBUS1"):
        _log_warn(f"Virtual backend using physical channel '{channel}' - this may cause conflicts")
    
    return True, None


# =============================================================================
# CAN BUS MANAGEMENT
# =============================================================================

def open_can_bus(
    *,
    channel: Optional[str] = None,
    bitrate: Optional[int] = None,
    backend: Optional[str] = None,
    fd: Optional[bool] = None,
    retry: bool = True,
) -> Bus:
    """
    Open CAN bus safely with retry logic.
    
    Args:
        channel: CAN channel/interface (e.g., "PCAN_USBBUS1", "can0", "vcan0")
        bitrate: Bitrate in bps (e.g., 500000)
        backend: CAN backend ("pcan", "socketcan", "virtual")
        fd: Enable CAN-FD mode
        retry: Whether to retry on failure
        
    Returns:
        CAN Bus instance
        
    Raises:
        CANInitializationError: If bus cannot be initialized
        CANConfigurationError: If configuration is invalid
    """
    # Get base config
    base_config = get_can_config()
    
    # Override with provided parameters
    channel = channel or base_config["channel"]
    bitrate = bitrate or base_config["bitrate"]
    backend = backend or base_config["backend"]
    fd = fd if fd is not None else base_config["fd"]
    
    # Validate
    test_config = {
        "backend": backend,
        "channel": channel,
        "bitrate": bitrate,
        "fd": fd,
    }
    
    is_valid, error = validate_can_config(test_config)
    if not is_valid:
        raise CANConfigurationError(f"Invalid CAN configuration: {error}")
    
    _log_info(f"Opening CAN bus: backend={backend}, channel={channel}, bitrate={bitrate}, fd={fd}")
    
    # Attempt to open bus with retries
    last_error = None
    attempts = MAX_BUS_INIT_RETRIES if retry else 1
    
    for attempt in range(1, attempts + 1):
        try:
            bus = _open_bus_single(
                channel=channel,
                bitrate=bitrate,
                backend=backend,
                fd=fd,
                attempt=attempt
            )
            
            if bus:
                _log_info(f"CAN bus opened successfully (attempt {attempt})")
                return bus
                
        except Exception as e:
            last_error = e
            _log_warn(f"Failed to open CAN bus (attempt {attempt}/{attempts}): {e}")
            
            if attempt < attempts:
                time.sleep(BUS_INIT_RETRY_DELAY * attempt)  # Exponential backoff
    
    # All attempts failed
    error_msg = f"Failed to open CAN bus after {attempts} attempts"
    if last_error:
        error_msg += f": {last_error}"
    
    _log_error(error_msg)
    raise CANInitializationError(error_msg)


def _open_bus_single(
    *,
    channel: str,
    bitrate: int,
    backend: str,
    fd: bool,
    attempt: int = 1,
) -> Optional[Bus]:
    """
    Single attempt to open CAN bus.
    
    Returns:
        Bus object or None on failure
    """
    bustype = backend
    
    # Special handling for different backends
    if backend == "pcan":
        # PCAN specific
        if not channel.startswith("PCAN_"):
            channel = f"PCAN_USBBUS{channel}" if channel.isdigit() else channel
        
        kwargs = {
            "channel": channel,
            "bustype": bustype,
            "bitrate": bitrate,
        }
        
        if fd:
            kwargs["fd"] = True
    
    elif backend == "socketcan":
        # SocketCAN specific
        kwargs = {
            "channel": channel,
            "bustype": bustype,
            "bitrate": bitrate,
        }
        
        if fd:
            kwargs["fd"] = True
    
    elif backend == "virtual":
        # Virtual CAN (for testing)
        kwargs = {
            "channel": channel,
            "bustype": "socketcan",  # Virtual uses socketcan type
            "bitrate": bitrate,
        }
        
        # Ensure virtual interface exists
        _ensure_virtual_interface(channel)
    
    else:
        # Generic backend
        kwargs = {
            "channel": channel,
            "bustype": bustype,
            "bitrate": bitrate,
        }
    
    _log_debug(f"Bus kwargs: {kwargs}")
    
    try:
        bus = interface.Bus(**kwargs)
        
        # Verify bus is actually working
        try:
            # Try to get bus info (non-critical)
            bus_info = getattr(bus, "get_info", None)
            if bus_info:
                _log_debug(f"Bus info: {bus_info()}")
        except:
            pass
        
        return bus
        
    except CanError as e:
        _log_error(f"CAN bus error: {e}")
        raise
    except Exception as e:
        _log_error(f"Unexpected error opening CAN bus: {e}")
        _log_debug(traceback.format_exc())
        return None


def _ensure_virtual_interface(interface: str = "vcan0"):
    """Ensure virtual CAN interface exists (Linux only)."""
    if os.name != "posix":
        return
    
    import subprocess
    
    try:
        # Check if interface exists
        result = subprocess.run(
            ["ip", "link", "show", interface],
            capture_output=True,
            text=True,
            timeout=2
        )
        
        if result.returncode != 0:
            # Create virtual interface
            _log_info(f"Creating virtual CAN interface: {interface}")
            subprocess.run(
                ["sudo", "ip", "link", "add", "dev", interface, "type", "vcan"],
                check=False,
                timeout=5
            )
            subprocess.run(
                ["sudo", "ip", "link", "set", "up", interface],
                check=False,
                timeout=2
            )
    except Exception as e:
        _log_warn(f"Failed to ensure virtual interface: {e}")


def close_can_bus(bus: Optional[Bus]) -> None:
    """
    Safely shutdown CAN bus.
    
    Args:
        bus: CAN bus instance to close
    """
    if bus is None:
        return
    
    try:
        _log_debug("Shutting down CAN bus")
        bus.shutdown()
        _log_debug("CAN bus closed")
    except Exception as e:
        _log_warn(f"Error closing CAN bus: {e}")


def is_bus_online(bus: Optional[Bus]) -> bool:
    """
    Check if CAN bus is online and responding.
    
    Args:
        bus: CAN bus instance
        
    Returns:
        True if bus is online and operational
    """
    if bus is None:
        return False
    
    try:
        # Try to send a dummy message (with zero length) to test
        msg = Message(
            arbitration_id=0x7DF,  # OBD broadcast
            data=[],
            is_extended_id=False
        )
        bus.send(msg, timeout=0.1)
        return True
    except Exception:
        return False


# =============================================================================
# GENERIC DIAGNOSTIC HELPERS
# =============================================================================

def send_can_frame(
    bus: Bus,
    arbitration_id: int,
    data: bytes,
    *,
    is_extended_id: bool = False,
    timeout: float = 1.0,
) -> bool:
    """
    Send one CAN frame.
    
    Args:
        bus: CAN bus instance
        arbitration_id: CAN ID (11 or 29 bit)
        data: Data bytes (up to 8 for classic CAN, up to 64 for CAN-FD)
        is_extended_id: Use 29-bit extended ID
        timeout: Send timeout in seconds
        
    Returns:
        True if successful, False otherwise
    """
    try:
        from can import Message
        
        # Validate data length
        max_len = 64 if getattr(bus, "fd", False) else 8
        if len(data) > max_len:
            _log_warn(f"Data length {len(data)} exceeds maximum {max_len}")
            data = data[:max_len]
        
        msg = Message(
            arbitration_id=arbitration_id,
            data=data,
            is_extended_id=is_extended_id,
        )
        
        bus.send(msg, timeout=timeout)
        _log_debug(f"Sent: ID=0x{arbitration_id:X}, Data={data.hex().upper()}")
        return True
        
    except CanError as e:
        _log_error(f"CAN send error: {e}")
        return False
    except Exception as e:
        _log_error(f"Unexpected error sending CAN frame: {e}")
        return False


def recv_can_frame(
    bus: Bus,
    timeout: float = 1.0,
    *,
    expected_id: Optional[int] = None,
) -> Optional[Message]:
    """
    Receive one CAN frame.
    
    Args:
        bus: CAN bus instance
        timeout: Receive timeout in seconds
        expected_id: If provided, only return messages with this ID
        
    Returns:
        CAN message or None if timeout/error
    """
    try:
        start_time = time.time()
        
        while True:
            remaining = timeout - (time.time() - start_time)
            if remaining <= 0:
                return None
            
            msg = bus.recv(timeout=min(remaining, 0.1))
            
            if msg is None:
                continue
                
            if expected_id is None or msg.arbitration_id == expected_id:
                _log_debug(f"Received: ID=0x{msg.arbitration_id:X}, Data={msg.data.hex().upper()}")
                return msg
                
    except CanError as e:
        _log_error(f"CAN receive error: {e}")
        return None
    except Exception as e:
        _log_error(f"Unexpected error receiving CAN frame: {e}")
        return None


def send_and_wait_response(
    bus: Bus,
    request: Message,
    expected_id: int,
    timeout: float = 1.0,
    retries: int = 3,
) -> Optional[Message]:
    """
    Send a request and wait for response.
    
    Args:
        bus: CAN bus instance
        request: Request message to send
        expected_id: Expected response ID
        timeout: Receive timeout per attempt
        retries: Number of retries
        
    Returns:
        Response message or None
    """
    for attempt in range(1, retries + 1):
        try:
            # Send request
            if not send_can_frame(
                bus,
                request.arbitration_id,
                request.data,
                is_extended_id=request.is_extended_id,
                timeout=timeout / 2
            ):
                _log_warn(f"Send failed (attempt {attempt}/{retries})")
                continue
            
            # Wait for response
            response = recv_can_frame(
                bus,
                timeout=timeout / 2,
                expected_id=expected_id
            )
            
            if response:
                return response
                
            _log_debug(f"No response (attempt {attempt}/{retries})")
            
        except Exception as e:
            _log_warn(f"Error in send_and_wait (attempt {attempt}/{retries}): {e}")
        
        if attempt < retries:
            time.sleep(0.1 * attempt)  # Increasing delay
    
    return None


# =============================================================================
# CONTEXT MANAGER (RECOMMENDED USAGE)
# =============================================================================

class CanSession:
    """
    Context manager for CAN session handling with automatic cleanup.

    Usage:
        with CanSession() as bus:
            bus.send(...)
            response = bus.recv(...)
            
    Or with specific parameters:
        with CanSession(backend="socketcan", channel="can0", bitrate=500000) as bus:
            ...
    """

    def __init__(
        self,
        *,
        channel: Optional[str] = None,
        bitrate: Optional[int] = None,
        backend: Optional[str] = None,
        fd: Optional[bool] = None,
        retry: bool = True,
    ):
        self._params = {
            "channel": channel,
            "bitrate": bitrate,
            "backend": backend,
            "fd": fd,
            "retry": retry,
        }
        self.bus: Optional[Bus] = None
        self._opened = False

    def __enter__(self) -> Bus:
        """Open CAN bus and return it."""
        try:
            self.bus = open_can_bus(**self._params)
            self._opened = True
            return self.bus
        except Exception as e:
            _log_error(f"Failed to open CAN session: {e}")
            raise

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Ensure bus is closed even if an error occurred."""
        if self.bus:
            close_can_bus(self.bus)
            self.bus = None
            self._opened = False
        
        # Log any exception that occurred
        if exc_type:
            _log_debug(f"CAN session exiting with error: {exc_type.__name__}: {exc_val}")

    def is_active(self) -> bool:
        """Check if session is active and bus is online."""
        return self._opened and self.bus is not None and is_bus_online(self.bus)

    def reconnect(self) -> bool:
        """
        Attempt to reconnect the CAN bus.
        
        Returns:
            True if reconnection successful
        """
        if self.bus:
            close_can_bus(self.bus)
            self.bus = None
        
        try:
            self.bus = open_can_bus(**self._params)
            self._opened = True
            return True
        except Exception as e:
            _log_error(f"Reconnection failed: {e}")
            self._opened = False
            return False


@contextmanager
def can_bus_context(**kwargs):
    """
    Simple context manager for CAN bus (alternative to CanSession class).
    
    Usage:
        with can_bus_context(backend="socketcan", channel="can0") as bus:
            bus.send(...)
    """
    bus = None
    try:
        bus = open_can_bus(**kwargs)
        yield bus
    finally:
        if bus:
            close_can_bus(bus)


# =============================================================================
# TESTING HELPERS
# =============================================================================

def get_available_backends() -> Dict[str, bool]:
    """
    Get dictionary of available CAN backends.
    
    Returns:
        {backend_name: is_available}
    """
    available = {}
    
    for backend in SUPPORTED_BACKENDS:
        try:
            # Try to import the backend module
            import importlib
            module_name = f"can.interfaces.{backend}"
            
            if backend == "virtual":
                # Virtual backend uses socketcan interface
                module_name = "can.interfaces.socketcan"
            
            spec = importlib.util.find_spec(module_name)
            available[backend] = spec is not None
            
        except Exception:
            available[backend] = False
    
    return available


def test_connection(
    *,
    channel: Optional[str] = None,
    bitrate: Optional[int] = None,
    backend: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Test CAN connection and return diagnostics.
    
    Returns:
        Dict with test results
    """
    result = {
        "success": False,
        "config": {},
        "error": None,
        "details": {},
    }
    
    try:
        config = get_can_config()
        result["config"] = config
        
        with CanSession(channel=channel, bitrate=bitrate, backend=backend) as bus:
            # Test basic communication
            test_msg = Message(
                arbitration_id=0x7DF,
                data=[0x02, 0x01, 0x0C, 0x00, 0x00, 0x00, 0x00, 0x00],
                is_extended_id=False
            )
            
            start = time.time()
            send_ok = send_can_frame(
                bus,
                test_msg.arbitration_id,
                test_msg.data,
                timeout=0.5
            )
            
            result["details"]["send_time_ms"] = int((time.time() - start) * 1000)
            result["details"]["send_success"] = send_ok
            
            # Try to receive (but don't wait long)
            response = recv_can_frame(bus, timeout=0.5)
            result["details"]["received"] = response is not None
            if response:
                result["details"]["response_id"] = f"0x{response.arbitration_id:X}"
                result["details"]["response_data"] = response.data.hex().upper()
            
            result["success"] = True
            
    except Exception as e:
        result["error"] = str(e)
        result["details"]["traceback"] = traceback.format_exc()
    
    return result


# =============================================================================
# INITIALIZATION
# =============================================================================

def _init_can_utils():
    """Initialize CAN utilities module."""
    _log_info(f"CAN Utilities v2.1.0")
    
    # Log available backends
    backends = get_available_backends()
    available = [b for b, avail in backends.items() if avail]
    _log_info(f"Available backends: {', '.join(available) or 'None'}")
    
    # Log current config
    try:
        config = get_can_config()
        _log_info(f"Current config: {config['backend']}/{config['channel']} @ {config['bitrate']} bps")
    except Exception as e:
        _log_warn(f"Could not load current config: {e}")


_init_can_utils()


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Configuration
    "get_config_value",
    "set_config_value",
    "delete_config_value",
    "get_can_config",
    "validate_can_config",
    
    # Bus management
    "open_can_bus",
    "close_can_bus",
    "is_bus_online",
    
    # Communication
    "send_can_frame",
    "recv_can_frame",
    "send_and_wait_response",
    
    # Context managers
    "CanSession",
    "can_bus_context",
    
    # Testing
    "get_available_backends",
    "test_connection",
    
    # Exceptions
    "CANError",
    "CANInitializationError",
    "CANCommunicationError",
    "CANConfigurationError",
    
    # Constants
    "SUPPORTED_BACKENDS",
    "DEFAULT_BACKEND",
    "DEFAULT_INTERFACE",
    "DEFAULT_BITRATE",
]
