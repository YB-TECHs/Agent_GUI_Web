# src/ocr_layer/security.py
import os, re
import logging
 
logger = logging.getLogger(__name__)
 
EXTENSIONS_OK  = {'.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.pdf'}
TAILLE_MAX     = 20 * 1024 * 1024  # 20 Mo
 
 
def valider_fichier(chemin: str) -> bool:
    """
    Valide un fichier image avant traitement OCR.
    Lève ValueError si le fichier est invalide.
    """
    if not os.path.isfile(chemin):
        raise FileNotFoundError(f'Fichier introuvable : {chemin}')
 
    ext = os.path.splitext(chemin)[1].lower()
    if ext not in EXTENSIONS_OK:
        raise ValueError(f'Extension non autorisée : {ext}. Autorisées : {EXTENSIONS_OK}')
 
    taille = os.path.getsize(chemin)
    if taille > TAILLE_MAX:
        raise ValueError(f'Fichier trop volumineux : {taille} octets (max 20 Mo)')
 
    logger.info(f'Fichier validé : {chemin} ({taille} octets)')
    return True
 
 
def masquer_donnees(texte: str) -> str:
    """Masque les données personnelles dans le texte extrait par OCR."""
    # Masquer emails
    texte = re.sub(r'[\w.+\-]+@[\w\-]+\.[a-zA-Z]{2,}', '[EMAIL]', texte)
    # Masquer téléphones
    texte = re.sub(r'\+?\d[\d\s\-().]{7,15}\d', '[TEL]', texte)
    return texte
