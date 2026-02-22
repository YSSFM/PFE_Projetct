# Importation bibliothèques nécessaires
import numpy as np
import cv2
import os

# Dataset public pour expérimentation
from sklearn.datasets import fetch_lfw_people

# Séparation train/test
from sklearn.model_selection import train_test_split

# Mesure performance
from sklearn.metrics import accuracy_score

# Import modules que nous avons créés
from feature_extractor import load_feature_extractor
from classifiers import create_knn, create_svm

# 1. Charger dataset LFW (dataset public académique)
print("Loading dataset")
lfw = fetch_lfw_people(min_faces_per_person=70, resize=0.5)

X = lfw.images
y = lfw.target
class_names = lfw.target_names

print("Dataset loaded:", X.shape)

# 2. Préparation des images pour MobileNet
IMG_SIZE = 224  # taille requise par MobileNet

processed_images = []

for img in X:

    # Convertir image grayscale --> RGB
    img_rgb = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)

    # Redimensionner
    img_resized = cv2.resize(img_rgb, (IMG_SIZE, IMG_SIZE))

    # Normalisation (0 --> 1)
    img_resized = img_resized / 255.0

    processed_images.append(img_resized)

processed_images = np.array(processed_images)

print("Images preprocessed:", processed_images.shape)

# 3. Extraction des features via CNN
print("Loading feature extractor")
feature_extractor = load_feature_extractor()

print("Extracting features")
features = feature_extractor.predict(processed_images)

print("Feature shape:", features.shape)

from sklearn.preprocessing import StandardScaler
scaler = StandardScaler()
features = scaler.fit_transform(features)

# 4. Separation train / test
X_train, X_test, y_train, y_test = train_test_split(
    features, y, test_size=0.3, random_state=42
)

# 5. Entraînement KNN
print("Training KNN")
knn = create_knn()
knn.fit(X_train, y_train)

knn_predictions = knn.predict(X_test)
knn_accuracy = accuracy_score(y_test, knn_predictions)

print("KNN Accuracy:", knn_accuracy)

# 6. Entraînement SVM
print("Training SVM")
svm = create_svm()
svm.fit(X_train, y_train)

svm_predictions = svm.predict(X_test)
svm_accuracy = accuracy_score(y_test, svm_predictions)

print("SVM Accuracy:", svm_accuracy)

# 7. Comparaison finale
print("\nFINAL RESULTS\n")
print("\nKNN Accuracy:", knn_accuracy)
print("\nSVM Accuracy:", svm_accuracy)

# 8. Sauvegarde des modèles
import pickle

# Sauvegarder scaler
with open("models/scaler.pkl", "wb") as f:
    pickle.dump(scaler, f)

# Sauvegarder SVM
with open("models/svm_model.pkl", "wb") as f:
    pickle.dump(svm, f)

# Sauvegarder KNN
with open("models/knn_model.pkl", "wb") as f:
    pickle.dump(knn, f)

print("Models saved successfully")
