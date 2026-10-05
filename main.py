"""
Driver Monitoring System (DMS) - Main Entry Point.
Integrates:
  1. Distracted Driving Detection (Ultralytics YOLOv8: phone, cigarette, drink, mask)
  2. Drowsiness (EAR), Gaze Distraction, Yawning (MAR), and Face Covering (MediaPipe Face Mesh)
  3. Emergency Contact & Twilio SMS Alert System
  4. Real-time OpenCV HUD Overlay and User Interface
"""

import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
import cv2
import numpy as np
import yaml

from detection import DistractionDetector
from eye_tracking import EyeTracker
from alerts import AlertManager
from contacts import ContactManager, interactive_prompt_add
from driver_profile import DriverProfileManager


def load_config(config_path: str = "config.yaml") -> Dict[str, Any]:
    """Load configuration YAML file."""
    path = Path(config_path)
    if not path.exists():
        print(f"[ERROR] Configuration file '{config_path}' not found.", file=sys.stderr)
        sys.exit(1)

    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def draw_overlay(
    frame: np.ndarray,
    fps: float,
    eye_data: Dict[str, Any],
    detection_data: Dict[str, Any],
    alert_summary: Dict[str, Any],
    toast_message: str,
    toast_expiry: float,
) -> None:
    """
    Renders an on-screen HUD overlay with live telemetry, alerts, and instructions.
    """
    img_h, img_w = frame.shape[:2]
    now = time.time()

    # 1. Semi-transparent telemetry panel (top-left)
    panel_w = 380
    panel_h = 280
    overlay = frame.copy()
    cv2.rectangle(overlay, (10, 10), (10 + panel_w, 10 + panel_h), (20, 20, 25), -1)
    alpha = 0.75
    cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)
    cv2.rectangle(frame, (10, 10), (10 + panel_w, 10 + panel_h), (80, 80, 80), 1)

    # Header in panel
    cv2.putText(
        frame,
        "DRIVER MONITORING SYSTEM",
        (20, 32),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (0, 255, 200),
        2,
        cv2.LINE_AA,
    )
    cv2.putText(
        frame,
        f"FPS: {fps:.1f}",
        (panel_w - 70, 32),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.45,
        (200, 200, 200),
        1,
        cv2.LINE_AA,
    )

    y_offset = 56
    line_spacing = 21

    # ---------------- FACE DETECTION STATUS ----------------
    face_detected = eye_data.get("face_detected", False)
    face_str = "DETECTED" if face_detected else "NO FACE DETECTED"
    face_col = (0, 255, 0) if face_detected else (0, 165, 255)
    cv2.putText(frame, f"Face: {face_str}", (20, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.44, face_col, 1, cv2.LINE_AA)
    y_offset += line_spacing

    # EAR Status (Drowsiness Alert)
    ear = eye_data.get("ear", 0.0)
    perclos = eye_data.get("perclos", 0.0)
    drowsy_warn = eye_data.get("drowsy_warning", False)
    micro_sleep = eye_data.get("micro_sleep_warning", False)
    ear_color = (0, 0, 255) if drowsy_warn or micro_sleep else (0, 255, 128)
    ear_str = f"EAR (Eyes): {ear:.3f} | PERCLOS: {perclos:.1%}"
    cv2.putText(frame, ear_str, (20, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.44, ear_color, 1, cv2.LINE_AA)
    y_offset += line_spacing

    # Gaze Direction
    gaze = eye_data.get("gaze", "unknown").upper()
    distracted_warn = eye_data.get("distraction_warning", False)
    gaze_duration = eye_data.get("distraction_duration", 0.0)
    gaze_col = (0, 0, 255) if distracted_warn else ((0, 255, 255) if gaze != "CENTER" else (0, 255, 128))
    gaze_tag = f" ({gaze_duration:.1f}s)" if gaze_duration > 0.2 else ""
    gaze_str = f"Gaze: {gaze}{gaze_tag}"
    cv2.putText(frame, gaze_str, (20, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.44, gaze_col, 1, cv2.LINE_AA)
    y_offset += line_spacing

    # MAR Status (Yawning Alert)
    mar = eye_data.get("mar", 0.0)
    is_yawning = eye_data.get("yawning_warning", False)
    yawns_total = eye_data.get("total_yawns", 0)
    yawn_dur = eye_data.get("yawn_duration", 0.0)
    mar_col = (0, 0, 255) if is_yawning else (0, 255, 128)
    yawn_tag = f" [YAWNING ALERT {yawn_dur:.1f}s]" if is_yawning else f" [Yawns: {yawns_total}]"
    mar_str = f"MAR (Mouth): {mar:.3f}{yawn_tag}"
    cv2.putText(frame, mar_str, (20, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.44, mar_col, 1, cv2.LINE_AA)
    y_offset += line_spacing

    # Face Covering / Mask Status & Alert
    is_masked = eye_data.get("mask_detected", False)
    mask_warn = eye_data.get("mask_warning", False)
    mask_conf = eye_data.get("mask_confidence", 0.0)
    mask_col = (0, 0, 255) if mask_warn else ((235, 206, 135) if is_masked else (180, 180, 180))
    mask_tag = " [COVER ALERT]" if mask_warn else ""
    mask_str = f"Face Cover: {'DETECTED (' + f'{mask_conf:.0%}' + ')' + mask_tag if is_masked else 'NONE'}"
    cv2.putText(frame, mask_str, (20, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.44, mask_col, 1, cv2.LINE_AA)
    y_offset += line_spacing

    # YOLO Distraction Status
    consec = detection_data.get("consecutive_counts", {})
    yolo_str = f"Objects: Phone={consec.get('phone', 0)} Crt={consec.get('cigarette', 0)} Drk={consec.get('drink', 0)}"
    cv2.putText(frame, yolo_str, (20, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (200, 200, 200), 1, cv2.LINE_AA)
    y_offset += line_spacing
    
    # Advanced: Stress & Head Pose
    stress = eye_data.get("is_stressed", False)
    pitch, yaw, roll = eye_data.get("head_pose", (0.0, 0.0, 0.0))
    head_str = f"Head: P:{pitch:.0f} Y:{yaw:.0f} R:{roll:.0f} | {'[HIGH STRESS]' if stress else '[CALM]'}"
    cv2.putText(frame, head_str, (20, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.44, (0, 0, 255) if stress else (0, 255, 128), 1, cv2.LINE_AA)
    y_offset += line_spacing

    # Active Alerts & Critical SMS
    num_alerts = alert_summary.get("alert_count", 0)
    num_crit = alert_summary.get("critical_count", 0)
    alert_color = (0, 0, 255) if num_alerts > 0 else (0, 255, 0)
    alert_text = f"Alerts: {num_alerts} Active | Critical: {num_crit}"
    cv2.putText(frame, alert_text, (20, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.44, alert_color, 1, cv2.LINE_AA)
    y_offset += line_spacing

    # SMS Dispatch status
    sms_count = alert_summary.get("sms_sent_total", 0)
    twilio_ready = alert_summary.get("twilio_configured", False)
    twilio_info = f"SMS Sent: {sms_count} (Twilio {'Ready' if twilio_ready else 'Local'})"
    cv2.putText(frame, twilio_info, (20, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.40, (180, 180, 180), 1, cv2.LINE_AA)

    # 2. Prominent Emergency Alert Banners (Top Center)
    active_alerts_list = alert_summary.get("active_alerts", [])
    critical_alerts_list = alert_summary.get("critical_alerts", [])

    if critical_alerts_list:
        banner_color = (0, 0, 220) if int(now * 3) % 2 == 0 else (0, 0, 150)
        banner_w = 700
        banner_h = 50
        bx = (img_w - banner_w) // 2
        by = 20
        cv2.rectangle(frame, (bx, by), (bx + banner_w, by + banner_h), banner_color, -1)
        cv2.rectangle(frame, (bx, by), (bx + banner_w, by + banner_h), (255, 255, 255), 2)
        crit_msg = f"CRITICAL: {critical_alerts_list[0]} - SMS SENT"
        cv2.putText(frame, crit_msg, (bx + 15, by + 33), cv2.FONT_HERSHEY_SIMPLEX, 0.60, (255, 255, 255), 2, cv2.LINE_AA)

    elif active_alerts_list:
        banner_w = 640
        banner_h = 44
        bx = (img_w - banner_w) // 2
        by = 20
        cv2.rectangle(frame, (bx, by), (bx + banner_w, by + banner_h), (0, 69, 255), -1)
        cv2.rectangle(frame, (bx, by), (bx + banner_w, by + banner_h), (255, 255, 255), 1)
        warn_msg = f"WARNING: {active_alerts_list[0]}"
        cv2.putText(frame, warn_msg, (bx + 16, by + 30), cv2.FONT_HERSHEY_SIMPLEX, 0.58, (255, 255, 255), 2, cv2.LINE_AA)

    # 3. Bottom Control Navigation Bar
    bar_h = 32
    bar_overlay = frame.copy()
    cv2.rectangle(bar_overlay, (0, img_h - bar_h), (img_w, img_h), (15, 15, 15), -1)
    cv2.addWeighted(bar_overlay, 0.8, frame, 0.2, 0, frame)

    nav_text = "[Q] Quit | [S] Snap | [C] Contact | [F] False Alarm | [T] True Pos"
    cv2.putText(
        frame,
        nav_text,
        (15, img_h - 10),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.45,
        (220, 220, 220),
        1,
        cv2.LINE_AA,
    )

    # 4. Toast Message
    if toast_message and now < toast_expiry:
        (tw, th), _ = cv2.getTextSize(toast_message, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 1)
        tx = (img_w - tw) // 2
        ty = img_h - 48
        cv2.rectangle(frame, (tx - 12, ty - th - 8), (tx + tw + 12, ty + 8), (0, 180, 0), -1)
        cv2.putText(frame, toast_message, (tx, ty), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1, cv2.LINE_AA)


def run() -> None:
    """Main execution loop for the Driver Monitoring System."""
    print("\n" + "=" * 65)
    print("      DRIVER MONITORING SYSTEM (DMS) - INITIALIZING")
    print("=" * 65)

    # 1. Load configuration
    config = load_config("config.yaml")

    cam_cfg = config.get("camera", {})
    yolo_cfg = config.get("yolo", {})
    eye_cfg = config.get("eye_tracking", {})
    alert_cfg = config.get("alerts", {})
    db_cfg = config.get("database", {})
    storage_cfg = config.get("storage", {})

    # Create snapshots directory
    snapshots_dir = Path(storage_cfg.get("snapshots_dir", "snapshots"))
    snapshots_dir.mkdir(parents=True, exist_ok=True)

    dataset_img_dir = Path("dataset/images/train")
    dataset_lbl_dir = Path("dataset/labels/train")
    dataset_img_dir.mkdir(parents=True, exist_ok=True)
    dataset_lbl_dir.mkdir(parents=True, exist_ok=True)
    class_map = {"phone": 0, "cigarette": 1, "drink": 2}

    # 2. Initialize Contact Manager
    contact_mgr = ContactManager(db_path=db_cfg.get("db_path", "contacts.db"))
    print(f"[INIT] Loaded {contact_mgr.get_contact_count()} registered emergency contact(s).")
    
    # 2.5 Initialize Driver Profile Manager
    profile_mgr = DriverProfileManager()

    # 3. Initialize Alert Manager
    alert_mgr = AlertManager(
        log_file=alert_cfg.get("log_file", "events.log"),
        critical_duration_seconds=alert_cfg.get("critical_duration_seconds", 5.0),
        sms_cooldown_seconds=alert_cfg.get("sms_cooldown_seconds", 60.0),
        contact_manager=contact_mgr,
        sound_beep=alert_cfg.get("sound_beep", True),
    )

    # 4. Initialize YOLO Distraction Detector
    try:
        detector = DistractionDetector(
            model_path=yolo_cfg.get("model_path", "runs/detect/train/weights/best.pt"),
            confidence_threshold=yolo_cfg.get("confidence_threshold", 0.6),
            consecutive_frames_threshold=yolo_cfg.get("consecutive_frames_threshold", 3),
            target_classes=yolo_cfg.get("target_classes", ["phone", "cigarette", "drink", "mask"]),
            allow_fallback_to_coco=yolo_cfg.get("allow_fallback_to_coco", True),
            fallback_model_path=yolo_cfg.get("fallback_model_path", "yolov8n.pt"),
        )
    except FileNotFoundError as e:
        print(f"[CRITICAL ERROR] {e}", file=sys.stderr)
        sys.exit(1)

    # 5. Initialize MediaPipe Eye, Mouth, and Face Covering Tracker
    eye_tracker = EyeTracker(
        ear_threshold=eye_cfg.get("ear_threshold", 0.25),
        ear_consecutive_frames=eye_cfg.get("ear_consecutive_frames", 20),
        gaze_distraction_seconds=eye_cfg.get("gaze_distraction_seconds", 2.0),
        gaze_horizontal_left_thresh=eye_cfg.get("gaze_horizontal_left_threshold", 0.38),
        gaze_horizontal_right_thresh=eye_cfg.get("gaze_horizontal_right_threshold", 0.62),
        gaze_vertical_up_thresh=eye_cfg.get("gaze_vertical_up_threshold", 0.35),
        gaze_vertical_down_thresh=eye_cfg.get("gaze_vertical_down_threshold", 0.65),
        mar_threshold=eye_cfg.get("mar_threshold", 0.55),
        mar_consecutive_frames=eye_cfg.get("mar_consecutive_frames", 15),
        yawn_alert_hold_seconds=eye_cfg.get("yawn_alert_hold_seconds", 3.0),
        face_cover_enabled=eye_cfg.get("face_cover_enabled", True),
        face_cover_confidence_threshold=eye_cfg.get("face_cover_confidence_threshold", 0.55),
        face_cover_consecutive_frames=eye_cfg.get("face_cover_consecutive_frames", 10),
        face_cover_trigger_alert=eye_cfg.get("face_cover_trigger_alert", True),
        draw_landmarks=eye_cfg.get("draw_landmarks", True),
    )

    # 6. Initialize Video Capture
    dev_index = cam_cfg.get("device_index", 0)
    print(f"[INIT] Opening camera at device index {dev_index}...")
    cap = cv2.VideoCapture(dev_index)

    if not cap.isOpened():
        print(
            f"\n[CAMERA ERROR] Could not open video device at index {dev_index}.\n"
            f"Please verify:\n"
            f"  1. A webcam is connected to your computer.\n"
            f"  2. Camera permissions are granted to Python/terminal.\n"
            f"  3. If using an external camera, try changing 'device_index' in config.yaml.\n",
            file=sys.stderr,
        )
        sys.exit(1)

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, cam_cfg.get("width", 1280))
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, cam_cfg.get("height", 720))

    window_name = "Driver Monitoring System (DMS)"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)

    print("\n" + "=" * 65)
    print(" [READY] DMS is running with YAWNING & FACE COVER alerts active!")
    print(" Press 'q' to quit, 's' for snapshot, 'c' to add emergency contact.")
    print("=" * 65 + "\n")

    prev_time = time.time()
    fps = 30.0
    toast_message = ""
    toast_expiry = 0.0
    smoking_frame_count = 0
    smoking_start_time = None

    try:
        while True:
            ret, frame = cap.read()
            if not ret or frame is None:
                print("[WARNING] Empty frame received from camera. Retrying...", file=sys.stderr)
                time.sleep(0.05)
                continue

            clean_frame = frame.copy()

            current_time = time.time()
            dt = current_time - prev_time
            if dt > 0:
                fps = 0.9 * fps + 0.1 * (1.0 / dt)
            prev_time = current_time

            # 1. Run YOLO Object Detection (phone, cigarette, drink, mask)
            detection_res = detector.process(frame)

            # 2. Run MediaPipe Face Mesh (Eyes, Gaze, Yawning, Face Cover)
            eye_res = eye_tracker.process(frame)
            
            # Active Driver Identification & Calibration
            if eye_res.get("face_detected"):
                if profile_mgr.current_driver_id is None:
                    driver_id = profile_mgr.identify_driver(clean_frame, face_bbox=eye_res.get("face_bbox"))
                    if driver_id:
                        thresh = profile_mgr.get_current_thresholds()
                        if thresh:
                            eye_tracker.ear_threshold = thresh["ear_threshold"]
                            eye_tracker.mar_threshold = thresh["mar_threshold"]
                            toast_message = f"Welcome {driver_id}! Profile loaded."
                            toast_expiry = time.time() + 4.0
                elif profile_mgr.is_calibrating:
                    profile_mgr.update_calibration(eye_res.get("ear", 0.0), eye_res.get("mar", 0.0))
                    toast_message = f"Calibrating {profile_mgr.current_driver_id}... Please drive normally."
                    toast_expiry = time.time() + 0.1
                    if not profile_mgr.is_calibrating:
                        thresh = profile_mgr.get_current_thresholds()
                        eye_tracker.ear_threshold = thresh["ear_threshold"]
                        eye_tracker.mar_threshold = thresh["mar_threshold"]
                        toast_message = "Calibration Complete!"
                        toast_expiry = time.time() + 3.0

            now = time.time()
            mouth_center = eye_res.get("mouth_center")
            cigarette_near_mouth = False

            if eye_res.get("face_detected") and mouth_center:
                for obj in detection_res.get("detected_objects", []):
                    if obj.get("class", "").lower() != "cigarette":
                        continue

                    x1, y1, x2, y2 = obj.get("box", (0, 0, 0, 0))
                    c_x = (x1 + x2) / 2.0
                    c_y = (y1 + y2) / 2.0
                    mouth_x, mouth_y = mouth_center
                    mouth_radius_x = max(90.0, abs(x2 - x1) * 1.8)
                    mouth_radius_y = max(70.0, abs(y2 - y1) * 1.8)

                    if abs(c_x - mouth_x) <= mouth_radius_x and abs(c_y - mouth_y) <= mouth_radius_y:
                        cigarette_near_mouth = True
                        break

            if cigarette_near_mouth:
                smoking_frame_count += 1
                if smoking_frame_count >= yolo_cfg.get("consecutive_frames_threshold", 3):
                    if smoking_start_time is None:
                        smoking_start_time = now
            else:
                smoking_frame_count = 0
                smoking_start_time = None

            smoking_warning = smoking_frame_count >= yolo_cfg.get("consecutive_frames_threshold", 3)
            smoking_duration = (now - smoking_start_time) if smoking_start_time is not None else 0.0

            # 3. Update Alert Manager state across all alert vectors
            alert_mgr.update_state(
                drowsy_warning=eye_res["drowsy_warning"],
                drowsy_duration=eye_res["drowsy_duration"],
                distraction_warning=eye_res["distraction_warning"],
                distraction_duration=eye_res["distraction_duration"],
                behavior_warnings=detection_res["active_warnings"],
                yawning_warning=eye_res["yawning_warning"],
                yawn_duration=eye_res["yawn_duration"],
                mask_warning=eye_res["mask_warning"],
                mask_duration=eye_res["mask_duration"],
                smoking_warning=smoking_warning,
                smoking_duration=smoking_duration,
                microsleep_warning=eye_res.get("micro_sleep_warning", False),
                hypnosis_warning=eye_res.get("hypnosis_warning", False),
                stress_warning=eye_res.get("is_stressed", False),
            )

            # 4. Render On-Screen HUD Overlay
            alert_summary = alert_mgr.get_status_summary()
            draw_overlay(
                frame=frame,
                fps=fps,
                eye_data=eye_res,
                detection_data=detection_res,
                alert_summary=alert_summary,
                toast_message=toast_message,
                toast_expiry=toast_expiry,
            ) 

            # 5. Display frame in window
            cv2.imshow(window_name, frame)

            # 6. Keyboard handling
            key = cv2.waitKey(1) & 0xFF

            if key == ord("q") or key == 27:
                print("[INFO] User initiated shutdown.")
                break

            elif key == ord("f") or key == ord("t"):
                timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                img_path = dataset_img_dir / f"frame_{timestamp_str}.jpg"
                lbl_path = dataset_lbl_dir / f"frame_{timestamp_str}.txt"
                
                cv2.imwrite(str(img_path), clean_frame)
                
                if key == ord("f"):
                    # False Alarm -> Background image (empty label file)
                    lbl_path.touch()
                    toast_message = "False Alarm Logged!"
                    print(f"[ACTIVE LEARNING] Saved false alarm background to: {img_path.name}")
                    
                    # Update personal thresholds if it was a drowsy or yawn alert
                    if alert_summary.get("active_alerts"):
                        active_msg = alert_summary["active_alerts"][0]
                        if "DROWSY" in active_msg or "DROWSINESS" in active_msg:
                            profile_mgr.record_false_alarm("drowsy")
                            thresh = profile_mgr.get_current_thresholds()
                            eye_tracker.ear_threshold = thresh["ear_threshold"]
                        elif "YAWNING" in active_msg or "YAWN" in active_msg:
                            profile_mgr.record_false_alarm("yawning")
                            thresh = profile_mgr.get_current_thresholds()
                            eye_tracker.mar_threshold = thresh["mar_threshold"]
                else:
                    # True Positive -> Save bounding boxes
                    h_img, w_img = clean_frame.shape[:2]
                    with open(lbl_path, "w") as f_lbl:
                        for obj in detection_res.get("detected_objects", []):
                            cls_name = obj.get("class")
                            cls_id = class_map.get(cls_name)
                            if cls_id is not None:
                                x1, y1, x2, y2 = obj.get("box")
                                cx = (x1 + x2) / 2.0 / w_img
                                cy = (y1 + y2) / 2.0 / h_img
                                bw = (x2 - x1) / w_img
                                bh = (y2 - y1) / h_img
                                f_lbl.write(f"{cls_id} {cx:.6f} {cy:.6f} {bw:.6f} {bh:.6f}\n")
                    toast_message = "True Detection Logged!"
                    print(f"[ACTIVE LEARNING] Saved true positive to: {img_path.name}")
                
                toast_expiry = time.time() + 2.0

            elif key == ord("s"):
                timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
                snap_path = snapshots_dir / f"snapshot_{timestamp_str}.jpg"
                cv2.imwrite(str(snap_path), frame)
                toast_message = f"Snapshot saved: {snap_path.name}"
                toast_expiry = time.time() + 3.0
                print(f"[SNAPSHOT] Saved image to: {snap_path.resolve()}")

            elif key == ord("c"):
                print("\n[PAUSED] Adding emergency contact in terminal...")
                new_contact = interactive_prompt_add(contact_mgr)
                if new_contact:
                    toast_message = f"Contact Added: {new_contact['name']}"
                    toast_expiry = time.time() + 3.0
                else:
                    toast_message = "Contact addition cancelled"
                    toast_expiry = time.time() + 2.0
                prev_time = time.time()

    except KeyboardInterrupt:
        print("\n[INFO] KeyboardInterrupt caught. Terminating DMS...")
    finally:
        cap.release()
        cv2.destroyAllWindows()
        eye_tracker.close()
        print("[CLEANUP] Camera released and windows destroyed. DMS terminated cleanly.\n")


def main():
    run()


if __name__ == "__main__":
    main()
