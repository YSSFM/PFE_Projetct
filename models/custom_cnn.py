# models/custom_cnn.py
import os
import numpy as np

# Gestion propre des importations TensorFlow/Keras
try:
    from tensorflow.keras.models import Sequential, load_model
    from tensorflow.keras.layers import Conv2D, MaxPooling2D, Flatten, Dense, Dropout, Input
    HAS_TF = True
except ImportError:
    HAS_TF = False

class CustomCNNFaceModel:
    """
    Réseau de Neurones Convolutif (CNN) personnalisé pour l'extraction de vecteurs faciaux.
    Corrigé pour utiliser la couche Input et éviter les avertissements Keras.
    """
    def __init__(self, model_path='models/saved_custom_cnn.h5'):
        self.input_shape = (128, 128, 3)
        self.model_path = model_path
        self.model = None
        
        if HAS_TF and os.path.exists(self.model_path):
            try:
                self.model = load_model(self.model_path)
                print("[INFO] Modèle personnalisé CNN chargé avec succès depuis le stockage.")
            except Exception as e:
                print(f"[REMARQUE] Erreur au chargement, reconstruction de l'architecture : {e}")
                self.build_model_architecture()
        else:
            self.build_model_architecture()

    def build_model_architecture(self):
        """
        Définit l'empilement de couches convolutives.
        Utilise Input(shape) en tête pour se conformer aux standards Keras récents.
        """
        if not HAS_TF:
            print("[ATTENTION] TensorFlow non détecté, exécution en mode simulation mathématique.")
            return

        self.model = Sequential([
            # Utilisation de la couche Input explicite demandée par Keras
            Input(shape=self.input_shape),
            
            # Bloc Convolutif 1
            Conv2D(32, (3, 3), activation='relu'),
            MaxPooling2D(pool_size=(2, 2)),
            
            # Bloc Convolutif 2
            Conv2D(64, (3, 3), activation='relu'),
            MaxPooling2D(pool_size=(2, 2)),
            
            # Bloc Convolutif 3
            Conv2D(128, (3, 3), activation='relu'),
            MaxPooling2D(pool_size=(2, 2)),
            
            # Vectorisation et Couches denses
            Flatten(),
            Dense(256, activation='relu'),
            Dropout(0.5),
            Dense(128, activation='linear')
        ])
        
        self.model.compile(optimizer='adam', loss='mse')
        print("[INFO] Nouvelle architecture CNN personnalisée initialisée sans warning.")

    def extract_features(self, face_image):
        if not HAS_TF or self.model is None:
            h = int(np.sum(face_image) % 128)
            np.random.seed(h)
            return np.random.rand(128).astype(np.float32)

        try:
            import cv2
            resized = cv2.resize(face_image, (128, 128))
            normalized = resized.astype('float32') / 255.0
            batch_img = np.expand_dims(normalized, axis=0)
            embedding = self.model.predict(batch_img)
            return embedding[0]
        except Exception as e:
            print(f"[ERREUR] Échec de l'inférence CNN : {e}")
            return np.zeros((128,), dtype=np.float32)

    def train_on_dataset(self, X_train, y_train):
        if not HAS_TF or self.model is None:
            print("[INFO] Mode d'entraînement simulé activé.")
            return True
            
        try:
            self.model.fit(X_train, y_train, epochs=5, batch_size=4, verbose=0)
            self.model.save(self.model_path)
            print("[INFO] Modèle CNN réentraîné et sauvegardé.")
            return True
        except Exception as e:
            print(f"[ERREUR] Échec lors de l'entraînement : {e}")
            return False