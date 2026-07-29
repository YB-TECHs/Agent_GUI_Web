# src/orchestrator_layer/prompt_templates.py
 
PROMPT_CLASSIFICATION = """Tu es un orchestrateur technique qui choisit la
meilleure méthode d'extraction de données pour une requête utilisateur.
 
Requête utilisateur : {requete}
Source ciblée : {url}
 
Trois méthodes disponibles :
- selenium : la page est un site web standard avec du texte HTML accessible
- ocr : la source est une image, un PDF scanné ou une capture d'écran texte
- omniparser : la source est une interface graphique native (boutons, icônes,
  peu ou pas de texte lisible directement)
 
Réponds UNIQUEMENT avec un objet JSON valide, sans texte autour, au format :
{{"type_interface": "selenium|ocr|omniparser", "confiance": 0.0 à 1.0,
"justification": "une phrase courte", "prompt_extraction": "instruction
précise pour guider l'extraction"}}
"""
 
PROMPTS_EXTRACTION = {
    'selenium': "Extrais le texte structuré du DOM : titres, contacts, "
                "liens et sections principales.",
    'ocr': "Lis le texte visible sur l'image après débruitage et "
           "redressement de perspective.",
    'omniparser': "Identifie les éléments interactifs (boutons, champs, "
                  "icônes) et leur fonction sémantique.",
}
 
 
def construire_prompt_classification(requete: str, url: str) -> str:
    """Injecte la requête et l'URL dans le template de classification."""
    return PROMPT_CLASSIFICATION.format(requete=requete, url=url)

