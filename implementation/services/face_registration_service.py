import cv2
import numpy as np
from db.database import get_connection, close_connection
from services.deep_face_service import get_recognizer

def register_faces():
    """
    Capture et enregistre l'empreinte faciale d'un étudiant.
    Fonctionnalité de capture par ESPACE préservée.
    """
    recognizer = get_recognizer()
    recognizer.initialize()

    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    # On garde votre logique de sélection automatique
    cursor.execute("SELECT id, nom, prenom FROM etudiant WHERE face_embedding IS NULL LIMIT 1")
    student = cursor.fetchone()
    cursor.close()
    
    if not student:
        print("⚠️ Aucun étudiant en attente.")
        close_connection(connection)
        return False

    cap = cv2.VideoCapture(0)
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    
    print(f"📸 Mode Capture pour : {student['prenom']} {student['nom']}")

    while True:
        ret, frame = cap.read()
        if not ret: break

        display_frame = frame.copy()
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.1, 5)

        for (x, y, w, h) in faces:
            cv2.rectangle(display_frame, (x, y), (x+w, y+h), (255, 0, 0), 2)

        cv2.imshow("Enregistrement - Appuyez sur ESPACE", display_frame)
        key = cv2.waitKey(1) & 0xFF

        if key == 32: # ESPACE - Fonctionnalité préservée
            if len(faces) > 0:
                x, y, w, h = faces[0]
                face_roi = frame[y:y+h, x:x+w]
                
                # On génère l'embedding au lieu de l'histogramme
                embedding = recognizer.get_face_embedding(face_roi)
                if embedding is not None:
                    # Sauvegarde directe (Fonctionnalité préservée)
                    success = recognizer.save_face_embedding(student['id'], embedding)
                    cap.release()
                    cv2.destroyAllWindows()
                    return success
            else:
                print("❌ Aucun visage détecté.")
        elif key == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    return False

def register_face(student_id=None):
    """ Alias pour assurer la liaison avec face_routes.py """
    return register_faces()