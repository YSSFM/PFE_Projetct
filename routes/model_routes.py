# routes/model_routes.py
# Route pour la sélection du modèle de reconnaissance faciale

from flask import Blueprint, render_template, session, redirect, url_for, request
import json
import os

model_bp = Blueprint('model', __name__)

# Fichier pour stocker le choix du modèle
MODEL_CONFIG_FILE = "models/model_choice.json"

def get_saved_model_choice():
    """Récupère le choix du modèle sauvegardé"""
    if os.path.exists(MODEL_CONFIG_FILE):
        try:
            with open(MODEL_CONFIG_FILE, 'r') as f:
                data = json.load(f)
                return data.get('model_type', 'pretrained')
        except:
            return 'pretrained'
    return 'pretrained'

def save_model_choice(model_type):
    """Sauvegarde le choix du modèle"""
    os.makedirs('models', exist_ok=True)
    with open(MODEL_CONFIG_FILE, 'w') as f:
        json.dump({'model_type': model_type}, f)

@model_bp.route('/choose-model')
def choose_model():
    """Page de sélection du modèle"""
    if 'user' not in session:
        return redirect(url_for('auth.login_page'))
    
    current_choice = get_saved_model_choice()
    return render_template('choose_model.html', current_choice=current_choice)

@model_bp.route('/select-model', methods=['POST'])
def select_model():
    """Enregistre le choix du modèle"""
    if 'user' not in session:
        return redirect(url_for('auth.login_page'))
    
    model_type = request.form.get('model_type', 'pretrained')
    save_model_choice(model_type)
    
    return redirect(url_for('student.dashboard'))

@model_bp.route('/get-current-model')
def get_current_model():
    """API pour récupérer le modèle actuel"""
    return {'model_type': get_saved_model_choice()}