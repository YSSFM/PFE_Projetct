# routes/auth_routes.py
from flask import Blueprint, render_template, request, redirect, url_for, session
from database import DatabaseContext

auth_bp = Blueprint('auth', __name__)
login_attempts = {} # Suivi local des tentatives de connexion pour bloquer le bruteforce

@auth_bp.route('/')
def login_page():
    return render_template('authentification.html')

@auth_bp.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')

    with DatabaseContext() as (cursor, conn):
        cursor.execute("SELECT PASSWORD FROM users WHERE USERNAME = %s", (username,))
        result = cursor.fetchone()

        if result and result[0] == password:
            session['user'] = username
            login_attempts[username] = 0 # Réinitialisation du compteur en cas de succès
            return redirect(url_for('student.accueil'))
        else:
            # Gestion basique des échecs répétés pour déclencher l'affichage du mot de passe oublié
            attempts = login_attempts.get(username, 0) + 1
            login_attempts[username] = attempts
            show_reset = attempts >= 2
            return render_template('authentification.html', error=True, show_reset=show_reset, username=username)

@auth_bp.route('/creer_compte', methods=['POST'])
def creer_compte():
    username = request.form.get('new_username')
    password = request.form.get('new_password')

    with DatabaseContext() as (cursor, conn):
        try:
            cursor.execute("INSERT INTO users (USERNAME, PASSWORD) VALUES (%s, %s)", (username, password))
            return render_template('authentification.html', account_created=True)
        except Exception:
            return render_template('authentification.html', error_create=True)

@auth_bp.route('/recuperer_password', methods=['POST'])
def recuperer_password():
    username = request.form.get('reset_username')
    with DatabaseContext() as (cursor, conn):
        cursor.execute("SELECT PASSWORD FROM users WHERE USERNAME = %s", (username,))
        result = cursor.fetchone()
        
        if result:
            return render_template('authentification.html', recovered_password=result[0], recovered_user=username)
        else:
            return render_template('authentification.html', error_reset=True)

@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login_page'))