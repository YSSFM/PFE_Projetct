# database.py
import mysql.connector

def get_db_connection():
    """
    Établit une connexion brute avec le serveur de base de données local MySQL.
    Configure le dictionnaire pour lever des exceptions explicites en cas d'erreur de syntaxe.
    """
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="reconnaisancefacial"
    )

class DatabaseContext:
    """
    Gestionnaire de contexte (Context Manager) pour automatiser l'ouverture,
    le commit automatique en fin de script valide, et la fermeture des curseurs SQL.
    Évite les fuites de connexions en fermant proprement les ressources, même si une erreur survient.
    """
    def __enter__(self):
        self.conn = get_db_connection()
        self.cursor = self.conn.cursor()
        return self.cursor, self.conn

    def __exit__(self, exc_type, exc_val, exc_tb):
        if hasattr(self, 'cursor') and self.cursor:
            self.cursor.close()
        if hasattr(self, 'conn') and self.conn:
            # S'il y a eu une exception, on annule la transaction courante (rollback)
            if exc_type is not None:
                self.conn.rollback()
            else:
                self.conn.commit()
            self.conn.close()