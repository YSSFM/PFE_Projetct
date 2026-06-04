-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Hôte : 127.0.0.1:3306
-- Généré le : jeu. 09 avr. 2026 à 22:54
-- Version du serveur : 9.1.0
-- Version de PHP : 8.3.14

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Base de données : `face_recognition`
--

-- --------------------------------------------------------

--
-- Structure de la table `admin`
--

DROP TABLE IF EXISTS `admin`;
CREATE TABLE IF NOT EXISTS `admin` (
  `id` int NOT NULL AUTO_INCREMENT,
  `username` varchar(50) NOT NULL,
  `email` varchar(100) NOT NULL,
  `password_hash` varchar(255) NOT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`),
  UNIQUE KEY `email` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- --------------------------------------------------------

--
-- Structure de la table `departement`
--

DROP TABLE IF EXISTS `departement`;
CREATE TABLE IF NOT EXISTS `departement` (
  `id` int NOT NULL AUTO_INCREMENT,
  `nom` varchar(100) NOT NULL,
  `chef` varchar(100) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `nom` (`nom`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Déchargement des données de la table `departement`
--

INSERT INTO `departement` (`id`, `nom`, `chef`, `created_at`) VALUES
(1, 'Informatique', NULL, '2026-02-15 00:17:19');

-- --------------------------------------------------------

--
-- Structure de la table `etudiant`
--

DROP TABLE IF EXISTS `etudiant`;
CREATE TABLE IF NOT EXISTS `etudiant` (
  `id` int NOT NULL AUTO_INCREMENT,
  `departement_id` int NOT NULL,
  `nom` varchar(100) NOT NULL,
  `prenom` varchar(100) NOT NULL,
  `matricule` varchar(30) NOT NULL,
  `sexe` enum('M','F') NOT NULL,
  `telephone` varchar(20) DEFAULT NULL,
  `face_embedding` longblob,
  `annee_academique` varchar(20) DEFAULT NULL,
  `semestre` varchar(20) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `matricule` (`matricule`),
  KEY `idx_departement` (`departement_id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Déchargement des données de la table `etudiant`
--

INSERT INTO `etudiant` (`id`, `departement_id`, `nom`, `prenom`, `matricule`, `sexe`, `telephone`, `face_embedding`, `annee_academique`, `semestre`, `created_at`) VALUES
(1, 1, 'Moussa', 'Youssouf', '2024001', 'M', NULL, 0x000000600c23c5bf00000020bb4dc33f0000004069a2b63f00000000cbcf9d3f00000000a97da0bf0000004047b1a2bf00000000896894bf00000080f092babf0000006054abbc3f00000060ce2ba8bf000000e0c45ad13f000000600c8393bf00000080ddddc9bf00000000f3c6c7bf000000202a19b23f00000040ff46c43f000000e02bb0c1bf000000e0cc45b9bf00000040d24bbfbf000000006183bfbf000000c0f2a3b4bf00000080885f733f000000009227873f00000020060eb03f0000000022d97abf00000020a679d3bf000000802c62b0bf000000800f61cabf000000004f3bb83f0000008099ecbebf00000020b07da7bf000000a0aa7e57bf00000060406ac4bf0000002038a8a3bf0000004018b7a7bf000000800ffa793f00000000b8307e3f000000408a7973bf000000a062afc63f00000000bcfb65bf000000802147bdbf000000001662adbf000000a042f39fbf00000040489dd03f00000080ac68c63f0000000071d2953f00000080797e9f3f00000080135f9e3f00000060b024b73f000000c0b91ac4bf000000c0be2ca53f000000800e7cbb3f000000c06fc4c63f000000e06801a03f000000c0fa14a5bf00000000a65acabf00000060abf2adbf000000c0d5a7823f00000020e1d7c6bf000000609d1caa3f000000606515b23f00000000990dc0bf000000804706c8bf000000a05889a33f000000803421d23f0000008006c7bc3f000000009bf3c0bf000000804920c3bf000000c045c5c73f0000002086c9bcbf0000004023aaae3f000000204dd9b83f000000c03c8dc2bf000000c00b1ec1bf000000e05768c9bf00000000fa05c63f000000e0e33ad73f000000a0dffbac3f000000e06f88c7bf00000080b12ea9bf000000c089e0cabf000000808d715bbf000000404428b0bf000000c09909aa3f000000007e9cb8bf000000003e7550bf000000e0d630bebf00000080411b903f00000060624ab63f000000c09242afbf000000e0d0ca9b3f000000e098dacc3f0000000068cd4dbf000000c02a3c723f000000e08e21a9bf00000080bc7087bf00000020f1ca94bf00000000379c9fbf000000602325a0bf000000401335a4bf000000a0334db93f000000607ae7babf000000406efa8b3f000000402de6983f000000608d14c8bf000000e0390ec03f0000006001c8a43f000000c0c0ef9e3f00000040236b9a3f000000e0032b953f000000c063f9b6bf000000e097e0bbbf00000020659ac83f000000404c1fcabf00000020a824c73f000000c032f6c73f000000408590b43f000000806316c23f000000a06f3eaa3f000000805a25c03f0000000002fd76bf00000020efa3b0bf000000201c2abebf000000804469a5bf000000c03c61b43f0000006002498bbf00000080d94da3bf00000000003fa73f, NULL, NULL, '2026-02-15 00:25:14');

-- --------------------------------------------------------

--
-- Structure de la table `image`
--

DROP TABLE IF EXISTS `image`;
CREATE TABLE IF NOT EXISTS `image` (
  `id` int NOT NULL AUTO_INCREMENT,
  `etudiant_id` int NOT NULL,
  `image` longblob NOT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_image_etudiant` (`etudiant_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- --------------------------------------------------------

--
-- Structure de la table `presence`
--

DROP TABLE IF EXISTS `presence`;
CREATE TABLE IF NOT EXISTS `presence` (
  `id` int NOT NULL AUTO_INCREMENT,
  `etudiant_id` int NOT NULL,
  `date` date NOT NULL,
  `heure` time NOT NULL,
  `session` varchar(50) DEFAULT NULL,
  `statut` enum('Présent','Absent') DEFAULT 'Présent',
  PRIMARY KEY (`id`),
  KEY `idx_etudiant` (`etudiant_id`),
  KEY `idx_date` (`date`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Déchargement des données de la table `presence`
--

INSERT INTO `presence` (`id`, `etudiant_id`, `date`, `heure`, `session`, `statut`) VALUES
(1, 1, '2026-02-21', '15:15:01', 'Matin', 'Présent');

-- --------------------------------------------------------

--
-- Structure de la table `rapport`
--

DROP TABLE IF EXISTS `rapport`;
CREATE TABLE IF NOT EXISTS `rapport` (
  `id` int NOT NULL AUTO_INCREMENT,
  `admin_id` int NOT NULL,
  `mois` varchar(20) DEFAULT NULL,
  `nb_jours_ouvrables` int DEFAULT '0',
  `nb_jours_present` int DEFAULT '0',
  `nb_jours_absent` int DEFAULT '0',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_admin` (`admin_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Contraintes pour les tables déchargées
--

--
-- Contraintes pour la table `etudiant`
--
ALTER TABLE `etudiant`
  ADD CONSTRAINT `fk_etudiant_departement` FOREIGN KEY (`departement_id`) REFERENCES `departement` (`id`) ON DELETE CASCADE ON UPDATE CASCADE;

--
-- Contraintes pour la table `image`
--
ALTER TABLE `image`
  ADD CONSTRAINT `fk_image_etudiant` FOREIGN KEY (`etudiant_id`) REFERENCES `etudiant` (`id`) ON DELETE CASCADE ON UPDATE CASCADE;

--
-- Contraintes pour la table `presence`
--
ALTER TABLE `presence`
  ADD CONSTRAINT `fk_presence_etudiant` FOREIGN KEY (`etudiant_id`) REFERENCES `etudiant` (`id`) ON DELETE CASCADE ON UPDATE CASCADE;

--
-- Contraintes pour la table `rapport`
--
ALTER TABLE `rapport`
  ADD CONSTRAINT `fk_rapport_admin` FOREIGN KEY (`admin_id`) REFERENCES `admin` (`id`) ON DELETE CASCADE ON UPDATE CASCADE;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
