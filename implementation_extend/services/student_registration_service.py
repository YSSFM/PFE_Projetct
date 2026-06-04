# ===================================================================
# services/student_registration_service.py
# VERSION FINALE
# ===================================================================

import os
import cv2
import shutil
import logging

from datetime import datetime

from mtcnn import MTCNN

from werkzeug.utils import secure_filename

from db.database import execute_query

logger = logging.getLogger(__name__)


# =========================================================
# CONFIG
# =========================================================

RAW_DATASET_PATH = "dataset/raw"

MIN_IMAGES = 5

IMG_SIZE = 160

ALLOWED_EXTENSIONS = {
    "jpg",
    "jpeg",
    "png"
}

detector = MTCNN()


# =========================================================
# SERVICE
# =========================================================

class StudentRegistrationService:

    @staticmethod
    def allowed(filename):

        return (
            "." in filename
            and
            filename.rsplit(".", 1)[1]
            .lower() in ALLOWED_EXTENSIONS
        )

    # -----------------------------------------------------
    # EXTRACT FACE
    # -----------------------------------------------------

    @staticmethod
    def extract_face(image):

        rgb = cv2.cvtColor(
            image,
            cv2.COLOR_BGR2RGB
        )

        detections = detector.detect_faces(rgb)

        if len(detections) == 0:
            return None

        best = max(
            detections,
            key=lambda x: x["confidence"]
        )

        if best["confidence"] < 0.95:
            return None

        x, y, w, h = best["box"]

        if w < 80 or h < 80:
            return None

        x = max(0, x)
        y = max(0, y)

        face = image[y:y+h, x:x+w]

        if face.size == 0:
            return None

        face = cv2.resize(
            face,
            (IMG_SIZE, IMG_SIZE)
        )

        return face

    # -----------------------------------------------------
    # SAVE AUGMENTATIONS
    # -----------------------------------------------------

    @staticmethod
    def save_augmentations(
        face,
        output_folder,
        prefix
    ):

        saved = 0

        variants = []

        variants.append(face)

        variants.append(
            cv2.flip(face, 1)
        )

        bright = cv2.convertScaleAbs(
            face,
            alpha=1.1,
            beta=10
        )

        variants.append(bright)

        dark = cv2.convertScaleAbs(
            face,
            alpha=0.9,
            beta=-10
        )

        variants.append(dark)

        for i, img in enumerate(variants):

            filename = (
                f"{prefix}_{i}.jpg"
            )

            path = os.path.join(
                output_folder,
                filename
            )

            cv2.imwrite(path, img)

            saved += 1

        return saved

    # -----------------------------------------------------
    # REGISTER
    # -----------------------------------------------------

    @staticmethod
    def register_student(
        student_data,
        photos
    ):

        if len(photos) < MIN_IMAGES:

            return (
                False,
                f"Minimum {MIN_IMAGES} photos"
            )

        exists = execute_query(
            """
            SELECT id
            FROM etudiant
            WHERE matricule=%s
            """,
            (student_data["matricule"],),
            fetch_one=True
        )

        if exists:

            return (
                False,
                "Matricule déjà existant"
            )

        student_id = execute_query(
            """
            INSERT INTO etudiant
            (
                departement_id,
                matricule,
                nom,
                prenom,
                sexe,
                telephone,
                email,
                annee_academique,
                semestre,
                is_active
            )
            VALUES
            (%s,%s,%s,%s,%s,%s,%s,%s,%s,TRUE)
            """,
            (
                student_data["departement_id"],
                student_data["matricule"],
                student_data["nom"],
                student_data["prenom"],
                student_data["sexe"],
                student_data.get("telephone"),
                student_data.get("email"),
                student_data.get("annee_academique"),
                student_data.get("semestre")
            )
        )

        if not student_id:

            return (
                False,
                "Erreur insertion"
            )

        folder_name = (
            f"{student_data['nom']} "
            f"{student_data['prenom']}"
        )

        folder_path = os.path.join(
            RAW_DATASET_PATH,
            folder_name
        )

        os.makedirs(folder_path, exist_ok=True)

        total_saved = 0

        try:

            for photo in photos:

                if not StudentRegistrationService.allowed(
                    photo.filename
                ):
                    continue

                tmp_name = secure_filename(
                    photo.filename
                )

                tmp_path = os.path.join(
                    folder_path,
                    tmp_name
                )

                photo.save(tmp_path)

                image = cv2.imread(tmp_path)

                os.remove(tmp_path)

                if image is None:
                    continue

                face = (
                    StudentRegistrationService
                    .extract_face(image)
                )

                if face is None:
                    continue

                ts = datetime.now().strftime(
                    "%Y%m%d_%H%M%S"
                )

                total_saved += (
                    StudentRegistrationService
                    .save_augmentations(
                        face,
                        folder_path,
                        ts
                    )
                )

            if total_saved < MIN_IMAGES:

                execute_query(
                    """
                    DELETE FROM etudiant
                    WHERE id=%s
                    """,
                    (student_id,),
                    commit=True
                )

                shutil.rmtree(folder_path)

                return (
                    False,
                    "Visages insuffisants"
                )

            return (
                True,
                student_id
            )

        except Exception as e:

            logger.error(e)

            return (
                False,
                str(e)
            )