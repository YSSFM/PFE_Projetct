# ===================================================================
# train_routes.py - ROUTES POUR L'ENTRAÎNEMENT DU MODÈLE CNN
# ===================================================================

from flask import Blueprint, jsonify, session, redirect, url_for
import threading
import logging
import subprocess
import sys
import os

logger = logging.getLogger(__name__)

train_bp = Blueprint("train", __name__, url_prefix="/api/train")

# Thread pour l'entraînement
_training_thread = None
_training_lock = threading.Lock()


def run_training():
    """Exécute l'entraînement du modèle CNN."""
    try:
        logger.info("🚀 Démarrage de l'entraînement CNN...")
        
        # Importer et exécuter l'entraînement
        from models.cnn_model import train_cnn
        train_cnn()
        
        logger.info("✅ Entraînement terminé avec succès")
        
        # Rafraîchir le service de reconnaissance
        from services.deep_face_service import refresh_embeddings
        refresh_embeddings()
        
    except Exception as e:
        logger.error(f"❌ Erreur pendant l'entraînement: {e}")


@train_bp.route("/start", methods=["POST"])
def start_training():
    """
    Démarre l'entraînement du modèle CNN.
    POST /api/train/start
    """
    global _training_thread
    
    if "admin" not in session:
        return jsonify({"error": "Non authentifié"}), 401
    
    with _training_lock:
        if _training_thread is not None and _training_thread.is_alive():
            return jsonify({
                "error": "Un entraînement est déjà en cours",
                "status": "running"
            }), 409
    
    _training_thread = threading.Thread(
        target=run_training,
        daemon=True,
        name="TrainingThread"
    )
    _training_thread.start()
    
    return jsonify({
        "message": "Entraînement démarré en arrière-plan",
        "status": "started"
    })


@train_bp.route("/status", methods=["GET"])
def training_status():
    """
    Vérifie l'état de l'entraînement.
    GET /api/train/status
    """
    is_running = False
    with _training_lock:
        if _training_thread is not None:
            is_running = _training_thread.is_alive()
    
    return jsonify({
        "training_active": is_running
    })


@train_bp.route("/dataset/process", methods=["POST"])
def process_dataset_route():
    """
    Traite le dataset et génère les embeddings.
    POST /api/train/dataset/process
    """
    if "admin" not in session:
        return jsonify({"error": "Non authentifié"}), 401
    
    def run_processing():
        try:
            from dataset import process_dataset
            process_dataset()
            from services.deep_face_service import refresh_embeddings
            refresh_embeddings()
        except Exception as e:
            logger.error(f"Erreur traitement dataset: {e}")
    
    thread = threading.Thread(target=run_processing, daemon=True)
    thread.start()
    
    return jsonify({
        "message": "Traitement du dataset démarré",
        "status": "started"
    })