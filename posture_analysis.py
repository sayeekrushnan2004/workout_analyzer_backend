"""
Posture Analysis Module
Adapted from standalone posture.py for API usage
"""

import cv2
import mediapipe as mp
import math
import numpy as np
from typing import Dict, Tuple, Optional, List
from dataclasses import dataclass
from datetime import datetime

# MediaPipe Pose Setup
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils

# Posture Thresholds
NECK_ANGLE_THRESH = 175
SPINE_TILT_THRESH = 10
SHOULDER_TILT_THRESH = 25
LEAN_THRESHOLD = 30
HEAD_DROP_THRESH = 60


@dataclass
class PostureMetrics:
    """Data class to store posture analysis metrics"""
    neck_angle: float
    spine_tilt: float
    shoulder_tilt: float
    nose_shoulder_dist: float
    shoulder_mid_x: int
    nose_x: int
    nose_y: int
    shoulder_y_avg: int


@dataclass
class PostureResult:
    """Result of posture analysis"""
    posture_status: str  # "Good Posture", "Leaning Left", etc.
    posture_score: int  # 0-100
    color: Tuple[int, int, int]  # BGR color for display
    metrics: PostureMetrics
    landmarks: Optional[List[Dict]] = None
    is_good_posture: bool = False


class PostureAnalyzer:
    """Main posture analysis class for API usage"""
    
    def __init__(self, 
                 min_detection_confidence: float = 0.5,
                 min_tracking_confidence: float = 0.5):
        """Initialize the posture analyzer"""
        self.pose = mp_pose.Pose(
            static_image_mode=False,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence
        )
        
    def calculate_angle(self, a: Tuple, b: Tuple, c: Tuple) -> float:
        """Calculate angle between three points"""
        ba = (a[0] - b[0], a[1] - b[1])
        bc = (c[0] - b[0], c[1] - b[1])
        
        dot_product = ba[0] * bc[0] + ba[1] * bc[1]
        mag_ba = math.sqrt(ba[0] ** 2 + ba[1] ** 2)
        mag_bc = math.sqrt(bc[0] ** 2 + bc[1] ** 2)
        
        if mag_ba * mag_bc == 0:
            return 0
        
        cos_val = dot_product / (mag_ba * mag_bc)
        cos_val = max(-1.0, min(1.0, cos_val))
        angle = math.acos(cos_val)
        
        return math.degrees(angle)
    
    def compute_posture_score(self, neck_angle: float, spine_tilt: float, shoulder_tilt: float) -> int:
        """Compute overall posture score (0-100)"""
        score = 100.0
        score -= abs(NECK_ANGLE_THRESH - neck_angle) * 0.4
        score -= spine_tilt * 0.4
        score -= shoulder_tilt * 0.4
        score = max(0, min(100, int(score)))
        return score
    
    def extract_keypoints(self, landmarks, width: int, height: int) -> Dict:
        """Extract key body points from MediaPipe landmarks"""
        lm = landmarks.landmark
        
        # Shoulders
        left_shoulder = (
            int(lm[mp_pose.PoseLandmark.LEFT_SHOULDER].x * width),
            int(lm[mp_pose.PoseLandmark.LEFT_SHOULDER].y * height)
        )
        right_shoulder = (
            int(lm[mp_pose.PoseLandmark.RIGHT_SHOULDER].x * width),
            int(lm[mp_pose.PoseLandmark.RIGHT_SHOULDER].y * height)
        )
        
        # Neck (midpoint between shoulders)
        neck = (
            (left_shoulder[0] + right_shoulder[0]) // 2,
            (left_shoulder[1] + right_shoulder[1]) // 2
        )
        
        # Hips
        left_hip = (
            int(lm[mp_pose.PoseLandmark.LEFT_HIP].x * width),
            int(lm[mp_pose.PoseLandmark.LEFT_HIP].y * height)
        )
        right_hip = (
            int(lm[mp_pose.PoseLandmark.RIGHT_HIP].x * width),
            int(lm[mp_pose.PoseLandmark.RIGHT_HIP].y * height)
        )
        
        # Mid hip
        mid_hip = (
            (left_hip[0] + right_hip[0]) // 2,
            (left_hip[1] + right_hip[1]) // 2
        )
        
        # Nose
        nose = (
            int(lm[mp_pose.PoseLandmark.NOSE].x * width),
            int(lm[mp_pose.PoseLandmark.NOSE].y * height)
        )
        
        return {
            'left_shoulder': left_shoulder,
            'right_shoulder': right_shoulder,
            'neck': neck,
            'left_hip': left_hip,
            'right_hip': right_hip,
            'mid_hip': mid_hip,
            'nose': nose
        }
    
    def calculate_metrics(self, keypoints: Dict) -> PostureMetrics:
        """Calculate posture metrics from keypoints"""
        neck_angle = self.calculate_angle(
            keypoints['nose'],
            keypoints['neck'],
            keypoints['mid_hip']
        )
        
        spine_tilt = abs(keypoints['neck'][0] - keypoints['mid_hip'][0])
        shoulder_tilt = abs(keypoints['left_shoulder'][1] - keypoints['right_shoulder'][1])
        
        shoulder_mid_x = (keypoints['left_shoulder'][0] + keypoints['right_shoulder'][0]) // 2
        shoulder_y_avg = (keypoints['left_shoulder'][1] + keypoints['right_shoulder'][1]) // 2
        nose_shoulder_dist = abs(keypoints['nose'][1] - shoulder_y_avg)
        
        return PostureMetrics(
            neck_angle=neck_angle,
            spine_tilt=spine_tilt,
            shoulder_tilt=shoulder_tilt,
            nose_shoulder_dist=nose_shoulder_dist,
            shoulder_mid_x=shoulder_mid_x,
            nose_x=keypoints['nose'][0],
            nose_y=keypoints['nose'][1],
            shoulder_y_avg=shoulder_y_avg
        )
    
    def classify_posture(self, metrics: PostureMetrics) -> Tuple[str, Tuple[int, int, int]]:
        """Classify posture based on metrics"""
        # Severely Slouched
        if metrics.nose_y > metrics.shoulder_y_avg + HEAD_DROP_THRESH:
            return "Severely Slouched", (0, 0, 255)
        
        # Slightly Slouched
        elif metrics.nose_y > metrics.shoulder_y_avg + HEAD_DROP_THRESH // 2:
            return "Slightly Slouched", (0, 165, 255)
        
        # Leaning Forward
        elif metrics.nose_shoulder_dist < 140:
            return "Leaning Forward", (0, 165, 255)
        
        # Leaning Backward
        elif metrics.nose_shoulder_dist > 200:
            return "Leaning Backward", (0, 165, 255)
        
        # Severe Lean Right
        elif metrics.nose_x > metrics.shoulder_mid_x + (LEAN_THRESHOLD * 2.4):
            return "Severe Lean Left", (0, 165, 255)
        
        # Severe Lean Left
        elif metrics.nose_x < metrics.shoulder_mid_x - (LEAN_THRESHOLD * 2.4):
            return "Severe Lean Right", (0, 165, 255)
        
        # Leaning Right
        elif metrics.nose_x > metrics.shoulder_mid_x + (LEAN_THRESHOLD * 0.5):
            return "Leaning Left", (0, 165, 255)
        
        # Leaning Left
        elif metrics.nose_x < metrics.shoulder_mid_x - (LEAN_THRESHOLD * 0.5):
            return "Leaning Right", (0, 165, 255)
        
        # Good Posture
        elif (metrics.neck_angle >= NECK_ANGLE_THRESH - 3 and
              metrics.spine_tilt <= SPINE_TILT_THRESH + 3 and
              metrics.shoulder_tilt <= SHOULDER_TILT_THRESH + 3):
            return "Good Posture", (0, 255, 0)
        
        # Bad Posture (default)
        else:
            return "Bad Posture", (0, 0, 255)
    
    def analyze_frame(self, frame: np.ndarray, draw_landmarks: bool = True) -> PostureResult:
        """
        Analyze a single frame for posture
        
        Args:
            frame: Input image (BGR format)
            draw_landmarks: Whether to draw pose landmarks on the frame
            
        Returns:
            PostureResult object with analysis results
        """
        # Convert to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Process frame
        results = self.pose.process(rgb_frame)
        
        # No person detected
        if not results.pose_landmarks:
            return PostureResult(
                posture_status="No person detected",
                posture_score=0,
                color=(255, 0, 0),
                metrics=None,
                is_good_posture=False
            )
        
        # Draw landmarks if requested
        if draw_landmarks:
            mp_drawing.draw_landmarks(
                frame,
                results.pose_landmarks,
                mp_pose.POSE_CONNECTIONS,
                mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=2),
                mp_drawing.DrawingSpec(color=(0, 0, 255), thickness=2)
            )
        
        # Extract keypoints
        height, width, _ = frame.shape
        keypoints = self.extract_keypoints(results.pose_landmarks, width, height)
        
        # Calculate metrics
        metrics = self.calculate_metrics(keypoints)
        
        # Classify posture
        posture_status, color = self.classify_posture(metrics)
        
        # Calculate score
        posture_score = self.compute_posture_score(
            metrics.neck_angle,
            metrics.spine_tilt,
            metrics.shoulder_tilt
        )
        
        # Check if good posture
        is_good = "Good" in posture_status
        
        # Extract landmarks for response
        landmarks_list = [{
            "index": idx,
            "name": mp_pose.PoseLandmark(idx).name,
            "x": lm.x,
            "y": lm.y,
            "z": lm.z,
            "visibility": lm.visibility
        } for idx, lm in enumerate(results.pose_landmarks.landmark)]
        
        return PostureResult(
            posture_status=posture_status,
            posture_score=posture_score,
            color=color,
            metrics=metrics,
            landmarks=landmarks_list,
            is_good_posture=is_good
        )
    
    def draw_posture_info(self, frame: np.ndarray, result: PostureResult) -> np.ndarray:
        """Draw posture information on the frame"""
        if result.metrics is None:
            cv2.putText(
                frame,
                result.posture_status,
                (30, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                result.color,
                2
            )
            return frame
        
        # Draw posture status
        cv2.putText(
            frame,
            f"Posture: {result.posture_status}",
            (30, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            result.color,
            2
        )
        
        # Draw score
        cv2.putText(
            frame,
            f"Score: {result.posture_score}",
            (30, 70),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 0, 0),
            2
        )
        
        return frame
    
    def close(self):
        """Release resources"""
        self.pose.close()


# Session storage for tracking posture sessions
class PostureSession:
    """Track a single posture analysis session"""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.start_time = datetime.now()
        self.total_frames = 0
        self.good_frames = 0
        self.bad_frames = 0
        self.current_bad_duration = 0
        self.longest_bad_duration = 0
        self.bad_posture_start = None
        self.score_history = []
        self.posture_history = []
        
    def update(self, result: PostureResult):
        """Update session with new frame result"""
        self.total_frames += 1
        
        if result.is_good_posture:
            self.good_frames += 1
            # Reset bad posture tracking
            if self.bad_posture_start is not None:
                if self.current_bad_duration > self.longest_bad_duration:
                    self.longest_bad_duration = self.current_bad_duration
                self.bad_posture_start = None
                self.current_bad_duration = 0
        else:
            self.bad_frames += 1
            # Track bad posture duration
            if self.bad_posture_start is None:
                self.bad_posture_start = datetime.now()
            else:
                self.current_bad_duration = (datetime.now() - self.bad_posture_start).total_seconds()
        
        # Store history
        self.score_history.append(result.posture_score)
        self.posture_history.append({
            "timestamp": datetime.now().isoformat(),
            "status": result.posture_status,
            "score": result.posture_score
        })
    
    def get_statistics(self) -> Dict:
        """Get session statistics"""
        duration = (datetime.now() - self.start_time).total_seconds()
        good_percent = (self.good_frames / self.total_frames * 100) if self.total_frames > 0 else 0
        bad_percent = (self.bad_frames / self.total_frames * 100) if self.total_frames > 0 else 0
        avg_score = sum(self.score_history) / len(self.score_history) if self.score_history else 0
        
        return {
            "session_id": self.session_id,
            "start_time": self.start_time.isoformat(),
            "duration_seconds": round(duration, 2),
            "total_frames": self.total_frames,
            "good_frames": self.good_frames,
            "bad_frames": self.bad_frames,
            "good_percent": round(good_percent, 2),
            "bad_percent": round(bad_percent, 2),
            "average_score": round(avg_score, 2),
            "longest_bad_duration": round(self.longest_bad_duration, 2),
            "current_bad_duration": round(self.current_bad_duration, 2)
        }

