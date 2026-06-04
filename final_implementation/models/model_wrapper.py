# models/model_wrapper.py
# WRAPPER POUR L'INTÉGRATION DES MODÈLES - S'ADAPTE À L'ARCHITECTURE INITIALE

import numpy as np
import cv2
import os
import pickle
import json
from .pretrained_cnn import PretrainedCNN

class FaceRecognitionModel:
    """
    Classe wrapper qui fait l'interface entre l'application Flask (webcam live)
    et nos modèles réels de reconnaissance faciale.
    """
    
    def __init__(self):
        # Initialisation du conteneur selon l'architecture d'origine
        self.pretrained_cnn_instance = PretrainedCNN(input_shape=(224, 224, 3), embedding_dim=512)
        self.custom_model = None # Sera complété plus tard lors de la phase "From Scratch"
        
        self.active_model = 'pretrained'  # 'pretrained' ou 'custom'
        self.embedding_dim = 512
        
        # Tes filtres d'intervalles de confiance fétiches 🎛️
        self.seuil_haut = 0.75
        self.seuil_bas = 0.50
        
        # Fichiers du classifieur de Transfer Learning
        self.svm_pipeline = None
        self.class_names = []
        
        # Chargement automatique des composants au démarrage de l'app
        self.load_models()
    
    def load_model_choice(self):
        """Lit dynamiquement le choix du modèle dans le fichier JSON de l'application"""
        config_file = "models/model_choice.json"
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    data = json.load(f)
                    return data.get('model_type', 'pretrained')
            except:
                pass
        return 'pretrained'
        
    def load_models(self):
        """Charge l'extracteur de caractéristiques et le classifieur SVM associé"""
        # Mise à jour du modèle actif selon le choix de l'utilisateur
        self.active_model = self.load_model_choice()
        print(f"[Wrapper] ⚙️ Modèle actif détecté : {self.active_model}")
        
        if self.active_model == 'pretrained':
            # 1. Charger l'extracteur MobileNetV2
            self.pretrained_cnn_instance.build()
            self.embedding_dim = 512
            
            # 2. Charger le classifieur SVM (.pkl) exporté de Colab
            path_classifier = 'models/recojy_classifier.pkl'
            if os.path.exists(path_classifier):
                with open(path_classifier, "rb") as f:
                    self.svm_pipeline = pickle.load(f)
                print("[Wrapper] ✅ Classifieur SVM Pré-entraîné chargé.")
                
            # 3. Charger le dictionnaire des noms associés
            path_classes = 'models/recojy_classes.pkl'
            if os.path.exists(path_classes):
                with open(path_classes, "rb") as f:
                    self.class_names = pickle.load(f)
                print(f"[Wrapper] ✅ Classes chargées : {self.class_names}")
        else:
            print("[Wrapper] ⚠️ Mode 'custom' sélectionné (En attente d'implémentation complète).")

    def set_active_model(self, model_type):
        """Permet aux routes de basculer le modèle dynamiquement"""
        if model_type in ['pretrained', 'custom']:
            self.active_model = model_type
            self.load_models()
            return True
        return False
    
    def preprocess_image(self, image):
        """
        Laissé ici pour la compatibilité avec l'ancienne structure,
        le prétraitement live est maintenant délégué directement au modèle.
        """
        return image
    
    def extract_embedding(self, face_image):
        """Extrait l'embedding en utilisant le modèle actif"""
        self.active_model = self.load_model_choice() # Vérification à la volée
        
        if self.active_model == 'pretrained':
            return self.pretrained_cnn_instance.extract_features(face_image)
        else:
            # Section réservée pour ton modèle custom from scratch
            return np.zeros(self.embedding_dim, dtype=np.float32)
    
    def compare_embeddings(self, embedding1, embedding2):
        """Comparaison par produit scalaire (similarité cosinus si vecteurs normalisés)"""
        if embedding1 is None or embedding2 is None:
            return 0.0
        return float(np.dot(embedding1, embedding2))
    
    def recognize_live_face(self, face_image):
        """
        Analyse le visage en direct de la webcam et applique la logique d'intervalles.
        Cette méthode s'interface parfaitement avec tes fichiers de service et de routes.
        Returns:
            tuple: (nom_predit, confiance, statut)
        """
        # 1. Extraction de l'embedding (Gère le redimensionnement et la normalisation en live)
        embedding = self.extract_embedding(face_image)
        
        if self.active_model == 'pretrained':
            if self.svm_pipeline is None or len(self.class_names) == 0:
                return "Modèle non prêt", 0.0, "ERREUR"
                
            # Ajustement du format pour l'entrée attendue par Scikit-Learn (1, 512)
            embedding_reshaped = np.expand_dims(embedding, axis=0)
            
            # 2. Calcul des probabilités par le SVM
            probabilities = self.svm_pipeline.predict_proba(embedding_reshaped)[0]
            max_idx = np.argmax(probabilities)
            confiance = probabilities[max_idx]
            nom_suspect = self.class_names[max_idx]
            
            # 3. Application rigoureuse de la logique d'intervalles 🎛️
            if confiance >= self.seuil_haut:
                return nom_suspect, float(confiance), "CERTITUDE"
            elif self.seuil_bas <= confiance < self.seuil_haut:
                return nom_suspect, float(confiance), "SUSPECT"
            else:
                return "Inconnu", float(confiance), "INCONNU"
                
        return "Inconnu", 0.0, "INCONNU"


# ===================================================================
# INSTANCE GLOBALE ET WRAPPERS POUR RESTER CONFORME À L'APP INITIALE
# ===================================================================

_model_instance = None

def get_model():
    global _model_instance
    if _model_instance is None:
        _model_instance = FaceRecognitionModel()
    return _model_instance

def extract_embedding(face_image):
    """Garantit que les scripts de services existants continuent de fonctionner"""
    model = get_model()
    return model.extract_embedding(face_image)

def predict_student_live(face_image):
    """
    Méthode principale à appeler dans presence_routes.py lors de la réception
    du flux vidéo de la webcam.
    """
    model = get_model()
    return model.recognize_live_face(face_image)