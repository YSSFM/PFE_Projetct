import cv2
import numpy as np
from db.database import get_connection, close_connection
from services.deep_face_service import get_recognizer
import os

def register_faces():
    """
    Capture un nouveau visage et l'enregistre pour l'étudiant sélectionné
    """
    print("=" * 50)
    print("📸 ENREGISTREMENT D'UN NOUVEAU VISAGE")
    print("=" * 50)
    
    # Récupérer le premier étudiant sans visage
    connection = get_connection()
    if connection is None:
        return False
    
    cursor = connection.cursor(dictionary=True)
    cursor.execute("""
        SELECT id, nom, prenom, matricule
        FROM etudiant
        WHERE face_embedding IS NULL
        LIMIT 1
    """)
    
    student = cursor.fetchone()
    cursor.close()
    close_connection(connection)
    
    if not student:
        print("⚠️ Aucun étudiant sans visage")
        print("   Veuillez d'abord ajouter un étudiant dans 'Gestion des étudiants'")
        return False
    
    print(f"\n👤 Enregistrement pour: {student['prenom']} {student['nom']}")
    print(f"   Matricule: {student['matricule']}")
    print("\n📸 Regardez la caméra...")
    print("💡 Appuyez sur ESPACE pour capturer")
    print("💡 Appuyez sur Q pour quitter")
    
    # Initialiser le reconnaisseur
    recognizer = get_recognizer()
    
    # Détecteur Haar
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    
    # Webcam
    cap = cv2.VideoCapture(0)
    cap.set(3, 640)
    cap.set(4, 480)
    
    if not cap.isOpened():
        print("❌ Webcam inaccessible")
        return False
    
    face_embedding = None
    captured_image = None
    
    while True:
        ret, frame = cap.read()
        if not ret:
            continue
        
        display_frame = frame.copy()
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(100, 100))
        
        for (x, y, w, h) in faces:
            cv2.rectangle(display_frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
            cv2.putText(display_frame, "VISAGE DETECTE", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        # Instructions
        cv2.putText(display_frame, f"Etudiant: {student['prenom']} {student['nom']}", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(display_frame, "Appuyez sur ESPACE pour capturer", (10, 60),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cv2.putText(display_frame, "Appuyez sur Q pour quitter", (10, 90),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        cv2.imshow("Enregistrement - RecoJY", display_frame)
        
        key = cv2.waitKey(1) & 0xFF
        
        if key == 32:  # ESPACE
            if len(faces) > 0:
                x, y, w, h = faces[0]
                face_roi = frame[y:y+h, x:x+w]
                
                # Générer l'empreinte
                face_embedding = recognizer.get_face_embedding(face_roi)
                captured_image = frame.copy()
                
                if face_embedding is not None:
                    print("✅ Visage capturé!")
                    break
                else:
                    print("❌ Erreur: Impossible d'extraire l'empreinte")
            else:
                print("❌ Aucun visage détecté!")
        
        elif key == ord('q'):
            print("❌ Enregistrement annulé")
            cap.release()
            cv2.destroyAllWindows()
            return False
    
    cap.release()
    cv2.destroyAllWindows()
    
    if face_embedding is None:
        return False
    
    # Sauvegarder l'empreinte
    connection = get_connection()
    if connection is None:
        return False
    
    cursor = connection.cursor()
    
    try:
        embedding_bytes = face_embedding.astype(np.float32).tobytes()
        cursor.execute("""
            UPDATE etudiant SET face_embedding = %s WHERE id = %s
        """, (embedding_bytes, student["id"]))
        connection.commit()
        print(f"✅ Visage enregistré pour {student['prenom']} {student['nom']}")
        
        # Sauvegarder l'image capturée (optionnel)
        try:
            _, img_encoded = cv2.imencode('.jpg', captured_image)
            with open(f"capture_{student['id']}.jpg", "wb") as f:
                f.write(img_encoded.tobytes())
        except:
            pass
        
        return True
    except Exception as e:
        connection.rollback()
        print(f"❌ Erreur sauvegarde: {e}")
        return False
    finally:
        cursor.close()
        close_connection(connection)


register_face = register_faces
