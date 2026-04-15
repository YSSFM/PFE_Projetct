# IMPORT DES BIBLIOTHÈQUES NÉCESSAIRES

# Import de Blueprint pour créer un groupe de routes Flask
from flask import Blueprint, request, jsonify, render_template, redirect, url_for, session

# Import de la fonction de connexion à la base de données
from db.database import get_connection

# Import de MySQL pour les erreurs
from mysql.connector import Error


# CRÉATION DU BLUEPRINT
# Création du Blueprint pour les routes étudiantes
student_bp = Blueprint("student", __name__)

# PAGE HTML DE GESTION DES ÉTUDIANTS
@student_bp.route("/students")
def students_page():
    """
    Affiche la page HTML de gestion des étudiants.
    Cette page permet d'ajouter, modifier, supprimer et lister les étudiants.
    """
    
    # Vérification de l'authentification admin
    if "admin" not in session:
        return redirect(url_for("admin"))
    
    # Rendu de la page HTML de gestion des étudiants
    return render_template("students.html")


# ROUTE POUR RÉCUPÉRER TOUS LES ÉTUDIANTS 
@student_bp.route("/api/students", methods=["GET"])
def api_get_students():
    """
    API REST : Récupère la liste de tous les étudiants au format JSON.
    Utilisée par le frontend JavaScript pour afficher les étudiants.
    """
    
    # Connexion à la base de données
    connection = get_connection()
    
    # Vérification de la connexion
    if connection is None:
        return jsonify({"error": "Erreur de connexion à la base de données"}), 500
    
    # Création d'un curseur avec dictionnaire
    cursor = connection.cursor(dictionary=True)
    
    try:
        # Requête pour récupérer les étudiants avec le nom du département
        cursor.execute("""
            SELECT e.*, d.nom as departement_nom 
            FROM etudiant e
            LEFT JOIN departement d ON d.id = e.departement_id
            ORDER BY e.id DESC
        """)
        
        # Récupération de tous les résultats
        students = cursor.fetchall()
        
        # Conversion des données pour l'affichage
        for student in students:
            # Conversion du BLOB en booléen pour savoir si un visage est enregistré
            student["has_face"] = student["face_embedding"] is not None
            # Suppression des données binaires de la réponse JSON
            student["face_embedding"] = None
        
        # Retour de la liste en JSON
        return jsonify(students)
        
    except Error as e:
        # En cas d'erreur SQL
        return jsonify({"error": str(e)}), 500
        
    finally:
        # Fermeture des ressources
        cursor.close()
        connection.close()


# ROUTE POUR AJOUTER UN ÉTUDIANT 
@student_bp.route("/api/students", methods=["POST"])
def api_add_student():
    """
    API REST : Ajoute un nouvel étudiant dans la base de données.
    Attend les données JSON : nom, prenom, matricule, departement_id, sexe
    """
    
    # Récupération des données JSON envoyées par le frontend
    data = request.json
    
    # Extraction des champs obligatoires
    nom = data.get("nom", "").strip()
    prenom = data.get("prenom", "").strip()
    matricule = data.get("matricule", "").strip()
    departement_id = data.get("departement_id")
    sexe = data.get("sexe", "M")  # 'M' ou 'F'
    telephone = data.get("telephone", "")
    annee_academique = data.get("annee_academique", "")
    semestre = data.get("semestre", "")
    
    # Validation des champs obligatoires
    if not nom:
        return jsonify({"error": "Le nom est obligatoire"}), 400
    if not prenom:
        return jsonify({"error": "Le prénom est obligatoire"}), 400
    if not matricule:
        return jsonify({"error": "Le matricule est obligatoire"}), 400
    if not departement_id:
        return jsonify({"error": "Le département est obligatoire"}), 400
    
    # Connexion à la base de données
    connection = get_connection()
    
    if connection is None:
        return jsonify({"error": "Erreur de connexion à la base de données"}), 500
    
    cursor = connection.cursor()
    
    try:
        # Insertion du nouvel étudiant
        cursor.execute(
            """
            INSERT INTO etudiant 
            (nom, prenom, matricule, departement_id, sexe, telephone, annee_academique, semestre)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (nom, prenom, matricule, departement_id, sexe, telephone, annee_academique, semestre)
        )
        
        # Validation de l'insertion
        connection.commit()
        
        # Récupération de l'ID du nouvel étudiant
        new_id = cursor.lastrowid
        
        # Retour du succès avec l'ID créé
        return jsonify({
            "message": "Étudiant ajouté avec succès",
            "id": new_id
        }), 201
        
    except Error as e:
        # En cas d'erreur (matricule déjà existant par exemple)
        connection.rollback()
        
        # Vérification si c'est une erreur de duplication
        if "Duplicate entry" in str(e):
            return jsonify({"error": "Ce matricule existe déjà"}), 400
        
        return jsonify({"error": str(e)}), 500
        
    finally:
        cursor.close()
        connection.close()


# ROUTE POUR MODIFIER UN ÉTUDIANT 
@student_bp.route("/api/students/<int:student_id>", methods=["PUT"])
def api_update_student(student_id):
    """
    API REST : Modifie les informations d'un étudiant existant.
    
    Paramètres:
        student_id (int): ID de l'étudiant à modifier
    """
    
    # Récupération des données JSON
    data = request.json
    
    # Extraction des champs
    nom = data.get("nom", "").strip()
    prenom = data.get("prenom", "").strip()
    matricule = data.get("matricule", "").strip()
    departement_id = data.get("departement_id")
    sexe = data.get("sexe", "M")
    telephone = data.get("telephone", "")
    annee_academique = data.get("annee_academique", "")
    semestre = data.get("semestre", "")
    
    # Validation des champs obligatoires
    if not nom:
        return jsonify({"error": "Le nom est obligatoire"}), 400
    if not prenom:
        return jsonify({"error": "Le prénom est obligatoire"}), 400
    if not matricule:
        return jsonify({"error": "Le matricule est obligatoire"}), 400
    
    # Connexion à la base de données
    connection = get_connection()
    
    if connection is None:
        return jsonify({"error": "Erreur de connexion à la base de données"}), 500
    
    cursor = connection.cursor()
    
    try:
        # Mise à jour de l'étudiant
        cursor.execute(
            """
            UPDATE etudiant
            SET nom=%s, prenom=%s, matricule=%s, departement_id=%s, 
                sexe=%s, telephone=%s, annee_academique=%s, semestre=%s
            WHERE id=%s
            """,
            (nom, prenom, matricule, departement_id, sexe, telephone, annee_academique, semestre, student_id)
        )
        
        # Vérification si un enregistrement a été modifié
        if cursor.rowcount == 0:
            return jsonify({"error": "Étudiant non trouvé"}), 404
        
        # Validation de la modification
        connection.commit()
        
        # Retour du succès
        return jsonify({"message": "Étudiant modifié avec succès"})
        
    except Error as e:
        # En cas d'erreur
        connection.rollback()
        
        if "Duplicate entry" in str(e):
            return jsonify({"error": "Ce matricule existe déjà"}), 400
        
        return jsonify({"error": str(e)}), 500
        
    finally:
        cursor.close()
        connection.close()


# ROUTE POUR SUPPRIMER UN ÉTUDIANT 
@student_bp.route("/api/students/<int:student_id>", methods=["DELETE"])
def api_delete_student(student_id):
    """
    API REST : Supprime un étudiant de la base de données.
    La suppression est en cascade : les présences et images sont aussi supprimées.
    
    Paramètres:
        student_id (int): ID de l'étudiant à supprimer
    """
    
    # Connexion à la base de données
    connection = get_connection()
    
    if connection is None:
        return jsonify({"error": "Erreur de connexion à la base de données"}), 500
    
    cursor = connection.cursor()
    
    try:
        # Suppression de l'étudiant (les clés étrangères avec ON DELETE CASCADE s'occupent du reste)
        cursor.execute(
            "DELETE FROM etudiant WHERE id = %s",
            (student_id,)
        )
        
        # Vérification si un enregistrement a été supprimé
        if cursor.rowcount == 0:
            return jsonify({"error": "Étudiant non trouvé"}), 404
        
        # Validation de la suppression
        connection.commit()
        
        # Retour du succès
        return jsonify({"message": "Étudiant supprimé avec succès"})
        
    except Error as e:
        # En cas d'erreur
        connection.rollback()
        return jsonify({"error": str(e)}), 500
        
    finally:
        cursor.close()
        connection.close()


# ROUTE POUR RÉCUPÉRER UN ÉTUDIANT SPÉCIFIQUE 
@student_bp.route("/api/students/<int:student_id>", methods=["GET"])
def api_get_student(student_id):
    """
    API REST : Récupère les informations d'un étudiant spécifique.
    
    Paramètres:
        student_id (int): ID de l'étudiant à récupérer
    """
    
    # Connexion à la base de données
    connection = get_connection()
    
    if connection is None:
        return jsonify({"error": "Erreur de connexion à la base de données"}), 500
    
    cursor = connection.cursor(dictionary=True)
    
    try:
        # Récupération de l'étudiant
        cursor.execute(
            """
            SELECT e.*, d.nom as departement_nom 
            FROM etudiant e
            LEFT JOIN departement d ON d.id = e.departement_id
            WHERE e.id = %s
            """,
            (student_id,)
        )
        
        student = cursor.fetchone()
        
        if not student:
            return jsonify({"error": "Étudiant non trouvé"}), 404
        
        # Suppression des données binaires
        student["has_face"] = student["face_embedding"] is not None
        student["face_embedding"] = None
        
        return jsonify(student)
        
    except Error as e:
        return jsonify({"error": str(e)}), 500
        
    finally:
        cursor.close()
        connection.close()


# ROUTE POUR RÉCUPÉRER LES DÉPARTEMENTS (API JSON)
@student_bp.route("/api/departements", methods=["GET"])
def api_get_departements():
    """
    API REST : Récupère la liste de tous les départements.
    Utilisée pour le formulaire d'ajout/modification d'étudiant.
    """
    
    # Connexion à la base de données
    connection = get_connection()
    
    if connection is None:
        return jsonify({"error": "Erreur de connexion à la base de données"}), 500
    
    cursor = connection.cursor(dictionary=True)
    
    try:
        # Récupération de tous les départements
        cursor.execute("SELECT id, nom FROM departement ORDER BY nom")
        departements = cursor.fetchall()
        
        return jsonify(departements)
        
    except Error as e:
        return jsonify({"error": str(e)}), 500
        
    finally:
        cursor.close()
        connection.close()


# ROUTES POUR LES TEMPLATES HTML (
# Route pour la liste des étudiants 
@student_bp.route("/students/list", methods=["GET"])
def get_students():
    """
    Route de compatibilité : retourne la liste des étudiants en JSON.
    Utilisée par d'anciennes versions du frontend.
    """
    return api_get_students()


# Route pour ajouter un étudiant 
@student_bp.route("/students", methods=["POST"])
def add_student():
    """
    Route de compatibilité : ajoute un étudiant via formulaire.
    Redirige vers la page de gestion après ajout.
    """
    
    # Récupération des données du formulaire
    nom = request.form.get("nom")
    prenom = request.form.get("prenom")
    matricule = request.form.get("matricule")
    departement_id = request.form.get("departement_id")
    
    # Connexion à la base de données
    connection = get_connection()
    cursor = connection.cursor()
    
    try:
        cursor.execute(
            """
            INSERT INTO etudiant 
            (nom, prenom, matricule, departement_id)
            VALUES (%s, %s, %s, %s)
            """,
            (nom, prenom, matricule, departement_id)
        )
        
        connection.commit()
        
        # Redirection vers la page de gestion
        return redirect(url_for("student.students_page"))
        
    except Exception as e:
        print("ERREUR :", e)
        return jsonify({"error": str(e)}), 400
        
    finally:
        cursor.close()
        connection.close()


# Route pour supprimer un étudiant (version URL - gardée pour compatibilité)
@student_bp.route("/students/<int:id>", methods=["DELETE"])
def delete_student(id):
    """
    Route de compatibilité : supprime un étudiant.
    """
    return api_delete_student(id)


# Route pour modifier un étudiant (version URL - gardée pour compatibilité)
@student_bp.route("/students/<int:id>", methods=["PUT"])
def update_student(id):
    """
    Route de compatibilité : modifie un étudiant.
    """
    return api_update_student(id)