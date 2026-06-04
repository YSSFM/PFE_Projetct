# routes/student_routes.py
# Routes pour la gestion des étudiants (inscription, liste, modification, suppression)

import base64
import os
import cv2
import numpy as np
import json
from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify, Response, send_file
from database import DatabaseContext
from service.face_service import detect_and_crop_face_cnn, trigger_automatic_training, generate_hybrid_embeddings

student_bp = Blueprint('student', __name__)

# Dossier pour les photos
PHOTOS_FOLDER = 'static/photos'
os.makedirs(PHOTOS_FOLDER, exist_ok=True)


# ==================== PAGES HTML ====================

@student_bp.route('/accueil')
def accueil():
    """Page d'accueil après connexion"""
    if 'user' not in session:
        return redirect(url_for('auth.login_page'))
    return render_template('index.html')

@student_bp.route('/detail_etudiant')
def detail_etudiant():
    """Page d'inscription des étudiants"""
    if 'user' not in session:
        return redirect(url_for('auth.login_page'))
    
    # Récupérer la liste des départements pour le formulaire
    with DatabaseContext() as (cursor, conn):
        cursor.execute("SELECT ID_DEPARTEMENT, NOM_DEPARTEMENT FROM departement ORDER BY NOM_DEPARTEMENT")
        departements = [{'ID_DEPARTEMENT': row[0], 'NOM_DEPARTEMENT': row[1]} for row in cursor.fetchall()]
    
    return render_template('detail_etudiant.html', departements=departements, success=False)


@student_bp.route('/gerer_etudiants')
def gerer_etudiants():
    """Page de gestion des étudiants (CRUD)"""
    if 'user' not in session:
        return redirect(url_for('auth.login_page'))
    return render_template('gerer_etudiants.html')


@student_bp.route('/modifier_etudiant/<cne>')
def modifier_etudiant(cne):
    """Page de modification d'un étudiant"""
    if 'user' not in session:
        return redirect(url_for('auth.login_page'))
    
    with DatabaseContext() as (cursor, conn):
        cursor.execute("SELECT ID_DEPARTEMENT, NOM_DEPARTEMENT FROM departement ORDER BY NOM_DEPARTEMENT")
        departements = [{'ID_DEPARTEMENT': row[0], 'NOM_DEPARTEMENT': row[1]} for row in cursor.fetchall()]
    
    return render_template('modifier_etudiant.html', departements=departements)


# ==================== API REST ====================

@student_bp.route('/api/etudiants/liste', methods=['GET'])
def api_liste_etudiants():
    """Liste complète des étudiants avec statistiques"""
    if 'user' not in session:
        return jsonify({'error': 'Non authentifié'}), 401
    
    with DatabaseContext() as (cursor, conn):
        cursor.execute("""
            SELECT 
                e.CNE_MASSAR, e.NOM, e.PRENOM, e.SEX, e.TELEPHONE, e.MAIL, 
                e.OPTIONS, e.ANNEE_ACADEMIQUE, e.SEMESTRE,
                d.NOM_DEPARTEMENT, d.ID_DEPARTEMENT,
                (SELECT COUNT(*) FROM image WHERE CNE_MASSAR = e.CNE_MASSAR) as photos_count,
                (SELECT COUNT(*) FROM presence WHERE CNE_MASSAR = e.CNE_MASSAR) as presences_count
            FROM etudiant e
            LEFT JOIN departement d ON d.ID_DEPARTEMENT = e.ID_DEPARTEMENT
            ORDER BY e.NOM, e.PRENOM
        """)
        columns = [desc[0] for desc in cursor.description]
        students = [dict(zip(columns, row)) for row in cursor.fetchall()]
        return jsonify(students)


@student_bp.route('/api/etudiant/<cne>', methods=['GET'])
def api_get_etudiant(cne):
    """Récupère les informations d'un étudiant"""
    if 'user' not in session:
        return jsonify({'error': 'Non authentifié'}), 401
    
    with DatabaseContext() as (cursor, conn):
        cursor.execute("""
            SELECT e.*, d.NOM_DEPARTEMENT, d.ID_DEPARTEMENT
            FROM etudiant e
            LEFT JOIN departement d ON d.ID_DEPARTEMENT = e.ID_DEPARTEMENT
            WHERE e.CNE_MASSAR = %s
        """, (cne,))
        row = cursor.fetchone()
        if not row:
            return jsonify({'error': 'Étudiant non trouvé'}), 404
        
        columns = [desc[0] for desc in cursor.description]
        return jsonify(dict(zip(columns, row)))


@student_bp.route('/api/etudiant/photos/<cne>', methods=['GET'])
def api_get_photos(cne):
    """Récupère les photos d'un étudiant en base64"""
    if 'user' not in session:
        return jsonify({'error': 'Non authentifié'}), 401
    
    with DatabaseContext() as (cursor, conn):
        cursor.execute("SELECT IMAGE FROM image WHERE CNE_MASSAR = %s", (cne,))
        rows = cursor.fetchall()
        photos_base64 = []
        for row in rows:
            if row[0]:
                b64 = base64.b64encode(row[0]).decode('utf-8')
                photos_base64.append(b64)
        return jsonify(photos_base64)


@student_bp.route('/api/etudiant/supprimer/<cne>', methods=['DELETE'])
def api_supprimer_etudiant(cne):
    """Supprime un étudiant et toutes ses données associées"""
    if 'user' not in session:
        return jsonify({'error': 'Non authentifié'}), 401
    
    with DatabaseContext() as (cursor, conn):
        try:
            # Supprimer les photos du dossier static
            for f in os.listdir(PHOTOS_FOLDER):
                if f.startswith(cne):
                    file_path = os.path.join(PHOTOS_FOLDER, f)
                    if os.path.exists(file_path):
                        os.remove(file_path)
            
            # Supprimer de la base (les foreign keys feront le reste)
            cursor.execute("DELETE FROM etudiant WHERE CNE_MASSAR = %s", (cne,))
            conn.commit()
            
            # Ré-entraîner le modèle
            trigger_automatic_training()
            
            return jsonify({'success': True})
        except Exception as e:
            conn.rollback()
            return jsonify({'error': str(e)}), 500


@student_bp.route('/api/etudiant/modifier', methods=['POST'])
def api_modifier_etudiant():
    """Modifie les informations d'un étudiant"""
    if 'user' not in session:
        return jsonify({'error': 'Non authentifié'}), 401
    
    cne_original = request.form.get('cne_original')
    cne = request.form.get('CNEMASSAR')
    nom = request.form.get('NOM')
    prenom = request.form.get('PRENOM')
    departement_id = request.form.get('ID_DEPARTEMENT')
    options = request.form.get('OPTIONS')
    annee = request.form.get('ANNEE_ACADEMIQUE')
    semestre = request.form.get('SEMESTRE')
    sexe = request.form.get('SEX')
    email = request.form.get('MAIL')
    telephone = request.form.get('TELEPHONE')
    
    with DatabaseContext() as (cursor, conn):
        try:
            # Mettre à jour l'étudiant
            cursor.execute("""
                UPDATE etudiant 
                SET CNE_MASSAR=%s, NOM=%s, PRENOM=%s, ID_DEPARTEMENT=%s, 
                    OPTIONS=%s, ANNEE_ACADEMIQUE=%s, SEMESTRE=%s, 
                    SEX=%s, MAIL=%s, TELEPHONE=%s
                WHERE CNE_MASSAR=%s
            """, (cne, nom, prenom, departement_id, options, annee, semestre, sexe, email, telephone, cne_original))
            
            # Si le CNE a changé, mettre à jour les références
            if cne_original != cne:
                cursor.execute("UPDATE image SET CNE_MASSAR=%s WHERE CNE_MASSAR=%s", (cne, cne_original))
                cursor.execute("UPDATE presence SET CNE_MASSAR=%s WHERE CNE_MASSAR=%s", (cne, cne_original))
                
                # Renommer les fichiers photos
                for f in os.listdir(PHOTOS_FOLDER):
                    if f.startswith(cne_original):
                        old_path = os.path.join(PHOTOS_FOLDER, f)
                        new_name = f.replace(cne_original, cne)
                        new_path = os.path.join(PHOTOS_FOLDER, new_name)
                        if os.path.exists(old_path):
                            os.rename(old_path, new_path)
            
            # Ajouter les nouvelles photos
            new_photos = request.files.getlist('new_photos')
            for photo in new_photos:
                if photo and photo.filename:
                    img_bytes = photo.read()
                    cropped_face, _ = detect_and_crop_face_cnn(img_bytes)
                    if cropped_face is not None:
                        cropped_face = cv2.resize(cropped_face, (128, 128))
                        _, buffer = cv2.imencode('.jpg', cropped_face)
                        cursor.execute("INSERT INTO image (CNE_MASSAR, IMAGE) VALUES (%s, %s)", (cne, buffer.tobytes()))
                        
                        # Sauvegarder aussi dans static/photos
                        import time
                        timestamp = int(time.time())
                        photo_path = os.path.join(PHOTOS_FOLDER, f"{cne}_{timestamp}.jpg")
                        cv2.imwrite(photo_path, cropped_face)
            
            conn.commit()
            trigger_automatic_training()
            return jsonify({'success': True})
            
        except Exception as e:
            conn.rollback()
            return jsonify({'error': str(e)}), 500


@student_bp.route('/api/etudiant/supprimer-photo/<cne>/<int:index>', methods=['DELETE'])
def api_supprimer_photo(cne, index):
    """Supprime une photo spécifique d'un étudiant"""
    if 'user' not in session:
        return jsonify({'error': 'Non authentifié'}), 401
    
    with DatabaseContext() as (cursor, conn):
        try:
            cursor.execute("SELECT ID_IMAGE FROM image WHERE CNE_MASSAR = %s", (cne,))
            rows = cursor.fetchall()
            if index < len(rows):
                cursor.execute("DELETE FROM image WHERE ID_IMAGE = %s", (rows[index][0],))
                conn.commit()
                trigger_automatic_training()
            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'error': str(e)}), 500


@student_bp.route('/api/departements', methods=['GET'])
def api_get_departements():
    """Liste des départements"""
    with DatabaseContext() as (cursor, conn):
        cursor.execute("SELECT ID_DEPARTEMENT, NOM_DEPARTEMENT FROM departement ORDER BY NOM_DEPARTEMENT")
        rows = cursor.fetchall()
        return jsonify([{'ID_DEPARTEMENT': row[0], 'NOM_DEPARTEMENT': row[1]} for row in rows])


@student_bp.route('/api/presences/count', methods=['GET'])
def api_presences_count():
    """Nombre total de présences"""
    with DatabaseContext() as (cursor, conn):
        cursor.execute("SELECT COUNT(*) FROM presence")
        return jsonify({'count': cursor.fetchone()[0]})


@student_bp.route('/api/students/count', methods=['GET'])
def api_students_count():
    """Nombre total d'étudiants"""
    with DatabaseContext() as (cursor, conn):
        cursor.execute("SELECT COUNT(*) FROM etudiant")
        return jsonify({'count': cursor.fetchone()[0]})


@student_bp.route('/api/attendance/today/count', methods=['GET'])
def api_today_attendance_count():
    """Nombre de présences aujourd'hui"""
    from datetime import date
    today = date.today().isoformat()
    with DatabaseContext() as (cursor, conn):
        cursor.execute("SELECT COUNT(*) FROM presence WHERE DATE_PRESENCE = %s", (today,))
        return jsonify({'count': cursor.fetchone()[0]})


@student_bp.route('/api/attendance/recent', methods=['GET'])
def api_recent_attendance():
    """Dernières présences"""
    from datetime import date
    today = date.today().isoformat()
    with DatabaseContext() as (cursor, conn):
        cursor.execute("""
            SELECT p.DATE_PRESENCE, p.HEURE, e.CNE_MASSAR, e.NOM, e.PRENOM
            FROM presence p
            JOIN etudiant e ON e.CNE_MASSAR = p.CNE_MASSAR
            WHERE p.DATE_PRESENCE = %s
            ORDER BY p.HEURE DESC
            LIMIT 10
        """, (today,))
        rows = cursor.fetchall()
        return jsonify([{'DATE_PRESENCE': str(r[0]), 'HEURE': str(r[1]), 'CNE_MASSAR': r[2], 'NOM': r[3], 'PRENOM': r[4]} for r in rows])


@student_bp.route('/api/embeddings/count', methods=['GET'])
def api_embeddings_count():
    """Nombre de photos/embeddings"""
    with DatabaseContext() as (cursor, conn):
        cursor.execute("SELECT COUNT(*) FROM image")
        return jsonify({'count': cursor.fetchone()[0]})


# ==================== ROUTE D'AJOUT (POST) ====================

@student_bp.route('/ajouter', methods=['POST'])
def ajouter_etudiant():
    """Ajoute un nouvel étudiant avec ses photos"""
    if 'user' not in session:
        return redirect(url_for('auth.login_page'))

    cne = request.form.get('CNEMASSAR')
    nom = request.form.get('NOM')
    prenom = request.form.get('PRENOM')
    sex = request.form.get('SEX')
    options = request.form.get('OPTIONS')
    id_dept = request.form.get('ID_DEPARTEMENT')
    annee = request.form.get('ANNEE_ACADEMIQUE')
    semestre = request.form.get('SEMESTRE')
    mail = request.form.get('MAIL')
    tel = request.form.get('TELEPHONE')
    
    # Récupérer les photos depuis le champ caché base64 ou depuis les fichiers
    photos_base64_str = request.form.get('photos_base64', '[]')
    photos_base64 = json.loads(photos_base64_str)
    
    with DatabaseContext() as (cursor, conn):
        try:
            # Vérifier si l'étudiant existe déjà
            cursor.execute("SELECT CNE_MASSAR FROM etudiant WHERE CNE_MASSAR = %s", (cne,))
            if cursor.fetchone():
                # Recharger les départements
                cursor.execute("SELECT ID_DEPARTEMENT, NOM_DEPARTEMENT FROM departement")
                departements = [{'ID_DEPARTEMENT': row[0], 'NOM_DEPARTEMENT': row[1]} for row in cursor.fetchall()]
                return render_template('detail_etudiant.html', error="Cet étudiant existe déjà", departements=departements, success=False)
            
            # Insérer l'étudiant
            cursor.execute("""
                INSERT INTO etudiant (CNE_MASSAR, ID_DEPARTEMENT, NOM, PRENOM, SEX, TELEPHONE, MAIL, OPTIONS, ANNEE_ACADEMIQUE, SEMESTRE)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (cne, id_dept, nom, prenom, sex, tel, mail, options, annee, semestre))
            
            # Traiter chaque photo
            photos_saved = 0
            for idx, photo_b64 in enumerate(photos_base64):
                if photo_b64:
                    # Convertir base64 en image
                    img_data = photo_b64.split(',')[1] if ',' in photo_b64 else photo_b64
                    img_bytes = base64.b64decode(img_data)
                    nparr = np.frombuffer(img_bytes, np.uint8)
                    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                    
                    if img is not None:
                        # Détection et rognage du visage
                        cropped_face, _ = detect_and_crop_face_cnn(img_bytes)
                        if cropped_face is not None:
                            cropped_face = cv2.resize(cropped_face, (128, 128))
                            _, buffer = cv2.imencode('.jpg', cropped_face)
                            cursor.execute("INSERT INTO image (CNE_MASSAR, IMAGE) VALUES (%s, %s)", (cne, buffer.tobytes()))
                            
                            # Sauvegarder aussi dans static/photos
                            photo_path = os.path.join(PHOTOS_FOLDER, f"{cne}_{idx}.jpg")
                            cv2.imwrite(photo_path, cropped_face)
                            photos_saved += 1
            
            conn.commit()
            
            # Déclencher l'entraînement automatique
            trigger_automatic_training()
            
            # Recharger les départements pour le template
            cursor.execute("SELECT ID_DEPARTEMENT, NOM_DEPARTEMENT FROM departement")
            departements = [{'ID_DEPARTEMENT': row[0], 'NOM_DEPARTEMENT': row[1]} for row in cursor.fetchall()]
            
            return render_template('detail_etudiant.html', success=True, departements=departements)
            
        except Exception as e:
            conn.rollback()
            print(f"Erreur: {e}")
            with DatabaseContext() as (cursor, conn):
                cursor.execute("SELECT ID_DEPARTEMENT, NOM_DEPARTEMENT FROM departement")
                departements = [{'ID_DEPARTEMENT': row[0], 'NOM_DEPARTEMENT': row[1]} for row in cursor.fetchall()]
            return render_template('detail_etudiant.html', error=str(e), departements=departements, success=False)


# ==================== RAPPORTS ET STATISTIQUES ====================

@student_bp.route('/rapport')
def rapport_page():
    """Page de génération de rapport"""
    if 'user' not in session:
        return redirect(url_for('auth.login_page'))
    return render_template('rapport_presence.html')


@student_bp.route('/api/stats/presences', methods=['GET'])
def api_stats_presences():
    """Statistiques de présence"""
    from datetime import date
    today = date.today().isoformat()
    
    with DatabaseContext() as (cursor, conn):
        cursor.execute("SELECT COUNT(*) FROM etudiant")
        total_students = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT CNE_MASSAR) FROM presence WHERE DATE_PRESENCE = %s", (today,))
        present_today = cursor.fetchone()[0]
        
        absent_today = total_students - present_today
        
        return jsonify({
            'total_students': total_students,
            'present_today': present_today,
            'absent_today': absent_today
        })


# ==================== API AVEC FILTRES ====================
@student_bp.route('/api/presences/periode', methods=['GET'])
def api_presences_periode():
    """Présences sur une période avec filtre par département et par filière"""
    start_date = request.args.get('start')
    end_date = request.args.get('end')
    departement = request.args.get('departement')
    filiere = request.args.get('filiere')
    
    query = """
        SELECT p.DATE_PRESENCE, p.HEURE, e.CNE_MASSAR, e.NOM, e.PRENOM, 
               d.NOM_DEPARTEMENT as DEPARTEMENT, e.OPTIONS
        FROM presence p
        JOIN etudiant e ON e.CNE_MASSAR = p.CNE_MASSAR
        LEFT JOIN departement d ON d.ID_DEPARTEMENT = e.ID_DEPARTEMENT
        WHERE p.DATE_PRESENCE BETWEEN %s AND %s
    """
    params = [start_date, end_date]
    
    if departement:
        query += " AND d.NOM_DEPARTEMENT = %s"
        params.append(departement)
    
    if filiere:
        query += " AND e.OPTIONS = %s"
        params.append(filiere)
    
    query += " ORDER BY p.DATE_PRESENCE DESC, p.HEURE DESC"
    
    with DatabaseContext() as (cursor, conn):
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        return jsonify([{
            'DATE_PRESENCE': str(r[0]),
            'HEURE': str(r[1]),
            'CNE_MASSAR': r[2],
            'NOM': r[3],
            'PRENOM': r[4],
            'DEPARTEMENT': r[5],
            'OPTIONS': r[6]
        } for r in rows])

@student_bp.route('/api/export/etudiants/csv', methods=['GET'])
def export_etudiants_csv():
    """Exporte la liste des étudiants en CSV"""
    import csv
    import io
    from flask import Response
    
    with DatabaseContext() as (cursor, conn):
        cursor.execute("""
            SELECT e.CNE_MASSAR, e.NOM, e.PRENOM, e.SEX, e.TELEPHONE, e.MAIL, 
                   e.OPTIONS, e.ANNEE_ACADEMIQUE, e.SEMESTRE, d.NOM_DEPARTEMENT
            FROM etudiant e
            LEFT JOIN departement d ON d.ID_DEPARTEMENT = e.ID_DEPARTEMENT
            ORDER BY e.NOM, e.PRENOM
        """)
        rows = cursor.fetchall()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['CNE Massar', 'Nom', 'Prénom', 'Sexe', 'Téléphone', 'Email', 'Filière', 'Année', 'Semestre', 'Département'])
    
    for row in rows:
        writer.writerow([str(r) if r else '' for r in row])
    
    response = Response(output.getvalue(), mimetype='text/csv')
    response.headers['Content-Disposition'] = 'attachment; filename=etudiants.csv'
    return response


@student_bp.route('/api/rapport/pdf', methods=['GET'])
def rapport_pdf_filtre():
    """Génère un rapport PDF avec filtre par département/filière"""
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet
    import tempfile
    from flask import send_file
    
    start_date = request.args.get('start')
    end_date = request.args.get('end')
    departement = request.args.get('departement')
    
    query = """
        SELECT e.CNE_MASSAR, e.NOM, e.PRENOM, d.NOM_DEPARTEMENT, e.OPTIONS,
               COUNT(p.ID_PRESENCE) as nb_presences
        FROM etudiant e
        LEFT JOIN departement d ON d.ID_DEPARTEMENT = e.ID_DEPARTEMENT
        LEFT JOIN presence p ON p.CNE_MASSAR = e.CNE_MASSAR AND p.DATE_PRESENCE BETWEEN %s AND %s
        WHERE 1=1
    """
    params = [start_date, end_date]
    
    if departement:
        query += " AND d.NOM_DEPARTEMENT = %s"
        params.append(departement)
    
    query += " GROUP BY e.CNE_MASSAR ORDER BY nb_presences DESC"
    
    with DatabaseContext() as (cursor, conn):
        cursor.execute(query, params)
        rows = cursor.fetchall()
    
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
    doc = SimpleDocTemplate(temp_file.name, pagesize=A4)
    styles = getSampleStyleSheet()
    
    elements = []
    title = f"Rapport de présence du {start_date} au {end_date}"
    if departement:
        title += f" - {departement}"
    elements.append(Paragraph(title, styles['Title']))
    elements.append(Spacer(1, 20))
    
    table_data = [['CNE Massar', 'Nom', 'Prénom', 'Département', 'Filière', 'Présences']]
    for row in rows:
        table_data.append([str(row[0]), row[1], row[2], row[3] or '-', row[4] or '-', str(row[5])])
    
    table = Table(table_data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.grey),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 10),
        ('BOTTOMPADDING', (0,0), (-1,0), 12),
        ('BACKGROUND', (0,1), (-1,-1), colors.beige),
        ('GRID', (0,0), (-1,-1), 1, colors.black)
    ]))
    elements.append(table)
    
    doc.build(elements)
    temp_file.close()
    
    return send_file(temp_file.name, as_attachment=True, download_name=f'rapport_presence_{start_date}_{end_date}.pdf')


@student_bp.route('/api/rapport/csv', methods=['GET'])
def rapport_csv_filtre():
    """Exporte les présences en CSV avec filtre"""
    import csv
    import io
    from flask import Response
    
    start_date = request.args.get('start')
    end_date = request.args.get('end')
    departement = request.args.get('departement')
    
    query = """
        SELECT p.DATE_PRESENCE, p.HEURE, e.CNE_MASSAR, e.NOM, e.PRENOM, e.MAIL, d.NOM_DEPARTEMENT
        FROM presence p
        JOIN etudiant e ON e.CNE_MASSAR = p.CNE_MASSAR
        LEFT JOIN departement d ON d.ID_DEPARTEMENT = e.ID_DEPARTEMENT
        WHERE p.DATE_PRESENCE BETWEEN %s AND %s
    """
    params = [start_date, end_date]
    
    if departement:
        query += " AND d.NOM_DEPARTEMENT = %s"
        params.append(departement)
    
    query += " ORDER BY p.DATE_PRESENCE, p.HEURE"
    
    with DatabaseContext() as (cursor, conn):
        cursor.execute(query, params)
        rows = cursor.fetchall()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Date', 'Heure', 'CNE Massar', 'Nom', 'Prénom', 'Email', 'Département'])
    
    for row in rows:
        writer.writerow([str(r) if r else '' for r in row])
    
    response = Response(output.getvalue(), mimetype='text/csv')
    response.headers['Content-Disposition'] = f'attachment; filename=presences_{start_date}_{end_date}.csv'
    return response

@student_bp.route('/choose-model')
def choose_model():
    """Page de sélection du modèle"""
    if 'user' not in session:
        return redirect(url_for('auth.login_page'))
    return render_template('choose_model.html')