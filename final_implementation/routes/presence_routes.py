# routes/presence_routes.py
# Routes pour la gestion des présences et la reconnaissance faciale

import cv2
import numpy as np
from flask import Blueprint, render_template, Response, session, redirect, url_for, jsonify, send_file, request
from datetime import datetime, date, timedelta
import face_recognition
from database import DatabaseContext
from service.face_service import generate_hybrid_embeddings, predict_student_svm, get_current_model
import csv
import io
import os
import tempfile
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

presence_bp = Blueprint('presence', __name__)

# État de la reconnaissance
recognition_active = False

# Configuration email
SMTP_CONFIG = {
    'server': 'smtp.gmail.com',
    'port': 587,
    'username': 'yssfmoussa2037@gmail.com',  
    'password': 'skkj oepr xnec lzdl'       
}


@presence_bp.route('/detection_faciale')
def detection_faciale():
    """Page de détection faciale"""
    if 'user' not in session:
        return redirect(url_for('auth.login_page'))
    return render_template('detection_faciale.html', active_model=get_current_model())


@presence_bp.route('/api/recognition/start', methods=['POST'])
def start_recognition():
    """Démarre la reconnaissance"""
    global recognition_active
    recognition_active = True
    return jsonify({'status': 'running'})


@presence_bp.route('/api/recognition/stop', methods=['POST'])
def stop_recognition():
    """Arrête la reconnaissance"""
    global recognition_active
    recognition_active = False
    return jsonify({'status': 'stopped'})


@presence_bp.route('/api/recognition/status', methods=['GET'])
def recognition_status():
    """Statut de la reconnaissance"""
    global recognition_active
    return jsonify({'active': recognition_active})


def generate_video_stream():
    """Génère le flux vidéo avec reconnaissance faciale"""
    global recognition_active
    cap = cv2.VideoCapture(0)
    
    while recognition_active:
        success, frame = cap.read()
        if not success:
            break
        
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_frame, model="hog")
        
        for (top, right, bottom, left) in face_locations:
            face_img = frame[top:bottom, left:right]
            if face_img.size > 0:
                embedding = generate_hybrid_embeddings(face_img)
                if embedding is not None:
                    cne = predict_student_svm(embedding)
                    
                    if cne != "Inconnu":
                        # Vérifier présence aujourd'hui
                        today = date.today().isoformat()
                        with DatabaseContext() as (cursor, conn):
                            cursor.execute("SELECT ID_PRESENCE FROM presence WHERE CNE_MASSAR=%s AND DATE_PRESENCE=%s", (cne, today))
                            if not cursor.fetchone():
                                now = datetime.now()
                                cursor.execute("INSERT INTO presence (DATE_PRESENCE, HEURE, STATUT, CNE_MASSAR) VALUES (%s, %s, 'Present', %s)", (today, now.strftime('%H:%M:%S'), cne))
                                conn.commit()
                        
                        cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
                        cv2.putText(frame, f"Present: {cne}", (left, top-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 2)
                    else:
                        cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)
                        cv2.putText(frame, "Inconnu", (left, top-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,0,255), 2)
        
        ret, buffer = cv2.imencode('.jpg', frame)
        yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
    
    cap.release()


@presence_bp.route('/video_feed')
def video_feed():
    """Flux vidéo MJPEG"""
    if 'user' not in session:
        return "Accès interdit", 403
    
    response = Response(generate_video_stream(), mimetype='multipart/x-mixed-replace; boundary=frame')
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response


# ==================== API PRÉSENCES ====================

@presence_bp.route('/api/presences/jour', methods=['GET'])
def api_presences_jour():
    """Liste des présences du jour"""
    today = date.today().isoformat()
    with DatabaseContext() as (cursor, conn):
        cursor.execute("""
            SELECT p.*, e.NOM, e.PRENOM 
            FROM presence p 
            JOIN etudiant e ON e.CNE_MASSAR = p.CNE_MASSAR 
            WHERE p.DATE_PRESENCE = %s 
            ORDER BY p.HEURE DESC
        """, (today,))
        rows = cursor.fetchall()
        return jsonify([{'HEURE': str(r[2]), 'NOM': r[5], 'PRENOM': r[6]} for r in rows])


@presence_bp.route('/api/presences/count', methods=['GET'])
def api_presences_count():
    """Nombre total de présences"""
    with DatabaseContext() as (cursor, conn):
        cursor.execute("SELECT COUNT(*) FROM presence")
        return jsonify({'count': cursor.fetchone()[0]})


@presence_bp.route('/api/rapport/pdf', methods=['GET'])
def rapport_pdf():
    """Génère un rapport PDF des présences"""
    start_date = request.args.get('start', date.today().replace(day=1).isoformat())
    end_date = request.args.get('end', date.today().isoformat())
    departement = request.args.get('departement')
    filiere = request.args.get('filiere')
    
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
    
    if filiere:
        query += " AND e.OPTIONS = %s"
        params.append(filiere)
    
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
    if filiere:
        title += f" - {filiere}"
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


@presence_bp.route('/api/rapport/csv', methods=['GET'])
def rapport_csv():
    """Exporte les présences au format CSV"""
    start_date = request.args.get('start', date.today().replace(day=1).isoformat())
    end_date = request.args.get('end', date.today().isoformat())
    departement = request.args.get('departement')
    filiere = request.args.get('filiere')
    
    query = """
        SELECT p.DATE_PRESENCE, p.HEURE, e.CNE_MASSAR, e.NOM, e.PRENOM, e.MAIL, d.NOM_DEPARTEMENT, e.OPTIONS
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
    
    query += " ORDER BY p.DATE_PRESENCE, p.HEURE"
    
    with DatabaseContext() as (cursor, conn):
        cursor.execute(query, params)
        rows = cursor.fetchall()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Date', 'Heure', 'CNE Massar', 'Nom', 'Prénom', 'Email', 'Département', 'Filière'])
    for row in rows:
        writer.writerow([str(r) if r else '' for r in row])
    
    response = Response(output.getvalue(), mimetype='text/csv')
    response.headers['Content-Disposition'] = f'attachment; filename=presences_{start_date}_{end_date}.csv'
    return response


@presence_bp.route('/api/train', methods=['POST'])
def api_train():
    """Déclenche l'entraînement du modèle"""
    from service.face_service import trigger_automatic_training
    result = trigger_automatic_training()
    return jsonify({'success': result})


# ==================== ENVOI D'EMAILS ====================

@presence_bp.route('/api/envoyer-emails', methods=['POST'])
def envoyer_emails():
    """Envoie des emails aux étudiants sélectionnés avec leur rapport"""
    data = request.get_json()
    students = data.get('students', [])
    subject = data.get('subject', 'Rapport de présence')
    message_body = data.get('message', '')
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    
    sent_count = 0
    errors = []
    
    for student in students:
        email = student.get('email')
        if not email or email == '':
            errors.append(f"{student.get('name', 'Inconnu')}: Pas d'email")
            continue
        
        try:
            # Générer le rapport PDF individuel
            with DatabaseContext() as (cursor, conn):
                cursor.execute("""
                    SELECT p.DATE_PRESENCE, p.HEURE
                    FROM presence p
                    WHERE p.CNE_MASSAR = %s AND p.DATE_PRESENCE BETWEEN %s AND %s
                    ORDER BY p.DATE_PRESENCE DESC
                """, (student['cne'], start_date, end_date))
                presences = cursor.fetchall()
                
                cursor.execute("SELECT NOM, PRENOM FROM etudiant WHERE CNE_MASSAR = %s", (student['cne'],))
                etudiant = cursor.fetchone()
            
            if not etudiant:
                errors.append(f"{student.get('cne')}: Étudiant non trouvé")
                continue
            
            # Créer le PDF
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
            doc = SimpleDocTemplate(temp_file.name, pagesize=A4)
            styles = getSampleStyleSheet()
            
            elements = []
            elements.append(Paragraph(f"Rapport de présence - {etudiant[0]} {etudiant[1]}", styles['Title']))
            elements.append(Spacer(1, 20))
            elements.append(Paragraph(f"Période du {start_date} au {end_date}", styles['Normal']))
            elements.append(Spacer(1, 20))
            
            table_data = [['Date', 'Heure']]
            for p in presences:
                table_data.append([str(p[0]), str(p[1])])
            
            if len(presences) == 0:
                table_data.append(['Aucune présence', 'sur la période'])
            
            table = Table(table_data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.grey),
                ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('GRID', (0,0), (-1,-1), 1, colors.black)
            ]))
            elements.append(table)
            
            doc.build(elements)
            temp_file.close()
            
            # Créer l'email
            msg = MIMEMultipart()
            msg['From'] = SMTP_CONFIG['username']
            msg['To'] = email
            msg['Subject'] = subject
            
            body = f"{message_body}\n\nÉtudiant: {student['name']}\nPériode: {start_date} au {end_date}\nNombre de présences: {len(presences)}\n\n---\nCe message a été généré automatiquement par le système de reconnaissance faciale."
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            # Attacher le PDF
            with open(temp_file.name, 'rb') as f:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(f.read())
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', f'attachment; filename=rapport_{student["cne"]}.pdf')
                msg.attach(part)
            
            # Envoyer l'email
            try:
                server = smtplib.SMTP(SMTP_CONFIG['server'], SMTP_CONFIG['port'])
                server.starttls()
                server.login(SMTP_CONFIG['username'], SMTP_CONFIG['password'])
                server.send_message(msg)
                server.quit()
                sent_count += 1
                print(f"✅ Email envoyé à {email}")
            except Exception as e:
                errors.append(f"{email}: {str(e)}")
                print(f"❌ Erreur envoi à {email}: {e}")
            
            # Nettoyer
            try:
                os.unlink(temp_file.name)
            except:
                pass
            
        except Exception as e:
            errors.append(f"{student.get('cne', 'Inconnu')}: {str(e)}")
            print(f"❌ Erreur génération rapport pour {student.get('cne')}: {e}")
    
    return jsonify({
        'sent': sent_count, 
        'total': len(students),
        'errors': errors
    })


# ==================== API MODÈLE ====================

@presence_bp.route('/api/active-model', methods=['GET'])
def api_active_model():
    """Retourne le modèle actif"""
    try:
        from service.recognition_core import get_current_model_type
        model_type = get_current_model_type()
        return jsonify({
            'model_type': model_type,
            'ready': True
        })
    except ImportError:
        return jsonify({
            'model_type': 'pretrained',
            'ready': False,
            'message': 'Module recognition_core non disponible'
        })


@presence_bp.route('/api/select-model', methods=['POST'])
def api_select_model():
    """Sélectionne le modèle à utiliser"""
    try:
        from service.recognition_core import set_current_model_type
        
        data = request.get_json()
        model_type = data.get('model_type', 'pretrained')
        
        if set_current_model_type(model_type):
            return jsonify({
                'success': True,
                'model_type': model_type,
                'message': f'Modèle {model_type} sélectionné'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Type de modèle invalide'
            }), 400
    except ImportError:
        return jsonify({
            'success': True,
            'model_type': 'pretrained',
            'message': 'Modèle par défaut utilisé (recognition_core non disponible)'
        })