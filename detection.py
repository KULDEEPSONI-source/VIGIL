"""
Distracted Driving Object Detection Module using Ultralytics YOLOv8.
Detects:
  - 'phone'
  - 'cigarette'
  - 'drink' (bottle / cup)

Applies consecutive-frame filtering (confidence > 0.6 for 3+ frames)
to eliminate flickering false positives before raising warnings.
"""

import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import cv2
import numpy as np
from ultralytics import YOLO


class DistractionDetector:
    """
    YOLOv8-based detector for distracted driving behaviors.
    Loads custom fine-tuned weights or provides a guided fallback to COCO weights.
    """

    # Bounding box color palette (BGR)
    CLASS_COLORS = {
        "phone": (220, 20, 60),      # Crimson
        "cigarette": (0, 69, 255),    # Orange-Red
        "drink": (238, 130, 238),    # Violet / Bright Pink
        "default": (0, 255, 255),    # Yellow
    }

    # Standard COCO class ID mapping for demonstration fallback
    COCO_FALLBACK_MAP = {
        67: "phone",     # cell phone
        39: "drink",     # bottle
        41: "drink",     # cup
    }

    def __init__(
        self,
        model_path: str = "runs/detect/train/weights/best.pt",
        confidence_threshold: float = 0.6,
        consecutive_frames_threshold: int = 3,
        target_classes: Optional[List[str]] = None,
        allow_fallback_to_coco: bool = True,
        fallback_model_path: str = "yolov8n.pt",
    ):
        self.model_path = model_path
        self.confidence_threshold = confidence_threshold
        self.consecutive_frames_threshold = consecutive_frames_threshold
        self.target_classes = target_classes or ["phone", "cigarette", "drink"]
        self.allow_fallback_to_coco = allow_fallback_to_coco
        self.fallback_model_path = fallback_model_path

        # State tracking for consecutive frames and active durations
        self.consecutive_counts: Dict[str, int] = {c: 0 for c in self.target_classes}
        self.start_times: Dict[str, Optional[float]] = {c: None for c in self.target_classes}
        self.active_warnings: Dict[str, float] = {}

        self.is_fallback_mode: bool = False
        self.model = self._load_model()

    def _load_model(self) -> YOLO:
        """
        Load fine-tuned YOLO model. If missing, print a clear error and instructions.
        Falls back to COCO weights if permitted by config.
        """
        model_file = Path(self.model_path)
        if model_file.exists():
            print(f"[DETECTION] Loading fine-tuned DMS weights from: {model_file.resolve()}")
            try:
                model = YOLO(str(model_file))
                print(f"[DETECTION] Model classes: {model.names}")
                return model
            except Exception as e:
                print(f"[DETECTION ERROR] Failed to load model at {model_file}: {e}", file=sys.stderr)

        # Model file is missing
        print("\n" + "!" * 70, file=sys.stderr)
        print(" [MODEL MISSING ERROR]", file=sys.stderr)
        print(f" Target model weights not found at: '{self.model_path}'", file=sys.stderr)
        print(" Please train the model first by running:", file=sys.stderr)
        print("     python train_yolo.py --data dataset/data.yaml", file=sys.stderr)
        print("!" * 70 + "\n", file=sys.stderr)

        if self.allow_fallback_to_coco:
            print(
                f"[DETECTION FALLBACK] 'allow_fallback_to_coco' is enabled in config.yaml.\n"
                f"Loading base pretrained weights '{self.fallback_model_path}' with COCO mapping:\n"
                f"  - COCO 67 (cell phone) -> 'phone'\n"
                f"  - COCO 39 (bottle)     -> 'drink'\n"
                f"  - COCO 41 (cup)        -> 'drink'\n"
                f"*(Note: 'cigarette' is not in COCO and requires training with train_yolo.py)*\n"
            )
            self.is_fallback_mode = True
            return YOLO(self.fallback_model_path)

        raise FileNotFoundError(
            f"Model weights file '{self.model_path}' was not found. "
            f"Please run 'python train_yolo.py' or enable 'allow_fallback_to_coco: true' in config.yaml."
        )

    def _map_detection_class(self, cls_id: int, original_name: str) -> Optional[str]:
        """Map raw YOLO class index/name to one of our target classes."""
        if self.is_fallback_mode:
            return self.COCO_FALLBACK_MAP.get(cls_id, None)

        # Direct custom model mapping
        clean_name = str(original_name).strip().lower()
        for target in self.target_classes:
            if target in clean_name or clean_name in target:
                return target
        return None

    def process(self, frame: np.ndarray) -> Dict:
        """
        Run inference on the given frame, filter detections, and draw bounding boxes.

        Args:
            frame: OpenCV BGR frame (modified in-place with bounding boxes)

        Returns:
            Dictionary with:
            - 'detected_objects': List of dicts (class, confidence, box, frames)
            - 'active_warnings': Dict of {class_name: duration_seconds}
            - 'highest_confidence': float
        """
        now = time.time()
        # Run inference (disable verbose output)
        results = self.model.predict(
            source=frame,
            conf=self.confidence_threshold,
            verbose=False,
            imgsz=640,
        )

        detected_in_this_frame: Dict[str, float] = {}
        raw_boxes = []

        if results and len(results) > 0 and results[0].boxes:
            boxes = results[0].boxes
            for box in boxes:
                cls_id = int(box.cls[0].item())
                orig_name = results[0].names.get(cls_id, str(cls_id))
                conf = float(box.conf[0].item())

                target_cls = self._map_detection_class(cls_id, orig_name)
                if not target_cls:
                    continue

                coords = [int(v) for v in box.xyxy[0].tolist()]
                raw_boxes.append((target_cls, conf, coords))

                # Track highest confidence for this class in this frame
                if target_cls not in detected_in_this_frame or conf > detected_in_this_frame[target_cls]:
                    detected_in_this_frame[target_cls] = conf

        # Update consecutive frame counters
        for target_cls in self.target_classes:
            if target_cls in detected_in_this_frame:
                self.consecutive_counts[target_cls] += 1
                if self.consecutive_counts[target_cls] >= self.consecutive_frames_threshold:
                    if self.start_times[target_cls] is None:
                        self.start_times[target_cls] = now
            else:
                self.consecutive_counts[target_cls] = 0
                self.start_times[target_cls] = None

        # Build active warnings dictionary
        self.active_warnings = {}
        for target_cls in self.target_classes:
            if (
                self.consecutive_counts[target_cls] >= self.consecutive_frames_threshold
                and self.start_times[target_cls] is not None
            ):
                duration = now - self.start_times[target_cls]
                self.active_warnings[target_cls] = duration

        # Draw bounding boxes and labels
        detected_list = []
        for target_cls, conf, (x1, y1, x2, y2) in raw_boxes:
            c_frames = self.consecutive_counts.get(target_cls, 0)
            is_warning = c_frames >= self.consecutive_frames_threshold
            color = self.CLASS_COLORS.get(target_cls, self.CLASS_COLORS["default"])

            # Thicker box if warning is active
            thickness = 3 if is_warning else 2
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness, lineType=cv2.LINE_AA)

            # Label text
            status_tag = f" [ALERT {c_frames}f]" if is_warning else f" [{c_frames}/{self.consecutive_frames_threshold}f]"
            label = f"{target_cls.upper()} {conf:.0%}{status_tag}"

            # Label background banner
            (w, h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 1)
            y_label_top = max(0, y1 - h - 8)
            cv2.rectangle(
                frame,
                (x1, y_label_top),
                (x1 + w + 8, y_label_top + h + 8),
                color,
                -1,
            )
            cv2.putText(
                frame,
                label,
                (x1 + 4, y_label_top + h + 4),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (255, 255, 255),
                1,
                lineType=cv2.LINE_AA,
            )

            detected_list.append({
                "class": target_cls,
                "confidence": conf,
                "box": (x1, y1, x2, y2),
                "consecutive_frames": c_frames,
                "is_warning": is_warning,
            })

        max_conf = max(detected_in_this_frame.values()) if detected_in_this_frame else 0.0

        return {
            "detected_objects": detected_list,
            "active_warnings": self.active_warnings,
            "highest_confidence": max_conf,
            "consecutive_counts": dict(self.consecutive_counts),
            "is_fallback_mode": self.is_fallback_mode,
        }
