import os
import sys
import time
import threading
import json
from datetime import datetime
import cv2
import yaml
from flask import Flask, Response, jsonify
from flask_cors import CORS

from detection import DistractionDetector
from eye_tracking import EyeTracker
from alerts import AlertManager
from contacts import ContactManager
from driver_profile import DriverProfileManager

app = Flask(__name__)
CORS(app)

# Global states
global_frame = None
global_telemetry = None
lock = threading.Lock()

def load_config(config_path: str = "config.yaml"):
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def run_dms():
    global global_frame, global_telemetry
    
    config = load_config("config.yaml")
    cam_cfg = config.get("camera", {})
    yolo_cfg = config.get("yolo", {})
    eye_cfg = config.get("eye_tracking", {})
    alert_cfg = config.get("alerts", {})
    db_cfg = config.get("database", {})

    contact_mgr = ContactManager(db_path=db_cfg.get("db_path", "contacts.db"))
    profile_mgr = DriverProfileManager()
    alert_mgr = AlertManager(
        log_file=alert_cfg.get("log_file", "events.log"),
        critical_duration_seconds=alert_cfg.get("critical_duration_seconds", 5.0),
        sms_cooldown_seconds=alert_cfg.get("sms_cooldown_seconds", 60.0),
        contact_manager=contact_mgr,
        sound_beep=alert_cfg.get("sound_beep", True),
    )

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
        return

    eye_tracker = EyeTracker(
        ear_threshold=eye_cfg.get("ear_threshold", 0.25),
        ear_consecutive_frames=eye_cfg.get("ear_consecutive_frames", 20),
        mar_threshold=eye_cfg.get("mar_threshold", 0.55),
        mar_consecutive_frames=eye_cfg.get("mar_consecutive_frames", 15),
        draw_landmarks=eye_cfg.get("draw_landmarks", True),
    )

    cap = cv2.VideoCapture(cam_cfg.get("device_index", 0))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, cam_cfg.get("width", 1280))
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, cam_cfg.get("height", 720))

    smoking_frame_count = 0
    smoking_start_time = None
    session_started_at = datetime.now()

    while True:
        ret, frame = cap.read()
        if not ret or frame is None:
            time.sleep(0.05)
            continue

        clean_frame = frame.copy()
        now = time.time()

        detection_res = detector.process(frame)
        eye_res = eye_tracker.process(frame)

        # Phone logic
        phone_conf = 0.0
        phone_detected = False
        for obj in detection_res.get("detected_objects", []):
            if obj.get("class", "").lower() == "phone":
                phone_detected = obj.get("is_warning", False)
                phone_conf = max(phone_conf, obj.get("confidence", 0.0) * 100)

        alert_mgr.update_state(
            drowsy_warning=eye_res.get("drowsy_warning", False),
            drowsy_duration=eye_res.get("drowsy_duration", 0.0),
            distraction_warning=eye_res.get("distraction_warning", False),
            distraction_duration=eye_res.get("distraction_duration", 0.0),
            behavior_warnings=detection_res.get("active_warnings", {}),
            yawning_warning=eye_res.get("yawning_warning", False),
            yawn_duration=eye_res.get("yawn_duration", 0.0),
            mask_warning=eye_res.get("mask_warning", False),
            mask_duration=eye_res.get("mask_duration", 0.0),
            smoking_warning=False,
            smoking_duration=0.0,
            microsleep_warning=eye_res.get("micro_sleep_warning", False),
            hypnosis_warning=eye_res.get("hypnosis_warning", False),
            stress_warning=eye_res.get("is_stressed", False),
        )

        alert_summary = alert_mgr.get_status_summary()
        
        # Calculate risk score (simple mock logic for real values)
        risk_score = 10
        status = "SAFE"
        if alert_summary.get("critical_count", 0) > 0:
            risk_score = 90
            status = "CRITICAL"
        elif alert_summary.get("alert_count", 0) > 0:
            risk_score = 65
            status = "HIGH_RISK"
        elif phone_detected or eye_res.get("yawning_warning", False):
            risk_score = 45
            status = "ATTENTION"

        pitch, yaw, roll = eye_res.get("head_pose", (0.0, 0.0, 0.0))

        telemetry = {
            "mode": "live",
            "connection": "connected",
            "timestamp": datetime.now().isoformat(),
            "driver": {"id": profile_mgr.current_driver_id or "UNKNOWN", "name": profile_mgr.current_driver_id or "Guest"},
            "session": {
                "id": "LIVE-01",
                "startedAt": session_started_at.isoformat(),
                "elapsedSec": int((datetime.now() - session_started_at).total_seconds())
            },
            "risk": {
                "score": risk_score,
                "status": status,
                "trend": "stable",
                "delta": 0,
                "contributors": [],
                "topContributor": "Distraction" if phone_detected else "Drowsiness" if eye_res.get("drowsy_warning") else None
            },
            "detections": {
                "eyeClosure": eye_res.get("drowsy_warning", False),
                "yawning": eye_res.get("yawning_warning", False),
                "headInstability": abs(yaw) > 30 or abs(pitch) > 30,
                "phoneDetected": phone_detected,
                "seatbelt": "not_monitored",
                "metrics": {
                    "ear": eye_res.get("ear", 0.0),
                    "mar": eye_res.get("mar", 0.0),
                    "yawDeg": yaw,
                    "pitchDeg": pitch,
                    "phoneConfidence": phone_conf if phone_conf > 0 else None,
                }
            },
            "warning": {"level": status, "title": "Alert", "message": alert_summary.get("active_alerts", [""])[0]} if alert_summary.get("active_alerts") else None,
            "newEvents": [] # Simplified for live
        }

        with lock:
            global_frame = frame.copy()
            global_telemetry = telemetry

    cap.release()

def generate_frames():
    # Wait for the first frame to be ready before starting the stream
    while True:
        with lock:
            frame = None
            if global_frame is not None:
                frame = global_frame.copy()
                
        if frame is None:
            time.sleep(0.1)
            continue
        
        ret, buffer = cv2.imencode('.jpg', frame)
        if not ret:
            time.sleep(0.1)
            continue
        
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
        time.sleep(0.03)

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/telemetry')
def get_telemetry():
    with lock:
        if global_telemetry is None:
            return jsonify({"status": "starting"})
        return jsonify(global_telemetry)

if __name__ == '__main__':
    t = threading.Thread(target=run_dms, daemon=True)
    t.start()
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
