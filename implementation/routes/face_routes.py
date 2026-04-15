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