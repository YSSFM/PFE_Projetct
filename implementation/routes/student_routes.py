from flask import Blueprint, request, jsonify
import face_recognition
import numpy as np
from database.db import get_connection

# Création d'un Blueprint
# Blueprint permet de séparer les routes
# pour garder une architecture propre
student_bp = Blueprint("students", __name__)

# Ajouter un étudiant

@student_bp.route("/students", methods=["POST"])
def add_student():
    """
    Ajoute un nouvel étudiant dans la base de données.
    """

    data = request.json  # Récupération des données envoyées en JSON

    try:
        connection = get_connection()
        cursor = connection.cursor()

        # Requête d'insertion
        query = """
        INSERT INTO etudiant 
        (departement_id, nom, prenom, matricule, sexe, telephone, annee_academique, semestre)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """

        values = (
            data["departement_id"],
            data["nom"],
            data["prenom"],
            data["matricule"],
            data["sexe"],
            data.get("telephone"),
            data.get("annee_academique"),
            data.get("semestre")
        )

        cursor.execute(query, values)
        connection.commit()

        return jsonify({"message": "Étudiant ajouté avec succès"})

    except Exception as e:
        return jsonify({"error": str(e)})

    finally:
        cursor.close()
        connection.close()

# Lister tous les étudiants

@student_bp.route("/students", methods=["GET"])
def get_students():
    """
    Retourne la liste de tous les étudiants.
    """

    try:
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("SELECT * FROM etudiant")
        students = cursor.fetchall()

        return jsonify(students)

    except Exception as e:
        return jsonify({"error": str(e)})

    finally:
        cursor.close()
        connection.close()

# Supprimer un étudiant

@student_bp.route("/students/<int:id>", methods=["DELETE"])
def delete_student(id):
    """
    Supprime un étudiant par son ID.
    """

    try:
        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("DELETE FROM etudiant WHERE id = %s", (id,))
        connection.commit()

        return jsonify({"message": "Étudiant supprimé"})

    except Exception as e:
        return jsonify({"error": str(e)})

    finally:
        cursor.close()
        connection.close()
