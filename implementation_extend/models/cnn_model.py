# ===================================================================
# models/cnn_model.py
# WRAPPER FACENET PROFESSIONNEL
# ===================================================================

import cv2
import torch
import numpy as np
import logging

from facenet_pytorch import InceptionResnetV1

logger = logging.getLogger(__name__)


# =========================================================
# CONFIG
# =========================================================

class ModelConfig:

    INPUT_SIZE = 160

    DEVICE = (
        "cuda"
        if torch.cuda.is_available()
        else "cpu"
    )


# =========================================================
# MODEL
# =========================================================

class FaceRecognitionModel:

    def __init__(self):

        self.model = None

        self.loaded = False

    # -----------------------------------------------------
    # LOAD
    # -----------------------------------------------------

    def load(self):

        try:

            self.model = (
                InceptionResnetV1(
                    pretrained="vggface2"
                )
                .eval()
                .to(ModelConfig.DEVICE)
            )

            self.loaded = True

            logger.info(
                "FaceNet chargé avec succès"
            )

            return True

        except Exception as e:

            logger.error(
                f"Erreur chargement modèle: {e}"
            )

            return False

    # -----------------------------------------------------
    # PREPROCESS
    # -----------------------------------------------------

    def preprocess(self, image):

        image = cv2.resize(
            image,
            (
                ModelConfig.INPUT_SIZE,
                ModelConfig.INPUT_SIZE
            )
        )

        image = cv2.cvtColor(
            image,
            cv2.COLOR_BGR2RGB
        )

        tensor = torch.tensor(
            image,
            dtype=torch.float32
        )

        tensor = tensor.permute(2, 0, 1)

        tensor = tensor.unsqueeze(0)

        tensor = tensor / 255.0

        return tensor.to(ModelConfig.DEVICE)

    # -----------------------------------------------------
    # EMBEDDING
    # -----------------------------------------------------

    def predict_embedding(self, image):

        if not self.loaded:
            return None

        try:

            tensor = self.preprocess(image)

            with torch.no_grad():

                embedding = self.model(tensor)

            embedding = (
                embedding
                .cpu()
                .numpy()[0]
            )

            norm = np.linalg.norm(embedding)

            if norm > 0:
                embedding = embedding / norm

            return embedding.astype(np.float32)

        except Exception as e:

            logger.error(
                f"Erreur embedding: {e}"
            )

            return None


# =========================================================
# TRAIN PLACEHOLDER
# =========================================================

def train_cnn():

    logger.info("""
    ==================================================
    FaceNet pré-entraîné utilisé.
    Aucun entraînement nécessaire.
    ==================================================
    """)

    return True