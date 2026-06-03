# models/pretrained_cnn.py
# CNN pré-entraîné MobileNetV2 adapté pour la reconnaissance faciale

import numpy as np
import tensorflow as tf
from tensorflow.keras import layers, models
from tensorflow.keras.applications import MobileNetV2
import os
import json
from datetime import datetime

class PretrainedCNN:
    """CNN pré-entraîné MobileNetV2"""
    
    def __init__(self, input_shape=(128, 128, 3), embedding_dim=128):
        self.input_shape = input_shape
        self.embedding_dim = embedding_dim
        self.base_model = None
        self.model = None
        self.is_built = False
        self.is_trained = False
        self.weights_path = "models/pretrained_cnn_weights.h5"
        self.metrics_path = "models/pretrained_cnn_metrics.json"
        
    def build(self, fine_tune=False):
        """Construit le modèle MobileNetV2 adapté"""
        # Chargement sans la tête de classification
        self.base_model = MobileNetV2(
            input_shape=self.input_shape,
            include_top=False,
            weights='imagenet',
            pooling='avg'
        )
        
        # Freeze les couches du modèle de base
        self.base_model.trainable = False
        
        # Construction du modèle complet
        inputs = layers.Input(shape=self.input_shape)
        
        # Prétraitement spécifique à MobileNetV2
        x = tf.keras.applications.mobilenet_v2.preprocess_input(inputs)
        x = self.base_model(x)
        
        # Couches additionnelles
        x = layers.Dense(512, activation='relu')(x)
        x = layers.BatchNormalization()(x)
        x = layers.Dropout(0.3)(x)
        
        x = layers.Dense(256, activation='relu')(x)
        x = layers.BatchNormalization()(x)
        x = layers.Dropout(0.3)(x)
        
        outputs = layers.Dense(self.embedding_dim, activation='linear', name='embedding')(x)
        
        self.model = models.Model(inputs=inputs, outputs=outputs)
        self.is_built = True
        
        self.model.compile(
            optimizer=tf.keras.optimizers.Adam(learning_rate=0.0001),
            loss='mse',
            metrics=['mae']
        )
        
        print(f"[PretrainedCNN] MobileNetV2 adapté. Paramètres: {self.model.count_params():,}")
        
        return self.model
    
    def get_model_summary(self):
        """Retourne un résumé du modèle"""
        if self.model is None:
            self.build()
        return {
            'total_params': self.model.count_params(),
            'trainable_params': 0,  # MobileNetV2 frozen
            'non_trainable_params': self.model.count_params(),
            'base_model_name': 'MobileNetV2',
            'pretrained_on': 'ImageNet',
            'input_shape': self.input_shape,
            'embedding_dim': self.embedding_dim
        }
    
    def load_weights(self):
        """Charge les poids fine-tunés"""
        if os.path.exists(self.weights_path):
            if self.model is None:
                self.build()
            self.model.load_weights(self.weights_path)
            self.is_trained = True
            print("[PretrainedCNN] Poids chargés")
            return True
        else:
            print("[PretrainedCNN] Aucun poids trouvé")
            if self.model is None:
                self.build()
            return False
    
    def save_weights(self):
        """Sauvegarde les poids"""
        if self.model is not None:
            os.makedirs("models", exist_ok=True)
            self.model.save_weights(self.weights_path)
            self.is_trained = True
            print("[PretrainedCNN] Poids sauvegardés")
    
    def extract_features(self, face_image):
        """Extrait l'empreinte faciale"""
        if self.model is None:
            self.build()
        
        if face_image.shape != self.input_shape:
            face_image = tf.image.resize(face_image, self.input_shape[:2])
        
        if face_image.dtype == np.uint8:
            face_image = face_image.astype(np.float32)
        
        if len(face_image.shape) == 3:
            face_image = np.expand_dims(face_image, axis=0)
        
        embedding = self.model.predict(face_image, verbose=0)
        embedding = embedding / (np.linalg.norm(embedding) + 1e-8)
        
        return embedding.flatten()