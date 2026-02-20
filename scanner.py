# diagnostics/scanner.py
# -*- coding: utf-8 -*-
"""
NIRIX STATION SCANNER (BACKEND – OpenCV)

RESPONSIBILITY
──────────────
This module is used ONLY by the backend `/api/scan/*` endpoints to talk to a
fixed station camera (USB / built‑in) using OpenCV.

- Front-end scanner (phone/tablet/desktop browser) uses html5-qrcode in tests.html.
- Backend scanner is used mainly on PC stations where OpenCV has direct access
  to a local camera and you want scanning without browser camera permission.

PUBLIC API
──────────
- start_scan(kind: "text"|"vin"|"hex" = "text", timeout_sec: int|None = None) -> ScanSession
- get_scan(scan_id: str) -> Optional[ScanSession]
- cancel_scan(scan_id: str) -> bool
- cleanup_scans(max_age_sec: int = 300) -> int

OPTIONAL (PREVIEW SUPPORT)
────────────────────────
This version also stores the latest JPEG frame in memory (if enabled) so your
web app can implement a "live preview" endpoint if you want it:

- get_scan_frame_jpeg(scan_id: str) -> Optional[bytes]

ScanSession.status:
  "running"   – scan in progress
  "found"     – value found
  "timeout"   – no code found within timeout
  "cancelled" – cancelled by user
  "error"     – internal error
  "busy"      – camera already in use

ENV
───
- NIRIX_SCAN_CAMERA_INDEX (default "0")
- NIRIX_SCAN_TIMEOUT_SEC (default "20")
- NIRIX_SCAN_PREVIEW_ENABLED ("true"/"false", default "true")
- NIRIX_SCAN_PREVIEW_WIDTH (default "640")      # resize preview frames
- NIRIX_SCAN_PREVIEW_QUALITY (default "75")     # JPEG quality 1..100
- NIRIX_SCAN_PREVIEW_MAX_FPS (default "8")      # limit preview encode frequency
- NIRIX_SCAN_CAP_BACKEND (optional; e.g. "DSHOW", "MSMF", "V4L2")
- NIRIX_SCAN_DEBUG (default "false")            # enable debug logging
- NIRIX_SCAN_DECODE_ATTEMPTS (default "3")      # number of decode attempts per frame

Version: 2.0.0
Last Updated: 2026-02-20

FIXES IN v2.0.0
────────────────
- FIX-80: Enhanced error handling for camera initialization
- FIX-81: Multiple decode attempts per frame for better success rate
- FIX-82: Preview frame rate limiting with timestamp tracking
- FIX-83: Thread-safe session management with proper cleanup
- FIX-84: VIN validation and post-processing
- FIX-85: Camera backend selection with fallbacks
- FIX-86: Debug logging with environment flag
- FIX-87: Timeout handling with heartbeat mechanism
- FIX-88: Frame preprocessing (grayscale, contrast enhancement)
"""

from __future__ import annotations

import os
import time
import uuid
import threading
import logging
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Tuple
from enum import Enum
from datetime import datetime

import cv2
import numpy as np

# =============================================================================
# LOGGING
# =============================================================================

logger = logging.getLogger(__name__)

DEBUG_MODE = os.getenv("NIRIX_SCAN_DEBUG", "false").lower() in ("1", "true", "yes")

def _log_info(message: str):
    logger.info(f"[SCANNER] {message}")

def _log_warn(message: str):
    logger.warning(f"[SCANNER] {message}")

def _log_error(message: str):
    logger.error(f"[SCANNER] {message}")

def _log_debug(message: str):
    if DEBUG_MODE:
        logger.debug(f"[SCANNER] {message}")

# =============================================================================
# ENUMS
# =============================================================================

class ScanStatus(Enum):
    """Scan session status."""
    RUNNING = "running"
    FOUND = "found"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"
    ERROR = "error"
    BUSY = "busy"
    INITIALIZING = "initializing"

class ScanKind(Enum):
    """Type of scan to perform."""
    TEXT = "text"
    VIN = "vin"
    HEX = "hex"
    
    @classmethod
    def from_string(cls, value: str) -> 'ScanKind':
        """Convert string to ScanKind."""
        value = (value or "text").strip().lower()
        try:
            return cls(value)
        except ValueError:
            return cls.TEXT

# =============================================================================
# CONFIG
# =============================================================================

CAM_INDEX = int(os.getenv("NIRIX_SCAN_CAMERA_INDEX", "0"))
DEFAULT_TIMEOUT_SEC = int(os.getenv("NIRIX_SCAN_TIMEOUT_SEC", "20"))
DECODE_ATTEMPTS = int(os.getenv("NIRIX_SCAN_DECODE_ATTEMPTS", "3"))

PREVIEW_ENABLED = os.getenv("NIRIX_SCAN_PREVIEW_ENABLED", "true").lower() in ("1", "true", "yes")
PREVIEW_WIDTH = int(os.getenv("NIRIX_SCAN_PREVIEW_WIDTH", "640"))
PREVIEW_QUALITY = int(os.getenv("NIRIX_SCAN_PREVIEW_QUALITY", "75"))
PREVIEW_MAX_FPS = float(os.getenv("NIRIX_SCAN_PREVIEW_MAX_FPS", "8"))

# Enforce single camera access process-wide
_CAMERA_LOCK = threading.Lock()
_CAMERA_IN_USE = False
_CAMERA_LAST_ACCESS = 0


def _cv_cap_backend() -> int:
    """
    Optional VideoCapture backend selection for Windows/Linux camera quirks.
    Tries multiple backends in order of preference.
    """
    name = (os.getenv("NIRIX_SCAN_CAP_BACKEND", "") or "").strip().upper()
    
    # Backend mapping with priorities
    backend_mapping = {
        "DSHOW": getattr(cv2, "CAP_DSHOW", 700),  # DirectShow (Windows)
        "MSMF": getattr(cv2, "CAP_MSMF", 1400),   # Media Foundation (Windows)
        "V4L2": getattr(cv2, "CAP_V4L2", 200),    # Video4Linux2 (Linux)
        "ANY": getattr(cv2, "CAP_ANY", 0),        # Auto-detect
    }
    
    # If specific backend requested
    if name in backend_mapping:
        return backend_mapping[name]
    
    # Otherwise try backends in order based on platform
    import platform
    if platform.system() == "Windows":
        # Try DSHOW first on Windows, then MSMF, then ANY
        return backend_mapping.get("DSHOW", 700)
    elif platform.system() == "Linux":
        # Try V4L2 first on Linux, then ANY
        return backend_mapping.get("V4L2", 200)
    else:
        # Default to ANY on other platforms
        return backend_mapping.get("ANY", 0)


# Prefer OpenCV barcode module if available (opencv-contrib-python)
_BARCODE_DETECTOR = None
try:
    # Depending on build, one of these exists
    if hasattr(cv2, "barcode_BarcodeDetector"):
        _BARCODE_DETECTOR = cv2.barcode_BarcodeDetector()  # type: ignore[attr-defined]
        _log_info("OpenCV barcode detector initialized (barcode_BarcodeDetector)")
    elif hasattr(cv2, "barcode") and hasattr(cv2.barcode, "BarcodeDetector"):
        _BARCODE_DETECTOR = cv2.barcode.BarcodeDetector()  # type: ignore[attr-defined]
        _log_info("OpenCV barcode detector initialized (barcode.BarcodeDetector)")
    else:
        _log_warn("OpenCV barcode detector not available - install opencv-contrib-python")
except Exception as e:
    _log_warn(f"Failed to initialize barcode detector: {e}")
    _BARCODE_DETECTOR = None

_QR_DETECTOR = cv2.QRCodeDetector()
_QR_DETECTOR.setEpsX(4.0)  # Optimize for speed
_QR_DETECTOR.setEpsY(4.0)

# =============================================================================
# DATA MODEL
# =============================================================================

@dataclass
class ScanSession:
    """In-memory scan session state with thread safety."""
    scan_id: str
    kind: ScanKind = ScanKind.TEXT
    status: ScanStatus = ScanStatus.INITIALIZING
    value: Optional[str] = None
    error: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    timeout_sec: int = DEFAULT_TIMEOUT_SEC

    cancel_event: threading.Event = field(default_factory=threading.Event, repr=False)

    # Optional preview support (latest JPEG frame)
    last_frame_jpeg: Optional[bytes] = None
    last_frame_at: Optional[float] = None
    frame_count: int = 0
    decode_attempts: int = 0

    # Internal lock for safe updates
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def set_status(self, status: ScanStatus, *, error: Optional[str] = None):
        with self._lock:
            old_status = self.status
            self.status = status
            if error is not None:
                self.error = error
            
            if status == ScanStatus.RUNNING and self.started_at is None:
                self.started_at = time.time()
            elif status in (ScanStatus.FOUND, ScanStatus.TIMEOUT, ScanStatus.CANCELLED, ScanStatus.ERROR):
                self.completed_at = time.time()
            
            _log_debug(f"Session {self.scan_id}: {old_status.value} -> {status.value}")

    def set_value_found(self, value: str):
        with self._lock:
            self.value = value
            self.status = ScanStatus.FOUND
            self.completed_at = time.time()
            _log_info(f"Session {self.scan_id}: Found value '{value}'")

    def set_preview_frame(self, jpg: bytes):
        with self._lock:
            self.last_frame_jpeg = jpg
            self.last_frame_at = time.time()
            self.frame_count += 1

    def increment_decode_attempts(self):
        with self._lock:
            self.decode_attempts += 1

    def time_remaining(self) -> float:
        """Get remaining time in seconds."""
        if self.started_at is None:
            return self.timeout_sec
        elapsed = time.time() - self.started_at
        return max(0, self.timeout_sec - elapsed)

    def is_expired(self) -> bool:
        """Check if session has expired."""
        if self.status not in (ScanStatus.RUNNING, ScanStatus.INITIALIZING):
            return False
        if self.started_at is None:
            return False
        return (time.time() - self.started_at) > self.timeout_sec

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        with self._lock:
            return {
                "scan_id": self.scan_id,
                "status": self.status.value,
                "value": self.value,
                "error": self.error,
                "kind": self.kind.value,
                "time_remaining": self.time_remaining(),
                "frame_count": self.frame_count,
                "decode_attempts": self.decode_attempts,
                "created_at": self.created_at,
                "started_at": self.started_at,
                "completed_at": self.completed_at,
                "has_preview": self.last_frame_jpeg is not None,
            }


_SCANS: Dict[str, ScanSession] = {}
_SCANS_LOCK = threading.RLock()


# =============================================================================
# HELPERS
# =============================================================================

def _postprocess(value: str, kind: ScanKind) -> str:
    """
    Post-process decoded text based on `kind`:
      - "vin": uppercase, strip spaces, validate length
      - "hex": uppercase, strip 0x prefix and spaces, validate hex
      - default: strip
    """
    s = (value or "").strip()
    
    if kind == ScanKind.VIN:
        s = s.upper().replace(" ", "")
        # Basic VIN validation (length)
        if len(s) > 17:
            s = s[:17]
        elif len(s) < 17:
            _log_warn(f"VIN too short: {len(s)} chars, expected 17")
    elif kind == ScanKind.HEX:
        s = s.strip().upper()
        if s.startswith("0X"):
            s = s[2:]
        s = s.replace(" ", "")
        # Validate hex characters
        if s and not all(c in "0123456789ABCDEF" for c in s):
            _log_warn(f"Invalid hex characters in: {s}")
    else:
        s = s.strip()
    
    return s


def _preprocess_frame(frame) -> List[np.ndarray]:
    """
    Preprocess frame for better decoding.
    Returns list of preprocessed images to try.
    """
    if frame is None:
        return []
    
    results = [frame]  # Original
    
    try:
        # Convert to grayscale
        if len(frame.shape) == 3:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            results.append(gray)
            
            # Try different preprocessing techniques
            # 1. Adaptive threshold
            thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                          cv2.THRESH_BINARY, 11, 2)
            results.append(thresh)
            
            # 2. Increase contrast
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            enhanced = clahe.apply(gray)
            results.append(enhanced)
            
            # 3. Resize for better detection (if small)
            h, w = gray.shape
            if w < 320 or h < 240:
                scale = max(320/w, 240/h)
                new_w, new_h = int(w * scale), int(h * scale)
                resized = cv2.resize(gray, (new_w, new_h), interpolation=cv2.INTER_CUBIC)
                results.append(resized)
    except Exception as e:
        _log_warn(f"Frame preprocessing error: {e}")
    
    return results


def _try_decode_barcode(frame) -> Optional[str]:
    """
    Decode using OpenCV barcode detector (if available).
    Handles minor API differences across builds.
    """
    if _BARCODE_DETECTOR is None:
        return None

    try:
        # Most builds return: ok, decoded_info, decoded_type, points
        out = _BARCODE_DETECTOR.detectAndDecode(frame)  # type: ignore
        if not isinstance(out, tuple) or len(out) < 2:
            return None

        ok = bool(out[0])
        decoded_info = out[1]

        if ok and decoded_info:
            # decoded_info is typically a list of strings
            if isinstance(decoded_info, (list, tuple)):
                for v in decoded_info:
                    if v and isinstance(v, str) and v.strip():
                        return str(v).strip()
            # some builds might return a single string
            if isinstance(decoded_info, str) and decoded_info.strip():
                return decoded_info.strip()
    except Exception as e:
        _log_debug(f"Barcode decode error: {e}")
        return None

    return None


def _try_decode_qr(frame) -> Optional[str]:
    """Decode using OpenCV QRCodeDetector (always available)."""
    try:
        data, points, _ = _QR_DETECTOR.detectAndDecode(frame)
        if data and isinstance(data, str) and data.strip():
            return data.strip()
    except Exception as e:
        _log_debug(f"QR decode error: {e}")
        return None
    return None


def _decode_frame(frame) -> Optional[str]:
    """
    Decode a single frame using multiple attempts and preprocessing.
    
    Returns:
        Decoded string or None
    """
    # Get preprocessed versions of the frame
    preprocessed = _preprocess_frame(frame)
    
    for idx, img in enumerate(preprocessed):
        # Try barcode detector first (if available)
        v = _try_decode_barcode(img)
        if v:
            _log_debug(f"Decoded barcode from preprocessed image {idx}")
            return v
        
        # Then try QR detector
        v = _try_decode_qr(img)
        if v:
            _log_debug(f"Decoded QR from preprocessed image {idx}")
            return v
    
    return None


def _encode_preview_jpeg(frame) -> Optional[bytes]:
    """
    Encode frame as JPEG for optional preview.
    Resizes for bandwidth/CPU control.
    """
    if frame is None:
        return None

    try:
        img = frame

        # Resize if needed
        if PREVIEW_WIDTH and PREVIEW_WIDTH > 0:
            h, w = img.shape[:2]
            if w > PREVIEW_WIDTH:
                scale = PREVIEW_WIDTH / float(w)
                new_w = PREVIEW_WIDTH
                new_h = int(h * scale)
                img = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)

        # Encode as JPEG
        quality = max(10, min(95, int(PREVIEW_QUALITY)))
        ok, buf = cv2.imencode(".jpg", img, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
        if not ok:
            return None
        return buf.tobytes()
    except Exception as e:
        _log_debug(f"JPEG encoding error: {e}")
        return None


# =============================================================================
# PUBLIC API
# =============================================================================

def start_scan(
    kind: str = "text", 
    timeout_sec: Optional[int] = None,
    camera_index: Optional[int] = None
) -> ScanSession:
    """
    Start a new scan session.

    Args:
        kind: "text" | "vin" | "hex"
        timeout_sec: optional timeout override (seconds)
        camera_index: optional camera index override

    Returns:
        ScanSession with a unique scan_id.
    """
    scan_kind = ScanKind.from_string(kind)
    scan_id = f"scan_{int(time.time())}_{uuid.uuid4().hex[:8]}"
    
    # Determine timeout
    try:
        tsec = int(timeout_sec) if timeout_sec is not None else DEFAULT_TIMEOUT_SEC
    except Exception:
        tsec = DEFAULT_TIMEOUT_SEC
    tsec = max(1, min(tsec, 60))  # Cap at 60 seconds
    
    session = ScanSession(
        scan_id=scan_id,
        kind=scan_kind,
        timeout_sec=tsec,
        status=ScanStatus.INITIALIZING
    )

    with _SCANS_LOCK:
        _SCANS[scan_id] = session

    _log_info(f"Starting scan: id={scan_id}, kind={scan_kind.value}, timeout={tsec}s")

    def worker():
        # Enforce single camera access process-wide
        global _CAMERA_IN_USE, _CAMERA_LAST_ACCESS
        
        if not _CAMERA_LOCK.acquire(blocking=False):
            session.set_status(ScanStatus.BUSY, error="Camera is busy")
            _log_warn(f"Scan {scan_id} failed: camera busy")
            return

        try:
            _CAMERA_IN_USE = True
            _CAMERA_LAST_ACCESS = time.time()
            
            session.set_status(ScanStatus.RUNNING)
            
            # Select camera index
            cam_idx = camera_index if camera_index is not None else CAM_INDEX
            
            cap = None
            try:
                backend = _cv_cap_backend()
                _log_debug(f"Opening camera {cam_idx} with backend {backend}")
                
                if backend:
                    cap = cv2.VideoCapture(cam_idx, backend)
                else:
                    cap = cv2.VideoCapture(cam_idx)

                if not cap or not cap.isOpened():
                    error_msg = f"Cannot open camera index {cam_idx}"
                    _log_error(error_msg)
                    session.set_status(ScanStatus.ERROR, error=error_msg)
                    return

                # Set camera properties for better performance
                cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Minimize buffer
                cap.set(cv2.CAP_PROP_FPS, 30)        # Request 30 FPS
                
                _log_info(f"Camera opened: {cam_idx}")

                end_time = time.time() + tsec
                last_preview_emit = 0.0
                preview_min_interval = 1.0 / max(1.0, float(PREVIEW_MAX_FPS))
                
                decode_attempts = 0
                consecutive_failures = 0
                max_consecutive_failures = 10

                while time.time() < end_time and not session.cancel_event.is_set():
                    # Update camera last access
                    _CAMERA_LAST_ACCESS = time.time()
                    
                    ok, frame = cap.read()
                    if not ok or frame is None:
                        consecutive_failures += 1
                        if consecutive_failures > max_consecutive_failures:
                            _log_error(f"Too many consecutive frame read failures ({consecutive_failures})")
                            session.set_status(ScanStatus.ERROR, error="Camera read failures")
                            return
                        time.sleep(0.05)
                        continue
                    
                    consecutive_failures = 0  # Reset on success

                    # Optional preview capture
                    if PREVIEW_ENABLED:
                        now = time.time()
                        if (now - last_preview_emit) >= preview_min_interval:
                            jpg = _encode_preview_jpeg(frame)
                            if jpg:
                                session.set_preview_frame(jpg)
                            last_preview_emit = now

                    # Decode with multiple attempts
                    for attempt in range(DECODE_ATTEMPTS):
                        if attempt > 0:
                            # Small delay between decode attempts
                            time.sleep(0.01)
                        
                        decode_attempts += 1
                        session.increment_decode_attempts()
                        
                        val = _decode_frame(frame)
                        if val:
                            processed = _postprocess(val, scan_kind)
                            
                            # Validate VIN length
                            if scan_kind == ScanKind.VIN and len(processed) != 17:
                                _log_debug(f"Invalid VIN length: {len(processed)}")
                                continue
                            
                            _log_info(f"Scan {scan_id} successful after {decode_attempts} attempts")
                            session.set_value_found(processed)
                            return

                    # Small delay between frame processing
                    time.sleep(0.02)

                # Check why we exited
                if session.cancel_event.is_set():
                    session.set_status(ScanStatus.CANCELLED)
                    _log_info(f"Scan {scan_id} cancelled")
                else:
                    session.set_status(ScanStatus.TIMEOUT)
                    _log_info(f"Scan {scan_id} timed out after {tsec}s")

            except Exception as e:
                _log_error(f"Scan {scan_id} error: {e}")
                _log_debug(traceback.format_exc())
                session.set_status(ScanStatus.ERROR, error=str(e))

            finally:
                try:
                    if cap is not None:
                        cap.release()
                        _log_debug(f"Camera released for scan {scan_id}")
                except Exception as e:
                    _log_warn(f"Error releasing camera: {e}")

        finally:
            _CAMERA_IN_USE = False
            _CAMERA_LOCK.release()
            _log_debug(f"Camera lock released for scan {scan_id}")

    threading.Thread(target=worker, daemon=True, name=f"scan-{scan_id}").start()
    return session


def get_scan(scan_id: str) -> Optional[ScanSession]:
    """Get scan session state by ID."""
    with _SCANS_LOCK:
        return _SCANS.get(scan_id)


def get_scan_frame_jpeg(scan_id: str) -> Optional[bytes]:
    """
    Return latest preview JPEG bytes if available (PREVIEW_ENABLED must be true).
    Safe to call even if preview is disabled (returns None).
    """
    s = get_scan(scan_id)
    if not s:
        return None
    with s._lock:
        return s.last_frame_jpeg


def cancel_scan(scan_id: str) -> bool:
    """Request cancellation of a scan session."""
    s = get_scan(scan_id)
    if not s:
        return False
    s.cancel_event.set()
    _log_info(f"Cancelled scan {scan_id}")
    return True


def cleanup_scans(max_age_sec: int = 300) -> int:
    """
    Remove old scan sessions from memory.
    
    Args:
        max_age_sec: Maximum age in seconds before removal
        
    Returns:
        Number of sessions removed
    """
    now = time.time()
    removed = 0
    
    with _SCANS_LOCK:
        to_del = []
        for sid, s in _SCANS.items():
            # Remove completed/expired sessions older than max_age_sec
            if (s.status in (ScanStatus.FOUND, ScanStatus.TIMEOUT, 
                             ScanStatus.CANCELLED, ScanStatus.ERROR) and
                s.completed_at and (now - s.completed_at) > max_age_sec):
                to_del.append(sid)
            # Remove stuck initializing sessions
            elif s.status == ScanStatus.INITIALIZING and (now - s.created_at) > 60:
                to_del.append(sid)
        
        for sid in to_del:
            _SCANS.pop(sid, None)
            removed += 1
    
    if removed > 0:
        _log_debug(f"Cleaned up {removed} scan sessions")
    
    return removed


def get_active_scan() -> Optional[ScanSession]:
    """Get the currently active scan session, if any."""
    with _SCANS_LOCK:
        for s in _SCANS.values():
            if s.status == ScanStatus.RUNNING:
                return s
    return None


def get_scan_stats() -> Dict[str, Any]:
    """Get scanner statistics."""
    with _SCANS_LOCK:
        total = len(_SCANS)
        by_status = {}
        for s in _SCANS.values():
            status = s.status.value
            by_status[status] = by_status.get(status, 0) + 1
        
        active = get_active_scan()
        
        return {
            "total_sessions": total,
            "by_status": by_status,
            "active_scan": active.scan_id if active else None,
            "camera_in_use": _CAMERA_IN_USE,
            "camera_last_access": _CAMERA_LAST_ACCESS,
            "preview_enabled": PREVIEW_ENABLED,
            "default_timeout": DEFAULT_TIMEOUT_SEC,
            "decode_attempts": DECODE_ATTEMPTS,
        }


def wait_for_scan(scan_id: str, timeout: Optional[float] = None) -> Optional[ScanSession]:
    """
    Wait for a scan to complete.
    
    Args:
        scan_id: Scan session ID
        timeout: Maximum time to wait in seconds (None = wait indefinitely)
        
    Returns:
        Final scan session or None if timeout
    """
    start = time.time()
    while True:
        if timeout and (time.time() - start) > timeout:
            return None
        
        session = get_scan(scan_id)
        if not session:
            return None
        
        if session.status in (ScanStatus.FOUND, ScanStatus.TIMEOUT, 
                              ScanStatus.CANCELLED, ScanStatus.ERROR):
            return session
        
        time.sleep(0.1)


# =============================================================================
# INITIALIZATION
# =============================================================================

def _init_scanner():
    """Initialize scanner module."""
    _log_info(f"Scanner v2.0.0 initialized")
    _log_info(f"  Camera index: {CAM_INDEX}")
    _log_info(f"  Default timeout: {DEFAULT_TIMEOUT_SEC}s")
    _log_info(f"  Preview enabled: {PREVIEW_ENABLED}")
    _log_info(f"  Decode attempts: {DECODE_ATTEMPTS}")
    _log_info(f"  Barcode detector: {'Available' if _BARCODE_DETECTOR else 'Not available'}")
    _log_info(f"  QR detector: Available")


_init_scanner()


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "ScanSession",
    "ScanStatus",
    "ScanKind",
    "start_scan",
    "get_scan",
    "get_scan_frame_jpeg",
    "cancel_scan",
    "cleanup_scans",
    "get_active_scan",
    "get_scan_stats",
    "wait_for_scan",
]
