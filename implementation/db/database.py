# -------------------------------------------------------------------
# IMPORT DES BIBLIOTHÈQUES NÉCESSAIRES
# -------------------------------------------------------------------

# Import du connecteur MySQL pour Python
import mysql.connector

# Import de la classe Error pour gérer les exceptions MySQL
from mysql.connector import Error

# Import pour pool de connexions (optimisation performance)
from mysql.connector import pooling


# -------------------------------------------------------------------
# CONFIGURATION DE LA BASE DE DONNÉES
# -------------------------------------------------------------------

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "face_recognition",
    "port": 3306,
    "charset": "utf8mb4",
    "autocommit": False,
    "pool_name": "face_pool",
    "pool_size": 10
}


# -------------------------------------------------------------------
# POOL DE CONNEXIONS (IMPORTANT POUR PERFORMANCE)
# -------------------------------------------------------------------

connection_pool = None

try:
    # Création du pool de connexions
    connection_pool = pooling.MySQLConnectionPool(
        pool_name="face_pool",
        pool_size=10,
        pool_reset_session=True,
        **{k: v for k, v in DB_CONFIG.items() if k not in ["pool_name", "pool_size"]}
    )
    print("✅ Pool de connexions MySQL initialisé (taille: 10)")
except Error as e:
    print(f"❌ Erreur création pool : {e}")
    connection_pool = None


# -------------------------------------------------------------------
# FONCTION DE CONNEXION À LA BASE DE DONNÉES
# -------------------------------------------------------------------

def get_connection():
    """
    Crée et retourne une connexion à la base de données MySQL
    en utilisant un pool de connexions pour améliorer la performance
    """

    try:
        # Utiliser le pool si disponible
        if connection_pool:
            connection = connection_pool.get_connection()
            if connection.is_connected():
                return connection

        # Fallback si pool échoue
        connection = mysql.connector.connect(**DB_CONFIG)
        if connection.is_connected():
            return connection

        return None

    except Error as e:
        print(f"❌ Erreur connexion MySQL : {e}")
        return None


# -------------------------------------------------------------------
# FERMETURE DE CONNEXION
# -------------------------------------------------------------------

def close_connection(connection):
    """
    Ferme proprement une connexion et la retourne au pool
    """

    try:
        if connection and connection.is_connected():
            connection.close()  # Avec pool, cela retourne la connexion au pool
    except Exception:
        pass


# -------------------------------------------------------------------
# CONTEXTE AUTOMATIQUE DATABASE
# -------------------------------------------------------------------

class DatabaseContext:
    """
    Gestionnaire de contexte pour opérations DB
    Utilisation : with DatabaseContext() as (conn, cursor):
    """

    def __enter__(self):
        self.connection = get_connection()
        if self.connection:
            self.cursor = self.connection.cursor(dictionary=True)
        else:
            self.cursor = None
        return self.connection, self.cursor

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            if self.cursor:
                self.cursor.close()
        except:
            pass

        try:
            if self.connection:
                self.connection.close()
        except:
            pass

        return False


# -------------------------------------------------------------------
# FONCTION POUR OBTENIR UN CURSEUR DICTIONNAIRE
# -------------------------------------------------------------------

def get_dict_cursor(connection):
    """
    Retourne un curseur qui retourne les résultats sous forme de dictionnaire
    """
    if connection is None:
        return None
    return connection.cursor(dictionary=True)


# -------------------------------------------------------------------
# TEST DE CONNEXION
# -------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 50)
    print("🧪 TEST DE CONNEXION À LA BASE DE DONNÉES")
    print("=" * 50)

    conn = get_connection()
    if conn:
        print("✅ Connexion OK")
        close_connection(conn)
    else:
        print("❌ Connexion échouée")