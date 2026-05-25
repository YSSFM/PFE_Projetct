# ===================================================================
# student_routes.py - VERSION CORRIGÉE STABLE
# ===================================================================

from flask import Blueprint, request, jsonify, render_template, redirect, url_for, session
from db.database import get_connection, execute_query
from mysql.connector import Error
import os
import time
import subprocess
import sys
import cv2

student_bp = Blueprint("student", __name__)

# ===================================================================
# UTILITAIRE SECURITE SESSION
# ===================================================================

def require_admin():
    return "admin" in session


# ===================================================================
# PAGES HTML
# ===================================================================

@student_bp.route("/students")
def students_page():
    if not require_admin():
        return redirect(url_for("admin"))
    return render_template("students.html")


@student_bp.route("/students/list")
def students_list():
    if not require_admin():
        return redirect(url_for("admin"))
    return render_template("students.html")


# ===================================================================
# GET ALL STUDENTS
# ===================================================================

@student_bp.route("/api/students", methods=["GET"])
def api_get_students():
    if not require_admin():
        return jsonify({"error": "Non authentifié"}), 401

    conn = get_connection()
    if not conn:
        return jsonify({"error": "Erreur connexion"}), 500

    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT e.*, d.nom AS departement_nom
            FROM etudiant e
            LEFT JOIN departement d ON d.id = e.departement_id
            WHERE e.is_active = TRUE
            ORDER BY e.id DESC
        """)
        students = cursor.fetchall()

        # OPTIMISATION: éviter requête dans boucle si possible
        for s in students:
            cursor.execute(
                "SELECT COUNT(*) AS count FROM face_embeddings WHERE etudiant_id=%s",
                (s["id"],)
            )
            s["has_face"] = cursor.fetchone()["count"] > 0
            s["face_embedding"] = None

        return jsonify(students)

    except Error as e:
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        conn.close()


# ===================================================================
# GET ONE STUDENT
# ===================================================================

@student_bp.route("/api/students/<int:student_id>", methods=["GET"])
def api_get_student(student_id):
    if not require_admin():
        return jsonify({"error": "Non authentifié"}), 401

    conn = get_connection()
    if not conn:
        return jsonify({"error": "Erreur connexion"}), 500

    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT e.*, d.nom AS departement_nom
            FROM etudiant e
            LEFT JOIN departement d ON d.id = e.departement_id
            WHERE e.id = %s
        """, (student_id,))

        student = cursor.fetchone()

        if not student:
            return jsonify({"error": "Étudiant introuvable"}), 404

        cursor.execute(
            "SELECT COUNT(*) AS count FROM face_embeddings WHERE etudiant_id=%s",
            (student_id,)
        )

        student["has_face"] = cursor.fetchone()["count"] > 0
        student["face_embedding"] = None

        return jsonify(student)

    except Error as e:
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        conn.close()


# ===================================================================
# ADD STUDENT
# ===================================================================

@student_bp.route("/api/students", methods=["POST"])
def api_add_student():
    if not require_admin():
        return jsonify({"error": "Non authentifié"}), 401

    data = request.get_json(silent=True) or {}

    nom = data.get("nom", "").strip()
    prenom = data.get("prenom", "").strip()
    matricule = data.get("matricule", "").strip()
    departement_id = data.get("departement_id")

    if not all([nom, prenom, matricule, departement_id]):
        return jsonify({"error": "Champs requis"}), 400

    conn = get_connection()
    if not conn:
        return jsonify({"error": "Erreur DB"}), 500

    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO etudiant
            (nom, prenom, matricule, departement_id, sexe, telephone,
             annee_academique, semestre, is_active)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,TRUE)
        """, (
            nom,
            prenom,
            matricule,
            departement_id,
            data.get("sexe", "M"),
            data.get("telephone", ""),
            data.get("annee_academique", ""),
            data.get("semestre", "")
        ))

        conn.commit()
        student_id = cursor.lastrowid

        # dossier dataset
        folder = f"{nom} {prenom}"
        path = os.path.join("dataset", "raw", folder)
        os.makedirs(path, exist_ok=True)

        return jsonify({"message": "Étudiant ajouté", "id": student_id}), 201

    except Error as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        conn.close()


# ===================================================================
# UPDATE STUDENT
# ===================================================================

@student_bp.route("/api/students/<int:student_id>", methods=["PUT"])
def api_update_student(student_id):
    if not require_admin():
        return jsonify({"error": "Non authentifié"}), 401

    data = request.get_json(silent=True) or {}

    conn = get_connection()
    if not conn:
        return jsonify({"error": "DB error"}), 500

    cursor = conn.cursor()

    try:
        cursor.execute("""
            UPDATE etudiant
            SET nom=%s, prenom=%s, matricule=%s,
                departement_id=%s, sexe=%s, telephone=%s,
                annee_academique=%s, semestre=%s
            WHERE id=%s
        """, (
            data.get("nom"),
            data.get("prenom"),
            data.get("matricule"),
            data.get("departement_id"),
            data.get("sexe", "M"),
            data.get("telephone", ""),
            data.get("annee_academique", ""),
            data.get("semestre", ""),
            student_id
        ))

        if cursor.rowcount == 0:
            return jsonify({"error": "Introuvable"}), 404

        conn.commit()
        return jsonify({"message": "Mis à jour"})

    except Error as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        conn.close()


# ===================================================================
# DELETE STUDENT (SOFT DELETE)
# ===================================================================

@student_bp.route("/api/students/<int:student_id>", methods=["DELETE"])
def api_delete_student(student_id):
    if not require_admin():
        return jsonify({"error": "Non authentifié"}), 401

    conn = get_connection()
    if not conn:
        return jsonify({"error": "DB error"}), 500

    cursor = conn.cursor()

    try:
        cursor.execute(
            "UPDATE etudiant SET is_active=FALSE WHERE id=%s",
            (student_id,)
        )

        conn.commit()
        return jsonify({"message": "Supprimé"})

    except Error as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        conn.close()


# ===================================================================
# UPLOAD PHOTOS
# ===================================================================

@student_bp.route("/api/upload-photos", methods=["POST"])
def api_upload_photos():
    if not require_admin():
        return jsonify({"error": "Non authentifié"}), 401

    student_id = request.form.get("student_id")
    files = request.files.getlist("photos")

    if not student_id:
        return jsonify({"error": "ID requis"}), 400

    if len(files) < 5:
        return jsonify({"error": "Min 5 photos"}), 400

    conn = get_connection()
    if not conn:
        return jsonify({"error": "DB error"}), 500

    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(
            "SELECT nom, prenom FROM etudiant WHERE id=%s",
            (student_id,)
        )
        student = cursor.fetchone()

        if not student:
            return jsonify({"error": "Introuvable"}), 404

        folder = f"{student['nom']} {student['prenom']}"
        path = os.path.join("dataset", "raw", folder)
        os.makedirs(path, exist_ok=True)

        saved = 0

        for i, f in enumerate(files):
            if f and f.filename.lower().endswith((".jpg", ".jpeg", ".png")):
                filename = f"{int(time.time())}_{i}.jpg"
                f.save(os.path.join(path, filename))
                saved += 1

        return jsonify({"message": f"{saved} photos sauvegardées"})

    finally:
        cursor.close()
        conn.close()


# ===================================================================
# DEPARTEMENTS
# ===================================================================

@student_bp.route("/api/departements", methods=["GET"])
def api_get_departements():
    conn = get_connection()
    if not conn:
        return jsonify({"error": "DB error"}), 500

    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("SELECT id, nom FROM departement ORDER BY nom")
        return jsonify(cursor.fetchall())

    finally:
        cursor.close()
        conn.close()