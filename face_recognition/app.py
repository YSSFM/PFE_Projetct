from flask import Flask, jsonify  # Flask pour créer l'API, jsonify pour retourner du JSON
from database.db import get_connection

# création de l'application Flask
app = Flask(__name__)  # __name__ permet à Flask de svoir où se trouve le pt d'entrée de l'app

from routes.student_routes import student_bp
app.register_blueprint(student_bp)

from routes.face_routes import face_bp
app.register_blueprint(face_bp)

# Route et test principal
@app.route("/")

def home():
    return jsonify({
        "message": "API Flask opérationnelle",
        "status": "OK"
    })

@app.route("/test-db")

def test_db():
    connection = get_connection()
    if connection:
        connection.close()
        return jsonify({"status": "Connexion MySQL OK"})
    else:
        return jsonify({"status": "Erreur connexion"})
    

# Lancement du serveur
if __name__ == "__main__":

    # debug=True permet :
    # recharger automatiquement en cas de modification
    # afficher les erreurs détaillées
    app.run(debug=True)
