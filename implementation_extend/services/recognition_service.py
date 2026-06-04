# ===================================================================
# services/recognition_service.py
# VERSION PROFESSIONNELLE STABLE
# ===================================================================

import cv2
import time
import logging

from services.deep_face_service import (
    get_face_recognition_service
)

from services.liveness_service import (
    LivenessService
)

from services.attendance_service import (
    AttendanceService
)

logger = logging.getLogger(__name__)


# =========================================================
# CONFIG
# =========================================================

class RecognitionRuntimeConfig:

    CAMERA_ID = 0

    CAMERA_WIDTH = 1280

    CAMERA_HEIGHT = 720

    COOLDOWN_SECONDS = 30

    REQUIRED_BLINKS = 1

    COLOR_GREEN = (0, 255, 0)

    COLOR_RED = (0, 0, 255)

    COLOR_YELLOW = (0, 255, 255)

    FONT = cv2.FONT_HERSHEY_SIMPLEX


# =========================================================
# SERVICE
# =========================================================

class ContinuousRecognitionService:

    def __init__(self):

        self.recognizer = None

        self.liveness = None

        self.cap = None

        self.running = False

        self.cooldowns = {}

        self.current_candidate = None

        self.current_candidate_since = 0

        self.blink_validated = False

    # -----------------------------------------------------
    # INITIALIZE
    # -----------------------------------------------------

    def initialize(self):

        logger.info("Initialisation RecognitionService")

        try:

            self.recognizer = (
                get_face_recognition_service()
            )

            if self.recognizer is None:

                logger.error(
                    "FaceRecognitionService = None"
                )

                raise Exception(
                    "Le service de reconnaissance est NULL"
                )

            logger.info(
                "FaceRecognitionService chargé"
            )

        except Exception as e:

            logger.error(
                f"Erreur chargement recognizer : {e}"
            )

            self.recognizer = None

        try:

            self.liveness = LivenessService()

            logger.info(
                "LivenessService chargé"
            )

        except Exception as e:

            logger.error(
                f"Erreur LivenessService : {e}"
            )

            self.liveness = None

        return self

    # -----------------------------------------------------
    # PROCESS FRAME
    # -----------------------------------------------------

    def process_frame(self, frame):

        if self.recognizer is None:

            cv2.putText(
                frame,
                "Recognizer non initialise",
                (20, 40),
                RecognitionRuntimeConfig.FONT,
                1,
                RecognitionRuntimeConfig.COLOR_RED,
                2
            )

            return frame

        faces = self.recognizer.detect_faces(frame)

        if len(faces) == 0:

            self.current_candidate = None

            self.blink_validated = False

            return frame

        # =================================================
        # UN SEUL VISAGE
        # =================================================

        if len(faces) > 1:

            cv2.putText(
                frame,
                "Une seule personne devant la camera",
                (20, 40),
                RecognitionRuntimeConfig.FONT,
                1,
                RecognitionRuntimeConfig.COLOR_RED,
                2
            )

            return frame

        face_data = faces[0]

        x1, y1, x2, y2 = face_data["box"]

        face = face_data["face"]

        embedding = (
            self.recognizer.get_face_embedding(face)
        )

        if embedding is None:

            return frame

        result = self.recognizer.recognize_face(
            embedding
        )

        # =================================================
        # UNKNOWN
        # =================================================

        if result is None:

            cv2.rectangle(
                frame,
                (x1, y1),
                (x2, y2),
                RecognitionRuntimeConfig.COLOR_RED,
                2
            )

            cv2.putText(
                frame,
                "Inconnu",
                (x1, y1 - 10),
                RecognitionRuntimeConfig.FONT,
                0.8,
                RecognitionRuntimeConfig.COLOR_RED,
                2
            )

            return frame

        # =================================================
        # RECOGNIZED
        # =================================================

        student_id = result["student_id"]

        name = result["name"]

        similarity = result["similarity"]

        now = time.time()

        # =================================================
        # COOLDOWN
        # =================================================

        if student_id in self.cooldowns:

            elapsed = (
                now -
                self.cooldowns[student_id]
            )

            if elapsed < RecognitionRuntimeConfig.COOLDOWN_SECONDS:

                cv2.rectangle(
                    frame,
                    (x1, y1),
                    (x2, y2),
                    RecognitionRuntimeConfig.COLOR_YELLOW,
                    2
                )

                cv2.putText(
                    frame,
                    f"{name} cooldown",
                    (x1, y1 - 10),
                    RecognitionRuntimeConfig.FONT,
                    0.7,
                    RecognitionRuntimeConfig.COLOR_YELLOW,
                    2
                )

                return frame

        # =================================================
        # BLINK VALIDATION
        # =================================================

        blink = self.liveness.detect_blink(frame)

        if not blink:

            cv2.rectangle(
                frame,
                (x1, y1),
                (x2, y2),
                RecognitionRuntimeConfig.COLOR_YELLOW,
                2
            )

            cv2.putText(
                frame,
                f"{name} - Clignez des yeux",
                (x1, y1 - 10),
                RecognitionRuntimeConfig.FONT,
                0.7,
                RecognitionRuntimeConfig.COLOR_YELLOW,
                2
            )

            return frame

        # =================================================
        # SUCCESS
        # =================================================

        AttendanceService.mark_attendance(
            student_id,
            confidence=similarity
        )

        self.cooldowns[student_id] = now

        cv2.rectangle(
            frame,
            (x1, y1),
            (x2, y2),
            RecognitionRuntimeConfig.COLOR_GREEN,
            3
        )

        cv2.putText(
            frame,
            f"{name} ({similarity:.2f})",
            (x1, y1 - 10),
            RecognitionRuntimeConfig.FONT,
            0.8,
            RecognitionRuntimeConfig.COLOR_GREEN,
            2
        )

        cv2.putText(
            frame,
            "Presence validee",
            (x1, y2 + 30),
            RecognitionRuntimeConfig.FONT,
            0.7,
            RecognitionRuntimeConfig.COLOR_GREEN,
            2
        )

        return frame

    # -----------------------------------------------------
    # START
    # -----------------------------------------------------

    def start_recognition(self):

        self.cap = cv2.VideoCapture(
            RecognitionRuntimeConfig.CAMERA_ID
        )

        if not self.cap.isOpened():

            logger.error("Camera inaccessible")

            return

        self.cap.set(
            cv2.CAP_PROP_FRAME_WIDTH,
            RecognitionRuntimeConfig.CAMERA_WIDTH
        )

        self.cap.set(
            cv2.CAP_PROP_FRAME_HEIGHT,
            RecognitionRuntimeConfig.CAMERA_HEIGHT
        )

        self.running = True

        logger.info("Reconnaissance demarree")

        while self.running:

            ret, frame = self.cap.read()

            if not ret:
                continue

            try:

                frame = self.process_frame(frame)

            except Exception as e:

                logger.error(
                    f"Erreur process_frame : {e}"
                )

            cv2.imshow(
                "Face Recognition",
                frame
            )

            key = cv2.waitKey(1) & 0xFF

            if key == ord("q"):
                break

            elif key == ord("r"):

                if self.recognizer:

                    self.recognizer.refresh()

                    logger.info("Cache refresh")

        self.stop_recognition()

    # -----------------------------------------------------
    # STOP
    # -----------------------------------------------------

    def stop_recognition(self):

        self.running = False

        if self.cap:
            self.cap.release()

        cv2.destroyAllWindows()


# =========================================================
# COMPAT
# =========================================================

def recognize_faces():

    service = (
        ContinuousRecognitionService()
        .initialize()
    )

    service.start_recognition()