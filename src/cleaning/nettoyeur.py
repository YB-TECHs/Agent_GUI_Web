# src/cleaning/nettoyeur.py
import re
from datetime import datetime
 
import pandas as pd
 
CLES_META = ('reponse_finale', 'source', 'erreur_llm', 'question',
             'timestamp', 'confiance_ocr')
 
 
def aplatir_resultats(sortie: dict) -> list[dict]:
    """
    Transforme la sortie réelle de pipeline_oriente() en lignes
    categorie/cle/valeur. Les données extraites viennent de
    sortie['resultats'] ; les métadonnées utiles (reponse_finale,
    source...) sont ajoutées à part, sous categorie='META'.
    """
    lignes = []
    donnees = sortie.get('resultats', {})
 
    for categorie, contenu in donnees.items():
        if categorie == 'IMAGES_DETECTEES':
            for img in contenu:
                url_img = str(img.get('url_image', ''))[:60]
                for sous_categorie, valeurs in img.get('contenu', {}).items():
                    for v in valeurs:
                        lignes.append({
                            'categorie': f'IMAGE_{sous_categorie}',
                            'cle': url_img,
                            'valeur': str(v),
                        })
            continue
 
        if isinstance(contenu, list):
            for item in contenu:
                lignes.append({'categorie': categorie, 'cle': 'item', 'valeur': str(item)})
        elif isinstance(contenu, dict):
            for cle, valeur in contenu.items():
                lignes.append({'categorie': categorie, 'cle': cle, 'valeur': str(valeur)})
        elif contenu:
            lignes.append({'categorie': categorie, 'cle': 'valeur', 'valeur': str(contenu)})
 
    for cle in CLES_META:
        valeur = sortie.get(cle)
        if valeur not in (None, ''):
            lignes.append({'categorie': 'META', 'cle': cle, 'valeur': str(valeur)})
 
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
 
 
def nettoyer(sortie: dict) -> pd.DataFrame:
    """Pipeline complet : aplatissement de la vraie structure → déduplication → typage."""
    lignes = aplatir_resultats(sortie)
    df = pd.DataFrame(lignes, columns=['categorie', 'cle', 'valeur'])
    if df.empty:
        return df
    df = df.drop_duplicates(subset=['categorie', 'cle', 'valeur']).reset_index(drop=True)
    df['valeur_typee'] = df['valeur'].apply(typer_valeur)
    return df
