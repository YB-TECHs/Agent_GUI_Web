# src/omniparser_layer/omni_extractor.py
import re
import logging
 
logger = logging.getLogger(__name__)
 
 
def classifier_elements_ui(elements: list[dict]) -> dict:
    """
    Classe les éléments UI détectés par OmniParser
    dans les 7 catégories du pipeline aveugle.
    Args:
        elements : liste retournée par analyser_screenshot()
    Returns:
        dict avec les 7 catégories
    """
    texte_complet = ' '.join([el['texte'] for el in elements])
 
    resultats = {
        'CONTACTS_EMAIL'   : list(set(re.findall(r'[\w.+-]+@[\w-]+\.[a-zA-Z]{2,}', texte_complet))),
        'CONTACTS_TEL'     : list(set(re.findall(r'\+?\d[\d\s\-().]{7,15}\d', texte_complet)))[:5],
        'LOCALISATION'     : _detecter_lieux(texte_complet),
        'IDENTITE'         : _extraire_titres(elements),
        'SERVICES_PRODUITS': _extraire_boutons_menus(elements),
        'RESEAUX_SOCIAUX'  : _detecter_reseaux(texte_complet),
        'INFORMATIONS'     : [el['texte'] for el in elements if 30 < len(el['texte']) < 200][:5],
    }
    logger.info(f'Classification UI : {sum(len(v) for v in resultats.values())} éléments classifiés')
    return resultats
 
 
def _detecter_lieux(texte: str) -> list:
    mots_geo = re.findall(r'\b(?:rue|avenue|city|cedex|bp|\d{4,6})\b.{0,60}', texte.lower())
    return list(set(mots_geo))[:5]
 
 
def _extraire_titres(elements: list) -> list:
    # Les éléments courts (< 60 chars) sont souvent des titres ou labels
    return [el['texte'] for el in elements if 3 < len(el['texte']) < 60][:8]
 
 
def _extraire_boutons_menus(elements: list) -> list:
    # Boutons et menus : textes très courts (< 30 chars)
    mots_action = ['voir', 'contact', 'service', 'about', 'accueil', 'menu',
                   'lire', 'découvrir', 'en savoir', 'solutions', 'offres']
    return [el['texte'] for el in elements
            if any(m in el['texte'].lower() for m in mots_action)][:8]
 
 
def _detecter_reseaux(texte: str) -> dict:
    reseaux = {}
    for p in ['linkedin', 'facebook', 'github', 'twitter', 'instagram']:
        if p in texte.lower():
            reseaux[p] = f'Mentionné dans l\'interface'
    return reseaux
