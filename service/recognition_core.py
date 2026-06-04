# ===================================================================
# service/recognition_core.py
# CŒUR DE LA RECONNAISSANCE FACIALE - À COMPLÉTER 
# ===================================================================
# 
# INSTRUCTIONS POUR L'INTÉGRATION DES MODÈLES :
# 
# 1. REMPLACER la fonction extract_embedding() par votre vrai modèle
# 2. IMPLÉMENTER les fonctions load_pretrained_model() et load_custom_model()
# 3. GARDER les mêmes signatures de fonctions
# 
# Le reste du système utilise ces fonctions. Ne pas modifier les noms.
# ===================================================================

import numpy as np
import cv2
import os
import json

# Configuration
MODELS_PATH = "models"
MODEL_CONFIG_FILE = os.path.join(MODELS_PATH, "model_choice.json")

# Variables globales pour les modèles (à initialiser)
_pretrained_model = None
_custom_model = None
_current_model_type = "pretrained"  # 'pretrained' ou 'custom'


# ===================================================================
# À COMPLÉTER - CHARGEMENT DES MODÈLES
# ===================================================================

def load_pretrained_model():
    """
    Charge le modèle pré-entraîné (MobileNetV2 ou autre)
    
    À COMPLÉTER :
    - Charger les poids du modèle pré-entraîné
    - Retourner le modèle chargé
    
    Returns:
        model: Modèle chargé ou None si erreur
    """
    global _pretrained_model
    
    # ========== À REMPLACER PAR NOTRE CODE ==========
    try:
        # Exemple de chargement (à remplacer par notre vrai modèle)
        # from tensorflow.keras.models import load_model
        # _pretrained_model = load_model(os.path.join(MODELS_PATH, "pretrained_model.h5"))
        
        # Simulation pour le test
        print("[INFO] Chargement du modèle pré-entraîné... (À remplacer par votre code)")
        _pretrained_model = {"name": "pretrained", "loaded": True}
        print("[INFO] Modèle pré-entraîné chargé avec succès")
        return _pretrained_model
    except Exception as e:
        print(f"[ERREUR] Chargement modèle pré-entraîné: {e}")
        return None


def load_custom_model():
    """
    Charge le modèle personnalisé (Custom CNN)
    
    À COMPLÉTER :
    - Charger les poids du modèle personnalisé
    - Retourner le modèle chargé
    
    Returns:
        model: Modèle chargé ou None si erreur
    """
    global _custom_model
    
    # ========== À REMPLACER PAR NOTRE CODE ==========
    try:
        # Exemple de chargement (à remplacer par notre vrai modèle)
        # from tensorflow.keras.models import load_model
        # _custom_model = load_model(os.path.join(MODELS_PATH, "custom_model.h5"))
        
        # Simulation pour le test
        print("[INFO] Chargement du modèle personnalisé... (À remplacer par notre code)")
        _custom_model = {"name": "custom", "loaded": True}
        print("[INFO] Modèle personnalisé chargé avec succès")
        return _custom_model
    except Exception as e:
        print(f"[ERREUR] Chargement modèle personnalisé: {e}")
        return None


# ===================================================================
# À COMPLÉTER - EXTRACTION D'EMBEDDING
# ===================================================================

def extract_embedding(face_image, model_type=None):
    """
    Extrait l'embedding d'un visage à partir du modèle sélectionné.
    
    À COMPLÉTER :
    - Prendre une image de visage (numpy array BGR ou RGB)
    - Prétraiter l'image (redimensionnement, normalisation)
    - Passer l'image dans le modèle
    - Retourner l'embedding (vecteur de dimension fixe, ex: 128)
    
    Args:
        face_image (numpy.ndarray): Image du visage (format BGR)
        model_type (str, optional): 'pretrained' ou 'custom'
    
    Returns:
        numpy.ndarray: Embedding du visage (vecteur 1D)
    """
    global _current_model_type, _pretrained_model, _custom_model
    
    if model_type is None:
        model_type = _current_model_type
    
    # ========== À REMPLACER PAR NOTRE CODE ==========
    # Ceci est un placeholder qui retourne un vecteur aléatoire
    # Remplacez par votre vrai modèle !
    
    if face_image is None or face_image.size == 0:
        return None
    
    # Prétraitement standard (à adapter selon notre modèle)
    try:
        # Redimensionnement
        img = cv2.resize(face_image, (160, 160))
        
        # Conversion RGB si nécessaire
        if len(img.shape) == 3 and img.shape[2] == 3:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        # Normalisation
        img = img.astype(np.float32) / 127.5 - 1.0
        
        # ========== INTÉGRATION DE NOTRE MODÈLE ICI ==========
        # Exemple avec notre modèle:
        # if model_type == 'pretrained':
        #     model = _pretrained_model
        # else:
        #     model = _custom_model
        # 
        # embedding = model.predict(np.expand_dims(img, axis=0))[0]
        # return embedding
        
        # Simulation (à remplacer)
        embedding = np.random.randn(128).astype(np.float32)
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm
        
        return embedding
        
    except Exception as e:
        print(f"[ERREUR] Extraction embedding: {e}")
        return None


# ===================================================================
# FONCTIONS DE GESTION DU MODÈLE - NE PAS MODIFIER
# ===================================================================

def get_current_model_type():
    """Retourne le type de modèle actif ('pretrained' ou 'custom')"""
    global _current_model_type
    return _current_model_type


def set_current_model_type(model_type):
    """Définit le type de modèle actif"""
    global _current_model_type
    if model_type in ['pretrained', 'custom']:
        _current_model_type = model_type
        _save_model_choice(model_type)
        print(f"[INFO] Modèle actif changé: {model_type}")
        return True
    return False


def _save_model_choice(model_type):
    """Sauvegarde le choix du modèle dans un fichier"""
    os.makedirs(MODELS_PATH, exist_ok=True)
    with open(MODEL_CONFIG_FILE, 'w') as f:
        json.dump({'model_type': model_type, 'confirmed': True}, f)


def _load_model_choice():
    """Charge le choix du modèle depuis le fichier"""
    global _current_model_type
    if os.path.exists(MODEL_CONFIG_FILE):
        try:
            with open(MODEL_CONFIG_FILE, 'r') as f:
                data = json.load(f)
                _current_model_type = data.get('model_type', 'pretrained')
        except:
            pass


def initialize_models():
    """Initialise tous les modèles au démarrage"""
    global _pretrained_model, _custom_model
    
    _load_model_choice()
    
    print("=" * 50)
    print("🔧 INITIALISATION DES MODÈLES")
    print("=" * 50)
    
    # Charger les deux modèles
    print("📦 Chargement du modèle pré-entraîné...")
    _pretrained_model = load_pretrained_model()
    
    print("📦 Chargement du modèle personnalisé...")
    _custom_model = load_custom_model()
    
    print(f"✅ Modèle actif: {_current_model_type}")
    print("=" * 50)
    
    return _pretrained_model is not None or _custom_model is not None


def get_active_model():
    """Retourne le modèle actif"""
    global _current_model_type, _pretrained_model, _custom_model
    if _current_model_type == 'pretrained':
        return _pretrained_model
    return _custom_model


def is_model_ready():
    """Vérifie si au moins un modèle est chargé"""
    global _pretrained_model, _custom_model
    return _pretrained_model is not None or _custom_model is not None


def get_model_info():
    """Retourne des informations sur les modèles"""
    return {
        'pretrained_loaded': _pretrained_model is not None,
        'custom_loaded': _custom_model is not None,
        'active_model': _current_model_type
    }


# Initialisation automatique au chargement du module
print("[INFO] Module recognition_core chargé")