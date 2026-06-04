# ===================================================================
# models/model_wrapper.py
# WRAPPER POUR L'INTÉGRATION DES MODÈLES - À COMPLÉTER
# ===================================================================
# 
# CE FICHIER SERT D'INTERFACE ENTRE NOTRE MODÈLE ET L'APPLICATION
# 
# ON DOIT :
# 1. IMPLÉMENTER la classe FaceRecognitionModel
# 2. REMPLACER les méthodes extract_embedding() et compare()
# 3. CHARGER les poids des modèles dans __init__ ou load_models()
# 
# ===================================================================

import numpy as np
import cv2
import os

class FaceRecognitionModel:
    """
    Classe wrapper pour le modèle de reconnaissance faciale.
    
    À COMPLÉTER :
    - Implémenter le chargement des modèles
    - Implémenter l'extraction d'embeddings
    - Implémenter la comparaison entre embeddings
    """
    
    def __init__(self):
        self.pretrained_model = None
        self.custom_model = None
        self.active_model = 'pretrained'  # 'pretrained' ou 'custom'
        self.embedding_dim = 128
        self.threshold = 0.55
        
        # Charger les modèles
        self.load_models()
    
    def load_models(self):
        """
        Charge les modèles pré-entraîné et personnalisé.
        
        À COMPLÉTER :
        - Charger les poids des modèles depuis les fichiers
        - Initialiser self.pretrained_model et self.custom_model
        """
        # ========== À REMPLACER PAR NOTRE CODE ==========
        print("[INFO] Chargement des modèles... (À implémenter)")
        
        # Exemple avec TensorFlow/Keras :
        # from tensorflow.keras.models import load_model
        # self.pretrained_model = load_model('models/pretrained_model.h5')
        # self.custom_model = load_model('models/custom_model.h5')
        
        # Simulation
        self.pretrained_model = {"name": "pretrained", "loaded": True}
        self.custom_model = {"name": "custom", "loaded": True}
        
        print("[INFO] Modèles chargés avec succès")
    
    def set_active_model(self, model_type):
        """
        Définit le modèle actif.
        
        Args:
            model_type (str): 'pretrained' ou 'custom'
        """
        if model_type in ['pretrained', 'custom']:
            self.active_model = model_type
            print(f"[INFO] Modèle actif: {model_type}")
            return True
        return False
    
    def preprocess_image(self, image):
        """
        Prétraite l'image pour le modèle.
        
        Args:
            image (numpy.ndarray): Image BGR
        
        Returns:
            numpy.ndarray: Image prétraitée
        """
        # Redimensionnement
        img = cv2.resize(image, (160, 160))
        
        # Conversion RGB
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        # Normalisation
        img = img.astype(np.float32) / 127.5 - 1.0
        
        return img
    
    def extract_embedding(self, face_image):
        """
        Extrait l'embedding d'un visage.
        
        À COMPLÉTER PAR VOTRE BINÔME :
        - Utiliser le modèle actif pour extraire l'embedding
        
        Args:
            face_image (numpy.ndarray): Image du visage
        
        Returns:
            numpy.ndarray: Embedding (vecteur 1D normalisé)
        """
        if face_image is None or face_image.size == 0:
            return None
        
        # Prétraitement
        img = self.preprocess_image(face_image)
        
        # ========== À REMPLACER PAR NOTRE CODE ==========
        # Exemple avec notre modèle :
        # if self.active_model == 'pretrained':
        #     embedding = self.pretrained_model.predict(np.expand_dims(img, axis=0))[0]
        # else:
        #     embedding = self.custom_model.predict(np.expand_dims(img, axis=0))[0]
        
        # Simulation (à remplacer)
        import numpy as np
        embedding = np.random.randn(self.embedding_dim).astype(np.float32)
        
        # Normalisation
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm
        
        return embedding
    
    def compare_embeddings(self, embedding1, embedding2):
        """
        Compare deux embeddings par similarité cosinus.
        
        Args:
            embedding1, embedding2: Vecteurs d'embedding
        
        Returns:
            float: Score de similarité (0-1)
        """
        if embedding1 is None or embedding2 is None:
            return 0.0
        
        similarity = np.dot(embedding1, embedding2)
        return float(similarity)
    
    def find_best_match(self, embedding, reference_embeddings, reference_labels):
        """
        Trouve le meilleur match parmi les références.
        
        Args:
            embedding: Embedding à comparer
            reference_embeddings: Liste des embeddings de référence
            reference_labels: Labels correspondants
        
        Returns:
            tuple: (best_label, best_score, best_index)
        """
        if embedding is None or len(reference_embeddings) == 0:
            return None, 0.0, -1
        
        best_score = -1.0
        best_idx = -1
        
        for i, ref_emb in enumerate(reference_embeddings):
            score = self.compare_embeddings(embedding, ref_emb)
            if score > best_score:
                best_score = score
                best_idx = i
        
        if best_score >= self.threshold and best_idx >= 0:
            return reference_labels[best_idx], best_score, best_idx
        
        return None, best_score, -1
    
    def set_threshold(self, threshold):
        """Définit le seuil de reconnaissance"""
        self.threshold = max(0.3, min(0.9, threshold))
    
    def get_model_info(self):
        """Retourne les informations sur les modèles"""
        return {
            'active_model': self.active_model,
            'embedding_dim': self.embedding_dim,
            'threshold': self.threshold,
            'pretrained_loaded': self.pretrained_model is not None,
            'custom_loaded': self.custom_model is not None
        }


# Instance globale
_model_instance = None


def get_model():
    """Récupère l'instance unique du modèle"""
    global _model_instance
    if _model_instance is None:
        _model_instance = FaceRecognitionModel()
    return _model_instance


def extract_embedding(face_image):
    """Wrapper pour l'extraction d'embedding"""
    model = get_model()
    return model.extract_embedding(face_image)


def compare_embeddings(emb1, emb2):
    """Wrapper pour la comparaison"""
    model = get_model()
    return model.compare_embeddings(emb1, emb2)