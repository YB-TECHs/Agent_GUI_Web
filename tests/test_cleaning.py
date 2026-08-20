# tests/test_cleaning.py
import pandas as pd
 
from src.cleaning.nettoyeur import aplatir_resultat, nettoyer, typer_valeur
from src.cleaning.regles_validation import valider_dataframe
 
 
def test_aplatir_ignore_champs_techniques():
    resultat = {'contacts': {'emails': ['a@b.com']}, 'source': 'selenium', 'prediction_llm': {'type_interface': 'selenium'}}
    lignes = aplatir_resultat(resultat)
    categories = {l['categorie'] for l in lignes}
    assert 'SOURCE' not in categories
    assert 'PREDICTION_LLM' not in categories
 
 
def test_nettoyer_deduplique():
    resultat = {'contacts': {'emails': 'a@b.com'}, 'autre': {'emails': 'a@b.com'}}
    df = nettoyer(resultat)
    doublons = df.duplicated(subset=['categorie', 'cle', 'valeur'])
    assert not doublons.any()
 
 
def test_typer_valeur_detecte_les_nombres():
    assert isinstance(typer_valeur('42.5'), float)
    assert typer_valeur('Caen, France') == 'Caen, France'
 
 
def test_validation_emails():
    df = pd.DataFrame([
        {'categorie': 'CONTACTS', 'cle': 'emails', 'valeur': 'contact@yb-techs.eu'},
        {'categorie': 'CONTACTS', 'cle': 'emails', 'valeur': 'pas-un-email'},
    ])
    rapport = valider_dataframe(df)
    assert rapport['emails']['valides'] == 1
    assert rapport['emails']['invalides'] == 1
