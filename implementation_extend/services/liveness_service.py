# ===================================================================
# services/liveness_service.py
# DETECTION CLIGNEMENT DES YEUX
# ===================================================================

import cv2
import mediapipe as mp
import numpy as np
import logging

logger = logging.getLogger(__name__)

class LivenessService:

    LEFT_EYE = [33, 160, 158, 133, 153, 144]
    RIGHT_EYE = [362, 385, 387, 263, 373, 380]

    EAR_THRESHOLD = 0.20

    def __init__(self):

        self.mesh = mp.solutions.face_mesh.FaceMesh(
            static_image_mode=False,
            max_num_faces=1,
            refine_landmarks=True
        )

    def eye_aspect_ratio(self, points):

        p2_p6 = np.linalg.norm(points[1] - points[5])
        p3_p5 = np.linalg.norm(points[2] - points[4])
        p1_p4 = np.linalg.norm(points[0] - points[3])

        return (p2_p6 + p3_p5) / (2.0 * p1_p4)

    def detect_blink(self, frame):

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        results = self.mesh.process(rgb)

        if not results.multi_face_landmarks:
            return False

        face = results.multi_face_landmarks[0]

        h, w, _ = frame.shape

        left = []
        right = []

        for idx in self.LEFT_EYE:
            lm = face.landmark[idx]
            left.append(np.array([lm.x * w, lm.y * h]))

        for idx in self.RIGHT_EYE:
            lm = face.landmark[idx]
            right.append(np.array([lm.x * w, lm.y * h]))

        left_ear = self.eye_aspect_ratio(left)
        right_ear = self.eye_aspect_ratio(right)

        ear = (left_ear + right_ear) / 2.0

        return ear < self.EAR_THRESHOLD