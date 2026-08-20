# tests/test_orchestrator.py
import pytest
 
from src.orchestrator_layer.llm_classifier import (
    classifier_requete, juger_resultat_selenium,
    traiter_resultat_ocr, formuler_reponse_omniparser,
)
from src.orchestrator_layer.pipeline_orchestre import pipeline_oriente
 
 
# ── TEST 1 : la prédiction a priori reste valide (inchangé depuis v1) ──
def test_classifier_retourne_type_valide():
    pred = classifier_requete('Extrais les contacts', 'https://yb-techs.eu/')
    assert pred['type_interface'] in ('selenium', 'ocr', 'omniparser')
 
 
# ── TEST 2 : jugement Selenium, cas 'suffisant' ─────────────────────
def test_juger_resultat_selenium_suffisant(monkeypatch):
    def faux_llm(prompt):
        return '{"suffisant": true, "reponse": "Voici les contacts."}'
    monkeypatch.setattr('src.orchestrator_layer.llm_classifier.appeler_llm', faux_llm)
    jugement = juger_resultat_selenium({'CONTACTS_EMAIL': ['a@b.com']}, 'contacts', 'https://test/')
    assert jugement == {'suffisant': True, 'reponse': 'Voici les contacts.'}
 
 
# ── TEST 3 : panne LLM → signal d'erreur, pas un faux 'insuffisant' ──
def test_juger_resultat_selenium_erreur_si_llm_indisponible(monkeypatch):
    def echoue(prompt):
        raise ConnectionError('Ollama arrêté')
    monkeypatch.setattr('src.orchestrator_layer.llm_classifier.appeler_llm', echoue)
    jugement = juger_resultat_selenium({}, 'test', 'https://test/')
    assert jugement == {'erreur': True}
 
 
# ── TEST 4 : traitement OCR corrige, juge et répond en un appel ─────
def test_traiter_resultat_ocr_suffisant(monkeypatch):
    def faux_llm(prompt):
        return ('{"texte_corrige": "contact@yb-techs.eu", "suffisant": true, '
                '"reponse": "Email : contact@yb-techs.eu"}')
    monkeypatch.setattr('src.orchestrator_layer.llm_classifier.appeler_llm', faux_llm)
    resultat = traiter_resultat_ocr('c0ntact@yb-t3chs.eu', 'email de contact')
    assert resultat['suffisant'] is True
    assert 'texte_corrige' in resultat
 
 
# ── TEST 5 : OmniParser ne juge jamais, formule toujours ────────────
def test_formuler_reponse_omniparser_toujours_une_reponse(monkeypatch):
    monkeypatch.setattr('src.orchestrator_layer.llm_classifier.appeler_llm',
                         lambda prompt: 'Réponse formulée à partir des icônes détectées.')
    resultat = formuler_reponse_omniparser({'IDENTITE': ['Accueil']}, 'que voit-on ?')
    assert 'reponse' in resultat
    assert resultat['reponse']
 
 
# ── TEST 6 : structure complète de pipeline_oriente() ───────────────
def test_pipeline_oriente_structure():
    resultat = pipeline_oriente('https://yb-techs.eu/', 'contacts')
    for cle in ('source', 'resultats', 'reponse_finale', 'erreur_llm',
                'prediction_llm', 'concordance'):
        assert cle in resultat
