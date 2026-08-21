# tests/test_cleaning.py
import pandas as pd
 
from src.cleaning.nettoyeur import aplatir_resultats, nettoyer, typer_valeur
from src.cleaning.regles_validation import valider_dataframe
 
 
def test_aplatir_lit_bien_resultats_imbrique():
    sortie = {
        'source': 'selenium', 'reponse_finale': 'Voici les contacts.',
        'erreur_llm': False,
        'resultats': {'CONTACTS_EMAIL': ['a@b.com'], 'RESEAUX_SOCIAUX': {'linkedin': 'https://...'}},
    }
    lignes = aplatir_resultats(sortie)
    categories = {l['categorie'] for l in lignes}
    assert 'CONTACTS_EMAIL' in categories
    assert 'META' in categories
 
 
def test_aplatir_gere_images_detectees():
    sortie = {
        'source': 'selenium',
        'resultats': {
            'IDENTITE': ['Accueil'],
            'IMAGES_DETECTEES': [
                {'url_image': 'https://exemple.test/logo.png',
                 'contenu': {'SERVICES_PRODUITS': ['Insert']}},
            ],
        },
    }
    lignes = aplatir_resultats(sortie)
    categories = {l['categorie'] for l in lignes}
    assert 'IMAGE_SERVICES_PRODUITS' in categories
 
 
def test_nettoyer_deduplique():
    sortie = {'source': 'selenium',
              'resultats': {'CONTACTS_EMAIL': ['a@b.com'], 'AUTRE': ['a@b.com']}}
    df = nettoyer(sortie)
    assert not df.duplicated(subset=['categorie', 'cle', 'valeur']).any()
 
 
def test_typer_valeur_detecte_les_nombres():
    assert isinstance(typer_valeur('42.5'), float)
    assert typer_valeur('Caen, France') == 'Caen, France'
 
 
def test_validation_filtre_par_categorie_pas_par_cle():
    df = pd.DataFrame([
        {'categorie': 'CONTACTS_EMAIL', 'cle': 'item', 'valeur': 'contact@yb-techs.eu'},
        {'categorie': 'CONTACTS_EMAIL', 'cle': 'item', 'valeur': 'pas-un-email'},
    ])
    rapport = valider_dataframe(df)
    assert rapport['CONTACTS_EMAIL']['valides'] == 1
    assert rapport['CONTACTS_EMAIL']['invalides'] == 1
