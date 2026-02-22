import mysql.connector
from mysql.connector import Error

# fonction de connexion à la base : elle crée et retourne une connexion à la base
def get_connection():
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="face_recognition"
        )

        if connection.is_connected():
            print("Connexion MySQL réussie !")
        return connection
    except Error as e:
        print("Erreur de connexion MySQL : ", e)
        return None
