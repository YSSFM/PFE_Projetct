# IMPORT DES BIBLIOTHÈQUES NÉCESSAIRES

# Import de la bibliothèque face_recognition pour la reconnaissance faciale
# Cette bibliothèque utilise dlib en arrière-plan
import face_recognition

# Import de numpy pour la manipulation des vecteurs d'encodage
# Les encodages faciaux sont des vecteurs de 128 nombres flottants
import numpy as np


# FONCTION POUR ENCODER UN VISAGE À PARTIR D'UNE IMAGE
def encode_face(image):
    """
    Détecte et encode un visage dans une image.
    L'encodage est un vecteur de 128 valeurs qui représente de manière unique un visage.
    
    Paramètres:
        image (numpy.ndarray): Image chargée (format RGB ou BGR)
    
    Retourne:
        numpy.ndarray: Vecteur d'encodage (128 valeurs) ou None si aucun visage détecté
    """
    
    # Détection de tous les visages dans l'image et calcul de leurs encodages
    # face_encodings retourne une liste d'encodages (un par visage détecté)
    face_encodings = face_recognition.face_encodings(image)
    
    # Vérification si au moins un visage a été détecté
    # len(face_encodings) == 0 signifie qu'aucun visage n'est présent
    if len(face_encodings) == 0:
        # Retour None pour indiquer l'absence de visage
        return None
    
    # Retourne l'encodage du PREMIER visage détecté
    # Si plusieurs visages sont présents, on ne prend que le premier
    # Dans un système plus avancé, on pourrait permettre de choisir
    return face_encodings[0]


# FONCTION POUR COMPARER DEUX VISAGES
def compare_faces(known_encoding, unknown_encoding, tolerance=0.5):
    """
    Compare un visage connu avec un visage inconnu pour vérifier s'ils correspondent.
    
    Paramètres:
        known_encoding (numpy.ndarray): Encodage du visage connu (128 valeurs)
        unknown_encoding (numpy.ndarray): Encodage du visage à tester
        tolerance (float): Seuil de similarité (plus c'est bas, plus c'est strict)
                           Valeur typique: 0.5 à 0.6
    
    Retourne:
        bool: True si les visages correspondent, False sinon
    """
    
    # Utilisation de la fonction compare_faces de face_recognition
    # Cette fonction calcule la distance entre les deux vecteurs d'encodage
    # Si la distance est inférieure à la tolérance, les visages correspondent
    match = face_recognition.compare_faces(
        [known_encoding],      # Le visage connu (dans une liste)
        unknown_encoding,      # Le visage inconnu
        tolerance=tolerance    # Seuil de tolérance
    )
    
    # match est une liste de booléens (un par visage connu)
    # On retourne le premier élément (True ou False)
    return match[0]

# FONCTION POUR CONVERTIR UN BLOB DE BASE DE DONNÉES EN VECTEUR NUMPY
def blob_to_numpy(blob):
    """
    Convertit des données binaires (BLOB) provenant de MySQL en vecteur numpy.
    Utile pour lire les encodages sauvegardés en base de données.
    
    Paramètres:
        blob (bytes): Données binaires stockées dans la base
    
    Retourne:
        numpy.ndarray: Vecteur d'encodage (128 nombres flottants)
    """
    
    # np.frombuffer lit des données binaires comme un tableau numpy
    # dtype=np.float64 indique que les nombres sont des flottants double précision
    # Les encodages face_recognition sont généralement en float64
    return np.frombuffer(blob, dtype=np.float64)


# FONCTION POUR CONVERTIR UN VECTEUR NUMPY EN BLOB
def numpy_to_blob(array):
    """
    Convertit un vecteur numpy en bytes pour stockage dans MySQL (type BLOB).
    
    Paramètres:
        array (numpy.ndarray): Vecteur d'encodage à sauvegarder
    
    Retourne:
        bytes: Données binaires à insérer dans la base
    """
    
    # array.tobytes() convertit le tableau numpy en bytes
    # Cette opération est réversible avec np.frombuffer
    return array.tobytes()


# FONCTION POUR DÉTECTER LES POSITIONS DES VISAGES
def detect_face_locations(image, model="hog"):
    """
    Détecte les positions de tous les visages dans une image.
    
    Paramètres:
        image (numpy.ndarray): Image à analyser (format RGB)
        model (str): Modèle de détection ("hog" pour rapide, "cnn" pour précis)
    
    Retourne:
        list: Liste de tuples (top, right, bottom, left) pour chaque visage
    """
    
    # Détection des positions des visages
    # model="hog" utilise HOG (Histogram of Oriented Gradients) - plus rapide
    # model="cnn" utilise un réseau de neurones - plus précis mais plus lent
    face_locations = face_recognition.face_locations(image, model=model)
    
    return face_locations


# FONCTION POUR DESSINER DES RECTANGLES AUTOUR DES VISAGES
def draw_face_rectangles(image, face_locations, color=(0, 255, 0), thickness=2):
    """
    Dessine des rectangles autour des visages détectés (utile pour l'affichage).
    Note: Cette fonction nécessite OpenCV (cv2).
    
    Paramètres:
        image (numpy.ndarray): Image sur laquelle dessiner
        face_locations (list): Liste des positions des visages
        color (tuple): Couleur du rectangle (B,G,R)
        thickness (int): Épaisseur du trait
    
    Retourne:
        numpy.ndarray: Image avec les rectangles dessinés
    """
    
    # Import d'OpenCV à l'intérieur de la fonction pour éviter une dépendance inutile
    # si cette fonction n'est pas appelée
    import cv2
    
    # Copie de l'image pour ne pas modifier l'originale
    result = image.copy()
    
    # Pour chaque visage détecté
    for (top, right, bottom, left) in face_locations:
        # Dessin du rectangle
        cv2.rectangle(result, (left, top), (right, bottom), color, thickness)
    
    return result

# FONCTION POUR CALCULER LA DISTANCE ENTRE DEUX ENCODAGES
def face_distance(known_encoding, unknown_encoding):
    """
    Calcule la distance euclidienne entre deux encodages faciaux.
    Plus la distance est petite, plus les visages sont similaires.
    
    Paramètres:
        known_encoding (numpy.ndarray): Premier encodage
        unknown_encoding (numpy.ndarray): Second encodage
    
    Retourne:
        float: Distance entre les deux vecteurs (0 = identique)
    """
    
    # Utilisation de la fonction face_distance de face_recognition
    # Cette fonction retourne la distance euclidienne
    distance = face_recognition.face_distance([known_encoding], unknown_encoding)
    
    # Retourne la distance (0.0 = parfaitement identique)
    # Valeur typique pour le même visage: < 0.5
    return distance[0]


# FONCTION POUR TROUVER LE MEILLEUR MATCH PARMI PLUSIEURS VISAGES CONNUS
def find_best_match(unknown_encoding, known_encodings, known_ids, tolerance=0.5):
    """
    Trouve l'identité correspondant le mieux à un visage inconnu.
    
    Paramètres:
        unknown_encoding (numpy.ndarray): Encodage du visage à identifier
        known_encodings (list): Liste des encodages connus
        known_ids (list): Liste des IDs correspondant aux encodages
        tolerance (float): Seuil de tolérance
    
    Retourne:
        tuple: (id, distance) ou (None, None) si aucun match trouvé
    """
    
    # Si aucun encodage connu n'est fourni
    if len(known_encodings) == 0:
        return None, None
    
    # Comparaison du visage inconnu avec tous les visages connus
    matches = face_recognition.compare_faces(known_encodings, unknown_encoding, tolerance)
    
    # Calcul des distances pour tous les visages connus
    distances = face_recognition.face_distance(known_encodings, unknown_encoding)
    
    # Recherche de l'index du meilleur match (distance la plus petite)
    if True in matches:
        # Récupération de tous les indices où matches est True
        match_indices = [i for i, m in enumerate(matches) if m]
        
        # Parmi ces indices, trouver celui avec la plus petite distance
        best_index = min(match_indices, key=lambda i: distances[i])
        
        # Vérification que la distance est inférieure à la tolérance
        if distances[best_index] <= tolerance:
            # Retourne l'ID et la distance
            return known_ids[best_index], distances[best_index]
    
    # Aucun match trouvé
    return None, None


# FONCTION POUR PRÉ-TRAITER UNE IMAGE (OPTIMISATION)
def preprocess_image(image, resize_factor=0.25):
    """
    Prétraite une image pour accélérer la détection de visages.
    
    Paramètres:
        image (numpy.ndarray): Image d'entrée
        resize_factor (float): Facteur de réduction (0.25 = 25% de la taille)
    
    Retourne:
        numpy.ndarray: Image prétraitée
    """
    
    # Import d'OpenCV
    import cv2
    
    # Redimensionnement de l'image
    if resize_factor != 1.0:
        new_width = int(image.shape[1] * resize_factor)
        new_height = int(image.shape[0] * resize_factor)
        image = cv2.resize(image, (new_width, new_height))
    
    # Conversion BGR -> RGB si nécessaire
    if len(image.shape) == 3 and image.shape[2] == 3:
        # OpenCV utilise BGR, face_recognition utilise RGB
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    return image