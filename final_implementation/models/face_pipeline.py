# models/face_pipeline.py
# Pipeline combinant les deux CNN

import numpy as np
from .custom_cnn import CustomCNN
from .pretrained_cnn import PretrainedCNN
import os
import pickle
import json
from datetime import datetime

class FacePipeline:
    """Pipeline de reconnaissance avec deux CNN"""
    
    def __init__(self, input_shape=(128, 128, 3)):
        self.input_shape = input_shape
        self.custom_cnn = CustomCNN(input_shape=input_shape, embedding_dim=128)
        self.pretrained_cnn = PretrainedCNN(input_shape=input_shape, embedding_dim=128)
        self.known_encodings = []
        self.known_ids = []
        self.encodings_path = "models/face_pipeline_encodings.pkl"
        self.metrics_path = "models/face_pipeline_metrics.json"
        self.recognition_stats = {
            'total_recognitions': 0,
            'successful_recognitions': 0,
            'failed_recognitions': 0,
            'average_distance': [],
            'recognition_history': []
        }
        
    def build_models(self):
        """Construit les deux modèles"""
        print("=" * 50)
        print("Construction du pipeline CNN...")
        self.custom_cnn.build()
        self.pretrained_cnn.build()
        print("Pipeline construit")
        print("=" * 50)
        
    def load_models(self):
        """Charge les poids"""
        self.custom_cnn.load_weights()
        self.pretrained_cnn.load_weights()
        
    def save_models(self):
        """Sauvegarde les poids"""
        self.custom_cnn.save_weights()
        self.pretrained_cnn.save_weights()
        
    def get_models_summary(self):
        """Résumé des modèles"""
        return {
            'custom_cnn': self.custom_cnn.get_model_summary(),
            'pretrained_cnn': self.pretrained_cnn.get_model_summary()
        }
        
    def extract_features_combined(self, face_image):
        """Extrait les embeddings combinés"""
        emb_custom = self.custom_cnn.extract_features(face_image)
        emb_pretrained = self.pretrained_cnn.extract_features(face_image)
        combined = np.concatenate([emb_custom, emb_pretrained])
        return combined
    
    def train_encodings(self, image_paths, cne_list):
        """Entraîne le pipeline sur des images"""
        import cv2
        
        self.known_encodings = []
        self.known_ids = []
        
        for img_path, cne in zip(image_paths, cne_list):
            img = cv2.imread(img_path)
            if img is None:
                continue
                
            rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            resized_img = cv2.resize(rgb_img, self.input_shape[:2])
            embedding = self.extract_features_combined(resized_img)
            
            self.known_encodings.append(embedding)
            self.known_ids.append(cne)
        
        self.save_encodings()
        print(f"[Pipeline] {len(self.known_encodings)} encodings entraînés")
        return len(self.known_encodings)
    
    def add_student_encoding(self, face_image, cne):
        """Ajoute un étudiant"""
        embedding = self.extract_features_combined(face_image)
        self.known_encodings.append(embedding)
        self.known_ids.append(cne)
        self.save_encodings()
        print(f"[Pipeline] Étudiant {cne} ajouté")
        return True
    
    def recognize_face(self, face_image, threshold=0.55):
        """Reconnaît un visage"""
        if len(self.known_encodings) == 0:
            return None, None, None
        
        unknown_encoding = self.extract_features_combined(face_image)
        distances = [np.linalg.norm(unknown_encoding - known) for known in self.known_encodings]
        min_distance = min(distances)
        
        self.recognition_stats['total_recognitions'] += 1
        
        if min_distance < threshold:
            index = np.argmin(distances)
            cne = self.known_ids[index]
            self.recognition_stats['successful_recognitions'] += 1
            self.recognition_stats['average_distance'].append(min_distance)
            return cne, min_distance, 'combined'
        else:
            self.recognition_stats['failed_recognitions'] += 1
            return None, min_distance, None
    
    def save_encodings(self):
        """Sauvegarde les encodings"""
        os.makedirs("models", exist_ok=True)
        with open(self.encodings_path, 'wb') as f:
            pickle.dump({'encodings': self.known_encodings, 'ids': self.known_ids}, f)
    
    def load_encodings(self):
        """Charge les encodings"""
        if os.path.exists(self.encodings_path):
            with open(self.encodings_path, 'rb') as f:
                data = pickle.load(f)
            self.known_encodings = data['encodings']
            self.known_ids = data['ids']
            print(f"[Pipeline] {len(self.known_encodings)} encodings chargés")
            return True
        return False
    
    def load_all_metrics(self):
        """Charge toutes les métriques"""
        metrics = {'pipeline_metrics': [], 'custom_metrics': [], 'pretrained_metrics': []}
        if os.path.exists(self.metrics_path):
            with open(self.metrics_path, 'r') as f:
                metrics['pipeline_metrics'] = json.load(f)
        return metrics
    
    def get_performance_report(self):
        """Rapport de performance"""
        success_rate = (self.recognition_stats['successful_recognitions'] / 
                       self.recognition_stats['total_recognitions']) if self.recognition_stats['total_recognitions'] > 0 else 0
        return {
            'models_summary': self.get_models_summary(),
            'recognition_performance': {
                'total_recognitions': self.recognition_stats['total_recognitions'],
                'success_rate': success_rate,
                'average_distance': np.mean(self.recognition_stats['average_distance']) if self.recognition_stats['average_distance'] else None,
                'total_students': len(set(self.known_ids))
            }
        }
    
    def is_ready(self):
        return len(self.known_encodings) > 0