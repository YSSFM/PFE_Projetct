# app.py
# Application principale Flask

import os
os.environ['OPENCV_VIDEOIO_MSMF_ENABLE'] = '0'
import json
from flask import Flask, session, redirect, url_for, render_template
from routes.auth_routes import auth_bp
from routes.student_routes import student_bp
from routes.presence_routes import presence_bp

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Enregistrement des blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(student_bp)
app.register_blueprint(presence_bp)


def is_model_chosen():
    """Vérifie si le modèle a déjà été choisi"""
    config_file = "models/model_choice.json"
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                data = json.load(f)
                return data.get('confirmed', False)
        except:
            pass
    return False


@app.route('/')
def index():
    """Page d'accueil"""
    if 'user' in session:
        # Vérifier si le modèle a été choisi
        if is_model_chosen():
            return redirect(url_for('student.accueil'))
        else:
            # Rediriger vers le choix du modèle
            return redirect(url_for('student.choose_model'))
    return redirect(url_for('auth.login_page'))


@app.route('/logout')
def logout():
    """Déconnexion"""
    session.clear()
    return redirect(url_for('auth.login_page'))


if __name__ == '__main__':
    # Création des dossiers nécessaires
    os.makedirs('models', exist_ok=True)
    os.makedirs('static/photos', exist_ok=True)
    
    print("=" * 50)
    print("✅ Serveur EST Meknès démarré")
    print("📁 Dossiers: models, static/photos")
    print("🔗 http://localhost:5000")
    print("=" * 50)
    
    # Désactiver le mode debug pour éviter les conflits avec OpenCV
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)