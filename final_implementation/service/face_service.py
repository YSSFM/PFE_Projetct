# service/face_service.py
# Service de reconnaissance faciale avec gestion du modèle actif

import os
import cv2
import numpy as np
import face_recognition
from sklearn.svm import SVC
import pickle
from database import DatabaseContext

# ==================== VARIABLES GLOBALES ====================

_active_model = 'pretrained'  # Valeur par défaut: 'pretrained' ou 'custom'
_current_model_type = 'pretrained'

# ==================== MODÈLES CNN (Placeholders) ====================
# À remplacer par vos vrais modèles

class CustomCNNFaceModel:
    """Modèle CNN personnalisé - À implémenter avec vos poids"""
    def __init__(self):
        self.model = None
        print("[INFO] Nouvelle architecture CNN personnalisée initialisée sans warning.")
    
    def extract_features(self, face_image):
        """Extrait les features du visage - À implémenter"""
        # Placeholder: retourne un vecteur aléatoire de dimension 128
        # À remplacer par votre vrai modèle
        return np.random.randn(128).astype(np.float32)

class PretrainedCNN:
    """Modèle CNN pré-entraîné - À implémenter avec vos poids"""
    def __init__(self):
        self.model = None
        print("[INFO] Modèle pré-entraîné chargé (MobileNetV2).")
    
    def extract_features(self, face_image):
        """Extrait les features du visage - À implémenter"""
        # Placeholder: retourne un vecteur aléatoire de dimension 128
        # À remplacer par votre vrai modèle
        return np.random.randn(128).astype(np.float32)

# Instances des extracteurs
custom_extractor = CustomCNNFaceModel()
pretrained_extractor = PretrainedCNN()

# Chemins des modèles
SVM_MODEL_PATH = "models/svm_classifier.pkl"
KNOWN_EMBEDDINGS_PATH = "models/known_embeddings.npy"
KNOWN_CNES_PATH = "models/known_cnes.npy"
MODEL_CONFIG_FILE = "models/model_choice.json"


# ==================== GESTION DU MODÈLE ACTIF ====================

def get_current_model():
    """Retourne le type de modèle actif ('pretrained' ou 'custom')"""
    global _current_model_type
    
    # Essayer de charger la configuration depuis le fichier
    if os.path.exists(MODEL_CONFIG_FILE):
        try:
            import json
            with open(MODEL_CONFIG_FILE, 'r') as f:
                data = json.load(f)
                _current_model_type = data.get('model_type', 'pretrained')
        except:
            pass
    
    return _current_model_type


def set_active_model(model_type):
    """Définit le modèle actif pour la reconnaissance"""
    global _current_model_type
    _current_model_type = model_type
    
    # Sauvegarder dans le fichier de configuration
    import json
    os.makedirs('models', exist_ok=True)
    with open(MODEL_CONFIG_FILE, 'w') as f:
        json.dump({'model_type': model_type, 'confirmed': True}, f)
    
    print(f"[INFO] Modèle actif changé: {model_type}")
    
    # Recharger les embeddings avec le nouveau modèle
    trigger_automatic_training()


def get_active_extractor():
    """Retourne l'extracteur correspondant au modèle actif"""
    current = get_current_model()
    if current == 'custom':
        return custom_extractor
    else:
        return pretrained_extractor


# ==================== DÉTECTION ET ROGNAGE DE VISAGE ====================

def detect_and_crop_face_cnn(image_bytes):
    """
    Étape 1 : Localise et rogne le visage pour le normaliser aux dimensions attendues (128x128).
    
    Args:
        image_bytes: Bytes de l'image
    
    Returns:
        tuple: (face_cropped, face_location)
    """
    try:
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None or img.size == 0:
            return None, None

        rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_img, model="hog")

        if len(face_locations) > 0:
            top, right, bottom, left = face_locations[0]
            face_crop = img[top:bottom, left:right]
            return face_crop, face_locations[0]
        return None, None
    except Exception as e:
        print(f"[ERREUR] Détection/Cadrage : {e}")
        return None, None


# ==================== GÉNÉRATION D'EMBEDDINGS ====================

def generate_hybrid_embeddings(face_image):
    """
    Étape 2 : Extrait les caractéristiques selon le modèle actif.
    
    Args:
        face_image: Image du visage (numpy array)
    
    Returns:
        np.array: Embedding de dimension 128
    """
    try:
        # Normalisation des dimensions pour les modèles
        face_resized = cv2.resize(face_image, (128, 128))
        
        # Utiliser l'extracteur actif
        extractor = get_active_extractor()
        embedding = extractor.extract_features(face_resized)
        
        return embedding.astype(np.float32)
    except Exception as e:
        print(f"[ERREUR] Génération de l'embedding : {e}")
        return None


# ==================== ENTRAÎNEMENT AUTOMATIQUE ====================

def trigger_automatic_training():
    """
    Étape 3 : Entraîne le classifieur SVM sur la base des embeddings extraits.
    """
    print("[AUTO-TRAIN] Extraction des images de la BD et entraînement du SVM...")
    try:
        X, y = [], []
        extractor = get_active_extractor()
        
        with DatabaseContext() as (cursor, conn):
            cursor.execute("SELECT CNE_MASSAR, IMAGE FROM image")
            rows = cursor.fetchall()
            
            for row in rows:
                cne, blob = row[0], row[1]
                if blob:
                    nparr = np.frombuffer(blob, np.uint8)
                    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                    if img is not None:
                        # Redimensionner pour l'extraction
                        img_resized = cv2.resize(img, (128, 128))
                        embedding = extractor.extract_features(img_resized)
                        if embedding is not None:
                            X.append(embedding)
                            y.append(cne)
        
        if len(X) > 0:
            # Entraînement du SVM
            clf = SVC(kernel='linear', probability=True)
            clf.fit(np.array(X), np.array(y))
            
            os.makedirs('models', exist_ok=True)
            with open(SVM_MODEL_PATH, 'wb') as f:
                pickle.dump(clf, f)
            
            # Sauvegarde des embeddings
            np.save(KNOWN_EMBEDDINGS_PATH, np.array(X))
            np.save(KNOWN_CNES_PATH, np.array(y))
            
            print(f"[AUTO-TRAIN] SVM entraîné avec succès ({len(set(y))} étudiants indexés).")
            return True
        else:
            print("[AUTO-TRAIN] Aucune image trouvée en BD pour l'entraînement.")
            return False
    except Exception as e:
        print(f"[ERREUR] Échec de l'auto-entraînement SVM : {e}")
        return False


# ==================== PRÉDICTION ====================

def predict_student_svm(hybrid_embedding, confidence_threshold=0.6):
    """
    Étape 4 : Utilise le modèle SVM sauvegardé pour prédire le CNE de l'étudiant.
    
    Args:
        hybrid_embedding: Embedding du visage
        confidence_threshold: Seuil de confiance (0-1)
    
    Returns:
        str: CNE de l'étudiant ou "Inconnu"
    """
    if not os.path.exists(SVM_MODEL_PATH):
        return "Inconnu"
    try:
        with open(SVM_MODEL_PATH, 'rb') as f:
            clf = pickle.load(f)
        
        embedding_reshaped = hybrid_embedding.reshape(1, -1)
        probabilities = clf.predict_proba(embedding_reshaped)[0]
        max_idx = np.argmax(probabilities)
        max_prob = probabilities[max_idx]
        
        if max_prob >= confidence_threshold:
            return clf.classes_[max_idx]
        return "Inconnu"
    except Exception as e:
        print(f"[ERREUR] Prédiction SVM : {e}")
        return "Inconnu"


# ==================== FONCTIONS COMPLÉMENTAIRES ====================

def get_embeddings_count():
    """Retourne le nombre d'embeddings stockés"""
    if os.path.exists(KNOWN_EMBEDDINGS_PATH):
        embeddings = np.load(KNOWN_EMBEDDINGS_PATH, allow_pickle=True)
        return len(embeddings)
    return 0


def get_students_count():
    """Retourne le nombre d'étudiants"""
    with DatabaseContext() as (cursor, conn):
        cursor.execute("SELECT COUNT(*) FROM etudiant")
        return cursor.fetchone()[0]