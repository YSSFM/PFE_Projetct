# ===================================================================
# face_preprocessing_service.py
# SERVICE PREPROCESSING VISAGE
# ===================================================================

import cv2
import numpy as np

# =========================================================
# CONFIG
# =========================================================

class PreprocessingConfig:
    IMG_SIZE = (160, 160)

# =========================================================
# SERVICE
# =========================================================

class FacePreprocessingService:

    @staticmethod
    def normalize_face(face_img):
        """
        Normalisation visage pour CNN
        """

        if face_img is None:
            return None

        face = cv2.resize(
            face_img,
            PreprocessingConfig.IMG_SIZE
        )

        face = face.astype("float32") / 255.0

        return face

    @staticmethod
    def augment_face(face_img):

        augmented = []

        augmented.append(face_img)

        # flip horizontal
        flip = cv2.flip(face_img, 1)
        augmented.append(flip)

        # brightness
        bright = cv2.convertScaleAbs(
            face_img,
            alpha=1.1,
            beta=15
        )

        augmented.append(bright)

        # rotation légère
        h, w = face_img.shape[:2]

        M = cv2.getRotationMatrix2D(
            (w // 2, h // 2),
            5,
            1
        )

        rotated = cv2.warpAffine(
            face_img,
            M,
            (w, h)
        )

        augmented.append(rotated)

        return augmented