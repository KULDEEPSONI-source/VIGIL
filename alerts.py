"""
Alert and Notification System for Driver Monitoring System (DMS).
Handles event logging to file, audio alerts, and Twilio SMS dispatch
to registered emergency contacts when critical events persist > 5 seconds.
Supports:
  - Drowsiness (EAR)
  - Gaze Distraction (Iris)
  - Yawning / Fatigue (MAR)
  - Face Covering / Mask (Face Occlusion)
  - Smoking (Cigarette sustained near mouth)
  - Distracted Driving Behaviors (YOLO)
"""

import os
import sys
import time
import logging
import threading
from datetime import datetime
from typing import List, Dict, Optional

# Attempt import of Twilio
try:
    from twilio.rest import Client as TwilioClient
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False

from contacts import ContactManager


class AlertManager:
    """
    Coordinates logging, visual/audio alerts, and SMS notifications.
    """

    def __init__(
        self,
        log_file: str = "events.log",
        critical_duration_seconds: float = 5.0,
        sms_cooldown_seconds: float = 60.0,
        contact_manager: Optional[ContactManager] = None,
        sound_beep: bool = True,
    ):
        self.log_file = log_file
        self.critical_duration_seconds = critical_duration_seconds
        self.sms_cooldown_seconds = sms_cooldown_seconds
        self.contact_manager = contact_manager or ContactManager()
        self.sound_beep = sound_beep

        self.last_sms_time: float = 0.0
        self.active_alerts: List[str] = []
        self.critical_alerts: List[str] = []
        self.total_alerts_count: int = 0
        self.sms_dispatched_count: int = 0
        self.last_beep_time: float = 0.0

        # Twilio credentials
        self.account_sid = os.environ.get("TWILIO_ACCOUNT_SID", "").strip()
        self.auth_token = os.environ.get("TWILIO_AUTH_TOKEN", "").strip()
        self.from_phone = os.environ.get("TWILIO_PHONE_NUMBER", "").strip()

        self._twilio_client = None
        self._init_twilio()
        self._init_logger()

    def _init_logger(self) -> None:
        """Initialize events file logger."""
        self.logger = logging.getLogger("DMS_Alerts")
        self.logger.setLevel(logging.INFO)

        # File handler
        file_handler = logging.FileHandler(self.log_file, encoding="utf-8")
        file_handler.setLevel(logging.INFO)
        formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(formatter)

        if not self.logger.handlers:
            self.logger.addHandler(file_handler)

    def _init_twilio(self) -> None:
        """Initialize Twilio client or report fallback status."""
        if not TWILIO_AVAILABLE:
            print(
                "[ALERTS] Twilio package not installed. SMS notifications will be simulated."
            )
            return

        if self.account_sid and self.auth_token and self.from_phone:
            try:
                self._twilio_client = TwilioClient(self.account_sid, self.auth_token)
                print("[ALERTS] Twilio client initialized successfully.")
            except Exception as e:
                print(f"[ALERTS WARNING] Twilio initialization failed: {e}. Falling back to logging.")
                self._twilio_client = None
        else:
            print(
                "[ALERTS] Twilio credentials not fully configured in environment variables "
                "(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER). "
                "Alerts will be logged locally to events.log and printed to console."
            )

    def log_event(self, level: str, message: str) -> None:
        """Log an event to events.log and terminal."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted = f"[{timestamp}] [{level.upper()}] {message}"
        print(formatted)

        if level.upper() == "CRITICAL":
            self.logger.critical(message)
        elif level.upper() == "WARNING":
            self.logger.warning(message)
        else:
            self.logger.info(message)

    def trigger_beep(self) -> None:
        """Play a non-blocking alert beep sound."""
        if not self.sound_beep:
            return

        now = time.time()
        if now - self.last_beep_time < 0.6:
            return
        self.last_beep_time = now

        def _play():
            try:
                if sys.platform == "win32":
                    import winsound
                    winsound.Beep(1200, 250)
                else:
                    sys.stdout.write("\a")
                    sys.stdout.flush()
            except Exception:
                pass

        threading.Thread(target=_play, daemon=True).start()

    def update_state(
        self,
        drowsy_warning: bool,
        drowsy_duration: float,
        distraction_warning: bool,
        distraction_duration: float,
        behavior_warnings: Dict[str, float],
        yawning_warning: bool = False,
        yawn_duration: float = 0.0,
        mask_warning: bool = False,
        mask_duration: float = 0.0,
        smoking_warning: bool = False,
        smoking_duration: float = 0.0,
        microsleep_warning: bool = False,
        hypnosis_warning: bool = False,
        stress_warning: bool = False,
    ) -> None:
        """
        Update the current alert state across all DMS safety vectors:
        - Drowsiness (EAR)
        - Gaze Distraction
        - Yawning (MAR)
        - Face Covering / Mask
        - Smoking (Cigarette sustained near mouth region)
        - Object Distractions (YOLO: phone, cigarette, drink, etc.)
        """
        current_warnings: List[str] = []
        current_criticals: List[str] = []

        # 1. Drowsiness (EAR)
        if drowsy_warning:
            msg = f"DROWSINESS ALERT ({drowsy_duration:.1f}s)"
            current_warnings.append(msg)
            if drowsy_duration >= self.critical_duration_seconds:
                current_criticals.append(f"CRITICAL DROWSINESS ({drowsy_duration:.1f}s)")

        # 2. Gaze Distraction (Iris away from center)
        if distraction_warning:
            msg = f"GAZE DISTRACTION ALERT ({distraction_duration:.1f}s)"
            current_warnings.append(msg)
            if distraction_duration >= self.critical_duration_seconds:
                current_criticals.append(f"CRITICAL DISTRACTION ({distraction_duration:.1f}s)")

        # 3. Yawning Alert (MAR)
        if yawning_warning:
            msg = f"YAWNING ALERT ({yawn_duration:.1f}s)"
            current_warnings.append(msg)
            if yawn_duration >= self.critical_duration_seconds:
                current_criticals.append(f"CRITICAL FATIGUE: PERSISTENT YAWNING ({yawn_duration:.1f}s)")

        # 4. Face Covering Alert (Lower-face occlusion / Mask)
        if mask_warning:
            msg = f"FACE COVERING ALERT ({mask_duration:.1f}s)"
            current_warnings.append(msg)
            if mask_duration >= self.critical_duration_seconds:
                current_criticals.append(f"CRITICAL SAFETY: FACE COVERED / OBSTRUCTED ({mask_duration:.1f}s)")

        # 5. Smoking Alert (Cigarette detected near mouth region)
        if smoking_warning:
            msg = f"SMOKING ALERT ({smoking_duration:.1f}s)"
            current_warnings.append(msg)
            if smoking_duration >= self.critical_duration_seconds:
                current_criticals.append(f"CRITICAL BEHAVIOR: SMOKING ({smoking_duration:.1f}s)")

        # 6. YOLO Behavior Alerts (phone, drink, etc.)
        # NOTE: "cigarette" is intentionally skipped here because it is
        # handled explicitly by the SMOKING ALERT above (section 5) to
        # avoid duplicate warnings and duplicate SMS dispatches.
        for cls_name, duration in behavior_warnings.items():
            if cls_name.lower() == "cigarette":
                continue
            msg = f"BEHAVIOR ALERT: {cls_name.upper()} ({duration:.1f}s)"
            current_warnings.append(msg)
            if duration >= self.critical_duration_seconds:
                current_criticals.append(
                    f"CRITICAL BEHAVIOR: {cls_name.upper()} ({duration:.1f}s)"
                )
        
        # 7. Advanced Cognitive / Fatigue Alerts
        if microsleep_warning:
            msg = "CRITICAL ALERT: MICRO-SLEEP DETECTED"
            current_warnings.append(msg)
            current_criticals.append(msg)
            
        if hypnosis_warning:
            msg = "WARNING: HIGHWAY HYPNOSIS (No blinks > 15s)"
            current_warnings.append(msg)
            
        if stress_warning:
            msg = "WARNING: HIGH STRESS / ANGER DETECTED"
            current_warnings.append(msg)

        # Detect new warnings to log and beep
        for warn in current_warnings:
            if warn not in self.active_alerts:
                self.log_event("WARNING", warn)
                self.trigger_beep()
                self.total_alerts_count += 1

        # Detect critical alerts and dispatch SMS
        if current_criticals:
            for crit in current_criticals:
                if crit not in self.critical_alerts:
                    self.log_event("CRITICAL", crit)
                    self.trigger_beep()
            self._dispatch_critical_sms(current_criticals)

        self.active_alerts = current_warnings
        self.critical_alerts = current_criticals

    def _dispatch_critical_sms(self, critical_reasons: List[str]) -> None:
        """Send emergency SMS to all registered contacts if cooldown permits."""
        now = time.time()
        if now - self.last_sms_time < self.sms_cooldown_seconds:
            return

        contacts = self.contact_manager.get_contacts()
        if not contacts:
            self.log_event(
                "INFO",
                "Critical alert fired, but no emergency contacts are registered in contacts.db.",
            )
            self.last_sms_time = now
            return

        reasons_text = ", ".join(critical_reasons)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sms_body = (
            f"[DMS CRITICAL ALERT] Driver requires immediate attention!\n"
            f"Event: {reasons_text}\n"
            f"Timestamp: {timestamp}\n"
            f"Please verify driver safety immediately."
        )

        self.last_sms_time = now
        self.sms_dispatched_count += len(contacts)

        # Dispatch asynchronously in background thread
        def _send_thread():
            self.log_event(
                "CRITICAL",
                f"Dispatching emergency SMS to {len(contacts)} contact(s)...",
            )
            for c in contacts:
                recipient_phone = c["phone"]
                recipient_name = c["name"]
                if self._twilio_client:
                    try:
                        msg = self._twilio_client.messages.create(
                            body=sms_body,
                            from_=self.from_phone,
                            to=recipient_phone,
                        )
                        self.log_event(
                            "INFO",
                            f"SMS successfully sent to {recipient_name} ({recipient_phone}), SID: {msg.sid}",
                        )
                    except Exception as e:
                        self.log_event(
                            "ERROR",
                            f"Failed to send SMS to {recipient_name} ({recipient_phone}): {e}",
                        )
                else:
                    self.log_event(
                        "INFO",
                        f"[SIMULATED SMS] To: {recipient_name} ({recipient_phone}) | Body:\n{sms_body}",
                    )

        threading.Thread(target=_send_thread, daemon=True).start()

    def get_status_summary(self) -> Dict:
        """Return status dictionary for UI overlay display."""
        return {
            "active_alerts": self.active_alerts,
            "critical_alerts": self.critical_alerts,
            "alert_count": len(self.active_alerts),
            "critical_count": len(self.critical_alerts),
            "sms_sent_total": self.sms_dispatched_count,
            "twilio_configured": bool(self._twilio_client),
        }