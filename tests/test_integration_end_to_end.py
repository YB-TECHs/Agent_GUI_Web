# tests/test_integration_end_to_end.py
import json
from pathlib import Path
 
import pytest
 
from src.orchestrator_layer.pipeline_orchestre import pipeline_oriente
from src.cleaning.nettoyeur import nettoyer
from src.cleaning.regles_validation import valider_dataframe
from src.storage.stockage import sauvegarder
from src.reports.generateur_rapport import generer_rapport_html
 
with open('data/tests/cas_usage_ybtechs.json', encoding='utf-8') as f:
    CAS_USAGE = json.load(f)
 
 
@pytest.mark.parametrize('cas', CAS_USAGE)
def test_chaine_complete(cas, tmp_path):
    sortie = pipeline_oriente(cas['url'], cas['question'])
    assert sortie['source'] in ('selenium', 'ocr', 'omniparser')
    assert 'resultats' in sortie
 
    df = nettoyer(sortie)
    assert 'IMAGE_' not in ''.join(df['categorie']) or 'IMAGES_DETECTEES' in sortie.get('resultats', {})
 
    validation = valider_dataframe(df)
    assert isinstance(validation, dict)
 
    chemins = sauvegarder(df, str(tmp_path / 'sortie'))
    assert Path(chemins['json']).exists()
 
    chemin_html = generer_rapport_html(
        source=cas['url'], df=df, validation=validation,
        chemin_sortie=str(tmp_path / 'rapport.html'),
    )
    assert Path(chemin_html).exists()
 
 
def test_repli_sans_echec_silencieux():
    """Sur une source difficile, le pipeline doit soit répondre, soit
    signaler erreur_llm=True — jamais planter ni renvoyer une réponse vide
    sans explication."""
    sortie = pipeline_oriente('https://yb-techs.eu/', 'Les contacts')
    assert sortie['reponse_finale'] is not None or sortie['erreur_llm'] is True
