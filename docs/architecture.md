# Architecture du pipeline

## Vue d'ensemble

Le système est une cascade à trois couches d'extraction (Selenium, OCR, OmniParser),
orchestrée par un LLM local (Llama 3.2 3B via Ollama). Chaque couche n'intervient que
si la précédente est jugée insuffisante — par une heuristique Python instantanée pour
le texte DOM, et après tentative de correction pour le texte OCR bruité.

Requête (URL + question)
│
▼
┌───────────────────┐
│ 1. Selenium │──── texte DOM suffisant ────► Formulation Llama ──► Réponse
│ (+ images du DOM │
│ via OmniParser │
│ si insuffisant) │
└─────────┬──────────┘
│ insuffisant
▼
┌───────────────────┐
│ 2. OCR │──── texte compris ──────────► Formulation Llama ──► Réponse
│ (EasyOCR + │ après correction
│ correction LLM) │
└─────────┬──────────┘
│ incompréhensible
▼
┌───────────────────┐
│ 3. OmniParser │──── dernier recours ─────────► Formulation Llama ──► Réponse
│ (YOLO + Florence-2)│ (toujours accepté)
└────────────────────┘


## Rôle de chaque module

| Module | Rôle |
|---|---|
| `src/selenium_layer/` | Navigation, extraction du DOM, détection et analyse des images du DOM |
| `src/ocr_layer/` | Lecture et classification du texte issu de la reconnaissance optique |
| `src/omniparser_layer/` | Détection et classification des éléments d'interface graphique |
| `src/orchestrator_layer/` | Prompts, appels LLM (classification, formulation, correction OCR, discussion), mémoire de conversation, cascade complète |
| `src/cleaning/` | Nettoyage, déduplication, typage, validation métier |
| `src/storage/` | Export JSON / CSV / SQLite |
| `src/reports/` | Génération de rapport de collecte HTML puis PDF |
| `src/api/` | Interface web FastAPI (analyse simple, mode discussion, extraction en chaîne) |

## Décisions techniques notables et leur justification

- **Modèle LLM : Llama 3.2 3B**, plutôt que Phi-3 Mini (choix initial). Changement décidé
  après plusieurs échecs répétés de Phi-3 Mini sur des tâches de formulation contrainte
  (citation fidèle, respect de règles de format) — voir Rapport Semaine 5, section
  "Diagnostic initial : le format de prompt lui-même".
- **Mémoire de conversation** : `/api/chat` d'Ollama plutôt que `/api/generate`, avec un
  historique glissant de 100 messages en mémoire (non persisté sur disque à ce jour).
  Partagée entre le mode pipeline et le mode discussion libre.
- **Décision de cascade** : une heuristique Python (`resultats_non_vides`), pas un jugement
  LLM. Un jugement LLM de suffisance a été testé et abandonné — trop lent et trop peu
  fiable sur un modèle de cette taille (voir Rapport Semaine 5, bug #13).
- **Génération PDF** : impression native Chrome (`Page.printToPDF` via CDP), pas WeasyPrint
  — conflit de DLL constaté avec Tesseract-OCR sous Windows (`libgobject-2.0-0.dll`).
- **Résolution ChromeDriver** : Selenium Manager (automatique), après un long diagnostic
  ayant d'abord suspecté un décalage de version, puis confirmé un TimeoutException
  intermittent d'origine différente — un mécanisme de réessai (`_naviguer_avec_retry`)
  a été retenu plutôt qu'une cause unique corrigible une fois pour toutes.
- **Communication Ollama** : proxy système désactivé explicitement (`proxies={'http': None,
  'https': None}`) — un proxy configuré au niveau de l'OS interceptait même les appels
  vers `localhost`, provoquant des `502 Bad Gateway` sans lien avec la charge machine.
- **Repli sur panne LLM** : à chaque étage, si l'appel LLM échoue, le pipeline renvoie les
  données brutes déjà extraites (`erreur_llm=True`) plutôt que de supposer un résultat.

## Structure de sortie de `pipeline_oriente()`

```python
{
    'question': str, 'url': str, 'source': 'selenium' | 'ocr' | 'omniparser' | 'discussion',
    'timestamp': str,
    'resultats': dict,          # données brutes classées, jamais réécrites par le LLM
    'reponse_finale': str | None,
    'erreur_llm': bool,
    'prediction_llm': dict,     # prédiction a priori, journalisée uniquement
    'concordance': bool,
    # présents uniquement si source == 'ocr' :
    'texte_ocr_brut': str, 'texte_ocr_corrige': str, 'confiance_ocr': float,
}
```

## Limites connues

- La mémoire de conversation est perdue au redémarrage du serveur (pas de persistance disque).
- La mémoire retient les échanges, pas les données brutes extraites : une question de suivi
  sans URL ne réutilise pas l'extraction précédente.
- L'extraction en chaîne ne bénéficie pas encore du mécanisme de réessai Selenium.
- Les KPI de précision OCR et d'IoU OmniParser (CDC section 8.3) n'ont pas été mesurés
  formellement, faute de données de référence annotées.