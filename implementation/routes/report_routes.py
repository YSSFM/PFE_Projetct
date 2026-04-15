# Import Blueprint
from flask import Blueprint, jsonify, send_file

# Import service
from services.report_service import generate_pdf, get_absents


# Création blueprint
report_bp = Blueprint("report", __name__)


# Générer rapport PDF
@report_bp.route("/report", methods=["GET"])
def report():

    # Générer PDF
    file = generate_pdf()

    # Retourner fichier
    return send_file(
        file,
        as_attachment=True
    )

# Liste absents
@report_bp.route("/absents", methods=["GET"])
def absents():

    # Récupérer absents
    data = get_absents()

    return jsonify(data)