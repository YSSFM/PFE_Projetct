from flask import Blueprint, jsonify
from services.recognition_service import recognize_faces
from services.face_registration_service import register_faces
import threading

recognition_bp = Blueprint("recognition", __name__)

active_threads = {}
thread_lock = threading.Lock()


def cleanup_finished_threads():
    with thread_lock:
        to_remove = []
        for key, thread in active_threads.items():
            if not thread.is_alive():
                to_remove.append(key)
        for key in to_remove:
            del active_threads[key]
            print(f"🧹 Thread {key} nettoyé")


@recognition_bp.route("/recognize")
def recognize():
    """Démarre la RECONNAISSANCE (marquage de présence)"""
    cleanup_finished_threads()
    
    with thread_lock:
        if "recognition" in active_threads and active_threads["recognition"].is_alive():
            return jsonify({"error": "Une reconnaissance est déjà en cours"}), 409
    
    recognition_thread = threading.Thread(target=recognize_faces, daemon=True, name="RecognitionThread")
    
    with thread_lock:
        active_threads["recognition"] = recognition_thread
    
    recognition_thread.start()
    
    return jsonify({
        "message": "Reconnaissance démarrée",
        "status": "running",
        "instruction": "Appuyez sur Q dans la fenêtre OpenCV pour arrêter"
    })


@recognition_bp.route("/recognize/register")
def register():
    """Démarre l'ENREGISTREMENT d'un nouveau visage"""
    cleanup_finished_threads()
    
    with thread_lock:
        if "register" in active_threads and active_threads["register"].is_alive():
            return jsonify({"error": "Un enregistrement est déjà en cours"}), 409
    
    register_thread = threading.Thread(target=register_faces, daemon=True, name="RegistrationThread")
    
    with thread_lock:
        active_threads["register"] = register_thread
    
    register_thread.start()
    
    return jsonify({
        "message": "Enregistrement démarré",
        "status": "running",
        "instruction": "Placez-vous face à la caméra et appuyez sur ESPACE"
    })


@recognition_bp.route("/recognize/stop", methods=["POST"])
def stop_recognition():
    """Arrête la reconnaissance"""
    with thread_lock:
        if "recognition" not in active_threads:
            return jsonify({"error": "Aucune reconnaissance en cours"}), 404
    
    return jsonify({
        "message": "Veuillez appuyer sur Q dans la fenêtre OpenCV pour arrêter",
        "instruction": "La fenêtre de reconnaissance doit être active"
    })


@recognition_bp.route("/recognize/status", methods=["GET"])
def recognition_status():
    """Retourne l'état des threads"""
    cleanup_finished_threads()
    status = {}
    with thread_lock:
        for key, thread in active_threads.items():
            status[key] = {"alive": thread.is_alive(), "name": thread.name}
    return jsonify({"active_threads": status, "count": len(status)})
