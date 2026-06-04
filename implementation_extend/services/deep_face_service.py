# ===================================================================
# services/deep_face_service.py
# VERSION FINALE PROFESSIONNELLE
# ===================================================================

import cv2
import numpy as np
import logging
from mtcnn import MTCNN
from facenet_pytorch import InceptionResnetV1

import torch

from db.database import (
    load_face_embeddings,
    save_face_embedding
)

logger = logging.getLogger(__name__)


# =========================================================
# CONFIG
# =========================================================

class RecognitionConfig:

    IMG_SIZE = 160

    MTCNN_CONFIDENCE = 0.95

    FACE_PADDING = 0.25

    RECOGNITION_THRESHOLD = 0.72

    DEVICE = "cuda" if torch.cuda.is_available() else "cpu"


# =========================================================
# SERVICE
# =========================================================

class FaceRecognitionService:

    def __init__(self):

        self.mtcnn = None

        self.model = None

        self.embeddings = []

        self.initialized = False

    # -----------------------------------------------------
    # INITIALIZE
    # -----------------------------------------------------

    def initialize(self):

        if self.initialized:
            return self

        logger.info("Chargement MTCNN...")

        self.mtcnn = MTCNN()

        logger.info("Chargement FaceNet...")

        self.model = InceptionResnetV1(
            pretrained="vggface2"
        ).eval().to(RecognitionConfig.DEVICE)

        self.refresh()

        self.initialized = True

        logger.info("FaceRecognitionService prêt")

        return self

    # -----------------------------------------------------
    # REFRESH CACHE
    # -----------------------------------------------------

    def refresh(self):

        self.embeddings = load_face_embeddings()

        logger.info(
            f"{len(self.embeddings)} embeddings chargés"
        )

    # -----------------------------------------------------
    # FACE DETECTION
    # -----------------------------------------------------

    def detect_faces(self, frame):

        rgb = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2RGB
        )

        detections = self.mtcnn.detect_faces(rgb)

        results = []

        for det in detections:

            confidence = det["confidence"]

            if confidence < RecognitionConfig.MTCNN_CONFIDENCE:
                continue

            x, y, w, h = det["box"]

            if w < 80 or h < 80:
                continue

            pad_x = int(w * RecognitionConfig.FACE_PADDING)
            pad_y = int(h * RecognitionConfig.FACE_PADDING)

            x1 = max(0, x - pad_x)
            y1 = max(0, y - pad_y)

            x2 = min(frame.shape[1], x + w + pad_x)
            y2 = min(frame.shape[0], y + h + pad_y)

            face = frame[y1:y2, x1:x2]

            if face.size == 0:
                continue

            results.append({
                "box": (x1, y1, x2, y2),
                "face": face,
                "confidence": confidence
            })

        return results

    # -----------------------------------------------------
    # EMBEDDING
    # -----------------------------------------------------

    def get_face_embedding(self, face):

        try:

            face = cv2.resize(
                face,
                (
                    RecognitionConfig.IMG_SIZE,
                    RecognitionConfig.IMG_SIZE
                )
            )

            face = cv2.cvtColor(
                face,
                cv2.COLOR_BGR2RGB
            )

            tensor = torch.tensor(
                face,
                dtype=torch.float32
            ).permute(2, 0, 1)

            tensor = tensor.unsqueeze(0)

            tensor = tensor / 255.0

            tensor = tensor.to(RecognitionConfig.DEVICE)

            with torch.no_grad():

                embedding = self.model(tensor)

            embedding = embedding.cpu().numpy()[0]

            norm = np.linalg.norm(embedding)

            if norm > 0:
                embedding = embedding / norm

            return embedding.astype(np.float32)

        except Exception as e:

            logger.error(f"Embedding error: {e}")

            return None

    # -----------------------------------------------------
    # RECOGNIZE
    # -----------------------------------------------------

    def recognize_face(self, embedding):

        if len(self.embeddings) == 0:
            return None

        best_similarity = -1

        best_student = None

        for row in self.embeddings:

            db_embedding = row["embedding"]

            similarity = np.dot(
                embedding,
                db_embedding
            )

            if similarity > best_similarity:

                best_similarity = similarity

                best_student = row

        if best_student is None:
            return None

        accepted = (
            best_similarity >=
            RecognitionConfig.RECOGNITION_THRESHOLD
        )

        save_recognition_log(
            student_id=(
                best_student["student_id"]
                if accepted else None
            ),
            predicted_name=best_student["name"],
            similarity_score=float(best_similarity),
            decision=(
                "Accepted"
                if accepted else "Rejected"
            )
        )

        if not accepted:
            return None

        return {
            "student_id": best_student["student_id"],
            "name": best_student["name"],
            "matricule": best_student["matricule"],
            "similarity": float(best_similarity)
        }

    # -----------------------------------------------------
    # SAVE EMBEDDING
    # -----------------------------------------------------

    def save_face_embedding(
        self,
        student_id,
        embedding,
        image_path=None,
        quality_score=1.0
    ):

        return save_embedding(
            student_id,
            embedding,
            image_path,
            quality_score
        )


# =========================================================
# SINGLETON
# =========================================================

_service = None


def get_face_recognition_service():

    global _service

    if _service is None:

        _service = FaceRecognitionService()

        _service.initialize()

    return _service


def refresh_embeddings():

    service = get_face_recognition_service()

    service.refresh()