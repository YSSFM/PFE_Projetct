import mysql.connector

# Ce module permet de centraliser la configuration et la distribution des connexions
# à la base de données MySQL pour l'ensemble de notre application Flask.

def get_db_connection():
    # Établit une connexion brute avec le serveur de base de données local
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="reconnaisancefacial"
    )

class DatabaseContext:
    # Ce gestionnaire de contexte automatise l'ouverture et la fermeture propre
    # des curseurs SQL, assurant la libération des ressources même en cas d'erreur.
    def __enter__(self):
        self.conn = get_db_connection()
        self.cursor = self.conn.cursor()
        return self.cursor, self.conn

    def __exit__(self, exc_type, exc_val, exc_tb):
        if hasattr(self, 'cursor') and self.cursor:
            self.cursor.close()
        if hasattr(self, 'conn') and self.conn:
            if exc_type is not None:
                self.conn.rollback()
            self.conn.close()