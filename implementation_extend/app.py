# ===================================================================
# app.py - APPLICATION FLASK (VERSION CORRIGÉE SAFE)
# ===================================================================

from flask import Flask, render_template, request, redirect, session, jsonify, url_for
from routes.train_routes import train_bp
from datetime import timedelta
import hashlib
import re
import secrets
import logging

# ===================================================================
# LOGGING
# ===================================================================

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ===================================================================
# BLUEPRINTS (NE PAS MODIFIER)
# ===================================================================

from routes.student_routes import student_bp
from routes.face_routes import face_bp
from routes.recognition_routes import recognition_bp
from routes.report_routes import report_bp
from routes.attendance_routes import attendance_bp

# ===================================================================
# DB
# ===================================================================

from db.database import get_connection, execute_query, init_connection_pool


# ===================================================================
# APP
# ===================================================================

app = Flask(__name__)

# ✔ sécurité améliorée (fallback si env)
app.secret_key = secrets.token_hex(32)

# session timeout
app.permanent_session_lifetime = timedelta(hours=1)


# ===================================================================
# UTILITAIRES
# ===================================================================

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password, hashed):
    return hash_password(password) == hashed


def validate_email(email):
    return re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email)


def validate_password_strength(password):
    if len(password) < 8:
        return False, "8 caractères minimum"
    if not re.search(r'[A-Z]', password):
        return False, "1 majuscule requise"
    if not re.search(r'[a-z]', password):
        return False, "1 minuscule requise"
    if not re.search(r'[0-9]', password):
        return False, "1 chiffre requis"
    return True, "OK"


# ===================================================================
# UI ROUTES (INCHANGÉES - IMPORTANT)
# ===================================================================

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/admin")
def admin():
    return render_template("admin_login.html")


@app.route("/admin/register")
def admin_register_page():
    return render_template("admin_register.html")


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


@app.route("/student/login")
def student_login():
    return render_template("login.html")


# ===================================================================
# LOGIN ADMIN (SAFE VERSION)
# ===================================================================

@app.route("/admin/login", methods=["POST"])
def admin_login_api():

    data = request.get_json()
    if not data:
        return jsonify({"error": "Données invalides"}), 400

    username_or_email = data.get("username", "").strip()
    password = data.get("password", "")

    if not username_or_email or not password:
        return jsonify({"error": "Champs requis"}), 400

    conn = get_connection()
    if not conn:
        return jsonify({"error": "Erreur DB"}), 500

    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT * FROM admin 
            WHERE username=%s OR email=%s
        """, (username_or_email, username_or_email))

        admin = cursor.fetchone()

        if not admin:
            return jsonify({"error": "Identifiants incorrects"}), 401

        if not verify_password(password, admin["password_hash"]):
            return jsonify({"error": "Identifiants incorrects"}), 401

        # session sécurisée
        session.clear()
        session.permanent = True
        session["admin"] = True
        session["admin_id"] = admin["id"]
        session["admin_username"] = admin["username"]

        logger.info(f"Admin login: {admin['username']}")

        return jsonify({
            "message": "Connexion réussie",
            "admin": {
                "id": admin["id"],
                "username": admin["username"]
            }
        })

    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({"error": "Erreur serveur"}), 500

    finally:
        cursor.close()
        conn.close()


# ===================================================================
# INSCRIPTION ADMIN (SAFE)
# ===================================================================

@app.route("/admin/register", methods=["POST"])
def admin_register_api():

    data = request.get_json()

    nom = data.get("nom", "").strip()
    prenom = data.get("prenom", "").strip()
    email = data.get("email", "").strip()
    username = data.get("username", "").strip()
    password = data.get("password", "")

    if not all([nom, prenom, email, username, password]):
        return jsonify({"error": "Champs requis"}), 400

    if not validate_email(email):
        return jsonify({"error": "Email invalide"}), 400

    ok, msg = validate_password_strength(password)
    if not ok:
        return jsonify({"error": msg}), 400

    conn = get_connection()
    if not conn:
        return jsonify({"error": "Erreur DB"}), 500

    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT id FROM admin 
            WHERE email=%s OR username=%s
        """, (email, username))

        if cursor.fetchone():
            return jsonify({"error": "Admin existe déjà"}), 400

        cursor.execute("""
            INSERT INTO admin (nom, prenom, email, username, password_hash)
            VALUES (%s,%s,%s,%s,%s)
        """, (nom, prenom, email, username, hash_password(password)))

        conn.commit()

        logger.info(f"Admin created: {username}")

        return jsonify({"message": "Admin créé"}), 201

    except Exception as e:
        conn.rollback()
        logger.error(f"Register error: {e}")
        return jsonify({"error": "Erreur serveur"}), 500

    finally:
        cursor.close()
        conn.close()


# ===================================================================
# LOGOUT
# ===================================================================

@app.route("/admin/logout")
def admin_logout():
    session.clear()
    return redirect(url_for("home"))


# ===================================================================
# PROFILE API (UNCHANGED LOGIC)
# ===================================================================

@app.route("/admin/api/profile", methods=["GET"])
def admin_get_profile():
    if "admin" not in session:
        return jsonify({"error": "Non authentifié"}), 401

    data = execute_query(
        "SELECT id, nom, prenom, email, username FROM admin WHERE id=%s",
        (session["admin_id"],),
        fetch_one=True
    )

    return jsonify(data or {})


@app.route("/admin/api/profile", methods=["PUT"])
def admin_update_profile():
    if "admin" not in session:
        return jsonify({"error": "Non authentifié"}), 401

    data = request.get_json()

    execute_query("""
        UPDATE admin 
        SET nom=%s, prenom=%s, email=%s, username=%s 
        WHERE id=%s
    """, (
        data.get("nom"),
        data.get("prenom"),
        data.get("email"),
        data.get("username"),
        session["admin_id"]
    ))

    return jsonify({"message": "Profil mis à jour"})


# ===================================================================
# FORGOT PASSWORD (SAFE)
# ===================================================================

@app.route("/admin/forgot-password", methods=["POST"])
def admin_forgot_password():

    data = request.get_json()
    email = data.get("email", "").strip()

    if not email:
        return jsonify({"error": "Email requis"}), 400

    token = secrets.token_urlsafe(32)

    execute_query("""
        UPDATE admin SET reset_token=%s WHERE email=%s
    """, (token, email))

    return jsonify({"message": "Email envoyé"})


# ===================================================================
# BLUEPRINTS (STRICTLY KEEP)
# ===================================================================

app.register_blueprint(student_bp)
app.register_blueprint(face_bp)
app.register_blueprint(recognition_bp)
app.register_blueprint(report_bp)
app.register_blueprint(attendance_bp)
app.register_blueprint(train_bp)


# ===================================================================
# ERRORS
# ===================================================================

@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404


@app.errorhandler(500)
def server_error(e):
    logger.error(f"Server error: {e}")
    return render_template("500.html"), 500


# ===================================================================
# START
# ===================================================================

if __name__ == "__main__":
    init_connection_pool()
    app.run(debug=True, host="0.0.0.0", port=5000)