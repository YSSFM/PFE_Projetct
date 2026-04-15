from flask import Blueprint, jsonify, request, render_template, session, redirect, url_for
from services.recognition_service import recognize_face
from services.face_registration_service import register_face
from db.database import get_connection, close_connection
import traceback
import os
import base64

face_bp = Blueprint("face", __name__)


# -------------------------------------------------------
# ROUTE: Page du formulaire d'inscription
# -------------------------------------------------------
@face_bp.route("/register-form")
def register_form():
    """Affiche le formulaire d'inscription"""
    if "admin" not in session:
        return redirect(url_for("admin"))
    return render_template("register_student.html")


# -------------------------------------------------------
# ROUTE: Récupérer l'image temporaire
# -------------------------------------------------------
@face_bp.route("/get_temp_encoding", methods=["GET"])
def get_temp_encoding():
    """Récupère l'image du visage capturé"""
    try:
        # Chercher la dernière image capturée
        for f in os.listdir('.'):
            if f.startswith('capture_') and f.endswith('.jpg'):
                with open(f, "rb") as img_file:
                    image_data = base64.b64encode(img_file.read()).decode('utf-8')
                return jsonify({"success": True, "image": image_data})
        return jsonify({"success": False, "error": "Aucune image"}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# -------------------------------------------------------
# ROUTE: Sauvegarder le nouvel étudiant
# -------------------------------------------------------
@face_bp.route("/save_new_student", methods=["POST"])
def save_new_student():
    """Sauvegarde un nouvel étudiant"""
    data = request.json
    
    nom = data.get("nom", "").strip()
    prenom = data.get("prenom", "").strip()
    matricule = data.get("matricule", "").strip()
    departement_id = data.get("departement_id", 1)
    sexe = data.get("sexe", "M")
    telephone = data.get("telephone", "")
    
    if not nom or not prenom or not matricule:
        return jsonify({"error": "Nom, prénom et matricule requis"}), 400
    
    # Chercher l'empreinte temporaire
    embedding_bytes = None
    for f in os.listdir('.'):
        if f.startswith('capture_') and f.endswith('.jpg'):
            # L'empreinte est déjà en base, l'étudiant doit être créé sans empreinte
            # L'utilisateur devra refaire l'enregistrement
            pass
    
    connection = get_connection()
    if connection is None:
        return jsonify({"error": "Erreur connexion DB"}), 500
    
    cursor = connection.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO etudiant (nom, prenom, matricule, departement_id, sexe, telephone)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (nom, prenom, matricule, departement_id, sexe, telephone))
        
        connection.commit()
        student_id = cursor.lastrowid
        
        return jsonify({"success": True, "message": "Étudiant ajouté avec succès", "id": student_id})
        
    except Exception as e:
        connection.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        close_connection(connection)


# -------------------------------------------------------
# ROUTE: Test API
# -------------------------------------------------------
@face_bp.route("/face-test", methods=["GET"])
def face_test():
    return jsonify({"message": "Face API fonctionne", "status": "OK"})
