# ============================================================
# db/database.py
# ============================================================

import os
import pickle
import logging
import mysql.connector

from mysql.connector import pooling
from dotenv import load_dotenv

# ============================================================
# CONFIG
# ============================================================

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================
# VARIABLES
# ============================================================

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", 3306)),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "face_recognition")
}

connection_pool = None

# ============================================================
# INITIALISATION POOL
# ============================================================

def init_connection_pool():
    """
    Initialise le pool de connexions MySQL
    """

    global connection_pool

    try:
        connection_pool = pooling.MySQLConnectionPool(
            pool_name="face_pool",
            pool_size=10,
            pool_reset_session=True,
            **DB_CONFIG
        )

        logger.info("Pool MySQL initialisé")

    except Exception as e:
        logger.error(f"Erreur pool MySQL : {e}")
        raise


# ============================================================
# GET CONNECTION
# ============================================================

def get_connection():
    """
    Retourne une connexion MySQL
    """

    global connection_pool

    try:

        if connection_pool is None:
            init_connection_pool()

        return connection_pool.get_connection()

    except Exception as e:
        logger.error(f"Erreur connexion DB : {e}")
        raise


# ============================================================
# CLOSE CONNECTION
# ============================================================

def close_connection(connection):
    """
    Ferme proprement une connexion
    """

    try:

        if connection and connection.is_connected():
            connection.close()

    except Exception as e:
        logger.error(f"Erreur fermeture connexion : {e}")


# ============================================================
# EXECUTE QUERY
# ============================================================

def execute_query(
    query,
    params=None,
    fetchone=False,
    fetchall=False,
    commit=False
):
    """
    Exécute une requête SQL
    """

    connection = None
    cursor = None

    try:

        connection = get_connection()

        cursor = connection.cursor(dictionary=True)

        cursor.execute(query, params or ())

        if commit:
            connection.commit()

        if fetchone:
            return cursor.fetchone()

        if fetchall:
            return cursor.fetchall()

        return cursor.lastrowid

    except Exception as e:

        logger.error(f"Erreur SQL : {e}")
        logger.error(f"Query : {query}")

        if connection:
            connection.rollback()

        raise

    finally:

        if cursor:
            cursor.close()

        if connection:
            close_connection(connection)


# ============================================================
# SAVE EMBEDDING
# ============================================================

def save_face_embedding(
    etudiant_id,
    embedding,
    image_path=None,
    quality_score=0.0
):
    """
    Sauvegarde un embedding FaceNet
    """

    try:

        embedding_binary = pickle.dumps(embedding)

        query = """
        INSERT INTO face_embeddings
        (
            etudiant_id,
            embedding_vector,
            image_path,
            quality_score
        )
        VALUES (%s, %s, %s, %s)
        """

        return execute_query(
            query,
            (
                etudiant_id,
                embedding_binary,
                image_path,
                quality_score
            ),
            commit=True
        )

    except Exception as e:
        logger.error(f"Erreur save embedding : {e}")
        raise


# ============================================================
# LOAD EMBEDDINGS
# ============================================================

def load_face_embeddings():
    """
    Charge tous les embeddings actifs
    """

    try:

        query = """
        SELECT
            fe.id,
            fe.etudiant_id,
            fe.embedding_vector,
            e.nom,
            e.prenom,
            e.matricule
        FROM face_embeddings fe
        INNER JOIN etudiant e
            ON fe.etudiant_id = e.id
        WHERE fe.is_active = TRUE
        """

        rows = execute_query(query, fetchall=True)

        embeddings = []

        for row in rows:

            embeddings.append({
                "id": row["id"],
                "etudiant_id": row["etudiant_id"],
                "nom": row["nom"],
                "prenom": row["prenom"],
                "matricule": row["matricule"],
                "embedding": pickle.loads(
                    row["embedding_vector"]
                )
            })

        logger.info(f"{len(embeddings)} embeddings chargés")

        return embeddings

    except Exception as e:
        logger.error(f"Erreur load embeddings : {e}")
        return []


# ============================================================
# TEST DB
# ============================================================

def test_connection():
    """
    Test connexion MySQL
    """

    try:

        connection = get_connection()

        if connection.is_connected():

            logger.info("Connexion MySQL OK")

            close_connection(connection)

            return True

        return False

    except Exception as e:

        logger.error(f"Erreur test connexion : {e}")

        return False