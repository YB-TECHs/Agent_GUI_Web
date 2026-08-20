# src/cleaning/nettoyeur.py
import re
from datetime import datetime
 
import pandas as pd
 
CLES_TECHNIQUES = {'meta', 'source', 'prediction_llm', 'concordance', 'timestamp_orchestrateur',
                    'trajectoires_similaires', 'exemples_few_shot', 'score_qualite'}
 
 
def aplatir_resultat(resultat: dict) -> list[dict]:
    """
    Transforme le dict imbriqué retourné par le pipeline (même principe que
    la cellule de sauvegarde CSV du notebook S2) en lignes categorie/cle/valeur.
    Fonctionne quelle que soit la couche d'origine (selenium/ocr/omniparser).
    """
    lignes = []
    for categorie, contenu in resultat.items():
        if categorie in CLES_TECHNIQUES:
            continue
        if isinstance(contenu, list):
            for item in contenu:
                lignes.append({'categorie': categorie.upper(), 'cle': 'item', 'valeur': str(item)})
        elif isinstance(contenu, dict):
            for cle, valeur in contenu.items():
                lignes.append({'categorie': categorie.upper(), 'cle': cle, 'valeur': str(valeur)})
        else:
            lignes.append({'categorie': categorie.upper(), 'cle': 'valeur', 'valeur': str(contenu)})
    return lignes
 
 
def typer_valeur(valeur: str):
    """Convertit une chaîne en date, nombre, ou la laisse telle quelle."""
    valeur = valeur.strip()
    for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%Y-%m-%dT%H:%M:%S'):
        try:
            return datetime.strptime(valeur, fmt)
        except ValueError:
            pass
    if re.fullmatch(r'-?\d+([.,]\d+)?', valeur):
        return float(valeur.replace(',', '.'))
    return valeur
 
 
def nettoyer(resultat: dict) -> pd.DataFrame:
    """Pipeline complet : aplatissement → déduplication → typage."""
    lignes = aplatir_resultat(resultat)
    df = pd.DataFrame(lignes, columns=['categorie', 'cle', 'valeur'])
    if df.empty:
        return df
    df = df.drop_duplicates(subset=['categorie', 'cle', 'valeur']).reset_index(drop=True)
    df['valeur_typee'] = df['valeur'].apply(typer_valeur)
    return df
