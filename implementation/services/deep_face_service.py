import cv2
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Input, Dense, GlobalAveragePooling2D, BatchNormalization, Dropout
from tensorflow.keras.applications import MobileNetV2
from mtcnn import MTCNN
from scipy.spatial.distance import cosine
import os
from db.database import get_connection

# Supprimer les warnings TensorFlow
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

# Configuration
SIMILARITY_THRESHOLD = 0.45
INPUT_SIZE = 160
EMBEDDING_DIM = 128


class MobileNetFaceRecognizer:
    """
    Reconnaissance faciale avec MobileNetV2 (TensorFlow) + Haar Cascade
    """
    
    def __init__(self):
        self.detector = None
        self.model = None
        self.known_encodings = []
        self.known_ids = []
        self.known_names = []
        self.is_initialized = False
        
    def initialize(self):
        """Initialise MobileNetV2"""
        print("=" * 60)
        print("🚀 INITIALISATION - MOBILENETV2")
        print("=" * 60)
        
        # Modèle MobileNetV2 (Transfer Learning)
        print("📦 Chargement de MobileNetV2...")
        
        base_model = MobileNetV2(
            weights='imagenet',
            include_top=False,
            input_shape=(INPUT_SIZE, INPUT_SIZE, 3)
        )
        
        # Geler les couches du modèle de base
        base_model.trainable = False
        
        # Architecture personnalisée pour l'extraction d'empreintes
        inputs = Input(shape=(INPUT_SIZE, INPUT_SIZE, 3))
        x = tf.keras.applications.mobilenet_v2.preprocess_input(inputs)
        x = base_model(x, training=False)
        x = GlobalAveragePooling2D()(x)
        x = Dense(512, activation='relu')(x)
        x = BatchNormalization()(x)
        x = Dropout(0.3)(x)
        x = Dense(256, activation='relu')(x)
        x = BatchNormalization()(x)
        x = Dropout(0.3)(x)
        outputs = Dense(EMBEDDING_DIM, name='embeddings')(x)
        
        self.model = Model(inputs, outputs)
        
        print(f"✅ MobileNetV2 chargé")
        print(f"   - Dimensions sortie: {EMBEDDING_DIM}")
        
        self.is_initialized = True
        print("=" * 60)
    
    def get_face_embedding(self, face_image):
        """
        Calcul de l'empreinte faciale avec MobileNetV2
        """
        if not self.is_initialized:
            self.initialize()
        
        if self.model is None:
            return None
        
        # Convertir BGR vers RGB (OpenCV utilise BGR)
        if len(face_image.shape) == 3 and face_image.shape[2] == 3:
            face_image = cv2.cvtColor(face_image, cv2.COLOR_BGR2RGB)
        
        # Redimensionner
        face_image = cv2.resize(face_image, (INPUT_SIZE, INPUT_SIZE))
        face_image = face_image.astype(np.float32) / 127.5 - 1.0
        
        batch = np.expand_dims(face_image, axis=0)
        embedding = self.model.predict(batch, verbose=0)
        embedding = embedding / (np.linalg.norm(embedding) + 1e-8)
        
        return embedding[0]
    
    def load_known_faces_from_db(self):
        """Chargement des visages enregistrés depuis la base"""
        print("📚 Chargement des visages depuis la base...")
        
        connection = get_connection()
        if connection is None:
            print("❌ Erreur connexion DB")
            return
        
        cursor = connection.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT id, nom, prenom, matricule, face_embedding 
            FROM etudiant 
            WHERE face_embedding IS NOT NULL
        """)
        
        students = cursor.fetchall()
        cursor.close()
        connection.close()
        
        self.known_encodings = []
        self.known_ids = []
        self.known_names = []
        
        for student in students:
            try:
                embedding = np.frombuffer(student["face_embedding"], dtype=np.float32)
                self.known_encodings.append(embedding)
                self.known_ids.append(student["id"])
                self.known_names.append(f"{student['prenom']} {student['nom']}")
                print(f"   - {student['prenom']} {student['nom']}")
            except Exception as e:
                print(f"⚠️ Erreur chargement: {e}")
        
        print(f"✅ {len(self.known_encodings)} visages chargés")
    
    def find_best_match(self, embedding, threshold=SIMILARITY_THRESHOLD):
        """
        Recherche du meilleur match avec distance cosinus
        Retourne: (student_id, student_name, distance)
        """
        if len(self.known_encodings) == 0:
            return None, None, None
        
        distances = []
        for known_enc in self.known_encodings:
            try:
                dist = cosine(embedding, known_enc)
                distances.append(dist)
            except Exception:
                distances.append(1.0)
        
        best_index = np.argmin(distances)
        best_distance = distances[best_index]
        
        if best_distance < threshold:
            return self.known_ids[best_index], self.known_names[best_index], best_distance
        
        return None, None, best_distance
    
    def save_face_embedding(self, student_id, embedding):
        """Sauvegarde de l'empreinte faciale en base"""
        connection = get_connection()
        if connection is None:
            return False
        
        cursor = connection.cursor()
        
        try:
            embedding_bytes = embedding.astype(np.float32).tobytes()
            cursor.execute(
                "UPDATE etudiant SET face_embedding = %s WHERE id = %s",
                (embedding_bytes, student_id)
            )
            connection.commit()
            print(f"✅ Empreinte sauvegardée pour étudiant {student_id}")
            return True
        except Exception as e:
            print(f"❌ Erreur sauvegarde: {e}")
            connection.rollback()
            return False
        finally:
            cursor.close()
            connection.close()


# Instance unique
_recognizer = None

def get_recognizer():
    global _recognizer
    if _recognizer is None:
        _recognizer = MobileNetFaceRecognizer()
        _recognizer.initialize()
    return _recognizer
