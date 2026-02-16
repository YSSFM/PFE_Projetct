from flask import Blueprint, request, jsonify
from database.db import get_connection
import face_recognition
import numpy as np
from PIL import Image
import io

face_bp = Blueprint("face", __name__)

@face_bp.route("/students/<int:student_id>/upload-face", methods=["POST"])
def upload_face(student_id):

    if "image" not in request.files:
        return jsonify({"error": "Aucune image envoyée"}), 400

    file = request.files["image"]

    connection = None
    cursor = None

    try:
        # Lire les bytes
        image_bytes = file.read()

        # Ouvrir avec PIL
        img = Image.open(io.BytesIO(image_bytes))

        # conversion RGB 8bits
        img = img.convert("RGB")

        # Convertir en numpy array
        image = np.array(img)

        # mémoire contiguë
        image = np.ascontiguousarray(image, dtype=np.uint8)

        # Détection visage
        face_locations = face_recognition.face_locations(image)

        if len(face_locations) == 0:
            return jsonify({"error": "Aucun visage détecté"}), 400

        # Extraction embedding
        face_encodings = face_recognition.face_encodings(image, face_locations)

        embedding = face_encodings[0]
        embedding_bytes = embedding.tobytes()

        # Connexion DB
        connection = get_connection()
        cursor = connection.cursor()

        # Vérifier si étudiant existe
        cursor.execute("SELECT id FROM etudiant WHERE id = %s", (student_id,))
        student = cursor.fetchone()

        if not student:
            return jsonify({"error": "Étudiant introuvable"}), 404

        # Mettre à jr embedding
        query = """
        UPDATE etudiant
        SET face_embedding = %s
        WHERE id = %s
        """

        cursor.execute(query, (embedding_bytes, student_id))
        connection.commit()

        return jsonify({"message": "Embedding enregistré avec succès"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
