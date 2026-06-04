# ===================================================================
# attendance_routes.py - ROUTES PRÉSENCE (CLEAN VERSION)
# ===================================================================

from flask import Blueprint, jsonify, request
from datetime import datetime, date

from services.attendance_service import AttendanceService
from db.database import execute_query

attendance_bp = Blueprint("attendance", __name__, url_prefix="/api/attendance")


# =========================================================
# UTILITAIRE SAFE DATE PARSER
# =========================================================
def parse_date(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


# =========================================================
# TODAY ATTENDANCE
# =========================================================
@attendance_bp.route("/today", methods=["GET"])
def get_today_attendance():
    data = AttendanceService.get_today_attendance()
    return jsonify(data)


# =========================================================
# ALL ATTENDANCE (LATEST 100)
# =========================================================
@attendance_bp.route("/all", methods=["GET"])
def get_all_attendance():

    query = """
        SELECT p.*, e.nom, e.prenom, e.matricule, d.nom AS departement
        FROM presence p
        JOIN etudiant e ON p.etudiant_id = e.id
        JOIN departement d ON e.departement_id = d.id
        ORDER BY p.presence_date DESC, p.presence_time DESC
        LIMIT 100
    """

    data = execute_query(query, fetch_all=True) or []
    return jsonify(data)


# =========================================================
# STUDENT HISTORY
# =========================================================
@attendance_bp.route("/student/<int:student_id>", methods=["GET"])
def get_student_attendance(student_id):
    data = AttendanceService.get_student_attendance(student_id)
    return jsonify(data)


# =========================================================
# STATS
# =========================================================
@attendance_bp.route("/stats", methods=["GET"])
def get_attendance_stats():

    start_date = parse_date(request.args.get("start_date"))
    end_date = parse_date(request.args.get("end_date"))

    stats = AttendanceService.get_attendance_stats(start_date, end_date)

    return jsonify(stats)


# =========================================================
# ABSENTS
# =========================================================
@attendance_bp.route("/absents", methods=["GET"])
def get_absents():

    target_date = parse_date(request.args.get("date"))

    if not target_date:
        target_date = date.today()

    data = AttendanceService.get_absents_for_date(target_date)

    return jsonify(data)