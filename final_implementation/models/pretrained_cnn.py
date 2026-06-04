# models/pretrained_cnn.py
# Modèle basé sur le Transfer Learning (MobileNetV2)

import numpy as np
import cv2
import os
from tensorflow.keras.models import load_model

class PretrainedCNN:
    """
    Classe gérant l'extracteur de caractéristiques pré-entraîné (MobileNetV2)
    exporté depuis Google Colab pour le projet RecoJY.
    """
    
    def __init__(self, input_shape=(224, 224, 3), embedding_dim=512):
        # Attention : MobileNetV2 requiert nativement du 224x224x3 et produit un embedding 512D
        self.input_shape = input_shape
        self.embedding_dim = embedding_dim
        self.model = None
        self.weights_path = "models/recojy_extractor.h5"
        
    def build(self):
        """Initialise ou charge le modèle d'extraction"""
        if os.path.exists(self.weights_path):
            try:
                self.model = load_model(self.weights_path, compile=False)
                print(f"[PretrainedCNN] ✅ Modèle chargé avec succès depuis {self.weights_path}")
            except Exception as e:
                print(f"[PretrainedCNN] ❌ Erreur lors du chargement du fichier .h5 : {str(e)}")
        else:
            print(f"[PretrainedCNN] ⚠️ Fichier {self.weights_path} introuvable. Le modèle n'est pas initialisé.")
            
    def load_weights(self):
        """Alias pour s'aligner avec la structure initiale de l'application"""
        self.build()
        
    def save_weights(self):
        """L'extracteur de caractéristiques est figé en production, pas besoin de ré-sauvegarder"""
        pass
        
    def get_model_summary(self):
        """Retourne un résumé du modèle si chargé"""
        if self.model:
            return f"MobileNetV2 Feature Extractor (Output: {self.embedding_dim}D)"
        return "Modèle non chargé"
        
    def extract_features(self, face_image):
        """
        Extrait l'embedding (la signature) d'un visage pour le live webcam.
        Applique un prétraitement adaptatif déterministe (sans augmentation de données destructrice).
        """
        if self.model is None:
            print("[PretrainedCNN] ❌ Impossible d'extraire : modèle non chargé.")
            return np.zeros(self.embedding_dim, dtype=np.float32)
            
        try:
            # --- Prétraitement adaptatif pour le Live Webcam ---
            # 1. Redimensionnement aux dimensions strictes de MobileNetV2 (224x224)
            img = cv2.resize(face_image, (self.input_shape[1], self.input_shape[0]))
            
            # 2. Conversion sécurisée en RGB (OpenCV lit en BGR)
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            
            # 3. Normalisation standard [0, 1] identique à l'entraînement
            img = img.astype(np.float32) / 255.0
            
            # 4. Ajout de la dimension de batch (1, 224, 224, 3)
            img_batch = np.expand_dims(img, axis=0)
            
            # Extraction par le réseau de neurones
            embedding = self.model.predict(img_batch, verbose=0)[0]
            return embedding
            
        except Exception as e:
            print(f"[PretrainedCNN] ❌ Erreur lors de l'extraction des caractéristiques : {str(e)}")
            return np.zeros(self.embedding_dim, dtype=np.float32)