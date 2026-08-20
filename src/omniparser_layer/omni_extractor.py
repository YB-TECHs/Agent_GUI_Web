# src/omniparser_layer/omni_extractor.py
import re
import logging
 
logger = logging.getLogger(__name__)
 

def classifier_elements_ui(elements: list[dict]) -> dict:
    texte_complet = ' '.join(el['texte'] for el in elements if el['texte'])
    boutons_menus = [el['texte'] for el in elements if el.get('interactif') and el['texte']][:8]
    textes_libres = [el['texte'] for el in elements if not el.get('interactif') and el['texte']]

    resultats = {
        'CONTACTS_EMAIL':
            list(set(re.findall(r'[\w.+-]+@[\w-]+\.[a-zA-Z]{2,}', texte_complet))),
        'CONTACTS_TEL':
            [t for t in set(re.findall(r'\+?\d[\d\s\-().]{7,15}\d', texte_complet))
             if 8 <= len(re.sub(r'\D', '', t)) <= 15][:5],
        'LOCALISATION': _detecter_lieux(texte_complet),
        'IDENTITE': [t for t in textes_libres if 3 < len(t) < 60][:8],
        'SERVICES_PRODUITS': boutons_menus,
        'RESEAUX_SOCIAUX': _detecter_reseaux(texte_complet),
        'INFORMATIONS': [t for t in textes_libres if 30 < len(t) < 200][:5],
    }
    logger.info(f'Classification UI : {sum(len(v) for v in resultats.values() if isinstance(v, list))} éléments classifiés')
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
