# ===================================================================
# dataset.py
# GÉNÉRATION DATASET + EMBEDDINGS
# ===================================================================

import os
import cv2
import logging

from services.face_registration_service import (
    FaceRegistrationService
)

from db.database import execute_query

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)

# =========================================================
# MAIN
# =========================================================

def main():

    logger.info("====================================")
    logger.info("DATASET GENERATOR")
    logger.info("====================================")

    students = execute_query(
        """
        SELECT id, nom, prenom
        FROM etudiant
        WHERE is_active = 1
        """,
        fetch_all=True
    )

    if not students:
        logger.warning("Aucun étudiant trouvé")
        return

    service = FaceRegistrationService().initialize()

    for student in students:

        student_id = student["id"]

        full_name = f"{student['nom']}_{student['prenom']}"

        logger.info(f"Traitement : {full_name}")

        success = service.register_student_faces(
            student_id,
            full_name
        )

        if success:
            logger.info(f"✅ Dataset créé : {full_name}")
        else:
            logger.warning(f"❌ Échec : {full_name}")

    logger.info("====================================")
    logger.info("FIN DATASET")
    logger.info("====================================")


if __name__ == "__main__":
    main()