# src/ocr_layer/ocr_engine.py
import easyocr
import pytesseract
from PIL import Image
import numpy as np
import logging
from src.ocr_layer.security import valider_fichier, masquer_donnees
from src.ocr_layer.preprocessor import ameliorer_image
 
logger  = logging.getLogger(__name__)
_reader = None  # Instance EasyOCR chargée une seule fois
 
 
def _get_reader():
    """Charge EasyOCR une seule fois (chargement lent ~10s)."""
    global _reader
    if _reader is None:
        logger.info('Chargement EasyOCR (fr + en)...')
        _reader = easyocr.Reader(['fr', 'en'], gpu=False)
        logger.info('EasyOCR prêt.')
    return _reader
 
 
def lire_image(chemin: str, preprocessing: bool = True) -> dict:
    """
    Extrait le texte d'une image avec EasyOCR (+ fallback Tesseract).
    Args:
        chemin       : chemin vers l'image
        preprocessing: si True, améliore l'image avant OCR
    Returns:
        dict avec 'texte', 'moteur', 'confiance', 'nb_mots'
    """
    valider_fichier(chemin)  # Sécurité : validation avant tout traitement
 
    img = ameliorer_image(chemin) if preprocessing else None
 
    # ── Tentative EasyOCR ────────────────────────────────────
    try:
        reader     = _get_reader()
        img_source = img if img is not None else chemin
        resultats  = reader.readtext(img_source, detail=1)
 
        texte      = ' '.join([r[1] for r in resultats])
        confiance  = round(sum([r[2] for r in resultats]) / max(len(resultats), 1), 2)
 
        if len(texte.strip()) > 20:
            logger.info(f'EasyOCR : {len(texte)} caractères, confiance {confiance}')
            return {
                'texte'    : masquer_donnees(texte),
                'moteur'   : 'easyocr',
                'confiance': confiance,
                'nb_mots'  : len(texte.split()),
            }
    except Exception as e:
        logger.warning(f'EasyOCR échoué : {e}')
 
    # ── Fallback Tesseract ────────────────────────────────────
    logger.info('Fallback : Tesseract...')
    try:
        img_pil = Image.fromarray(img) if img is not None else Image.open(chemin)
        texte   = pytesseract.image_to_string(img_pil, lang='fra+eng')
        return {
            'texte'    : masquer_donnees(texte),
            'moteur'   : 'tesseract',
            'confiance': None,
            'nb_mots'  : len(texte.split()),
        }
    except Exception as e:
        logger.error(f'Tesseract échoué : {e}')
        return {'texte': '', 'moteur': 'aucun', 'confiance': 0, 'nb_mots': 0}

