# ===================================================================
# report_service.py - SERVICE DE GÉNÉRATION DE RAPPORTS
# VERSION ALIGNÉE ARCHITECTURE (CLEAN)
# ===================================================================

from db.database import get_connection
from datetime import date, datetime, timedelta
import tempfile
import os
import csv

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

# =========================================================
# PDF FONT (SAFE)
# =========================================================
try:
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    font_paths = [
        "C:/Windows/Fonts/arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    ]

    for path in font_paths:
        if os.path.exists(path):
            pdfmetrics.registerFont(TTFont("CustomFont", path))
            break
except:
    pass


# =========================================================
# PDF GLOBAL REPORT
# =========================================================
def generate_pdf(start_date=None, end_date=None):

    conn = get_connection()
    if not conn:
        return None

    cursor = conn.cursor(dictionary=True)

    if not end_date:
        end_date = date.today()

    if not start_date:
        start_date = date(end_date.year, end_date.month, 1)

    query = """
        SELECT 
            e.nom, e.prenom, e.matricule,
            d.nom AS departement,
            p.presence_date,
            p.presence_time,
            p.session,
            p.statut
        FROM presence p
        JOIN etudiant e ON e.id = p.etudiant_id
        JOIN departement d ON d.id = e.departement_id
        WHERE p.presence_date BETWEEN %s AND %s
        ORDER BY p.presence_date DESC
    """

    cursor.execute(query, (start_date, end_date))
    data = cursor.fetchall()

    # stats étudiants
    cursor.execute("SELECT COUNT(*) AS total FROM etudiant WHERE is_active = TRUE")
    total_students = cursor.fetchone()["total"]

    cursor.close()
    conn.close()

    # PDF file
    file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    path = file.name
    file.close()

    doc = SimpleDocTemplate(path, pagesize=A4)
    styles = getSampleStyleSheet()

    title = Paragraph("RAPPORT DE PRÉSENCE", styles["Heading1"])

    elements = []
    elements.append(title)
    elements.append(Spacer(1, 10))

    # stats simples
    present = len([d for d in data if d["statut"] == "Present"])
    absent = len([d for d in data if d["statut"] == "Absent"])

    stats = Table([
        ["Total étudiants", total_students],
        ["Présents", present],
        ["Absents", absent],
    ])

    stats.setStyle(TableStyle([
        ("GRID", (0,0), (-1,-1), 0.5, colors.black)
    ]))

    elements.append(stats)
    elements.append(Spacer(1, 10))

    # table détaillée
    table_data = [["Nom", "Prénom", "Matricule", "Date", "Session", "Statut"]]

    for row in data:
        table_data.append([
            row["nom"],
            row["prenom"],
            row["matricule"],
            row["presence_date"].strftime("%d/%m/%Y"),
            row["session"],
            row["statut"]
        ])

    table = Table(table_data)
    table.setStyle(TableStyle([
        ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
        ("BACKGROUND", (0,0), (-1,0), colors.blue),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
    ]))

    elements.append(table)

    doc.build(elements)

    return path


# =========================================================
# ABSENTS (VERSION CLEAN -> utilise logique DB directe)
# =========================================================
def get_absents(target_date=None):

    conn = get_connection()
    if not conn:
        return []

    cursor = conn.cursor(dictionary=True)

    if not target_date:
        target_date = date.today()

    query = """
        SELECT e.id, e.nom, e.prenom, e.matricule, d.nom AS departement
        FROM etudiant e
        JOIN departement d ON d.id = e.departement_id
        WHERE e.is_active = TRUE
        AND e.id NOT IN (
            SELECT etudiant_id
            FROM presence
            WHERE presence_date = %s
              AND statut = 'Present'
        )
    """

    cursor.execute(query, (target_date,))
    result = cursor.fetchall()

    cursor.close()
    conn.close()

    return result


# =========================================================
# RAPPORT ÉTUDIANT
# =========================================================
def generate_student_report(student_id, start_date=None, end_date=None):

    conn = get_connection()
    if not conn:
        return None

    cursor = conn.cursor(dictionary=True)

    if not end_date:
        end_date = date.today()

    if not start_date:
        start_date = end_date - timedelta(days=30)

    cursor.execute("""
        SELECT e.*, d.nom AS departement
        FROM etudiant e
        JOIN departement d ON d.id = e.departement_id
        WHERE e.id = %s
    """, (student_id,))

    student = cursor.fetchone()
    if not student:
        return None

    cursor.execute("""
        SELECT presence_date, presence_time, session, statut
        FROM presence
        WHERE etudiant_id = %s
        AND presence_date BETWEEN %s AND %s
    """, (student_id, start_date, end_date))

    attendances = cursor.fetchall()

    cursor.close()
    conn.close()

    file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    path = file.name
    file.close()

    doc = SimpleDocTemplate(path, pagesize=A4)
    styles = getSampleStyleSheet()

    elements = []
    elements.append(Paragraph(f"Rapport - {student['nom']} {student['prenom']}", styles["Heading1"]))
    elements.append(Spacer(1, 10))

    table_data = [["Date", "Session", "Statut"]]

    for a in attendances:
        table_data.append([
            a["presence_date"].strftime("%d/%m/%Y"),
            a["session"],
            a["statut"]
        ])

    table = Table(table_data)
    table.setStyle(TableStyle([
        ("GRID", (0,0), (-1,-1), 0.5, colors.black),
        ("BACKGROUND", (0,0), (-1,0), colors.grey)
    ]))

    elements.append(table)
    doc.build(elements)

    return path


# =========================================================
# EXPORT CSV
# =========================================================
def export_to_csv(start_date=None, end_date=None):

    conn = get_connection()
    if not conn:
        return None

    cursor = conn.cursor(dictionary=True)

    if not end_date:
        end_date = date.today()

    if not start_date:
        start_date = date(end_date.year, end_date.month, 1)

    cursor.execute("""
        SELECT e.matricule, e.nom, e.prenom,
               p.presence_date, p.presence_time,
               p.session, p.statut
        FROM presence p
        JOIN etudiant e ON e.id = p.etudiant_id
        WHERE p.presence_date BETWEEN %s AND %s
    """, (start_date, end_date))

    data = cursor.fetchall()

    cursor.close()
    conn.close()

    file = tempfile.NamedTemporaryFile(delete=False, suffix=".csv")
    path = file.name
    file.close()

    if data:
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)

    return path