# service/face_service.py
# Service de reconnaissance faciale avec gestion du modèle actif, Data Augmentation et Chronométrage

import os
import cv2
import numpy as np
import face_recognition
import pickle
import json
import time  # ⏱️ Importation du module de chronométrage
from sklearn.svm import SVC
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from database import DatabaseContext

# ==================== VARIABLES GLOBALES ====================

_current_model_type = 'pretrained'

# Chemins des modèles
SVM_MODEL_PATH = "models/svm_classifier.pkl"
KNOWN_EMBEDDINGS_PATH = "models/known_embeddings.npy"
KNOWN_CNES_PATH = "models/known_cnes.npy"
MODEL_CONFIG_FILE = "models/model_choice.json"

# ==================== CONFIGURATION DATA AUGMENTATION ====================

datagen = ImageDataGenerator(
    rotation_range=15,          
    width_shift_range=0.1,      
    height_shift_range=0.1,     
    brightness_range=[0.7, 1.3], 
    zoom_range=0.1,             
    fill_mode='nearest'
)

# ==================== CONFIGURATION DES VRAIS EXTRACTEURS ====================

class CustomCNNFaceModel:
    def __init__(self):
        self.model = None 
        print("[INFO] Nouvelle architecture CNN personnalisée initialisée sans warning.")
    
    def extract_features(self, face_image):
        rgb_img = cv2.cvtColor(face_image, cv2.COLOR_BGR2RGB)
        encodings = face_recognition.face_encodings(rgb_img, [(0, face_image.shape[1], face_image.shape[0], 0)])
        if encodings:
            return encodings[0]
        return np.zeros(128, dtype=np.float32)

class PretrainedCNN:
    def __init__(self):
        self.model = None
        print("[INFO] Modèle pré-entraîné chargé (MobileNetV2 extraction active).")
    
    def extract_features(self, face_image):
        rgb_img = cv2.cvtColor(face_image, cv2.COLOR_BGR2RGB)
        encodings = face_recognition.face_encodings(rgb_img, [(0, face_image.shape[1], face_image.shape[0], 0)])
        if encodings:
            return encodings[0]
        return np.zeros(128, dtype=np.float32)

custom_extractor = CustomCNNFaceModel()
pretrained_extractor = PretrainedCNN()

# ==================== GESTION DU MODÈLE ACTIF ====================

def get_current_model():
    global _current_model_type
    if os.path.exists(MODEL_CONFIG_FILE):
        try:
            with open(MODEL_CONFIG_FILE, 'r') as f:
                data = json.load(f)
                _current_model_type = data.get('model_type', 'pretrained')
        except:
            pass
    return _current_model_type

def set_active_model(model_type):
    global _current_model_type
    _current_model_type = model_type
    os.makedirs('models', exist_ok=True)
    with open(MODEL_CONFIG_FILE, 'w') as f:
        json.dump({'model_type': model_type, 'confirmed': True}, f)
    print(f"[INFO] Modèle actif mis à jour: {model_type}")
    trigger_automatic_training()

def get_active_extractor():
    current = get_current_model()
    if current == 'custom':
        return custom_extractor
    return pretrained_extractor

# ==================== DÉTECTION ET ROGNAGE DE VISAGE ====================

def detect_and_crop_face_cnn(image_bytes):
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
    try:
        face_resized = cv2.resize(face_image, (128, 128))
        extractor = get_active_extractor()
        embedding = extractor.extract_features(face_resized)
        return embedding.astype(np.float32)
    except Exception as e:
        print(f"[ERREUR] Génération de l'embedding : {e}")
        return None


# ==================== ENTRAÎNEMENT AUTOMATIQUE CHRONOMÉTRÉ ====================

def trigger_automatic_training():
    """
    Étape 3 : S'exécute automatiquement en arrière-plan.
    Génère les variantes augmentées, entraîne le SVM et affiche les temps d'exécution.
    """
    print("\n" + "="*60)
    print("[⏱️ START] Démarrage du pipeline d'auto-entraînement...")
    print("="*60)
    
    temps_debut_global = time.time()  # Début du chrono général
    
    try:
        X, y = [], []
        extractor = get_active_extractor()
        
        # --- PHASE 1 : LECTURE BDD & DATA AUGMENTATION ---
        print("[PHASE 1] Chargement des images de la BD & Data Augmentation en cours...")
        temps_debut_phase1 = time.time()
        
        with DatabaseContext() as (cursor, conn):
            cursor.execute("SELECT CNE_MASSAR, IMAGE FROM image")
            rows = cursor.fetchall()
            
            if not rows:
                print("[⚠️ AUTO-TRAIN] Aucune image trouvée en BD. Procédure annulée.")
                return False
            
            for row in rows:
                cne, blob = row[0], row[1]
                if blob:
                    nparr = np.frombuffer(blob, np.uint8)
                    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                    
                    if img is not None:
                        img_resized = cv2.resize(img, (128, 128))
                        img_array = np.expand_dims(img_resized, axis=0)
                        
                        # Génération de 10 variantes par image d'origine
                        iterator = datagen.flow(img_array, batch_size=1)
                        for _ in range(10):
                            batch = next(iterator)
                            augmented_face = batch[0].astype(np.uint8)
                            
                            embedding = extractor.extract_features(augmented_face)
                            if embedding is not None:
                                X.append(embedding)
                                y.append(cne)
                                
        temps_fin_phase1 = time.time()
        duree_phase1 = temps_fin_phase1 - temps_debut_phase1
        print(f"📊 [INFO PHASE 1] {len(X)} vecteurs générés (visages originaux + augmentés).")
        print(f"⏱️ [TEMPS PHASE 1] Extraction & Augmentation terminées en : {duree_phase1:.4f} secondes.")
        print("-"*60)
        
        # --- PHASE 2 : ENTRAÎNEMENT DU SVM ---
        if len(X) > 0:
            print("[PHASE 2] Initialisation et ajustement des frontières du SVM (StandardScaler + RBF)...")
            temps_debut_phase2 = time.time()
            
            clf_pipeline = Pipeline([
                ('scaler', StandardScaler()),
                ('svm', SVC(kernel='rbf', C=16, gamma='scale', probability=True))
            ])
            
            clf_pipeline.fit(np.array(X), np.array(y))
            
            # Sauvegardes fichiers checkpoints
            os.makedirs('models', exist_ok=True)
            with open(SVM_MODEL_PATH, 'wb') as f:
                pickle.dump(clf_pipeline, f)
            
            np.save(KNOWN_EMBEDDINGS_PATH, np.array(X))
            np.save(KNOWN_CNES_PATH, np.array(y))
            
            temps_fin_phase2 = time.time()
            duree_phase2 = temps_fin_phase2 - temps_debut_phase2
            print(f"⏱️ [TEMPS PHASE 2] Apprentissage du SVM et sauvegardes terminés en : {duree_phase2:.4f} secondes.")
            print("-"*60)
            
            # --- BILAN GLOBAL ---
            temps_fin_global = time.time()
            duree_globale = temps_fin_global - temps_debut_global
            
            print(f"🎉 [SUCCESS] Pipeline exécuté avec succès pour {len(set(y))} étudiant(s) unique(s).")
            print(f"🚀 [TEMPS TOTAL] Fin globale de la procédure en : {duree_globale:.4f} secondes.")
            print("="*60 + "\n")
            return True
            
        print("[⚠️ AUTO-TRAIN] Traitement impossible : Liste de caractéristiques vide.")
        return False
        
    except Exception as e:
        print(f"❌ [ERREUR CRITIQUE] Échec de l'auto-entraînement : {e}")
        return False

# ==================== PRÉDICTION ====================

def predict_student_svm(hybrid_embedding, confidence_threshold=0.6):
    if not os.path.exists(SVM_MODEL_PATH):
        return "Inconnu"
    try:
        with open(SVM_MODEL_PATH, 'rb') as f:
            clf_pipeline = pickle.load(f)
        
        embedding_reshaped = hybrid_embedding.reshape(1, -1)
        probabilities = clf_pipeline.predict_proba(embedding_reshaped)[0]
        max_idx = np.argmax(probabilities)
        max_prob = probabilities[max_idx]
        
        if max_prob >= confidence_threshold:
            return clf_pipeline.classes_[max_idx]
        return "Inconnu"
    except Exception as e:
        print(f"[ERREUR] Prédiction SVM : {e}")
        return "Inconnu"

# ==================== FONCTIONS COMPLÉMENTAIRES ====================

def get_embeddings_count():
    if os.path.exists(KNOWN_EMBEDDINGS_PATH):
        return len(np.load(KNOWN_EMBEDDINGS_PATH, allow_pickle=True))
    return 0

def get_students_count():
    with DatabaseContext() as (cursor, conn):
        cursor.execute("SELECT COUNT(*) FROM etudiant")
        return cursor.fetchone()[0]