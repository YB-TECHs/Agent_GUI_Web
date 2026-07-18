# tests/test_ocr.py
import pytest, sys, os
sys.path.insert(0, r'E:\NIVEAU4\Stage\Projet1')
 
from src.ocr_layer.security import valider_fichier, masquer_donnees
from src.ocr_layer.preprocessor import ameliorer_image
from src.ocr_layer.ocr_engine import lire_image
from src.ocr_layer.pipeline_ocr import classifier_texte
import numpy as np
 
# ── Chemin vers les fixtures ──────────────────────────────────
FIXTURE = 'tests/fixtures/ocr'
IMG     = os.path.join(FIXTURE, 'IMG1.png')
 
 
# ── TEST 1 : fichier valide ───────────────────────────────────
def test_valider_fichier_ok():
    """Un fichier PNG existant et < 20Mo doit être validé."""
    assert os.path.isfile(IMG), f'Image de test manquante : {IMG}'
    assert valider_fichier(IMG) is True
 
 
# ── TEST 2 : mauvaise extension ──────────────────────────────
def test_valider_fichier_extension_interdite():
    """Un fichier .exe doit lever ValueError."""
    with pytest.raises((ValueError, FileNotFoundError)):
        valider_fichier('tests/fixtures/ocr/fake.exe')
 
 
# ── TEST 3 : masquage email ───────────────────────────────────
def test_masquer_email():
    """Les emails doivent être remplacés par [EMAIL]."""
    texte   = 'Contactez contact@yb-techs.eu pour plus d\'infos'
    masque  = masquer_donnees(texte)
    assert '[EMAIL]' in masque
    assert 'contact@yb-techs.eu' not in masque
 
 
# ── TEST 4 : masquage téléphone ──────────────────────────────
def test_masquer_telephone():
    """Les téléphones doivent être remplacés par [TEL]."""
    texte  = 'Appelez-nous au +33 6 12 34 56 78'
    masque = masquer_donnees(texte)
    assert '[TEL]' in masque
 
 
# ── TEST 5 : preprocessing retourne un ndarray ───────────────
def test_preprocessing():
    """L'image améliorée doit être un tableau numpy."""
    img = ameliorer_image(IMG)
    assert isinstance(img, np.ndarray)
    assert img.ndim == 2  # niveaux de gris = 2 dimensions
 
 
# ── TEST 6 : OCR retourne un dict avec texte ─────────────────
def test_ocr_retourne_texte():
    """lire_image doit retourner un dict avec clé texte non vide."""
    resultat = lire_image(IMG)
    assert isinstance(resultat, dict)
    assert 'texte'  in resultat
    assert 'moteur' in resultat
    assert len(resultat['texte']) > 0
 
 
# ── TEST 7 : classification aveugle ──────────────────────────
def test_classifier_texte():
    """classifier_texte doit retourner un dict avec les 5 catégories."""
    texte = 'Contactez info@yb-techs.eu à Caen, Normandie, France'
    cats  = classifier_texte(texte)
    assert 'CONTACTS_EMAIL' in cats
    assert 'LOCALISATION'   in cats
    assert 'info@yb-techs.eu' in cats['CONTACTS_EMAIL'] or cats['CONTACTS_EMAIL'] == ['[EMAIL]']
