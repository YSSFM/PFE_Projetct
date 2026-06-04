# IMPORT DES BIBLIOTHÈQUES NÉCESSAIRES

# Import de la fonction de connexion à la base de données
from db.database import get_connection

# Import de ReportLab pour la génération de PDF
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.units import mm, cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.fonts import addMapping
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Import de datetime pour les dates
from datetime import date, datetime, timedelta

# Import du module os pour les chemins de fichiers
import os

# Import du module tempfile pour les fichiers temporaires
import tempfile


# CONFIGURATION DES FONTS POUR LE PDF 
# Tentative d'ajout d'un font supportant l'UTF-8 (pour les accents)
try:
    # Chemin vers une police standard (à adapter selon le système)
    # Sur Windows: "C:/Windows/Fonts/arial.ttf"
    # Sur Linux: "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    font_paths = [
        "C:/Windows/Fonts/arial.ttf",           # Windows
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",  # Linux
        "/System/Library/Fonts/Helvetica.ttc"   # macOS
    ]
    
    font_registered = False
    for font_path in font_paths:
        if os.path.exists(font_path):
            pdfmetrics.registerFont(TTFont('CustomFont', font_path))
            font_registered = True
            break
    
    if not font_registered:
        print("⚠️ Aucune police UTF-8 trouvée, utilisation de Helvetica")
        # Utilisation de la police par défaut
        pass
except Exception as e:
    print(f"Erreur chargement police: {e}")


# FONCTION POUR GÉNÉRER LE RAPPORT PDF
def generate_pdf(start_date=None, end_date=None):
    """
    Génère un rapport PDF détaillé des présences.
    
    Paramètres:
        start_date (date, optionnel): Date de début du rapport
        end_date (date, optionnel): Date de fin du rapport
    
    Retourne:
        str: Chemin vers le fichier PDF généré
    """
    
    # Connexion à la base de données
    connection = get_connection()
    
    # Vérification de la connexion
    if connection is None:
        print("Impossible de générer le PDF: connexion DB échouée")
        return None
    
    # Création d'un curseur avec dictionnaire
    cursor = connection.cursor(dictionary=True)
    
    # Définition des dates par défaut (si non fournies)
    if end_date is None:
        end_date = date.today()
    
    if start_date is None:
        # Par défaut: premier jour du mois en cours
        start_date = date(end_date.year, end_date.month, 1)
    
    # Construction de la requête SQL pour récupérer les présences
    # Cette requête joint les tables presence et etudiant
    query = """
        SELECT 
            e.id as etudiant_id,
            e.nom,
            e.prenom,
            e.matricule,
            d.nom as departement,
            p.date,
            p.heure,
            p.session,
            p.statut
        FROM presence p
        JOIN etudiant e ON e.id = p.etudiant_id
        JOIN departement d ON d.id = e.departement_id
        WHERE p.date BETWEEN %s AND %s
        ORDER BY p.date DESC, e.nom ASC, e.prenom ASC
    """
    
    # Exécution de la requête
    cursor.execute(query, (start_date, end_date))
    
    # Récupération de toutes les lignes
    data = cursor.fetchall()
    
    # Requête pour obtenir le nombre total d'étudiants
    cursor.execute("SELECT COUNT(*) as total FROM etudiant")
    total_students = cursor.fetchone()["total"]
    
    # Requête pour obtenir les statistiques par jour
    stats_query = """
        SELECT 
            p.date,
            COUNT(DISTINCT p.etudiant_id) as presents,
            (SELECT COUNT(*) FROM etudiant) as total_etudiants
        FROM presence p
        WHERE p.date BETWEEN %s AND %s AND p.statut = 'Présent'
        GROUP BY p.date
        ORDER BY p.date DESC
    """
    cursor.execute(stats_query, (start_date, end_date))
    daily_stats = cursor.fetchall()
    
    # Fermeture du curseur et de la connexion
    cursor.close()
    connection.close()
    
    # Création d'un fichier temporaire pour le PDF
    # tempfile crée un fichier unique dans le dossier temporaire du système
    temp_file = tempfile.NamedTemporaryFile(
        suffix=".pdf",  # Extension .pdf
        delete=False,   # Ne pas supprimer automatiquement
        prefix="rapport_presence_"  # Préfixe du nom
    )
    pdf_path = temp_file.name
    temp_file.close()
    
    # Création du document PDF
    # SimpleDocTemplate gère la mise en page automatique
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=A4,           # Format A4 (210mm x 297mm)
        rightMargin=20*mm,     # Marge droite
        leftMargin=20*mm,      # Marge gauche
        topMargin=20*mm,       # Marge haute
        bottomMargin=20*mm     # Marge basse
    )
    
    # Récupération des styles par défaut
    styles = getSampleStyleSheet()
    
    # Création d'un style personnalisé pour le titre
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        alignment=1,  # 0=left, 1=center, 2=right
        spaceAfter=30
    )
    
    # Création d'un style pour les sous-titres
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Heading2'],
        fontSize=12,
        alignment=1,
        textColor=colors.grey,
        spaceAfter=20
    )
    
    # Création d'un style pour l'en-tête de tableau
    header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.white,
        alignment=1,
        fontName='Helvetica-Bold'
    )
    
    # Liste des éléments à ajouter au PDF
    elements = []
    
    # TITRE DU RAPPORT 
    title = Paragraph(
        f"RAPPORT DE PRÉSENCE",
        title_style
    )
    elements.append(title)
    
    # SOUS-TITRE 
    period_str = f"Période du {start_date.strftime('%d/%m/%Y')} au {end_date.strftime('%d/%m/%Y')}"
    subtitle = Paragraph(period_str, subtitle_style)
    elements.append(subtitle)
    
    # DATE DE GÉNÉRATION 
    date_str = f"Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}"
    date_para = Paragraph(date_str, styles['Normal'])
    elements.append(date_para)
    elements.append(Spacer(1, 10*mm))
    
    # STATISTIQUES GLOBALES 
    # Calcul des statistiques
    total_presents = len([row for row in data if row['statut'] == 'Présent'])
    total_absents = len([row for row in data if row['statut'] == 'Absent'])
    total_records = len(data)
    
    # Tableau des statistiques
    stats_data = [
        ["Statistiques", "Valeur"],
        ["Total étudiants", str(total_students)],
        ["Total présences enregistrées", str(total_records)],
        ["Nombre de présents", str(total_presents)],
        ["Nombre d'absents", str(total_absents)]
    ]
    
    # Calcul du taux de présence (si des présences ont été enregistrées)
    if total_records > 0:
        presence_rate = (total_presents / total_records) * 100
        stats_data.append(["Taux de présence", f"{presence_rate:.1f}%"])
    
    # Création du tableau des statistiques
    stats_table = Table(stats_data, colWidths=[80*mm, 80*mm])
    
    # Style du tableau des statistiques
    stats_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (1, 0), colors.HexColor('#1e3a8a')),
        ('TEXTCOLOR', (0, 0), (1, 0), colors.white),
        ('ALIGN', (0, 0), (1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (1, 0), 12),
        ('BACKGROUND', (0, 1), (1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ALIGN', (1, 1), (1, -1), 'CENTER'),
    ]))
    
    elements.append(stats_table)
    elements.append(Spacer(1, 10*mm))
    
    # --- STATISTIQUES PAR JOUR (si disponibles) ---
    if daily_stats:
        elements.append(Paragraph("Statistiques par jour", styles['Heading2']))
        elements.append(Spacer(1, 5*mm))
        
        # Préparation des données du tableau
        daily_data = [["Date", "Présents", "Total", "Taux"]]
        
        for stat in daily_stats:
            date_obj = stat['date']
            presents = stat['presents']
            total = stat['total_etudiants']
            rate = (presents / total * 100) if total > 0 else 0
            
            daily_data.append([
                date_obj.strftime('%d/%m/%Y'),
                str(presents),
                str(total),
                f"{rate:.1f}%"
            ])
        
        # Création du tableau
        daily_table = Table(daily_data, colWidths=[60*mm, 30*mm, 30*mm, 30*mm])
        
        # Style du tableau
        daily_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2563eb')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f0f0')]),
        ]))
        
        elements.append(daily_table)
        elements.append(Spacer(1, 10*mm))
    
    # DÉTAIL DES PRÉSENCES 
    elements.append(Paragraph("Détail des présences", styles['Heading2']))
    elements.append(Spacer(1, 5*mm))
    
    # Vérification s'il y a des données
    if len(data) == 0:
        # Message si aucune donnée
        no_data_para = Paragraph(
            "Aucune donnée de présence trouvée pour la période sélectionnée.",
            styles['Normal']
        )
        elements.append(no_data_para)
    else:
        # Préparation des données du tableau détaillé
        # En-têtes du tableau
        table_data = [
            ["Date", "Heure", "Session", "Matricule", "Nom", "Prénom", "Statut"]
        ]
        
        # Ajout des lignes de données
        for row in data:
            table_data.append([
                row['date'].strftime('%d/%m/%Y') if row['date'] else "",
                str(row['heure'])[:5] if row['heure'] else "",
                row['session'] or "N/A",
                row['matricule'],
                row['nom'].upper(),
                row['prenom'],
                row['statut']
            ])
        
        # Création du tableau
        # A4 largeur ~ 190mm, on répartit
        detail_table = Table(table_data, colWidths=[30*mm, 25*mm, 25*mm, 35*mm, 30*mm, 30*mm, 20*mm])
        
        # Style du tableau détaillé
        detail_table.setStyle(TableStyle([
            # Style de l'en-tête
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3a8a')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            
            # Style des cellules
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            
            # Couleur pour les présents (vert) et absents (rouge)
            ('TEXTCOLOR', (6, 1), (6, -1), colors.green),
        ]))
        
        # Coloration conditionnelle pour les absents
        for i, row in enumerate(table_data[1:], start=1):
            if row[6] == "Absent":
                detail_table.setStyle(TableStyle([
                    ('TEXTCOLOR', (6, i), (6, i), colors.red),
                ]))
        
        elements.append(detail_table)
    
    # Construction du PDF
    doc.build(elements)
    
    # Affichage d'un message de confirmation
    print(f"PDF généré avec succès: {pdf_path}")
    print(f"   - {len(data)} enregistrements")
    print(f"   - Période: {start_date} → {end_date}")
    
    # Retour du chemin vers le fichier PDF
    return pdf_path


# FONCTION POUR RÉCUPÉRER LA LISTE DES ABSENTS
def get_absents(target_date=None):
    """
    Récupère la liste des étudiants absents pour une date donnée.
    
    Paramètres:
        target_date (date, optionnel): Date à vérifier (par défaut: aujourd'hui)
    
    Retourne:
        list: Liste des étudiants absents avec leurs informations
    """
    
    # Si aucune date n'est fournie, utiliser la date du jour
    if target_date is None:
        target_date = date.today()
    
    # Connexion à la base de données
    connection = get_connection()
    
    # Vérification de la connexion
    if connection is None:
        print("Erreur de connexion DB pour récupérer les absents")
        return []
    
    # Création d'un curseur avec dictionnaire
    cursor = connection.cursor(dictionary=True)
    
    # Requête pour trouver les étudiants sans présence à la date donnée
    # Cette requête sélectionne tous les étudiants dont l'ID n'apparaît pas
    # dans la table presence pour la date spécifiée
    query = """
        SELECT 
            e.id,
            e.nom,
            e.prenom,
            e.matricule,
            d.nom as departement,
            e.sexe,
            e.telephone
        FROM etudiant e
        JOIN departement d ON d.id = e.departement_id
        WHERE e.id NOT IN (
            SELECT DISTINCT etudiant_id
            FROM presence
            WHERE date = %s AND statut = 'Présent'
        )
        ORDER BY e.nom ASC, e.prenom ASC
    """
    
    # Exécution de la requête
    cursor.execute(query, (target_date,))
    
    # Récupération de tous les absents
    absents = cursor.fetchall()
    
    # Fermeture des ressources
    cursor.close()
    connection.close()
    
    # Affichage du résultat dans la console
    print(f"Absents du {target_date}: {len(absents)} étudiants")
    
    # Retour de la liste des absents
    return absents


# FONCTION POUR GÉNÉRER UN RAPPORT SPÉCIFIQUE PAR ÉTUDIANT
def generate_student_report(student_id, start_date=None, end_date=None):
    """
    Génère un rapport PDF pour un étudiant spécifique.
    
    Paramètres:
        student_id (int): ID de l'étudiant
        start_date (date, optionnel): Date de début
        end_date (date, optionnel): Date de fin
    
    Retourne:
        str: Chemin vers le fichier PDF généré
    """
    
    # Connexion à la base de données
    connection = get_connection()
    
    if connection is None:
        return None
    
    cursor = connection.cursor(dictionary=True)
    
    # Définition des dates par défaut
    if end_date is None:
        end_date = date.today()
    
    if start_date is None:
        # 30 jours par défaut
        start_date = end_date - timedelta(days=30)
    
    # Récupération des informations de l'étudiant
    cursor.execute(
        """
        SELECT e.*, d.nom as departement
        FROM etudiant e
        JOIN departement d ON d.id = e.departement_id
        WHERE e.id = %s
        """,
        (student_id,)
    )
    student = cursor.fetchone()
    
    if not student:
        cursor.close()
        connection.close()
        return None
    
    # Récupération des présences de l'étudiant
    cursor.execute(
        """
        SELECT date, heure, session, statut
        FROM presence
        WHERE etudiant_id = %s AND date BETWEEN %s AND %s
        ORDER BY date DESC
        """,
        (student_id, start_date, end_date)
    )
    attendances = cursor.fetchall()
    
    cursor.close()
    connection.close()
    
    # Création du fichier PDF
    temp_file = tempfile.NamedTemporaryFile(
        suffix=".pdf",
        delete=False,
        prefix=f"rapport_etudiant_{student_id}_"
    )
    pdf_path = temp_file.name
    temp_file.close()
    
    # Création du document
    doc = SimpleDocTemplate(pdf_path, pagesize=A4)
    styles = getSampleStyleSheet()
    
    elements = []
    
    # Titre
    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=14, alignment=1)
    title = Paragraph(f"Rapport de présence - {student['nom']} {student['prenom']}", title_style)
    elements.append(title)
    elements.append(Spacer(1, 10*mm))
    
    # Informations étudiant
    info_text = f"""
    <b>Matricule:</b> {student['matricule']}<br/>
    <b>Département:</b> {student['departement']}<br/>
    <b>Période:</b> du {start_date.strftime('%d/%m/%Y')} au {end_date.strftime('%d/%m/%Y')}
    """
    info_para = Paragraph(info_text, styles['Normal'])
    elements.append(info_para)
    elements.append(Spacer(1, 10*mm))
    
    # Statistiques
    total_days = (end_date - start_date).days + 1
    present_count = len([a for a in attendances if a['statut'] == 'Présent'])
    absent_count = len([a for a in attendances if a['statut'] == 'Absent'])
    
    if total_days > 0:
        attendance_rate = (present_count / total_days) * 100
    else:
        attendance_rate = 0
    
    stats_data = [
        ["Total jours", str(total_days)],
        ["Présent", str(present_count)],
        ["Absent", str(absent_count)],
        ["Taux de présence", f"{attendance_rate:.1f}%"]
    ]
    
    stats_table = Table(stats_data, colWidths=[60*mm, 60*mm])
    stats_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e0e0e0')),
        ('ALIGN', (1, 0), (1, -1), 'CENTER'),
    ]))
    
    elements.append(stats_table)
    elements.append(Spacer(1, 10*mm))
    
    # Détail des présences
    if attendances:
        elements.append(Paragraph("Détail des présences", styles['Heading2']))
        
        table_data = [["Date", "Heure", "Session", "Statut"]]
        for att in attendances:
            table_data.append([
                att['date'].strftime('%d/%m/%Y'),
                str(att['heure'])[:5],
                att['session'],
                att['statut']
            ])
        
        detail_table = Table(table_data, colWidths=[40*mm, 30*mm, 40*mm, 30*mm])
        detail_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3a8a')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ]))
        
        elements.append(detail_table)
    else:
        elements.append(Paragraph("Aucune donnée de présence pour cette période", styles['Normal']))
    
    doc.build(elements)
    
    return pdf_path


# FONCTION POUR EXPORTER LES DONNÉES EN CSV
def export_to_csv(start_date=None, end_date=None):
    """
    Exporte les données de présence au format CSV.
    
    Paramètres:
        start_date (date, optionnel): Date de début
        end_date (date, optionnel): Date de fin
    
    Retourne:
        str: Chemin vers le fichier CSV généré
    """
    
    import csv
    
    # Connexion et récupération des données (même requête que generate_pdf)
    connection = get_connection()
    
    if connection is None:
        return None
    
    cursor = connection.cursor(dictionary=True)
    
    if end_date is None:
        end_date = date.today()
    
    if start_date is None:
        start_date = date(end_date.year, end_date.month, 1)
    
    query = """
        SELECT 
            e.matricule,
            e.nom,
            e.prenom,
            d.nom as departement,
            p.date,
            p.heure,
            p.session,
            p.statut
        FROM presence p
        JOIN etudiant e ON e.id = p.etudiant_id
        JOIN departement d ON d.id = e.departement_id
        WHERE p.date BETWEEN %s AND %s
        ORDER BY p.date DESC, e.nom ASC
    """
    
    cursor.execute(query, (start_date, end_date))
    data = cursor.fetchall()
    
    cursor.close()
    connection.close()
    
    # Création du fichier CSV
    temp_file = tempfile.NamedTemporaryFile(
        suffix=".csv",
        delete=False,
        prefix="export_presence_"
    )
    csv_path = temp_file.name
    temp_file.close()
    
    # Écriture du fichier CSV
    with open(csv_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
        if data:
            fieldnames = list(data[0].keys())
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
    
    print(f"Export CSV généré: {csv_path} ({len(data)} lignes)")
    
    return csv_path