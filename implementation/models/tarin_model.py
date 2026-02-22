import os
import numpy as np
import cv2
from tensorflow.keras.utils import to_categorical
from cnn_model import create_cnn_model

DATASET_PATH = "dataset"
IMG_SIZE = 128

def load_dataset():
    """
    Charge les images et crée X, y
    """

    images = []
    labels = []
    class_names = os.listdir(DATASET_PATH)

    for label, class_name in enumerate(class_names):

        class_path = os.path.join(DATASET_PATH, class_name)

        for img_name in os.listdir(class_path):

            img_path = os.path.join(class_path, img_name)

            img = cv2.imread(img_path)  # Lire image
            img = cv2.resize(img, (IMG_SIZE, IMG_SIZE))  # Redimensionner
            img = img / 255.0  # Normalisation

            images.append(img)
            labels.append(label)

    return np.array(images), to_categorical(labels), class_names


# Charger dataset
X, y, class_names = load_dataset()

# Créer modèle
model = create_cnn_model(len(class_names))

# Entraînement
model.fit(X, y, epochs=20, batch_size=32)

# Sauvegarde modèle
model.save("face_model.h5")

print("Model trained and saved successfully")
