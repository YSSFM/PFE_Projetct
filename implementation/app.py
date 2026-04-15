<<<<<<< HEAD
# -------------------------------------------------------------------
# IMPORT DES BIBLIOTHÈQUES NÉCESSAIRES
# -------------------------------------------------------------------

from flask import Flask, render_template, request, redirect, session, jsonify, url_for
from routes.student_routes import student_bp
from routes.face_routes import face_bp
from routes.recognition_routes import recognition_bp
from routes.report_routes import report_bp
from db.database import get_connection
import hashlib
import secrets
from datetime import datetime, timedelta
import re

# -------------------------------------------------------------------
# CRÉATION DE L'APPLICATION
# -------------------------------------------------------------------

app = Flask(__name__)
app.secret_key = "votre_cle_secrete_tres_longue_et_difficile_a_deviner_2025"
app.permanent_session_lifetime = timedelta(hours=1)

# -------------------------------------------------------------------
# FONCTIONS UTILITAIRES
# -------------------------------------------------------------------

def hash_password(password):
    """Hache un mot de passe avec SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, hashed):
    """Vérifie si un mot de passe correspond à son haché"""
    return hash_password(password) == hashed

def validate_email(email):
    """Valide le format d'un email"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password_strength(password):
    """Vérifie la force d'un mot de passe"""
    if len(password) < 8:
        return False, "Le mot de passe doit contenir au moins 8 caractères"
    if not re.search(r'[A-Z]', password):
        return False, "Le mot de passe doit contenir au moins une majuscule"
    if not re.search(r'[a-z]', password):
        return False, "Le mot de passe doit contenir au moins une minuscule"
    if not re.search(r'[0-9]', password):
        return False, "Le mot de passe doit contenir au moins un chiffre"
    return True, "Mot de passe valide"

# -------------------------------------------------------------------
# ROUTES PRINCIPALES
# -------------------------------------------------------------------

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/about")
def about():
    """Affiche la page À propos"""
    return render_template("about.html")

@app.route("/admin")
def admin():
    return render_template("admin_login.html")

@app.route("/admin/register")
def admin_register_page():
    return render_template("admin_register.html")

@app.route("/admin/login", methods=["POST"])
def admin_login_api():
    """API de connexion admin (JSON)"""
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "Données invalides"}), 400
    
    username_or_email = data.get("username", "").strip()
    password = data.get("password", "")
    
    if not username_or_email or not password:
        return jsonify({"error": "Veuillez remplir tous les champs"}), 400
    
    connection = get_connection()
    if connection is None:
        return jsonify({"error": "Erreur de connexion à la base de données"}), 500
    
    cursor = connection.cursor(dictionary=True)
    
    try:
        cursor.execute(
            "SELECT id, nom, prenom, email, username, password_hash FROM admin WHERE username = %s OR email = %s",
            (username_or_email, username_or_email)
        )
        admin = cursor.fetchone()
        
        if not admin or not verify_password(password, admin["password_hash"]):
            return jsonify({"error": "Identifiants incorrects"}), 401
        
        session.permanent = True
        session["admin"] = True
        session["admin_id"] = admin["id"]
        session["admin_nom"] = admin["nom"]
        session["admin_prenom"] = admin["prenom"]
        session["admin_username"] = admin["username"]
        
        return jsonify({
            "message": "Connexion réussie",
            "admin": {
                "id": admin["id"],
                "nom": admin["nom"],
                "prenom": admin["prenom"],
                "username": admin["username"]
            }
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        connection.close()

@app.route("/admin/register", methods=["POST"])
def admin_register_api():
    """API d'inscription admin (JSON)"""
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "Données invalides"}), 400
    
    nom = data.get("nom", "").strip()
    prenom = data.get("prenom", "").strip()
    email = data.get("email", "").strip().lower()
    username = data.get("username", "").strip()
    password = data.get("password", "")
    
    # Validation des champs
    if not nom:
        return jsonify({"error": "Le nom est requis"}), 400
    if not prenom:
        return jsonify({"error": "Le prénom est requis"}), 400
    if not email:
        return jsonify({"error": "L'email est requis"}), 400
    if not validate_email(email):
        return jsonify({"error": "Email invalide"}), 400
    if not username:
        return jsonify({"error": "Le nom d'utilisateur est requis"}), 400
    if not password:
        return jsonify({"error": "Le mot de passe est requis"}), 400
    
    # Validation de la force du mot de passe
    is_valid, message = validate_password_strength(password)
    if not is_valid:
        return jsonify({"error": message}), 400
    
    connection = get_connection()
    if connection is None:
        return jsonify({"error": "Erreur de connexion à la base de données"}), 500
    
    cursor = connection.cursor()
    
    try:
        # Vérifier si l'email ou username existe déjà
        cursor.execute(
            "SELECT id FROM admin WHERE email = %s OR username = %s",
            (email, username)
        )
        if cursor.fetchone():
            return jsonify({"error": "Cet email ou nom d'utilisateur existe déjà"}), 400
        
        # Hashage du mot de passe
        password_hash = hash_password(password)
        
        # Insertion du nouvel administrateur
        cursor.execute(
            "INSERT INTO admin (nom, prenom, email, username, password_hash) VALUES (%s, %s, %s, %s, %s)",
            (nom, prenom, email, username, password_hash)
        )
        connection.commit()
        
        return jsonify({"message": "Compte créé avec succès"}), 201
        
    except Exception as e:
        connection.rollback()
        print(f"❌ Erreur inscription: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        connection.close()

@app.route("/admin/logout")
def admin_logout():
    session.clear()
    return redirect(url_for("home"))

@app.route("/dashboard")
def dashboard():
    if "admin" not in session:
        return redirect(url_for("admin"))
    return render_template("dashboard.html", username=session.get("admin_username"))

@app.route("/admin/profile")
def admin_profile():
    if "admin" not in session:
        return redirect(url_for("admin"))
    return render_template("admin_profile.html")

@app.route("/admin/api/profile", methods=["GET"])
def admin_get_profile():
    if "admin" not in session:
        return jsonify({"error": "Non authentifié"}), 401
    
    connection = get_connection()
    if connection is None:
        return jsonify({"error": "Erreur de connexion"}), 500
    
    cursor = connection.cursor(dictionary=True)
    
    try:
        cursor.execute(
            "SELECT id, nom, prenom, email, username, created_at FROM admin WHERE id = %s",
            (session["admin_id"],)
        )
        admin = cursor.fetchone()
        
        if not admin:
            return jsonify({"error": "Administrateur non trouvé"}), 404
        
        return jsonify(admin)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        connection.close()

@app.route("/admin/api/profile", methods=["PUT"])
def admin_update_profile():
    if "admin" not in session:
        return jsonify({"error": "Non authentifié"}), 401
    
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "Données invalides"}), 400
    
    nom = data.get("nom", "").strip()
    prenom = data.get("prenom", "").strip()
    email = data.get("email", "").strip().lower()
    username = data.get("username", "").strip()
    
    if not nom or not prenom or not email or not username:
        return jsonify({"error": "Tous les champs sont requis"}), 400
    if not validate_email(email):
        return jsonify({"error": "Email invalide"}), 400
    
    connection = get_connection()
    if connection is None:
        return jsonify({"error": "Erreur de connexion"}), 500
    
    cursor = connection.cursor()
    
    try:
        # Vérifier si l'email ou username n'est pas utilisé par un autre admin
        cursor.execute(
            "SELECT id FROM admin WHERE (email = %s OR username = %s) AND id != %s",
            (email, username, session["admin_id"])
        )
        if cursor.fetchone():
            return jsonify({"error": "Cet email ou nom d'utilisateur est déjà utilisé"}), 400
        
        # Mise à jour
        cursor.execute(
            "UPDATE admin SET nom = %s, prenom = %s, email = %s, username = %s WHERE id = %s",
            (nom, prenom, email, username, session["admin_id"])
        )
        connection.commit()
        
        # Mise à jour de la session
        session["admin_nom"] = nom
        session["admin_prenom"] = prenom
        session["admin_username"] = username
        
        return jsonify({"message": "Profil mis à jour avec succès"})
    except Exception as e:
        connection.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        connection.close()

@app.route("/admin/forgot-password", methods=["POST"])
def admin_forgot_password():
    data = request.get_json()
    email = data.get("email", "").strip().lower()
    
    if not email:
        return jsonify({"error": "L'email est requis"}), 400
    
    connection = get_connection()
    if connection is None:
        return jsonify({"error": "Erreur de connexion"}), 500
    
    cursor = connection.cursor()
    
    try:
        cursor.execute("SELECT id FROM admin WHERE email = %s", (email,))
        admin = cursor.fetchone()
        
        if not admin:
            return jsonify({"message": "Si cet email existe, un lien de réinitialisation a été envoyé"}), 200
        
        token = secrets.token_urlsafe(32)
        expiry = datetime.now() + timedelta(hours=24)
        
        try:
            cursor.execute(
                "UPDATE admin SET reset_token = %s, reset_token_expiry = %s WHERE email = %s",
                (token, expiry, email)
            )
            connection.commit()
        except Exception as e:
            print(f"⚠️ Impossible de sauvegarder le token: {e}")
        
        print(f"🔐 Lien de réinitialisation pour {email}: /admin/reset-password/{token}")
        return jsonify({"message": "Si cet email existe, un lien de réinitialisation a été envoyé"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        connection.close()

@app.route("/student/login")
def student_login():
    return render_template("login.html")

# -------------------------------------------------------------------
# ENREGISTREMENT DES BLUEPRINTS
# -------------------------------------------------------------------

app.register_blueprint(student_bp)
app.register_blueprint(face_bp)
app.register_blueprint(recognition_bp)
app.register_blueprint(report_bp)

# -------------------------------------------------------------------
# GESTION DES ERREURS
# -------------------------------------------------------------------

@app.errorhandler(404)
def page_not_found(error):
    return render_template("404.html"), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template("500.html"), 500

# -------------------------------------------------------------------
# POINT D'ENTRÉE
# -------------------------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
=======
from flask import Flask, jsonify  # Flask pour créer l'API, jsonify pour retourner du JSON
from database.db import get_connection

# création de l'application Flask
app = Flask(__name__)  # __name__ permet à Flask de svoir où se trouve le pt d'entrée de l'app

from routes.student_routes import student_bp
app.register_blueprint(student_bp)

from routes.face_routes import face_bp
app.register_blueprint(face_bp)

# Route et test principal
@app.route("/")

def home():
    return jsonify({
        "message": "API Flask operationnelle",
        "status": "OK"
    })

@app.route("/test-db")

def test_db():
    connection = get_connection()
    if connection:
        connection.close()
        return jsonify({"status": "Connexion MySQL OK"})
    else:
        return jsonify({"status": "Erreur connexion"})
    

# Lancement du serveur
if __name__ == "__main__":

    # debug=True permet :
    # recharger automatiquement en cas de modification
    # afficher les erreurs détaillées
    app.run(debug=True)
>>>>>>> 588a313535814a9ddfc347cdb31606df74e1aa90
