# ===================================================================
# services/attendance_service.py
# VERSION FINALE
# ===================================================================

from datetime import datetime, date
from db.database import execute_query
import logging

logger = logging.getLogger(__name__)

class AttendanceService:

    @staticmethod
    def mark_attendance(student_id, confidence=0.0):

        today = date.today()

        now = datetime.now()

        current_time = now.time()

        hour = now.hour

        if hour < 12:
            session = "Matin"
        elif hour < 18:
            session = "Apres-midi"
        else:
            session = "Soir"

        existing = execute_query(
            """
            SELECT id
            FROM presence
            WHERE
                etudiant_id=%s
                AND presence_date=%s
                AND session=%s
            """,
            (
                student_id,
                today,
                session
            ),
            fetch_one=True
        )

        if existing:
            return False

        query = """
            INSERT INTO presence
            (
                etudiant_id,
                presence_date,
                presence_time,
                session,
                statut,
                confidence_score,
                verification_mode
            )
            VALUES (%s,%s,%s,%s,%s,%s,%s)
        """

        execute_query(
            query,
            (
                student_id,
                today,
                current_time,
                session,
                "Present",
                confidence,
                "FaceRecognition"
            ),
            commit=True
        )

        logger.info(f"Présence enregistrée: {student_id}")

        return True

    @staticmethod
    def get_today_attendance():

        query = """
            SELECT
                p.*,
                e.nom,
                e.prenom,
                e.matricule
            FROM presence p
            JOIN etudiant e
                ON e.id = p.etudiant_id
            WHERE p.presence_date = CURDATE()
            ORDER BY p.presence_time DESC
        """

        return execute_query(query, fetch_all=True) or []

    @staticmethod
    def get_student_attendance(student_id):

        query = """
            SELECT *
            FROM presence
            WHERE etudiant_id=%s
            ORDER BY presence_date DESC
        """

        return execute_query(
            query,
            (student_id,),
            fetch_all=True
        ) or []