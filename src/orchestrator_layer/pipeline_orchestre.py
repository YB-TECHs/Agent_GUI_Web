# src/orchestrator_layer/pipeline_orchestre.py
import logging
from datetime import datetime
 
from src.omniparser_layer.pipeline_omni import pipeline_tri_couche
from src.orchestrator_layer.llm_classifier import classifier_requete
 
logger = logging.getLogger(__name__)
 
 
def pipeline_oriente(url: str, question: str) -> dict:
    """
    Pipeline orchestré : le LLM prédit la couche avant extraction,
    le pipeline tri-couche (S2 à S4) exécute l'extraction réelle,
    puis les deux résultats sont comparés.
    """
    prediction = classifier_requete(question, url)
 
    resultat = pipeline_tri_couche(url, question)
 
    concordance = prediction['type_interface'] == resultat['source']
    resultat['prediction_llm'] = prediction
    resultat['concordance'] = concordance
    resultat['timestamp_orchestrateur'] = datetime.now().isoformat()
 
    logger.info(f"Prédit={prediction['type_interface']} "
                f"Réel={resultat['source']} Concordance={concordance}")
    return resultat
