"""
Drowsiness, Gaze, Yawning, and Face Covering Tracking Module using MediaPipe Face Mesh.
Computes:
  1. Eye Aspect Ratio (EAR) for Drowsiness detection.
  2. Iris position for Gaze Distraction estimation (left/right/up/down/center).
  3. Mouth Aspect Ratio (MAR) for Yawning detection and alert hold.
  4. Lower-Face Texture & Color ROI analysis for Face Mask / Cover detection.
"""

import math
import time
from typing import Dict, Tuple, Optional, List
import cv2
import numpy as np
import mediapipe as mp


class EyeTracker:
    """
    Tracks eye state (EAR), gaze direction, mouth state (MAR/yawning),
    and face mask / cover status using MediaPipe FaceMesh.
    """

    # 6-point eye landmark indices for MediaPipe Face Mesh
    # Right eye (Driver right side, viewer left side)
    RIGHT_EYE_INDICES = [33, 160, 158, 133, 153, 144]
    # Left eye (Driver left side, viewer right side)
    LEFT_EYE_INDICES = [362, 385, 387, 263, 373, 380]

    # Iris landmarks
    RIGHT_IRIS_CENTER = 468
    RIGHT_IRIS_POINTS = [468, 469, 470, 471, 472]
    LEFT_IRIS_CENTER = 473
    LEFT_IRIS_POINTS = [473, 474, 475, 476, 477]

    # Mouth landmark indices for MAR (Mouth Aspect Ratio) & Yawning
    MOUTH_CORNER_LEFT = 78
    MOUTH_CORNER_RIGHT = 308
    MOUTH_CENTER_TOP = 13
    MOUTH_CENTER_BOTTOM = 14
    MOUTH_LEFT_TOP = 82
    MOUTH_LEFT_BOTTOM = 87
    MOUTH_RIGHT_TOP = 312
    MOUTH_RIGHT_BOTTOM = 317

    # Inner lip loop for polygon drawing
    INNER_LIP_INDICES = [78, 82, 13, 312, 308, 317, 14, 87]

    def __init__(
        self,
        ear_threshold: float = 0.25,
        ear_consecutive_frames: int = 20,
        gaze_distraction_seconds: float = 2.0,
        gaze_horizontal_left_thresh: float = 0.38,
        gaze_horizontal_right_thresh: float = 0.62,
        gaze_vertical_up_thresh: float = 0.35,
        gaze_vertical_down_thresh: float = 0.65,
        mar_threshold: float = 0.55,
        mar_consecutive_frames: int = 15,
        yawn_alert_hold_seconds: float = 3.0,
        face_cover_enabled: bool = True,
        face_cover_confidence_threshold: float = 0.55,
        face_cover_consecutive_frames: int = 10,
        face_cover_trigger_alert: bool = True,
        draw_landmarks: bool = True,
    ):
        self.ear_threshold = ear_threshold
        self.ear_consecutive_frames = ear_consecutive_frames
        self.gaze_distraction_seconds = gaze_distraction_seconds

        self.gaze_h_left = gaze_horizontal_left_thresh
        self.gaze_h_right = gaze_horizontal_right_thresh
        self.gaze_v_up = gaze_vertical_up_thresh
        self.gaze_v_down = gaze_vertical_down_thresh

        # Yawning settings
        self.mar_threshold = mar_threshold
        self.mar_consecutive_frames = mar_consecutive_frames
        self.yawn_alert_hold_seconds = yawn_alert_hold_seconds

        # Face cover / mask settings
        self.face_cover_enabled = face_cover_enabled
        self.face_cover_confidence_threshold = face_cover_confidence_threshold
        self.face_cover_consecutive_frames = face_cover_consecutive_frames
        self.face_cover_trigger_alert = face_cover_trigger_alert

        self.draw_landmarks = draw_landmarks

        # Internal state tracking - Drowsiness
        self.drowsy_frame_count: int = 0
        self.drowsy_start_time: Optional[float] = None
        self.is_drowsy: bool = False

        # Internal state tracking - Gaze Distraction
        self.gaze_away_start_time: Optional[float] = None
        self.is_distracted: bool = False
        self.current_gaze: str = "center"

        # Internal state tracking - Yawning
        self.yawn_frame_count: int = 0
        self.yawn_start_time: Optional[float] = None
        self.is_yawning: bool = False
        self.yawn_alert_until: float = 0.0
        self.total_yawns_count: int = 0

        # Internal state tracking - Mask / Face cover
        self.mask_frame_count: int = 0
        self.mask_start_time: Optional[float] = None
        self.is_masked: bool = False
        self.mask_confidence: float = 0.0

        # MediaPipe FaceMesh initialization
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )

    @staticmethod
    def _euclidean_distance(pt1: Tuple[float, float], pt2: Tuple[float, float]) -> float:
        """Calculate Euclidean distance between two 2D points."""
        return math.hypot(pt1[0] - pt2[0], pt1[1] - pt2[1])

    def calculate_ear(
        self, landmarks, eye_indices: List[int], img_w: int, img_h: int
    ) -> float:
        """
        Compute Eye Aspect Ratio (EAR) for a single eye given 6 landmarks.
        EAR = (|p2 - p6| + |p3 - p5|) / (2 * |p1 - p4|)
        """
        pts = [
            (landmarks[idx].x * img_w, landmarks[idx].y * img_h)
            for idx in eye_indices
        ]
        p1, p2, p3, p4, p5, p6 = pts

        v1 = self._euclidean_distance(p2, p6)
        v2 = self._euclidean_distance(p3, p5)
        h = self._euclidean_distance(p1, p4)

        if h == 0:
            return 0.0

        return (v1 + v2) / (2.0 * h)

    def calculate_mar(self, landmarks, img_w: int, img_h: int) -> float:
        """
        Compute Mouth Aspect Ratio (MAR) to detect yawning.
        MAR = (|P13 - P14| + |P82 - P87| + |P312 - P317|) / (3 * |P78 - P308|)
        """
        def pt(idx):
            return (landmarks[idx].x * img_w, landmarks[idx].y * img_h)

        c_left = pt(self.MOUTH_CORNER_LEFT)
        c_right = pt(self.MOUTH_CORNER_RIGHT)
        v_center = self._euclidean_distance(pt(self.MOUTH_CENTER_TOP), pt(self.MOUTH_CENTER_BOTTOM))
        v_left = self._euclidean_distance(pt(self.MOUTH_LEFT_TOP), pt(self.MOUTH_LEFT_BOTTOM))
        v_right = self._euclidean_distance(pt(self.MOUTH_RIGHT_TOP), pt(self.MOUTH_RIGHT_BOTTOM))

        horizontal = self._euclidean_distance(c_left, c_right)
        if horizontal <= 1e-4:
            return 0.0

        mar = (v_center + v_left + v_right) / (3.0 * horizontal)
        return float(mar)

    def detect_mask_face_cover(
        self, frame: np.ndarray, landmarks, img_w: int, img_h: int
    ) -> Tuple[bool, float, Optional[Tuple[int, int, int, int]]]:
        """
        Analyze lower-face ROI (between nose and chin) to detect face mask or face cover.
        Checks:
          1. Surgical mask color profiles (Cyan/Blue, White, Dark/Black) in HSV.
          2. Color consistency & variance compared to uncovered forehead skin.
          3. Lip-to-skin contrast (absent when covered by mask fabric).
        """
        if not self.face_cover_enabled:
            return False, 0.0, None

        nose_y = int(landmarks[1].y * img_h)
        chin_y = int(landmarks[152].y * img_h)
        left_x = int(landmarks[234].x * img_w)
        right_x = int(landmarks[454].x * img_w)
        forehead_y = int(landmarks[10].y * img_h)

        x1 = max(0, min(left_x, right_x) - 10)
        x2 = min(img_w - 1, max(left_x, right_x) + 10)
        y1 = max(0, nose_y - 10)
        y2 = min(img_h - 1, chin_y + 15)

        if x2 <= x1 or y2 <= y1:
            return False, 0.0, None

        lower_patch = frame[y1:y2, x1:x2]
        if lower_patch.size == 0:
            return False, 0.0, None

        fh_top = max(0, forehead_y - 20)
        fh_bottom = min(img_h - 1, forehead_y + 15)
        fh_cx = int(landmarks[10].x * img_w)
        fh_left = max(0, fh_cx - 20)
        fh_right = min(img_w - 1, fh_cx + 20)
        forehead_patch = frame[fh_top:fh_bottom, fh_left:fh_right]

        hsv_lower = cv2.cvtColor(lower_patch, cv2.COLOR_BGR2HSV)
        h_chan = hsv_lower[:, :, 0]
        s_chan = hsv_lower[:, :, 1]
        v_chan = hsv_lower[:, :, 2]

        blue_mask = (h_chan >= 85) & (h_chan <= 135) & (s_chan >= 35)
        blue_ratio = float(np.mean(blue_mask))

        white_mask = (v_chan > 175) & (s_chan < 35)
        white_ratio = float(np.mean(white_mask))

        dark_mask = (v_chan < 50)
        dark_ratio = float(np.mean(dark_mask))

        std_lower = float(np.std(lower_patch))

        score = 0.0
        if blue_ratio > 0.28:
            score += 0.85
        elif white_ratio > 0.40:
            score += 0.75
        elif dark_ratio > 0.35:
            score += 0.70

        if std_lower < 18.0:
            score += 0.30

        if forehead_patch.size > 0:
            mean_lower = np.mean(lower_patch, axis=(0, 1))
            mean_fh = np.mean(forehead_patch, axis=(0, 1))
            color_distance = float(np.linalg.norm(mean_lower - mean_fh))
            if color_distance > 50.0:
                score += 0.35

        confidence = min(1.0, score)
        is_masked = confidence >= self.face_cover_confidence_threshold
        bbox = (x1, y1, x2, y2)
        return is_masked, confidence, bbox

    def estimate_gaze(
        self, landmarks, img_w: int, img_h: int, avg_ear: float
    ) -> Tuple[str, float, float]:
        """Estimate gaze direction from iris positions relative to eye landmarks."""
        if avg_ear < 0.18:
            return "eyes-closed", 0.5, 0.5

        r_outer = landmarks[33]
        r_inner = landmarks[133]
        r_top = ((landmarks[160].y + landmarks[158].y) / 2.0)
        r_bottom = ((landmarks[153].y + landmarks[144].y) / 2.0)
        r_iris = landmarks[self.RIGHT_IRIS_CENTER]

        l_inner = landmarks[362]
        l_outer = landmarks[263]
        l_top = ((landmarks[385].y + landmarks[387].y) / 2.0)
        l_bottom = ((landmarks[373].y + landmarks[380].y) / 2.0)
        l_iris = landmarks[self.LEFT_IRIS_CENTER]

        r_h_span = max(r_inner.x - r_outer.x, 1e-5)
        r_h_ratio = (r_iris.x - r_outer.x) / r_h_span

        l_h_span = max(l_outer.x - l_inner.x, 1e-5)
        l_h_ratio = (l_iris.x - l_inner.x) / l_h_span

        avg_h_ratio = (r_h_ratio + l_h_ratio) / 2.0

        r_v_span = max(r_bottom - r_top, 1e-5)
        r_v_ratio = (r_iris.y - r_top) / r_v_span

        l_v_span = max(l_bottom - l_top, 1e-5)
        l_v_ratio = (l_iris.y - l_top) / l_v_span

        avg_v_ratio = (r_v_ratio + l_v_ratio) / 2.0

        if avg_h_ratio < self.gaze_h_left:
            direction = "looking-right"
        elif avg_h_ratio > self.gaze_h_right:
            direction = "looking-left"
        elif avg_v_ratio < self.gaze_v_up:
            direction = "looking-up"
        elif avg_v_ratio > self.gaze_v_down:
            direction = "looking-down"
        else:
            direction = "center"

        return direction, avg_h_ratio, avg_v_ratio

    def draw_annotations(
        self,
        frame: np.ndarray,
        landmarks,
        img_w: int,
        img_h: int,
        is_drowsy: bool,
        is_yawning: bool,
        is_masked: bool,
        mask_bbox: Optional[Tuple[int, int, int, int]],
    ) -> None:
        """Draw landmarks for eyes, irises, mouth, and mask on frame for debugging."""
        eye_color = (0, 0, 255) if is_drowsy else (0, 255, 128)
        mouth_color = (0, 0, 255) if is_yawning else (0, 255, 200)
        iris_color = (0, 215, 255)

        r_pts = np.array(
            [[int(landmarks[i].x * img_w), int(landmarks[i].y * img_h)] for i in self.RIGHT_EYE_INDICES],
            dtype=np.int32,
        )
        cv2.polylines(frame, [r_pts], isClosed=True, color=eye_color, thickness=1, lineType=cv2.LINE_AA)

        l_pts = np.array(
            [[int(landmarks[i].x * img_w), int(landmarks[i].y * img_h)] for i in self.LEFT_EYE_INDICES],
            dtype=np.int32,
        )
        cv2.polylines(frame, [l_pts], isClosed=True, color=eye_color, thickness=1, lineType=cv2.LINE_AA)

        r_iris_pt = (
            int(landmarks[self.RIGHT_IRIS_CENTER].x * img_w),
            int(landmarks[self.RIGHT_IRIS_CENTER].y * img_h),
        )
        l_iris_pt = (
            int(landmarks[self.LEFT_IRIS_CENTER].x * img_w),
            int(landmarks[self.LEFT_IRIS_CENTER].y * img_h),
        )
        cv2.circle(frame, r_iris_pt, 3, iris_color, -1, lineType=cv2.LINE_AA)
        cv2.circle(frame, l_iris_pt, 3, iris_color, -1, lineType=cv2.LINE_AA)

        if not is_masked:
            m_pts = np.array(
                [[int(landmarks[i].x * img_w), int(landmarks[i].y * img_h)] for i in self.INNER_LIP_INDICES],
                dtype=np.int32,
            )
            cv2.polylines(frame, [m_pts], isClosed=True, color=mouth_color, thickness=2 if is_yawning else 1, lineType=cv2.LINE_AA)

        if is_masked and mask_bbox:
            mx1, my1, mx2, my2 = mask_bbox
            cv2.rectangle(frame, (mx1, my1), (mx2, my2), (235, 206, 135), 2, lineType=cv2.LINE_AA)
            cv2.putText(
                frame,
                "FACE COVER / MASK",
                (mx1, max(0, my1 - 6)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.50,
                (235, 206, 135),
                1,
                lineType=cv2.LINE_AA,
            )

    def process(self, frame: np.ndarray) -> Dict:
        """Process a single video frame for eyes, gaze, yawning, and mask cover."""
        img_h, img_w = frame.shape[:2]
        now = time.time()

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(rgb_frame)

        if not results.multi_face_landmarks:
            self.drowsy_frame_count = 0
            self.drowsy_start_time = None
            self.is_drowsy = False
            self.gaze_away_start_time = None
            self.is_distracted = False
            self.current_gaze = "no-face"
            self.yawn_frame_count = 0
            self.yawn_start_time = None
            self.is_yawning = False
            self.mask_frame_count = 0
            self.mask_start_time = None
            self.is_masked = False
            return {
                "face_detected": False,
                "ear": 0.0,
                "drowsy_warning": False,
                "drowsy_duration": 0.0,
                "gaze": "no-face",
                "gaze_ratio_h": 0.5,
                "gaze_ratio_v": 0.5,
                "distraction_warning": False,
                "distraction_duration": 0.0,
                "mar": 0.0,
                "yawning_warning": False,
                "yawn_duration": 0.0,
                "total_yawns": self.total_yawns_count,
                "mask_detected": False,
                "mask_confidence": 0.0,
                "mask_warning": False,
                "mask_duration": 0.0,
            }

        landmarks = results.multi_face_landmarks[0].landmark

        # 1. EAR Calculation (Drowsiness)
        r_ear = self.calculate_ear(landmarks, self.RIGHT_EYE_INDICES, img_w, img_h)
        l_ear = self.calculate_ear(landmarks, self.LEFT_EYE_INDICES, img_w, img_h)
        avg_ear = (r_ear + l_ear) / 2.0

        if avg_ear < self.ear_threshold:
            self.drowsy_frame_count += 1
            if self.drowsy_frame_count >= self.ear_consecutive_frames:
                if self.drowsy_start_time is None:
                    self.drowsy_start_time = now
                self.is_drowsy = True
            else:
                self.is_drowsy = False
        else:
            self.drowsy_frame_count = 0
            self.drowsy_start_time = None
            self.is_drowsy = False

        drowsy_duration = (now - self.drowsy_start_time) if self.drowsy_start_time else 0.0

        # 2. Gaze Estimation
        gaze, h_ratio, v_ratio = self.estimate_gaze(landmarks, img_w, img_h, avg_ear)
        self.current_gaze = gaze

        if gaze not in ("center", "eyes-closed"):
            if self.gaze_away_start_time is None:
                self.gaze_away_start_time = now
            elapsed_away = now - self.gaze_away_start_time
            self.is_distracted = (elapsed_away >= self.gaze_distraction_seconds)
        else:
            self.gaze_away_start_time = None
            self.is_distracted = False

        distraction_duration = (
            (now - self.gaze_away_start_time) if self.gaze_away_start_time else 0.0
        )

        # 3. Mask / Face Cover Detection
        is_masked_raw, mask_conf, mask_bbox = self.detect_mask_face_cover(frame, landmarks, img_w, img_h)
        if is_masked_raw:
            self.mask_frame_count += 1
            if self.mask_frame_count >= self.face_cover_consecutive_frames:
                if self.mask_start_time is None:
                    self.mask_start_time = now
                self.is_masked = True
        else:
            self.mask_frame_count = 0
            self.mask_start_time = None
            self.is_masked = False

        self.mask_confidence = mask_conf
        mask_duration = (now - self.mask_start_time) if self.mask_start_time else 0.0
        mask_alert_active = self.is_masked and self.face_cover_trigger_alert

        # 4. MAR Calculation (Yawning)
        if not self.is_masked:
            mar = self.calculate_mar(landmarks, img_w, img_h)
            if mar >= self.mar_threshold:
                self.yawn_frame_count += 1
                if self.yawn_frame_count >= self.mar_consecutive_frames:
                    if self.yawn_start_time is None:
                        self.yawn_start_time = now
                        self.total_yawns_count += 1
                    self.is_yawning = True
                    self.yawn_alert_until = now + self.yawn_alert_hold_seconds
                else:
                    self.is_yawning = False
            else:
                self.yawn_frame_count = 0
                self.yawn_start_time = None
                self.is_yawning = False
        else:
            mar = 0.0
            self.yawn_frame_count = 0
            self.yawn_start_time = None
            self.is_yawning = False

        yawn_alert_active = self.is_yawning or (now < self.yawn_alert_until)
        yawn_duration = (now - self.yawn_start_time) if self.yawn_start_time else (
            (self.yawn_alert_until - now) if now < self.yawn_alert_until else 0.0
        )

        # 5. Draw landmarks if enabled
        if self.draw_landmarks:
            self.draw_annotations(
                frame=frame,
                landmarks=landmarks,
                img_w=img_w,
                img_h=img_h,
                is_drowsy=self.is_drowsy,
                is_yawning=yawn_alert_active,
                is_masked=self.is_masked,
                mask_bbox=mask_bbox,
            )

        mouth_center = (
            int((landmarks[78].x + landmarks[308].x) * img_w / 2.0),
            int((landmarks[78].y + landmarks[308].y) * img_h / 2.0),
        )

        return {
            "face_detected": True,
            "ear": float(avg_ear),
            "drowsy_warning": self.is_drowsy,
            "drowsy_duration": drowsy_duration,
            "gaze": gaze,
            "gaze_ratio_h": float(h_ratio),
            "gaze_ratio_v": float(v_ratio),
            "distraction_warning": self.is_distracted,
            "distraction_duration": distraction_duration,
            "mar": float(mar),
            "yawning_warning": yawn_alert_active,
            "yawn_duration": yawn_duration,
            "total_yawns": self.total_yawns_count,
            "mask_detected": self.is_masked,
            "mask_confidence": float(mask_conf),
            "mask_warning": mask_alert_active,
            "mask_duration": mask_duration,
            "mouth_center": mouth_center,
        }

    def close(self) -> None:
        """Release MediaPipe resources."""
        if hasattr(self, "face_mesh") and self.face_mesh:
            self.face_mesh.close()
