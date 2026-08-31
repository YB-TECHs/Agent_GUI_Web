# Guide d'utilisation

## Option 1 — Notebook Python

```python
from src.orchestrator_layer.pipeline_orchestre import pipeline_oriente

resultat = pipeline_oriente('https://exemple.com/', 'Les contacts')

print(resultat['source'])          # quelle couche a répondu
print(resultat['reponse_finale'])  # réponse en langage naturel
print(resultat['erreur_llm'])      # True si le LLM n'a pas pu répondre (données brutes disponibles quand même)
print(resultat['resultats'])       # données brutes classées
```

## Option 2 — Interface web

```powershell
cd E:\NIVEAU4\Stage\Projet1
.\agent_pipe\Scripts\Activate.ps1
uvicorn src.api.app:app --reload
```
Ouvre `http://127.0.0.1:8000/` :
- **Analyse simple** : renseigne un lien et une question, ou laisse le lien vide pour
  une discussion libre avec Llama.
- **Historique** (bouton dans l'en-tête) : consulte les 100 derniers échanges de la session.
- **Extraction en chaîne** (bouton dans l'en-tête) : dépose un fichier `.xlsx` ou `.json`
  contenant une liste de couples `url`/`question` (formats illustrés sur la page elle-même),
  reçois en retour un PDF récapitulatif de tous les cas traités.

## Option 3 — Traitement par lot en script

```powershell
python scripts\executer_cas_usage.py
```
Lit `data/tests/cas_usage_ybtechs.json`, traite chaque cas, produit un fichier
JSON/CSV/SQLite par cas dans `data/processed/`, et un rapport PDF unique
(`data/processed/rapport_semaine7.pdf`).

## Interpréter une sortie

| Champ | Signification |
|---|---|
| `source` | Couche qui a effectivement répondu : `selenium`, `ocr`, `omniparser` ou `discussion` |
| `reponse_finale` | Réponse en français, prête à afficher — ou `None` si le LLM a échoué |
| `erreur_llm` | Si `True`, se référer à `resultats` (toujours fiable) plutôt qu'à `reponse_finale` |
| `concordance` | Indique si la prédiction a priori (`prediction_llm`) correspond à la couche réellement utilisée — indicateur informatif, ne pilote aucune décision |