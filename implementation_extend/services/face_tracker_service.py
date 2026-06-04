# ===================================================================
# face_tracker_service.py
# TRACKER VISAGE UNIQUE
# ===================================================================

import time
import math


class FaceTracker:

    def __init__(self):

        self.current_face = None
        self.last_seen = 0

        self.timeout = 2.0

    # =========================================================
    # DISTANCE ENTRE DEUX VISAGES
    # =========================================================

    def distance(self, box1, box2):

        x1, y1, w1, h1 = box1
        x2, y2, w2, h2 = box2

        c1x = x1 + w1 / 2
        c1y = y1 + h1 / 2

        c2x = x2 + w2 / 2
        c2y = y2 + h2 / 2

        return math.sqrt((c1x - c2x) ** 2 + (c1y - c2y) ** 2)

    # =========================================================
    # UPDATE TRACKER
    # =========================================================

    def update(self, detections):

        now = time.time()

        if len(detections) == 0:

            if now - self.last_seen > self.timeout:
                self.current_face = None

            return None

        best = max(detections, key=lambda d: d["confidence"])

        if self.current_face is None:
            self.current_face = best
            self.last_seen = now
            return best

        dist = self.distance(
            self.current_face["box"],
            best["box"]
        )

        if dist < 80:
            self.current_face = best
            self.last_seen = now
            return best

        return self.current_face