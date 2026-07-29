# tests/test_orchestrator.py
import json
import pytest
 
from src.orchestrator_layer.llm_classifier import classifier_requete, PREDICTION_PAR_DEFAUT
from src.orchestrator_layer.pipeline_orchestre import pipeline_oriente
 
 
# ── TEST 1 : le classifieur retourne toujours un type valide ──────
def test_classifier_retourne_type_valide():
    pred = classifier_requete('Extrais les contacts', 'https://yb-techs.eu/')
    assert pred['type_interface'] in ('selenium', 'ocr', 'omniparser')
 
 
# ── TEST 2 : repli si Ollama est injoignable ───────────────────────
def test_classifier_fallback_si_llm_indisponible(monkeypatch):
    def echoue(*args, **kwargs):
        raise ConnectionError('Ollama arrêté')
    monkeypatch.setattr('src.orchestrator_layer.llm_classifier.appeler_llm', echoue)
    pred = classifier_requete('test', 'https://yb-techs.eu/')
    assert pred == PREDICTION_PAR_DEFAUT
 
 
# ── TEST 3 : le pipeline orchestré renvoie prediction + concordance ─
def test_pipeline_oriente_structure():
    res = pipeline_oriente('https://yb-techs.eu/', 'contacts')
    assert 'prediction_llm' in res
    assert 'concordance' in res
    assert isinstance(res['concordance'], bool)
 
 
# ── TEST 4 : précision de routage sur les 30 cas > 85 % ────────────
def test_precision_routage_30_cas():
    with open('data/tests/cas_routage.json', encoding='utf-8') as f:
        cas = json.load(f)
    corrects = 0
    for c in cas:
        pred = classifier_requete(c['question'], c['url'])
        if pred['type_interface'] == c['attendu']:
            corrects += 1
    precision = corrects / len(cas)
    print(f'Précision routage : {precision:.0%} ({corrects}/{len(cas)})')
    assert precision > 0.85
