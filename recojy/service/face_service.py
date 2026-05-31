import os
import cv2
import numpy as np
import face_recognition
from models.custom_cnn import CustomCNNFaceModel

# Ce service orchestre la logique de traitement d'images et d'analyse biométrique.

# Instanciation de notre modèle personnalisé
custom_model = CustomCNNFaceModel()

def detect_and_crop_face_cnn(image_bytes, use_custom=False):
    try:
        # Convertir les octets en tableau numpy
        nparr = np.frombuffer(image_bytes, np.uint8)
        # Lire l'image avec OpenCV
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # SÉCURITÉ : Vérifier si l'image est valide et non vide
        if img is None or img.size == 0 or img.shape[0] == 0 or img.shape[1] == 0:
            print("Erreur face_service : Image reçue vide ou non décodable.")
            return None, None

        # S'assurer que l'image est bien au format 8 bits standard 
        if len(img.shape) == 3 and img.shape[2] == 4:
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

        # Convertir en RGB pour face_recognition (exigé par dlib)
        rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        rgb_img = np.ascontiguousarray(rgb_img, dtype=np.uint8)

        # Détecter les visages (utiliser hog si cnn est trop lourd ou pose problème)
        face_locations = face_recognition.face_locations(rgb_img, model="hog")

        if len(face_locations) > 0:
            top, right, bottom, left = face_locations[0]
            # Rogner le visage détecté
            cropped_face = img[top:bottom, left:right]
            
            # Ré-encoder l'image rognée en JPG pour la base de données
            _, encoded_img = cv2.imencode('.jpg', cropped_face)
            return cropped_face, encoded_img.tobytes()
        
        # Si aucun visage n'est détecté, retourner l'image entière pour éviter le blocage
        print("Attention : Aucun visage détecté, sauvegarde de l'image entière.")
        _, encoded_img = cv2.imencode('.jpg', img)
        return img, encoded_img.tobytes()

    except Exception as e:
        print(f"Erreur interne critique dans face_service : {e}")
        return None, None

def generate_face_embeddings(rgb_img, use_custom=False):
    try:
        # S'assurer que la matrice est au bon format 8-bit RGB
        rgb_img = np.ascontiguousarray(rgb_img, dtype=np.uint8)
        encodings = face_recognition.face_encodings(rgb_img)
        if len(encodings) > 0:
            return encodings[0]
        return None
    except Exception as e:
        print(f"Erreur génération embeddings : {e}")
        return None