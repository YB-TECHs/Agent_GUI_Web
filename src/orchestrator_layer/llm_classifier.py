# src/orchestrator_layer/llm_classifier.py
import json
import logging
import requests

from src.orchestrator_layer.memoire_conversation import ajouter_message, obtenir_historique
from src.orchestrator_layer.prompt_templates import (
    construire_prompt_classification,
    construire_prompt_correction_ocr,
    construire_tour_discussion,
    construire_tour_utilisateur,
    SYSTEM_DISCUSSION,
    SYSTEM_FORMULATION,
)

logger = logging.getLogger(__name__)

OLLAMA_URL = 'http://localhost:11434/api/generate'
OLLAMA_CHAT_URL = 'http://localhost:11434/api/chat'
MODELE = 'llama3.2'
TIMEOUT_S = 120

PREDICTION_PAR_DEFAUT = {
    'type_interface': 'selenium', 'confiance': 0.0,
    'justification': 'LLM indisponible', 'prompt_extraction': '',
}

MOTS_REFUS = ['regret', 'je ne peux pas', 'cannot', 'sans contexte',
              'contexte supplémentaire', "n'est pas possible", 'erreurs ocr',
              'impossible de', 'veuillez fournir', 'je suis prêt',
              'pourriez-vous', 'pouvez-vous', 'merci de fournir']
FACTEUR_LONGUEUR_MAX = 3


def appeler_llm(prompt: str, num_predict: int = 120, stop: list | None = None,
                 tentatives: int = 2) -> str:
    """Appel Ollama /api/generate (sans mémoire) — utilisé pour classification et correction OCR."""
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
                proxies={'http': None, 'https': None},
            )
            reponse.raise_for_status()
            return reponse.json().get('response', '').strip()
        except Exception as e:
            derniere_erreur = e
            if essai < tentatives - 1:
                logger.warning(f"Appel Ollama échoué (essai {essai+1}/{tentatives}) : {e} — nouvel essai dans 3s")
                import time
                time.sleep(3)
    raise derniere_erreur


def appeler_llm_chat(messages: list[dict], num_predict: int = 180, tentatives: int = 2) -> str:
    """Appel Ollama /api/chat (avec mémoire) — utilisé pour formuler_reponse et repondre_discussion."""
    options = {'temperature': 0.2, 'num_predict': num_predict, 'repeat_penalty': 1.3}
    derniere_erreur = None
    for essai in range(tentatives):
        try:
            reponse = requests.post(
                OLLAMA_CHAT_URL,
                json={'model': MODELE, 'messages': messages, 'stream': False, 'options': options},
                timeout=TIMEOUT_S,
                proxies={'http': None, 'https': None},
            )
            reponse.raise_for_status()
            return reponse.json()['message']['content'].strip()
        except Exception as e:
            derniere_erreur = e
            if essai < tentatives - 1:
                logger.warning(f"Appel Ollama chat échoué (essai {essai+1}/{tentatives}) : {e} — nouvel essai dans 3s")
                import time
                time.sleep(3)
    raise derniere_erreur


def classifier_requete(requete: str, url: str) -> dict:
    """Prédiction a priori — journalisée uniquement, ne pilote aucun routage réel."""
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
    return any(v for v in resultats.values())


def formuler_reponse(resultats, question: str) -> str | None:
    """
    Formule une réponse à partir de données déjà jugées exploitables,
    avec mémoire des échanges précédents (jusqu'à 100 messages).
    """
    tour = construire_tour_utilisateur(resultats, question)
    messages = [{'role': 'system', 'content': SYSTEM_FORMULATION}, *obtenir_historique(), {'role': 'user', 'content': tour}]
    try:
        reponse = appeler_llm_chat(messages, num_predict=180)
        reponse = reponse.strip().strip('"').strip()
        if not reponse or any(p in reponse.lower() for p in MOTS_REFUS):
            logger.warning("Réponse rejetée (préambule parasite)")
            return None
        ajouter_message('user', tour)
        ajouter_message('assistant', reponse)
        return reponse
    except Exception as e:
        logger.warning(f"Formulation impossible ({e})")
        return None


def repondre_discussion(question: str) -> str | None:
    """
    Réponse en pure discussion (mode sans URL), avec la même mémoire
    partagée que le mode pipeline — Llama peut se référer à une analyse
    de site faite plus tôt dans la conversation.
    """
    tour = construire_tour_discussion(question)
    messages = [{'role': 'system', 'content': SYSTEM_DISCUSSION}, *obtenir_historique(), {'role': 'user', 'content': tour}]
    try:
        reponse = appeler_llm_chat(messages, num_predict=200)
        reponse = reponse.strip().strip('"').strip()
        if not reponse:
            return None
        ajouter_message('user', tour)
        ajouter_message('assistant', reponse)
        return reponse
    except Exception as e:
        logger.warning(f"Discussion impossible ({e})")
        return None


def corriger_texte_ocr(texte_ocr: str) -> str | None:
    """Corrige un texte OCR bruité. Retourne None si incompréhensible (refus ou invention détectée)."""
    prompt = construire_prompt_correction_ocr(texte_ocr)
    try:
        corrige = appeler_llm(prompt, num_predict=150)

        if not corrige.strip() or any(mot in corrige.lower() for mot in MOTS_REFUS):
            logger.warning("Phi-3/Llama n'a pas compris le texte OCR (refus/évasif) → incompréhensible")
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