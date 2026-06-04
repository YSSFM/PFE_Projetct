# services/anti_spoofing.py
# Détection de clignement des yeux (Eye Aspect Ratio - EAR)
# Utilisé pour éviter les attaques par photo

import cv2
import numpy as np
from scipy.spatial import distance as dist

def eye_aspect_ratio(eye):
    """
    Calcule l'Eye Aspect Ratio (EAR) pour un œil donné.
    Plus l'œil est ouvert, plus le EAR est grand.
    
    Args:
        eye: points de repère de l'œil (6 points)
        
    Returns:
        float: ratio d'aspect
    """
    # Distance verticale entre les paupières (points 1-5 et 2-4)
    A = dist.euclidean(eye[1], eye[5])
    B = dist.euclidean(eye[2], eye[4])
    
    # Distance horizontale entre les coins (points 0-3)
    C = dist.euclidean(eye[0], eye[3])
    
    # Calcul du EAR
    ear = (A + B) / (2.0 * C)
    return ear

class AntiSpoofingDetector:
    """
    Détecteur anti-spoofing basé sur le clignement des yeux.
    L'utilisateur doit cligner un certain nombre de fois pour être validé.
    """
    
    def __init__(self, ear_threshold=0.23, consec_frames_required=2, required_blinks=1):
        """
        Args:
            ear_threshold: seuil en dessous duquel on considère l'œil fermé
            consec_frames_required: nombre de frames consécutives nécessaires pour valider un clignement
            required_blinks: nombre de clignements requis
        """
        self.EYE_AR_THRESH = ear_threshold
        self.EYE_AR_CONSEC_FRAMES = consec_frames_required
        self.REQUIRED_BLINKS = required_blinks
        self.reset()
    
    def reset(self):
        """Réinitialise le compteur de clignements"""
        self.counter = 0          # Compteur de frames consécutives avec œil fermé
        self.total_blinks = 0     # Nombre total de clignements détectés
        self.validated = False    # Validation atteinte ?
        
    def process_eyes(self, left_eye, right_eye):
        """
        Traite les yeux détectés et met à jour l'état du clignement.
        
        Args:
            left_eye: points de repère de l'œil gauche
            right_eye: points de repère de l'œil droit
            
        Returns:
            tuple: (total_blinks, validated)
        """
        # Calcul des EAR pour les deux yeux
        left_ear = eye_aspect_ratio(left_eye)
        right_ear = eye_aspect_ratio(right_eye)
        ear = (left_ear + right_ear) / 2.0
        
        # Détection de clignement
        if ear < self.EYE_AR_THRESH:
            self.counter += 1
        else:
            # Si on vient de sortir d'une séquence de paupières fermées
            if self.counter >= self.EYE_AR_CONSEC_FRAMES:
                self.total_blinks += 1
                if self.total_blinks >= self.REQUIRED_BLINKS:
                    self.validated = True
            self.counter = 0
        
        return self.total_blinks, self.validated
    
    def get_status_message(self):
        """Retourne un message d'état pour l'affichage"""
        if self.validated:
            return f"✅ Authentifié - {self.total_blinks}/{self.REQUIRED_BLINKS} clignements"
        elif self.total_blinks > 0:
            return f"👁️ Clignements détectés : {self.total_blinks}/{self.REQUIRED_BLINKS}"
        else:
            return f"👀 Clignez des yeux pour vous authentifier (0/{self.REQUIRED_BLINKS})"
    
    def get_validation_text(self):
        """Texte à afficher pour demander le clignement"""
        if not self.validated:
            return f"👁️ Veuillez cligner {self.REQUIRED_BLINKS} fois"
        return "✅ Authentification réussie"