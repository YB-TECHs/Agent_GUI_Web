# src/orchestrator_layer/prompt_templates.py
import json

PROMPT_CLASSIFICATION = """Tu es un orchestrateur technique qui choisit la meilleure méthode d'extraction de données pour une requête utilisateur.

Requête utilisateur : {requete}
Source ciblée : {url}

Trois méthodes disponibles :
- selenium : la page est un site web standard avec du texte HTML accessible
- ocr : la source est une image, un PDF scanné ou une capture d'écran texte
- omniparser : la source est une interface graphique native

Réponds UNIQUEMENT avec un objet JSON valide, sans texte autour, au format :
{{"type_interface": "selenium|ocr|omniparser", "confiance": 0.0 à 1.0,
"justification": "une phrase courte", "prompt_extraction": "instruction
précise pour guider l'extraction"}}
"""

PROMPT_FORMULATION = """Tu es un assistant qui répond à des questions en te basant uniquement sur des données déjà extraites automatiquement d'une page web, fournies ci-dessous. Ces données sont toujours complètes : ne demande jamais qu'on te les fournisse, même si elles semblent courtes ou vides.

Les données sont organisées par catégorie technique (IDENTITE, CONTACTS_EMAIL, INFORMATIONS, RESEAUX_SOCIAUX...) pour t'aider à comprendre leur nature. Ne mentionne jamais ces noms de catégorie dans ta réponse — seulement leur contenu.

Comment répondre :
- Réponds directement à la question posée, ni plus ni moins.
- Si la question porte sur une information précise (un lien, un email, un texte exact...), donne cette valeur exactement telle qu'elle apparaît dans les données, sans la traduire ni la modifier.
- Si la question porte sur une compréhension globale (résumé, sujet, thème...), réponds en la langue de la question en 1 à 2 phrases simples, en synthétisant le sens des données même si elles sont dans une autre langue.
- Si l'information demandée n'est pas présente dans les données, réponds exactement : "Aucune information pertinente n'a été trouvée."
- Ne pose aucune question, ne demande aucune précision, ne commente pas ta démarche.

Exemples :

Données extraites :
IDENTITE: ['Bonjour', 'Contact', 'À propos', 'Services']
Question : Quel texte y a-t-il sur cette page ?
Réponse : Le texte trouvé est : Bonjour, Contact, À propos, Services.

Données extraites :
RESEAUX_SOCIAUX: {{'linkedin': 'https://linkedin.com/company/x', 'facebook': 'https://facebook.com/x'}}
Question : Quel est le lien Facebook ?
Réponse : Le lien Facebook est : https://facebook.com/x.

Données extraites :
RESEAUX_SOCIAUX: {{'linkedin': 'https://linkedin.com/company/x'}}
Question : Quel est le lien Twitter ?
Réponse : Aucune information pertinente n'a été trouvée.

Données extraites :
IDENTITE: ['Willkommen bei TechCorp', 'Über uns']
INFORMATIONS: ['Wir bieten Cloud-Lösungen für Unternehmen jeder Größe.']
Question : De quoi parle ce site ?
Réponse : Ce site présente une entreprise (TechCorp) qui propose des solutions cloud pour les entreprises.

À toi maintenant :
Données extraites :
{resultats}

Question : {question}
Réponse :"""


PROMPT_CORRECTION_OCR = """Le texte suivant vient d'une lecture OCR imparfaite d'une image. Corrige UNIQUEMENT les erreurs de caractères évidentes (lettres confondues, mots coupés), en te basant sur le contexte et la probabilité — par exemple, '@onlact' est probablement 'Contact'.

RÈGLES STRICTES :
- N'interprète rien! Dit juste ce que tu vois dans les valeurs des résultats d'extraction
- Ne remplace JAMAIS un mot par une phrase ou un paragraphe entier.
- N'invente AUCUN mot, nom, contexte ou situation absent du texte brut.
- Le texte corrigé doit rester approximativement de la même longueur que le texte brut.
- Si un mot est vraiment illisible ou trop court pour être deviné, laisse-le tel quel.
- Ne t'excuse jamais, ne dis jamais que la correction est impossible.

Réponds uniquement avec le texte corrigé, rien d'autre.

Texte brut ({longueur} caractères) : {texte_ocr}

Texte corrigé (longueur similaire, pas de phrase inventée) :"""


def construire_prompt_classification(requete: str, url: str) -> str:
    return PROMPT_CLASSIFICATION.format(requete=requete, url=url)


def _formater_resultats_pour_prompt(resultats, max_caracteres: int = 1200) -> str:
    """
    Formate resultats en texte structuré (categorie: valeurs) — donne au
    modèle le contexte sémantique de chaque donnée (ex. IDENTITE = titre),
    plutôt qu'une liste plate sans repère.
    """
    if not isinstance(resultats, dict):
        texte = str(resultats)
        return texte[:max_caracteres] + (" [...tronqué]" if len(texte) > max_caracteres else "")

    lignes = []
    images = resultats.get('IMAGES_DETECTEES')

    for categorie, valeur in resultats.items():
        if categorie == 'IMAGES_DETECTEES' or not valeur:
            continue
        lignes.append(f"{categorie}: {valeur}")

    if images:
        lignes.append("Éléments détectés dans des images de la page :")
        for i, img in enumerate(images, 1):
            lignes.append(f"Image {i} : {img['contenu']}")

    texte = "\n".join(lignes)
    return texte[:max_caracteres] + (" [...tronqué]" if len(texte) > max_caracteres else "")


def construire_prompt_formulation(resultats, question: str) -> str:
    texte_resultats = _formater_resultats_pour_prompt(resultats)
    return PROMPT_FORMULATION.format(resultats=texte_resultats, question=question)


def construire_prompt_correction_ocr(texte_ocr: str) -> str:
    return PROMPT_CORRECTION_OCR.format(texte_ocr=texte_ocr[:1500], longueur=len(texte_ocr))
