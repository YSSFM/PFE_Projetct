CREATE DATABASE IF NOT EXISTS face_recognition
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

USE face_recognition;

CREATE TABLE IF NOT EXISTS admin (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS departement (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nom VARCHAR(100) NOT NULL UNIQUE,
    chef VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS etudiant (
    id INT AUTO_INCREMENT PRIMARY KEY,
    departement_id INT NOT NULL,
    nom VARCHAR(100) NOT NULL,
    prenom VARCHAR(100) NOT NULL,
    matricule VARCHAR(30) NOT NULL UNIQUE,
    sexe ENUM('M', 'F') NOT NULL,
    telephone VARCHAR(20),
    face_embedding LONGBLOB,

    annee_academique VARCHAR(20),
    semestre VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_departement (departement_id),

    CONSTRAINT fk_etudiant_departement
        FOREIGN KEY (departement_id)
        REFERENCES departement(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS presence (
    id INT AUTO_INCREMENT PRIMARY KEY,
    etudiant_id INT NOT NULL,
    date DATE NOT NULL,
    heure TIME NOT NULL,
    session VARCHAR(50),
    statut ENUM('Présent', 'Absent') DEFAULT 'Présent',

    INDEX idx_etudiant (etudiant_id),
    INDEX idx_date (date),

    CONSTRAINT fk_presence_etudiant
        FOREIGN KEY (etudiant_id)
        REFERENCES etudiant(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS image (
    id INT AUTO_INCREMENT PRIMARY KEY,
    etudiant_id INT NOT NULL,
    image LONGBLOB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_image_etudiant (etudiant_id),

    CONSTRAINT fk_image_etudiant
        FOREIGN KEY (etudiant_id)
        REFERENCES etudiant(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS rapport (
    id INT AUTO_INCREMENT PRIMARY KEY,
    admin_id INT NOT NULL,
    mois VARCHAR(20),
    nb_jours_ouvrables INT DEFAULT 0,
    nb_jours_present INT DEFAULT 0,
    nb_jours_absent INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_admin (admin_id),

    CONSTRAINT fk_rapport_admin
        FOREIGN KEY (admin_id)
        REFERENCES admin(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB;
