# ===================================================================
# face_registration_service.py
# VERSION STABLE
# ===================================================================

import os
import cv2
import logging
from datetime import datetime

from services.deep_face_service import (
    get_face_recognition_service
)

from db.database import save_face_embedding

logger = logging.getLogger(__name__)

# =========================================================
# CONFIG
# =========================================================

class RegistrationConfig:

    CAMERA_ID = 0

    WIDTH = 640
    HEIGHT = 480

    IMG_SIZE = (160, 160)

    MAX_IMAGES = 5

    DATASET_PATH = "dataset/raw"

# =========================================================
# SERVICE
# =========================================================

class FaceRegistrationService:

    def __init__(self):

        self.recognizer = None
        self.face_detector = None

    # =====================================================
    # INITIALIZATION
    # =====================================================

    def initialize(self):

        self.recognizer = get_face_recognition_service()

        cascade_path = (
            cv2.data.haarcascades
            + "haarcascade_frontalface_default.xml"
        )

        self.face_detector = cv2.CascadeClassifier(
            cascade_path
        )

        os.makedirs(
            RegistrationConfig.DATASET_PATH,
            exist_ok=True
        )

        logger.info(
            "FaceRegistrationService initialisé"
        )

        return self

    # =====================================================
    # REGISTER
    # =====================================================

    def register_student_faces(
        self,
        student_id,
        student_name
    ):

        student_folder = os.path.join(
            RegistrationConfig.DATASET_PATH,
            student_name
        )

        os.makedirs(student_folder, exist_ok=True)

        cap = cv2.VideoCapture(
            RegistrationConfig.CAMERA_ID
        )

        cap.set(
            cv2.CAP_PROP_FRAME_WIDTH,
            RegistrationConfig.WIDTH
        )

        cap.set(
            cv2.CAP_PROP_FRAME_HEIGHT,
            RegistrationConfig.HEIGHT
        )

        if not cap.isOpened():

            logger.error(
                "Impossible d'ouvrir la webcam"
            )

            return False

        logger.info(
            f"Capture dataset : {student_name}"
        )

        count = 0

        while count < RegistrationConfig.MAX_IMAGES:

            ret, frame = cap.read()

            if not ret:
                continue

            gray = cv2.cvtColor(
                frame,
                cv2.COLOR_BGR2GRAY
            )

            faces = self.face_detector.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(100, 100)
            )

            for (x, y, w, h) in faces:

                face = frame[y:y+h, x:x+w]

                if face.size == 0:
                    continue

                face = cv2.resize(
                    face,
                    RegistrationConfig.IMG_SIZE
                )

                filename = (
                    f"{student_id}_"
                    f"{count}_"
                    f"{datetime.now().strftime('%H%M%S')}.jpg"
                )

                filepath = os.path.join(
                    student_folder,
                    filename
                )

                cv2.imwrite(filepath, face)

                embedding = (
                    self.recognizer
                    .get_face_embedding(face)
                )

                if embedding is not None:

                    save_face_embedding(
                        student_id=student_id,
                        embedding=embedding,
                        image_path=filepath,
                        quality_score=1.0
                    )

                count += 1

                logger.info(
                    f"Image {count}/"
                    f"{RegistrationConfig.MAX_IMAGES}"
                )

                cv2.rectangle(
                    frame,
                    (x, y),
                    (x+w, y+h),
                    (0, 255, 0),
                    2
                )

                cv2.putText(
                    frame,
                    f"{count}/{RegistrationConfig.MAX_IMAGES}",
                    (x, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 0),
                    2
                )

            cv2.imshow(
                "Enregistrement Dataset",
                frame
            )

            key = cv2.waitKey(1)

            if key == ord("q"):
                break

        cap.release()

        cv2.destroyAllWindows()

        logger.info(
            f"Dataset terminé : {student_name}"
        )

        return True