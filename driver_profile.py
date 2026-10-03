import json
from pathlib import Path
from typing import Dict, List, Optional
import numpy as np
import cv2


class DriverProfileManager:
    """
    Manages personalized driver profiles.
    Stores baseline EAR/MAR, and dynamic thresholds.
    Uses OpenCV LBPH for fast, lightweight face recognition.
    """
    def __init__(self, profile_file: str = "dataset/driver_profiles.json"):
        self.profile_file = Path(profile_file)
        self.profile_file.parent.mkdir(parents=True, exist_ok=True)
        self.model_file = self.profile_file.parent / "face_model.yml"
        self.profiles: Dict[str, Dict] = {}
        self.current_driver_id: Optional[str] = None
        self.is_calibrating = False
        self.calibration_frames = 0
        self.calibration_ear_history = []
        self.calibration_mar_history = []
        
        self.recognizer = cv2.face.LBPHFaceRecognizer_create()
        self.model_trained = False
        
        self.load_profiles()

    def load_profiles(self):
        if self.profile_file.exists():
            with open(self.profile_file, "r") as f:
                self.profiles = json.load(f)
        else:
            self.profiles = {}
            
        if self.model_file.exists():
            self.recognizer.read(str(self.model_file))
            self.model_trained = True

    def save_profiles(self):
        with open(self.profile_file, "w") as f:
            json.dump(self.profiles, f, indent=4)
        if self.model_trained:
            self.recognizer.write(str(self.model_file))

    def identify_driver(self, frame: np.ndarray, face_bbox: tuple) -> Optional[str]:
        """Attempt to identify the driver from the current frame using MediaPipe bounding box."""
        if not face_bbox:
            return None
            
        x, y, w, h = face_bbox
        # Add a little padding
        img_h, img_w = frame.shape[:2]
        x1 = max(0, x - int(w*0.1))
        y1 = max(0, y - int(h*0.1))
        x2 = min(img_w, x + w + int(w*0.1))
        y2 = min(img_h, y + h + int(h*0.1))
        
        if x2 - x1 <= 0 or y2 - y1 <= 0:
            return None
            
        face_roi = frame[y1:y2, x1:x2]
        gray = cv2.cvtColor(face_roi, cv2.COLOR_BGR2GRAY)
        face_roi_resized = cv2.resize(gray, (200, 200))
        
        if self.model_trained:
            label_id, confidence = self.recognizer.predict(face_roi_resized)
            # Lower confidence is better in LBPH (distance). < 80 is a decent match.
            if confidence < 80:
                driver_str = f"Driver_{label_id}"
                if driver_str in self.profiles:
                    self.current_driver_id = driver_str
                    return driver_str

        # New driver
        new_label_id = len(self.profiles) + 1
        new_id = f"Driver_{new_label_id}"
        
        # Train model with initial face
        if self.model_trained:
            self.recognizer.update([face_roi_resized], np.array([new_label_id]))
        else:
            self.recognizer.train([face_roi_resized], np.array([new_label_id]))
            self.model_trained = True
            
        self.profiles[new_id] = {
            "name": new_id,
            "label_id": new_label_id,
            "baseline_ear": 0.30,
            "baseline_mar": 0.40,
            "ear_threshold": 0.25,
            "mar_threshold": 0.55,
            "total_drives": 1
        }
        self.current_driver_id = new_id
        self.save_profiles()
        self.start_calibration()
        return new_id

    def start_calibration(self):
        """Start gathering baseline data for the current driver."""
        self.is_calibrating = True
        self.calibration_frames = 0
        self.calibration_ear_history = []
        self.calibration_mar_history = []
        print(f"[PROFILE] Starting calibration for {self.current_driver_id}...")

    def update_calibration(self, current_ear: float, current_mar: float):
        """Collect frames for calibration."""
        if not self.is_calibrating:
            return

        self.calibration_ear_history.append(current_ear)
        self.calibration_mar_history.append(current_mar)
        self.calibration_frames += 1

        if self.calibration_frames >= 150:  # ~5 seconds of frames at 30fps
            self._finish_calibration()

    def _finish_calibration(self):
        """Finalize baselines and adjust thresholds."""
        self.is_calibrating = False
        if not self.current_driver_id or self.current_driver_id not in self.profiles:
            return

        # Calculate means, throwing out bottom/top 10% outliers
        ear_sorted = sorted(self.calibration_ear_history)
        mar_sorted = sorted(self.calibration_mar_history)
        
        clip = int(len(ear_sorted) * 0.1)
        avg_ear = np.mean(ear_sorted[clip:-clip])
        avg_mar = np.mean(mar_sorted[clip:-clip])

        # Adaptive logic:
        # Drowsy threshold is typically 80% of their normal open eye ratio
        ear_thresh = round(avg_ear * 0.8, 3)
        # Yawn threshold is typically 140% of their normal closed mouth ratio
        mar_thresh = round(avg_mar * 1.4, 3)

        profile = self.profiles[self.current_driver_id]
        profile["baseline_ear"] = round(avg_ear, 3)
        profile["baseline_mar"] = round(avg_mar, 3)
        profile["ear_threshold"] = min(0.30, max(0.18, ear_thresh))
        profile["mar_threshold"] = min(0.70, max(0.40, mar_thresh))
        
        self.save_profiles()
        print(f"[PROFILE] Calibration complete for {self.current_driver_id}.")
        print(f"   -> EAR Threshold set to: {profile['ear_threshold']}")
        print(f"   -> MAR Threshold set to: {profile['mar_threshold']}")

    def record_false_alarm(self, alert_type: str):
        """Learn from false alarms by tweaking the thresholds."""
        if not self.current_driver_id or self.current_driver_id not in self.profiles:
            return
            
        profile = self.profiles[self.current_driver_id]
        
        if alert_type == "drowsy":
            # If false alarm for drowsy, their eyes are naturally smaller than the threshold. Lower it.
            profile["ear_threshold"] = max(0.15, profile["ear_threshold"] - 0.01)
            print(f"[PROFILE] Lowered EAR threshold for {self.current_driver_id} to {profile['ear_threshold']:.3f}")
            
        elif alert_type == "yawning":
            # If false alarm for yawn, their mouth naturally opens wider. Raise it.
            profile["mar_threshold"] = min(0.80, profile["mar_threshold"] + 0.02)
            print(f"[PROFILE] Raised MAR threshold for {self.current_driver_id} to {profile['mar_threshold']:.3f}")

        self.save_profiles()

    def get_current_thresholds(self):
        """Returns the specific thresholds for the active driver."""
        if not self.current_driver_id or self.current_driver_id not in self.profiles:
            return None
        profile = self.profiles[self.current_driver_id]
        return {
            "ear_threshold": profile.get("ear_threshold", 0.25),
            "mar_threshold": profile.get("mar_threshold", 0.55)
        }
