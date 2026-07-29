# src/orchestrator_layer/llm_classifier.py
import json
import logging
import requests
 
from src.orchestrator_layer.prompt_templates import construire_prompt_classification
 
logger = logging.getLogger(__name__)
 
OLLAMA_URL = 'http://localhost:11434/api/generate'
MODELE = 'phi3:mini'
TIMEOUT_S = 30
 
PREDICTION_PAR_DEFAUT = {
    'type_interface': 'selenium',
    'confiance': 0.0,
    'justification': 'LLM indisponible — repli sur routage heuristique',
    'prompt_extraction': '',
}
 
 
def appeler_llm(prompt: str) -> str:
    """Envoie un prompt à Phi-3 Mini via l'API Ollama et retourne le texte brut."""
    reponse = requests.post(
        OLLAMA_URL,
        json={'model': MODELE, 'prompt': prompt, 'stream': False,
              'options': {'temperature': 0.1}},
        timeout=TIMEOUT_S,
    )
    reponse.raise_for_status()
    return reponse.json().get('response', '')
 
 
def classifier_requete(requete: str, url: str) -> dict:
    """
    Demande au LLM de prédire la couche d'extraction et de générer
    un prompt d'extraction adapté. Retombe sur PREDICTION_PAR_DEFAUT
    en cas d'échec (timeout, JSON invalide, service Ollama arrêté).
    """
    prompt = construire_prompt_classification(requete, url)
    try:
        brut = appeler_llm(prompt)
        debut = brut.find('{')
        fin = brut.rfind('}') + 1
        prediction = json.loads(brut[debut:fin])
        assert prediction['type_interface'] in ('selenium', 'ocr', 'omniparser')
        logger.info(f"LLM → {prediction['type_interface']} "
                    f"(confiance {prediction.get('confiance', '?')})")
        return prediction
    except Exception as e:
        logger.warning(f'Classification LLM impossible ({e}) — repli heuristique')
        return PREDICTION_PAR_DEFAUT
