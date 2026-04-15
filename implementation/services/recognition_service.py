import cv2
import numpy as np
from db.database import get_connection, close_connection
from services.attendance_service import mark_attendance
from services.deep_face_service import get_recognizer

# Configuration
RECOGNITION_THRESHOLD = 0.45
FRAME_SKIP = 2

def recognize_faces():
    """
    Moteur principal de reconnaissance pour le marquage des présences.
    Utilise MobileNetV2 pour l'extraction d'empreintes.
    """
    print("=" * 50)
    print("📸 RECONNAISSANCE FACIALE")
    print("=" * 50)
    
    # Initialisation du reconnaisseur
    recognizer = get_recognizer()
    recognizer.initialize()
    recognizer.load_known_faces_from_db()
    
    if len(recognizer.known_encodings) == 0:
        print("❌ Aucun visage enregistré dans la base")
        print("   Utilisez d'abord 'Enregistrement visage'")
        return
    
    # Détecteur Haar pour la détection rapide
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    
    # Webcam
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
    if not cap.isOpened():
        print("❌ Webcam inaccessible")
        return
    
    print("🎥 Reconnaissance en cours...")
    print("💡 Appuyez sur Q pour quitter")
    
    marked_today = set()
    frame_count = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_count += 1
        display_frame = frame.copy()
        
        if frame_count % FRAME_SKIP == 0:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(100, 100))

            for (x, y, w, h) in faces:
                face_roi = frame[y:y+h, x:x+w]
                
                # Extraire l'empreinte avec MobileNetV2
                embedding = recognizer.get_face_embedding(face_roi)
                
                if embedding is not None:
                    # Trouver le meilleur match
                    student_id, name, distance = recognizer.find_best_match(embedding, RECOGNITION_THRESHOLD)

                    if student_id:
                        # Visage reconnu
                        color = (0, 255, 0)
                        label = f"{name} ({int((1-distance)*100)}%)"
                        
                        if student_id not in marked_today:
                            if mark_attendance(student_id):
                                marked_today.add(student_id)
                                print(f"✅ {name} - Présence marquée")
                    else:
                        # Visage non reconnu
                        color = (0, 0, 255)
                        label = "INCONNU"

                    # Dessiner le rectangle et le nom
                    cv2.rectangle(display_frame, (x, y), (x+w, y+h), color, 2)
                    cv2.putText(display_frame, label, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        
        # Informations à l'écran
        cv2.putText(display_frame, f"Visages en base: {len(recognizer.known_encodings)} | Presences: {len(marked_today)}", 
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cv2.putText(display_frame, "Appuyez sur Q", 
                   (10, display_frame.shape[0]-20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
        
        cv2.imshow('Reconnaissance Faciale - RecoJY', display_frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    print(f"🏁 FIN - {len(marked_today)} présences marquées")

# Alias pour compatibilité
recognize_face = recognize_faces
