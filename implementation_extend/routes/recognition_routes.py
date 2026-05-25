# ===================================================================
# recognition_routes.py - ROUTES POUR LA RECONNAISSANCE FACIALE
# VERSION STABLE CORRIGÉE
# ===================================================================

from flask import Blueprint, jsonify, render_template, session, redirect, url_for
import threading
import logging
from datetime import datetime

from services.recognition_service import ContinuousRecognitionService
from services.deep_face_service import get_face_recognition_service, refresh_embeddings

logger = logging.getLogger(__name__)

recognition_bp = Blueprint("recognition", __name__)

# =========================================================
# THREAD MANAGEMENT
# =========================================================

active_threads = {}
thread_lock = threading.Lock()


def cleanup_finished_threads():
    """Nettoie les threads terminés."""
    with thread_lock:
        to_remove = []
        for key, thread in active_threads.items():
            if not thread.is_alive():
                to_remove.append(key)
        
        for key in to_remove:
            del active_threads[key]
            logger.info(f"🧹 Thread supprimé: {key}")


# =========================================================
# SERVICE SINGLETON POUR LA RECONNAISSANCE
# =========================================================

_recognition_service = None


def get_recognition_service():
    """Récupère l'instance unique du service de reconnaissance."""
    global _recognition_service
    if _recognition_service is None:
        _recognition_service = ContinuousRecognitionService()
    return _recognition_service


# =========================================================
# FONCTION DE RECONNAISSANCE EN THREAD
# =========================================================

def run_recognition_pipeline():
    """Exécute le pipeline de reconnaissance dans un thread séparé."""
    service = get_recognition_service()
    service.start_recognition()


# =========================================================
# ROUTES
# =========================================================

@recognition_bp.route("/recognize")
def recognize():
    """
    Démarre la reconnaissance faciale.
    GET /api/recognize
    """
    cleanup_finished_threads()
    
    with thread_lock:
        if "recognition" in active_threads and active_threads["recognition"].is_alive():
            return jsonify({
                "error": "La reconnaissance est déjà en cours",
                "status": "running"
            }), 409
    
    # Créer et démarrer le thread
    thread = threading.Thread(
        target=run_recognition_pipeline,
        daemon=True,
        name="RecognitionThread"
    )
    
    with thread_lock:
        active_threads["recognition"] = thread
    
    thread.start()
    
    return jsonify({
        "message": "Reconnaissance faciale démarrée",
        "status": "running",
        "instruction": "Appuyez sur 'q' pour arrêter"
    })


@recognition_bp.route("/recognize/stop", methods=["POST"])
def stop_recognition():
    """
    Arrête la reconnaissance faciale.
    POST /api/recognize/stop
    """
    service = get_recognition_service()
    service.stop_recognition()
    
    cleanup_finished_threads()
    
    return jsonify({
        "message": "Reconnaissance arrêtée",
        "status": "stopped"
    })


@recognition_bp.route("/recognize/status", methods=["GET"])
def recognition_status():
    """
    Vérifie l'état de la reconnaissance.
    GET /api/recognize/status
    """
    cleanup_finished_threads()
    
    is_running = False
    with thread_lock:
        if "recognition" in active_threads:
            is_running = active_threads["recognition"].is_alive()
    
    # Obtenir le nombre d'embeddings chargés
    try:
        recognizer = get_face_recognition_service()
        embedding_count = recognizer.get_embedding_count() if recognizer else 0
    except:
        embedding_count = 0
    
    return jsonify({
        "recognition_active": is_running,
        "embeddings_loaded": embedding_count,
        "active_threads": len(active_threads)
    })


@recognition_bp.route("/recognize/refresh", methods=["POST"])
def refresh_embeddings_route():
    """
    Rafraîchit les embeddings depuis la base de données.
    POST /api/recognize/refresh
    """
    try:
        refresh_embeddings()
        recognizer = get_face_recognition_service()
        count = recognizer.get_embedding_count() if recognizer else 0
        return jsonify({
            "message": "Embeddings rafraîchis",
            "embeddings_count": count
        })
    except Exception as e:
        logger.error(f"Erreur rafraîchissement: {e}")
        return jsonify({"error": str(e)}), 500


@recognition_bp.route("/recognize/test")
def recognition_test():
    """
    Page de test pour la reconnaissance.
    GET /recognize/test
    """
    return render_template("recognition_test.html")


# =========================================================
# PAGE D'ENREGISTREMENT
# =========================================================

@recognition_bp.route("/register")
def register_page():
    """Page d'enregistrement des visages."""
    if "admin" not in session:
        return redirect(url_for("admin"))
    return render_template("register_faces.html")