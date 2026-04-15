import cv2
import numpy as np
from db.database import get_connection, close_connection
from services.attendance_service import mark_attendance
from services.deep_face_service import get_recognizer

# Configuration technique
RECOGNITION_THRESHOLD = 0.45  # Seuil pour MobileNetV2
FRAME_SKIP = 2

def recognize_faces():
    """
    Moteur principal de reconnaissance pour le marquage des présences.
    Remplace l'ancienne logique d'histogrammes par le Deep Learning.
    """
    recognizer = get_recognizer()
    recognizer.initialize()
    recognizer.load_known_faces_from_db()
    
    # Haar Cascade utilisé uniquement pour le dessin rapide des boîtes
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    
    cap = cv2.VideoCapture(0)
    marked_today = set()
    frame_count = 0

    while True:
        ret, frame = cap.read()
        if not ret: break

        frame_count += 1
        display_frame = frame.copy()
        
        if frame_count % FRAME_SKIP == 0:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(100, 100))

            for (x, y, w, h) in faces:
                face_roi = frame[y:y+h, x:x+w]
                
                # Appel au nouveau moteur de reconnaissance (MobileNetV2)
                student_id, name, distance = recognizer.identify_face(face_roi, threshold=RECOGNITION_THRESHOLD)

                if student_id:
                    color = (0, 255, 0)
                    label = f"{name} ({int((1-distance)*100)}%)"
                    
                    # Logique de présence (Fonctionnalité préservée)
                    if student_id not in marked_today:
                        if mark_attendance(student_id):
                            marked_today.add(student_id)
                else:
                    color = (0, 0, 255)
                    label = "Inconnu"

                cv2.rectangle(display_frame, (x, y), (x+w, y+h), color, 2)
                cv2.putText(display_frame, label, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

        cv2.imshow('Reconnaissance Faciale - Mode Presence', display_frame)
        if cv2.waitKey(1) & 0xFF == ord('q'): break

    cap.release()
    cv2.destroyAllWindows()

def recognize_face():
    """ Alias pour assurer la liaison avec face_routes.py sans erreur d'import """
    return recognize_faces()