# IMPORT DES BIBLIOTHÈQUES NÉCESSAIRES

# Import de la fonction de connexion à la base de données
from db.database import get_connection

# Import des modules datetime pour les dates et heures
from datetime import datetime, date, time

# Import du module time pour les temporisations
import time


# FONCTION POUR MARQUER LA PRÉSENCE D'UN ÉTUDIANT
def mark_attendance(student_id):
    """
    Cette fonction marque la présence d'un étudiant dans la base de données.
    Elle vérifie d'abord si l'étudiant n'est pas déjà marqué présent aujourd'hui.
    
    Paramètres:
        student_id (int): L'identifiant de l'étudiant
    
    Retourne:
        bool: True si la présence a été marquée, False si déjà présent
    """
    
    # Connexion à la base de données MySQL
    connection = get_connection()
    
    # Vérification que la connexion a réussi
    if connection is None:
        # Affichage d'une erreur dans la console
        print(f"Erreur de connexion DB pour marquer présence étudiant {student_id}")
        # Retour False car la présence n'a pas pu être marquée
        return False
    
    # Création d'un curseur avec dictionnaire pour récupérer les résultats nommés
    # dictionary=True permet d'accéder aux colonnes par leur nom: row["colonne"]
    cursor = connection.cursor(dictionary=True)
    
    # Récupération de la date actuelle (sans l'heure)
    # Exemple: 2024-01-15
    today = date.today()
    
    # Récupération de l'heure actuelle (avec les minutes et secondes)
    # Exemple: 14:30:25
    now = datetime.now()
    
    # Détermination de la session (Matin ou Après-midi)
    # Si l'heure est avant 12h00, c'est le matin
    if now.hour < 12:
        session = "Matin"
    else:
        # Sinon, c'est l'après-midi
        session = "Après-midi"
    
    # Vérification si l'étudiant a déjà été marqué présent aujourd'hui
    # Cette requête SQL sélectionne toutes les présences de l'étudiant pour la date du jour
    cursor.execute(
        """
        SELECT * FROM presence
        WHERE etudiant_id = %s AND date = %s
        """,
        (student_id, today)
    )
    
    # Récupération du premier résultat (None si aucun)
    existing = cursor.fetchone()
    
    # Si un enregistrement existe déjà pour cet étudiant aujourd'hui
    if existing:
        # Affichage d'un message dans la console
        print(f"Étudiant ID {student_id} déjà présent aujourd'hui ({today})")
        
        # Fermeture du curseur
        cursor.close()
        # Fermeture de la connexion
        connection.close()
        
        # Retour False car la présence n'a pas été marquée (déjà présent)
        return False
    
    # Si l'étudiant n'est pas encore marqué présent aujourd'hui
    # Insertion d'un nouvel enregistrement dans la table presence
    
    try:
        # Exécution de la requête d'insertion
        cursor.execute(
            """
            INSERT INTO presence
            (etudiant_id, date, heure, session, statut)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                student_id,      # ID de l'étudiant
                today,           # Date du jour (YYYY-MM-DD)
                now.time(),      # Heure actuelle (HH:MM:SS)
                session,         # "Matin" ou "Après-midi"
                "Présent"        # Statut par défaut
            )
        )
        
        # Validation de l'insertion dans la base de données
        # Sans commit(), les modifications ne sont pas sauvegardées
        connection.commit()
        
        # Affichage d'un message de succès dans la console
        print(f"Présence marquée pour étudiant ID {student_id} à {now.time()} ({session})")
        
        # Retour True car la présence a été marquée avec succès
        return True
        
    except Exception as e:
        # En cas d'erreur SQL (ex: contrainte violée, colonne manquante)
        # Annulation des modifications (rollback)
        connection.rollback()
        
        # Affichage de l'erreur dans la console
        print(f"Erreur lors du marquage de présence: {e}")
        
        # Retour False car l'insertion a échoué
        return False
        
    finally:
        # Ce bloc s'exécute toujours, qu'il y ait erreur ou non
        # Fermeture du curseur pour libérer les ressources
        cursor.close()
        # Fermeture de la connexion
        connection.close()


# FONCTION POUR MARQUER LES ÉTUDIANTS ABSENTS
def mark_absents():
    """
    Cette fonction marque comme absents tous les étudiants qui n'ont pas
    encore été marqués présents aujourd'hui.
    Elle est généralement appelée à la fin de la journée.
    """
    
    # Connexion à la base de données
    connection = get_connection()
    
    # Vérification que la connexion a réussi
    if connection is None:
        print("Erreur de connexion DB pour marquer les absents")
        return
    
    # Création d'un curseur avec dictionnaire
    cursor = connection.cursor(dictionary=True)
    
    # Date du jour
    today = date.today()
    
    # Heure actuelle
    now = datetime.now()
    
    # Récupération de la liste de tous les étudiants
    cursor.execute("SELECT id FROM etudiant")
    students = cursor.fetchall()
    
    # Compteur pour le nombre d'absents marqués
    absents_count = 0
    
    # Parcours de chaque étudiant
    for student in students:
        
        # Vérification si l'étudiant a déjà une présence aujourd'hui
        cursor.execute(
            """
            SELECT * FROM presence
            WHERE etudiant_id = %s AND date = %s
            """,
            (student["id"], today)
        )
        
        # Récupération du résultat
        existing = cursor.fetchone()
        
        # Si l'étudiant n'a pas de présence aujourd'hui
        if not existing:
            
            try:
                # Insertion d'un enregistrement "Absent"
                cursor.execute(
                    """
                    INSERT INTO presence
                    (etudiant_id, date, heure, session, statut)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        student["id"],   # ID de l'étudiant
                        today,           # Date du jour
                        now.time(),      # Heure actuelle
                        "N/A",           # Session non applicable pour les absents
                        "Absent"         # Statut "Absent"
                    )
                )
                
                # Incrémentation du compteur
                absents_count += 1
                
            except Exception as e:
                # Affichage de l'erreur si l'insertion échoue
                print(f"Erreur pour étudiant {student['id']}: {e}")
    
    # Validation de toutes les insertions
    connection.commit()
    
    # Affichage du résumé
    print(f"{absents_count} étudiants marqués absents aujourd'hui ({today})")
    
    # Fermeture des ressources
    cursor.close()
    connection.close()


# FONCTION POUR RÉCUPÉRER LES PRÉSENCES D'UN ÉTUDIANT
def get_student_attendance(student_id, start_date=None, end_date=None):
    """
    Récupère l'historique des présences d'un étudiant sur une période.
    
    Paramètres:
        student_id (int): ID de l'étudiant
        start_date (date, optionnel): Date de début
        end_date (date, optionnel): Date de fin
    
    Retourne:
        list: Liste des enregistrements de présence
    """
    
    # Connexion à la base de données
    connection = get_connection()
    
    if connection is None:
        return []
    
    cursor = connection.cursor(dictionary=True)
    
    # Construction de la requête SQL avec filtres optionnels
    query = """
        SELECT * FROM presence
        WHERE etudiant_id = %s
    """
    params = [student_id]
    
    # Ajout du filtre date de début si fourni
    if start_date:
        query += " AND date >= %s"
        params.append(start_date)
    
    # Ajout du filtre date de fin si fourni
    if end_date:
        query += " AND date <= %s"
        params.append(end_date)
    
    # Tri par date décroissante (les plus récentes d'abord)
    query += " ORDER BY date DESC, heure DESC"
    
    # Exécution de la requête
    cursor.execute(query, tuple(params))
    
    # Récupération des résultats
    attendances = cursor.fetchall()
    
    # Fermeture des ressources
    cursor.close()
    connection.close()
    
    return attendances


# FONCTION POUR CALCULER LE TAUX DE PRÉSENCE
def get_attendance_rate(student_id, start_date=None, end_date=None):
    """
    Calcule le taux de présence d'un étudiant sur une période.
    
    Paramètres:
        student_id (int): ID de l'étudiant
        start_date (date, optionnel): Date de début
        end_date (date, optionnel): Date de fin
    
    Retourne:
        float: Taux de présence en pourcentage (0-100)
    """
    
    # Récupération des présences
    attendances = get_student_attendance(student_id, start_date, end_date)
    
    # Comptage des présents
    present_count = sum(1 for a in attendances if a["statut"] == "Présent")
    
    # Calcul du taux
    if len(attendances) > 0:
        rate = (present_count / len(attendances)) * 100
    else:
        rate = 0
    
    return round(rate, 2)