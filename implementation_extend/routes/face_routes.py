# ===================================================================
# face_routes.py - ROUTES VISAGE (VERSION CORRIGÉE AVEC MTCNN)
# VERSION COMPLÈTE FIABILISÉE - HARMONISATION PIPELINE CNN
# ===================================================================

from flask import Blueprint, jsonify, request, render_template, session, redirect, url_for
from db.database import get_connection, close_connection, execute_query
from services.deep_face_service import get_face_recognition_service
import os
import base64
import cv2
import numpy as np
import logging
import time
from mtcnn import MTCNN

logger = logging.getLogger(__name__)

face_bp = Blueprint("face", __name__)

# =========================================================
# CONFIGURATION
# =========================================================
DATASET_PATH = "dataset/raw"
os.makedirs(DATASET_PATH, exist_ok=True)

# Détecteur MTCNN (unifié avec le reste du projet)
detector = MTCNN()


# =========================================================
# PAGE INSCRIPTION
# =========================================================
@face_bp.route("/register-form")
def register_form():
    if "admin" not in session:
        return redirect(url_for("admin"))
    return render_template("register_student.html")


# =========================================================
# UTILITAIRE: DÉCODAGE IMAGE BASE64
# =========================================================
def decode_base64_image(img_base64):
    try:
        img_data = base64.b64decode(img_base64.split(",")[-1])
        np_arr = np.frombuffer(img_data, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        return img
    except Exception as e:
        logger.error(f"Erreur decode image: {e}")
        return None


# =========================================================
# EXTRACTION VISAGE AVEC MTCNN (UNIFIÉE)
# =========================================================
def extract_face_mtcnn(img, min_confidence=0.95, padding=0.2):
    """
    Extrait le visage avec MTCNN - identique à dataset.py
    """
    if img is None:
        return None
    
    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    
    try:
        faces = detector.detect_faces(rgb)
    except Exception as e:
        logger.error(f"Erreur MTCNN: {e}")
        return None
    
    if len(faces) == 0:
        return None
    
    # Prendre le meilleur visage
    best = max(faces, key=lambda x: x["confidence"])
    
    if best["confidence"] < min_confidence:
        return None
    
    x, y, w, h = best["box"]
    
    if w < 50 or h < 50:
        return None
    
    # Ajouter du padding
    x = max(0, x - int(w * padding))
    y = max(0, y - int(h * padding))
    w = min(img.shape[1] - x, w + int(2 * w * padding))
    h = min(img.shape[0] - y, h + int(2 * h * padding))
    
    face = img[y:y+h, x:x+w]
    
    return face if face.size > 0 else None


# =========================================================
# SAVE STUDENT + DATASET CNN
# =========================================================
@face_bp.route("/save_new_student", methods=["POST"])
def save_new_student():
    data = request.json

    nom = data.get("nom", "").strip()
    prenom = data.get("prenom", "").strip()
    matricule = data.get("matricule", "").strip()
    departement_id = data.get("departement_id", 1)
    sexe = data.get("sexe", "M")
    telephone = data.get("telephone", "")
    images = data.get("images", [])

    # Validation
    if not nom or not prenom or not matricule:
        return jsonify({"error": "Champs obligatoires manquants"}), 400

    if len(images) < 5:
        return jsonify({"error": "Minimum 5 images requises"}), 400

    connection = get_connection()
    if connection is None:
        return jsonify({"error": "Erreur DB"}), 500

    cursor = connection.cursor()

    try:
        # Vérifier doublon
        cursor.execute("SELECT id FROM etudiant WHERE matricule=%s", (matricule,))
        if cursor.fetchone():
            return jsonify({"error": "Matricule existe déjà"}), 400

        # Insert étudiant
        cursor.execute("""
            INSERT INTO etudiant (nom, prenom, matricule, departement_id, sexe, telephone)
            VALUES (%s,%s,%s,%s,%s,%s)
        """, (nom, prenom, matricule, departement_id, sexe, telephone))

        student_id = cursor.lastrowid
        connection.commit()

        # Créer dossier dataset
        folder = f"{nom} {prenom}"
        path = os.path.join(DATASET_PATH, folder)
        os.makedirs(path, exist_ok=True)

        saved = 0

        # Sauvegarder les images avec extraction MTCNN
        for i, img_b64 in enumerate(images):
            img = decode_base64_image(img_b64)
            if img is None:
                continue
            
            # Extraire le visage avec MTCNN (unifié)
            face = extract_face_mtcnn(img)
            
            if face is None:
                logger.warning(f"Image {i}: aucun visage détecté")
                continue
            
            # Redimensionner pour le dataset
            face_resized = cv2.resize(face, (160, 160))
            
            filename = f"{matricule}_{int(time.time())}_{i}.jpg"
            filepath = os.path.join(path, filename)
            
            cv2.imwrite(filepath, face_resized)
            saved += 1

        return jsonify({
            "success": True,
            "student_id": student_id,
            "images_saved": saved,
            "folder": folder
        })

    except Exception as e:
        connection.rollback()
        logger.error(f"Erreur save student: {e}")
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        close_connection(connection)


# =========================================================
# GÉNÉRATION EMBEDDINGS (après inscription)
# =========================================================
@face_bp.route("/api/generate-embeddings/<int:student_id>", methods=["POST"])
def generate_embeddings(student_id):
    connection = get_connection()
    if connection is None:
        return jsonify({"error": "DB error"}), 500

    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute("SELECT nom, prenom, matricule FROM etudiant WHERE id=%s", (student_id,))
        student = cursor.fetchone()

        if not student:
            return jsonify({"error": "Étudiant introuvable"}), 404

        folder = f"{student['nom']} {student['prenom']}"
        path = os.path.join(DATASET_PATH, folder)

        if not os.path.exists(path):
            return jsonify({"error": "Dataset introuvable"}), 404

        recognizer = get_face_recognition_service()
        count = 0

        for file in os.listdir(path):
            if file.lower().endswith((".jpg", ".png", ".jpeg")):
                img_path = os.path.join(path, file)
                img = cv2.imread(img_path)

                if img is None:
                    continue

                # CORRECTION DE FIABILITÉ CRITIQUE :
                # Bien que l'image stockée dans le dossier brut soit déjà recadrée par la route d'inscription,
                # la fonction `get_face_embedding()` requiert une validation stricte de l'espace de couleur (RGB).
                # Passer l'image par `extract_face_strictly` ou appeler directement `get_face_embedding` (qui
                # gère désormais la conversion BGR->RGB de manière sécurisée) protège l'alignement des poids du CNN.
                embedding = recognizer.get_face_embedding(img)

                if embedding is not None:
                    recognizer.save_face_embedding(student_id, embedding, img_path, 1.0)
                    count += 1

        # Rafraîchir synchrone du cache mémoire du service
        recognizer.refresh()

        return jsonify({
            "message": "Embeddings générés",
            "count": count,
            "total_in_db": recognizer.get_embedding_count()
        })

    except Exception as e:
        logger.error(f"Erreur embeddings: {e}")
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        close_connection(connection)


# =========================================================
# TEST API
# =========================================================
@face_bp.route("/face-test")
def face_test():
    return jsonify({"message": "Face API OK", "status": "running", "detector": "MTCNN"})