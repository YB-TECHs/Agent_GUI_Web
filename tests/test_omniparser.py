# tests/test_omniparser.py
import pytest, sys, os
sys.path.insert(0, r'E:\NIVEAU4\Stage\Projet1')
 
from src.omniparser_layer.omni_extractor import (
    classifier_elements_ui, _detecter_lieux,
    _extraire_titres, _detecter_reseaux
)
from src.omniparser_layer.pipeline_omni import pipeline_tri_couche
 
IMG = 'tests/fixtures/ocr/screenshot_ybtechs.png'
 
 
# ── TEST 1 : classifier_elements_ui retourne un dict ──────────
def test_classifier_retourne_dict():
    elements = [{'texte': 'Contactez-nous', 'index': 1, 'coordonnees': [0,0,100,50]}]
    result   = classifier_elements_ui(elements)
    assert isinstance(result, dict)
    assert 'IDENTITE' in result
    assert 'CONTACTS_EMAIL' in result
 
 
# ── TEST 2 : détection email dans éléments UI ─────────────────
def test_detection_email():
    elements = [{'texte': 'Email : contact@yb-techs.eu', 'index': 1, 'coordonnees': []}]
    result   = classifier_elements_ui(elements)
    assert len(result['CONTACTS_EMAIL']) > 0
 
 
# ── TEST 3 : détection réseau social ──────────────────────────
def test_detection_reseau():
    reseaux = _detecter_reseaux('Suivez-nous sur linkedin et facebook')
    assert 'linkedin' in reseaux
    assert 'facebook' in reseaux
 
 
# ── TEST 4 : extraction titres ────────────────────────────────
def test_extraction_titres():
    elements = [
        {'texte': 'YB-TECHs — IA pour les PMEs', 'index': 1, 'coordonnees': []},
        {'texte': 'x', 'index': 2, 'coordonnees': []},  # Trop court → ignoré
    ]
    titres = _extraire_titres(elements)
    assert 'YB-TECHs — IA pour les PMEs' in titres
 
 
# ── TEST 5 : pipeline retourne dict avec clé source ───────────
def test_pipeline_tri_couche_ybtechs():
    res = pipeline_tri_couche('https://yb-techs.eu/', 'contacts')
    assert isinstance(res, dict)
    assert 'source'    in res
    assert 'resultats' in res
    assert res['source'] in ['selenium', 'ocr', 'omniparser']
 
 
# ── TEST 6 : source = selenium pour yb-techs.eu ───────────────
def test_source_selenium_pour_ybtechs():
    res = pipeline_tri_couche('https://yb-techs.eu/', 'contacts')
    assert res['source'] == 'selenium'
