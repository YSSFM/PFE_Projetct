-- ============================================================
-- BASE DE DONNÉES RECONNAISSANCE FACIALE - VERSION CORRIGÉE
-- ============================================================

DROP DATABASE IF EXISTS face_recognition;
CREATE DATABASE face_recognition;
USE face_recognition;

SET SQL_MODE = 'NO_AUTO_VALUE_ON_ZERO';

-- ============================================================
-- TABLE ADMIN
-- ============================================================
CREATE TABLE admin (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nom VARCHAR(100) NOT NULL,
    prenom VARCHAR(100) NOT NULL,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    reset_token VARCHAR(255) DEFAULT NULL,
    reset_token_expiry DATETIME DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- TABLE DEPARTEMENT
-- ============================================================
CREATE TABLE departement (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nom VARCHAR(100) UNIQUE NOT NULL,
    chef VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- TABLE ETUDIANT (SANS face_embedding)
-- ============================================================
CREATE TABLE etudiant (
    id INT AUTO_INCREMENT PRIMARY KEY,
    departement_id INT NOT NULL,
    matricule VARCHAR(30) UNIQUE NOT NULL,
    nom VARCHAR(100) NOT NULL,
    prenom VARCHAR(100) NOT NULL,
    sexe ENUM('M', 'F') NOT NULL,
    telephone VARCHAR(20),
    email VARCHAR(100),
    annee_academique VARCHAR(20),
    semestre VARCHAR(20),
    is_active BOOLEAN DEFAULT TRUE,
    date_inscription TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_etudiant_departement
        FOREIGN KEY (departement_id)
        REFERENCES departement(id)
        ON DELETE CASCADE
);

-- ============================================================
-- TABLE FACE_EMBEDDINGS (PLUSIEURS PAR ÉTUDIANT)
-- ============================================================
CREATE TABLE face_embeddings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    etudiant_id INT NOT NULL,
    embedding_vector LONGBLOB NOT NULL,
    image_path VARCHAR(255),
    quality_score DECIMAL(5,2) DEFAULT 0,
    capture_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    CONSTRAINT fk_embedding_student
        FOREIGN KEY (etudiant_id)
        REFERENCES etudiant(id)
        ON DELETE CASCADE
);

-- ============================================================
-- TABLE PRESENCE (SIMPLIFIÉE)
-- ============================================================
CREATE TABLE presence (
    id INT AUTO_INCREMENT PRIMARY KEY,
    etudiant_id INT NOT NULL,
    presence_date DATE NOT NULL,
    presence_time TIME NOT NULL,
    session ENUM('Matin', 'Apres-midi', 'Soir') DEFAULT 'Matin',
    statut ENUM('Present', 'Absent', 'Retard') DEFAULT 'Present',
    confidence_score DECIMAL(5,4),
    verification_mode ENUM('FaceRecognition', 'Manual') DEFAULT 'FaceRecognition',
    UNIQUE KEY unique_presence (etudiant_id, presence_date, session),
    CONSTRAINT fk_presence_etudiant
        FOREIGN KEY (etudiant_id)
        REFERENCES etudiant(id)
        ON DELETE CASCADE
);

-- ============================================================
-- TABLE RECOGNITION_LOGS
-- ============================================================
CREATE TABLE recognition_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    etudiant_id INT,
    predicted_name VARCHAR(100),
    similarity_score DECIMAL(5,4),
    decision ENUM('Accepted', 'Rejected'),
    capture_path VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_logs_etudiant
        FOREIGN KEY (etudiant_id)
        REFERENCES etudiant(id)
        ON DELETE SET NULL
);

-- ============================================================
-- TABLE RAPPORT
-- ============================================================
CREATE TABLE rapport (
    id INT AUTO_INCREMENT PRIMARY KEY,
    admin_id INT NOT NULL,
    mois VARCHAR(20),
    nb_jours_ouvrables INT DEFAULT 0,
    nb_jours_present INT DEFAULT 0,
    nb_jours_absent INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_rapport_admin
        FOREIGN KEY (admin_id)
        REFERENCES admin(id)
        ON DELETE CASCADE
);

-- ============================================================
-- INDEX POUR PERFORMANCES
-- ============================================================
CREATE INDEX idx_presence_etudiant ON presence(etudiant_id);
CREATE INDEX idx_presence_date ON presence(presence_date);
CREATE INDEX idx_embeddings_etudiant ON face_embeddings(etudiant_id);
CREATE INDEX idx_etudiant_matricule ON etudiant(matricule);
CREATE INDEX idx_etudiant_departement ON etudiant(departement_id);

-- ============================================================
-- DONNÉES DE TEST
-- ============================================================
INSERT INTO departement (nom, chef) VALUES ('Informatique', 'Dr. Diop');

-- Mot de passe: Admin123 (hashé en SHA-256)
INSERT INTO admin (nom, prenom, username, email, password_hash) VALUES
('Admin', 'Système', 'admin', 'admin@face-recognition.com', 
 '8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918');

INSERT INTO etudiant (departement_id, matricule, nom, prenom, sexe, annee_academique, semestre) VALUES
(1, '2024001', 'Moussa', 'Youssouf', 'M', '2025-2026', 'S6'),
(1, '2024002', 'Diallo', 'Aissatou', 'F', '2025-2026', 'S6');

-- ============================================================
-- FIN DU SCRIPT
-- ============================================================