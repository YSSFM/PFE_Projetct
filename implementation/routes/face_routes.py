<<<<<<< HEAD
# -------------------------------------------------------
# IMPORTS
# -------------------------------------------------------

# Flask pour gérer les routes API
from flask import Blueprint, jsonify, request, session, redirect, url_for

# Import service reconnaissance
from services.recognition_service import recognize_face

# Import service enregistrement visage
from services.face_registration_service import register_face

# Import base de données
from db.database import get_connection, close_connection

# Import pour logs
import traceback


# -------------------------------------------------------
# CRÉATION DU BLUEPRINT
# -------------------------------------------------------

# Blueprint Flask pour routes reconnaissance
face_bp = Blueprint("face", __name__)


# -------------------------------------------------------
# ROUTE : RECONNAISSANCE VISAGE
# -------------------------------------------------------

@face_bp.route("/recognize", methods=["GET"])
def recognize():
    """
    Cette route :
    - Lance la caméra
    - Détecte un visage
    - Compare avec base de données
    - Enregistre présence
    """

    try:
        print("=" * 50)
        print("📸 Route: /recognize")
        print("=" * 50)

        # Appel service reconnaissance
        student = recognize_face()

        # Si étudiant reconnu
        if student:
            print(f"✅ Étudiant reconnu : {student['prenom']} {student['nom']}")

            return jsonify({
                "success": True,
                "message": "Présence enregistrée",
                "student": student
            })
        else:
            print("❌ Aucun étudiant reconnu")

            return jsonify({
                "success": False,
                "message": "Aucun visage reconnu"
            })

    except Exception as e:
        print("❌ Erreur reconnaissance")
        print(traceback.format_exc())

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# -------------------------------------------------------
# ROUTE : ENREGISTRER NOUVEAU VISAGE
# -------------------------------------------------------

@face_bp.route("/register-face", methods=["POST"])
def register_new_face():
    """
    Cette route :
    - Reçoit ID étudiant
    - Lance caméra
    - Enregistre visage
    """

    try:
        print("=" * 50)
        print("📸 Route: /register-face")
        print("=" * 50)

        # Récupération JSON
        data = request.json

        # Vérification données
        if not data or "student_id" not in data:
            return jsonify({
                "success": False,
                "message": "student_id requis"
            }), 400

        student_id = data["student_id"]

        print(f"👤 Enregistrement visage étudiant ID : {student_id}")

        # Appel service enregistrement
        success = register_face(student_id)

        if success:
            print("✅ Visage enregistré avec succès")

            return jsonify({
                "success": True,
                "message": "Visage enregistré avec succès"
            })
        else:
            print("❌ Échec enregistrement")

            return jsonify({
                "success": False,
                "message": "Impossible d'enregistrer le visage"
            }), 400

    except Exception as e:
        print("❌ Erreur enregistrement visage")
        print(traceback.format_exc())

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# -------------------------------------------------------
# ROUTE : TEST API
# -------------------------------------------------------

@face_bp.route("/face-test", methods=["GET"])
def face_test():
    """
    Route test pour vérifier API
    """

    return jsonify({
        "message": "Face API fonctionne",
        "status": "OK"
    })
=======
# Importation des modules nécessaires
from flask import Blueprint, request, jsonify, send_file
import cv2  # OpenCV pour accéder à la webcam
import face_recognition
import numpy as np
from database.db import get_connection
from datetime import datetime, date
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import fonts
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
import os

face_bp = Blueprint("face", __name__)

# ROUTE 1 : Enregistrer un visage
@face_bp.route("/register-face/<int:etudiant_id>", methods=["POST"])
def register_face(etudiant_id):

    if "image" not in request.files:
        return jsonify({"error": "No sent image"}), 400

    file = request.files["image"]
    image = face_recognition.load_image_file(file)
    encodings = face_recognition.face_encodings(image)

    if len(encodings) == 0:
        return jsonify({"error": "No face detected"}), 400

    encoding_bytes = encodings[0].tobytes()

    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            "UPDATE etudiant SET face_embedding = %s WHERE id = %s",
            (encoding_bytes, etudiant_id)
        )
        connection.commit()
        return jsonify({"message": "Face successfully registered"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        connection.close()

# ROUTE 2 : Reconnaissance + Présence automatique
@face_bp.route("/recognize", methods=["POST"])
def recognize():

    if "image" not in request.files:
        return jsonify({"error": "No image sent"}), 400

    file = request.files["image"]
    image = face_recognition.load_image_file(file)
    encodings = face_recognition.face_encodings(image)

    if len(encodings) == 0:
        return jsonify({"error": "No face detected"}), 400

    unknown_encoding = encodings[0]

    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT id, nom, prenom, face_embedding 
            FROM etudiant 
            WHERE face_embedding IS NOT NULL
        """)
        students = cursor.fetchall()

        for student in students:

            known_encoding = np.frombuffer(student["face_embedding"], dtype=np.float64)

            match = face_recognition.compare_faces(
                [known_encoding],
                unknown_encoding,
                tolerance=0.5
            )

            if match[0]:

                now = datetime.now()
                today_date = now.date()
                current_time = now.time()

                # SESSION AUTOMATIQUE
                if now.hour < 12:
                    session = "Matin"
                else:
                    session = "Après-midi"

                cursor.execute("""
                    SELECT * FROM presence 
                    WHERE etudiant_id = %s AND date = %s
                """, (student["id"], today_date))

                existing = cursor.fetchone()

                if existing:
                    return jsonify({
                        "message": "Presence already registered today",
                        "nom": student["nom"],
                        "prenom": student["prenom"]
                    })

                cursor.execute("""
                    INSERT INTO presence (etudiant_id, date, heure, session, statut)
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    student["id"],
                    today_date,
                    current_time,
                    session,
                    "Présent"
                ))

                connection.commit()

                return jsonify({
                    "message": "Presence registered successfully",
                    "session": session,
                    "nom": student["nom"],
                    "prenom": student["prenom"]
                })

        return jsonify({"message": "Unknown student"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        connection.close()

# ROUTE 3 : Génération Rapport PDF
@face_bp.route("/generate-report", methods=["GET"])
def generate_report():

    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    today_date = date.today()

    cursor.execute("""
        SELECT e.nom, e.prenom, p.date, p.heure, p.session
        FROM presence p
        JOIN etudiant e ON e.id = p.etudiant_id
        WHERE p.date = %s
    """, (today_date,))

    records = cursor.fetchall()

    file_path = "rapport_presence.pdf"
    doc = SimpleDocTemplate(file_path)
    elements = []

    data = [["Nom", "Prenom", "Date", "Heure", "Session"]]

    for row in records:
        data.append([
            row["nom"],
            row["prenom"],
            str(row["date"]),
            str(row["heure"]),
            row["session"]
        ])

    table = Table(data)
    table.setStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.grey),
        ('GRID', (0,0), (-1,-1), 1, colors.black)
    ])

    elements.append(table)
    doc.build(elements)

    cursor.close()
    connection.close()

    return send_file(file_path, as_attachment=True)

# ROUTE 4 : Marquer automatiquement les absents
def mark_absents():

    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    today_date = date.today()

    cursor.execute("SELECT id FROM etudiant")
    students = cursor.fetchall()

    for student in students:

        cursor.execute("""
            SELECT * FROM presence 
            WHERE etudiant_id = %s AND date = %s
        """, (student["id"], today_date))

        existing = cursor.fetchone()

        if not existing:
            cursor.execute("""
                INSERT INTO presence (etudiant_id, date, heure, session, statut)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                student["id"],
                today_date,
                datetime.now().time(),
                "N/A",
                "Absent"
            ))

    connection.commit()
    cursor.close()
    connection.close()

    return jsonify({"message": "Absent students marked successfully"})

# ROUTE 5 : Reconnaissance en temps réel via Webcam
@face_bp.route("/live-recognition", methods=["GET"])
def live_recognition():

    # Ouvrir la webcam 
    video_capture = cv2.VideoCapture(0)

    # Connexion à la base de données
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    # Récupérer tous les étudiants ayant un encodage
    cursor.execute("""
        SELECT id, nom, prenom, face_embedding 
        FROM etudiant 
        WHERE face_embedding IS NOT NULL
    """)
    students = cursor.fetchall()

    # Liste pour stocker les encodages connus
    known_encodings = []
    known_students = []

    # Conversion des BLOB en numpy array
    for student in students:
        encoding = np.frombuffer(student["face_embedding"], dtype=np.float64)
        known_encodings.append(encoding)
        known_students.append(student)

    print("Webcam started. Press Q to quit.")

    # Boucle infinie pour lire les frames vidéo
    while True:

        # Lire une frame de la webcam
        ret, frame = video_capture.read()

        # Si lecture échoue, on arrête
        if not ret:
            break

        # Convertir BGR (OpenCV) vers RGB (face_recognition)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Détecter les visages dans la frame
        face_locations = face_recognition.face_locations(rgb_frame)

        # Générer les encodages des visages détectés
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

        # Pour chaque visage détecté
        for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):

            # Comparer avec les encodages connus
            matches = face_recognition.compare_faces(
                known_encodings,
                face_encoding,
                tolerance=0.5
            )

            name = "Unknown"

            # Si un match est trouvé
            if True in matches:

                # Récupérer l’index du match
                match_index = matches.index(True)

                # Récupérer infos étudiant
                student = known_students[match_index]

                name = student["nom"] + " " + student["prenom"]

                # Enregistrer la présence automatiquement
                now = datetime.now()
                today_date = now.date()

                # Vérifier si présence déjà enregistrée
                cursor.execute("""
                    SELECT * FROM presence 
                    WHERE etudiant_id = %s AND date = %s
                """, (student["id"], today_date))

                existing = cursor.fetchone()

                if not existing:
                    cursor.execute("""
                        INSERT INTO presence (etudiant_id, date, heure, session, statut)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (
                        student["id"],
                        today_date,
                        now.time(),
                        "Live",
                        "Présent"
                    ))
                    connection.commit()

            # Dessiner un rectangle autour du visage
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)

            # Afficher le nom sous le rectangle
            cv2.putText(
                frame,
                name,
                (left, top - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 0),
                2
            )

        # Afficher la fenêtre vidéo
        cv2.imshow("Live Face Recognition", frame)

        # Quitter si touche Q pressée
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Libérer la webcam
    video_capture.release()

    # Fermer toutes les fenêtres OpenCV
    cv2.destroyAllWindows()

    # Fermer connexion base
    cursor.close()
    connection.close()

    return jsonify({"message": "Live recognition stopped"})
>>>>>>> 588a313535814a9ddfc347cdb31606df74e1aa90
