# src/orchestrator_layer/llm_classifier.py
import json
import logging
import time
import requests

from src.orchestrator_layer.prompt_templates import (
    construire_prompt_classification,
    construire_prompt_formulation,
    construire_prompt_correction_ocr,
)

logger = logging.getLogger(__name__)

OLLAMA_URL = 'http://localhost:11434/api/generate'
#MODELE = 'phi3:mini'
MODELE = 'llama3.2' 
TIMEOUT_S = 120

PREDICTION_PAR_DEFAUT = {
    'type_interface': 'selenium', 'confiance': 0.0,
    'justification': 'LLM indisponible', 'prompt_extraction': '',
}

MOTS_REFUS = ['regret', 'je ne peux pas', 'cannot', 'sans contexte',
              'contexte supplémentaire', "n'est pas possible", 'erreurs ocr',
              'impossible de']
FACTEUR_LONGUEUR_MAX = 3


def appeler_llm(prompt: str, num_predict: int = 120, stop: list | None = None,
                 tentatives: int = 2) -> str:
    """Appel Ollama borné, avec réessai en cas d'échec transitoire (502, timeout)."""
    options = {'temperature': 0.2, 'num_predict': num_predict, 'repeat_penalty': 1.3}
    if stop:
        options['stop'] = stop

    derniere_erreur = None
    for essai in range(tentatives):
        try:
            reponse = requests.post(
                OLLAMA_URL,
                json={'model': MODELE, 'prompt': prompt, 'stream': False, 'options': options},
                timeout=TIMEOUT_S,
            )
            reponse.raise_for_status()
            return reponse.json().get('response', '').strip()
        except Exception as e:
            derniere_erreur = e
            if essai < tentatives - 1:
                logger.warning(f"Appel Ollama échoué (essai {essai+1}/{tentatives}) : {e} — nouvel essai dans 3s")
                time.sleep(3)
    raise derniere_erreur


def classifier_requete(requete: str, url: str) -> dict:
    """Prédiction a priori — journalisée uniquement, ne pilote plus rien."""
    prompt = construire_prompt_classification(requete, url)
    try:
        brut = appeler_llm(prompt, num_predict=150)
        debut, fin = brut.find('{'), brut.rfind('}') + 1
        prediction = json.loads(brut[debut:fin])
        assert prediction['type_interface'] in ('selenium', 'ocr', 'omniparser')
        return prediction
    except Exception as e:
        logger.warning(f"Classification a priori impossible ({e})")
        return PREDICTION_PAR_DEFAUT


def resultats_non_vides(resultats: dict) -> bool:
    """Heuristique instantanée, sans LLM : au moins une catégorie contient une valeur."""
    return any(v for v in resultats.values())


def formuler_reponse(donnees, question: str) -> str | None:
    """Rédige une réponse courte (2 phrases max) à partir de données déjà jugées exploitables."""
    prompt = construire_prompt_formulation(donnees, question)
    try:
        #return appeler_llm(prompt, num_predict=100, stop=['\n\n', 'Question :', 'Question de'])
        return appeler_llm(prompt, num_predict=100, stop=['Question :'])
    except Exception as e:
        logger.warning(f"Formulation impossible ({e})")
        return None


def corriger_texte_ocr(texte_ocr: str) -> str | None:
    """
    Tente de comprendre/corriger un texte OCR bruité.
    Retourne le texte corrigé si llama y arrive vraiment, ou None si le
    texte reste incompréhensible — signal explicite pour cascader vers
    OmniParser.
    """
    prompt = construire_prompt_correction_ocr(texte_ocr)
    try:
        corrige = appeler_llm(prompt, num_predict=150)

        if not corrige.strip() or any(mot in corrige.lower() for mot in MOTS_REFUS):
            logger.warning("llama n'a pas compris le texte OCR (refus/évasif) → incompréhensible")
            return None

        if len(corrige) > len(texte_ocr) * FACTEUR_LONGUEUR_MAX + 20:
            logger.warning(
                f"Correction suspecte : {len(corrige)} caractères produits pour "
                f"{len(texte_ocr)} en entrée — probable invention → incompréhensible"
            )
            return None

        return corrige
    except Exception as e:
        logger.warning(f"Correction OCR impossible ({e}) → incompréhensible")
        return None