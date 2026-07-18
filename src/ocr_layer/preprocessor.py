# src/ocr_layer/preprocessor.py
import cv2
import numpy as np
import logging
 
logger = logging.getLogger(__name__)
 
 
def ameliorer_image(chemin_entree: str, chemin_sortie: str = None) -> np.ndarray:
    """
    Améliore une image pour l'OCR.
    Args:
        chemin_entree : chemin vers l'image originale
        chemin_sortie : si fourni, sauvegarde l'image améliorée
    Returns:
        Image améliorée sous forme de tableau numpy
    """
    img = cv2.imread(chemin_entree)
    if img is None:
        raise ValueError(f'Impossible de lire l\'image : {chemin_entree}')
 
    # Étape 1 — Conversion en niveaux de gris
    gris = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
 
    # Étape 2 — Débruitage (filtre gaussien léger)
    debruite = cv2.GaussianBlur(gris, (3, 3), 0)
 
    # Étape 3 — Binarisation adaptative (meilleure que le seuillage global)
    # Sépare le texte du fond même si l'éclairage est inégal
    binaire = cv2.adaptiveThreshold(
        debruite, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 11, 2
    )
 
    # Étape 4 — Dilatation légère pour reconnecter les caractères fragmentés
    kernel  = np.ones((1, 1), np.uint8)
    resultat = cv2.dilate(binaire, kernel, iterations=1)
 
    if chemin_sortie:
        cv2.imwrite(chemin_sortie, resultat)
        logger.info(f'Image améliorée sauvegardée : {chemin_sortie}')
 
    logger.info(f'Preprocessing terminé pour : {chemin_entree}')
    return resultat
