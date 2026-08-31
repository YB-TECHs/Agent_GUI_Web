# Agent GUI/Web avec RAG — YB-TECHs

Agent intelligent de collecte de données, capable de choisir automatiquement la bonne
méthode d'extraction (site web classique, document scanné, interface graphique native)
selon la source visée, et de répondre en langage naturel aux questions posées dessus.

Projet réalisé dans le cadre d'un stage M1 Data Science chez YB-TECHs.

## Fonctionnement en une phrase

Une cascade Selenium → OCR → OmniParser, où chaque couche n'intervient que si la
précédente est jugée insuffisante, orchestrée par un LLM local (Llama 3.2 via Ollama)
qui formule la réponse finale à partir des données réellement trouvées.

## Installation rapide

Voir [`docs/guide_installation.md`](docs/guide_installation.md) pour le détail complet.
En résumé :
```powershell
git clone <url-du-depot>
cd Projet1
python -m venv agent_pipe
.\agent_pipe\Scripts\Activate.ps1
pip install -r requirements.txt
ollama pull llama3.2
```

## Usage minimal

```python
from src.orchestrator_layer.pipeline_orchestre import pipeline_oriente

resultat = pipeline_oriente('https://exemple.com/', 'Quels sont les contacts ?')
print(resultat['reponse_finale'])
```

Ou via l'interface web :
```powershell
uvicorn src.api.app:app --reload
```
puis ouvrir `http://127.0.0.1:8000/`.

Voir [`docs/guide_utilisation.md`](docs/guide_utilisation.md) pour les autres modes
(discussion libre, extraction en chaîne par fichier Excel/JSON).

## Architecture

Voir [`docs/architecture.md`](docs/architecture.md).

## Tests

```powershell
python -m pytest tests/ -v --cov=src --cov-report=term-missing
```

## Structure du dépôt
src/
├── selenium_layer/ # Extraction DOM + images du DOM
├── ocr_layer/ # Lecture et classification OCR
├── omniparser_layer/ # Détection d'éléments d'interface (YOLO + Florence-2)
├── orchestrator_layer/ # Prompts, appels LLM, mémoire, cascade complète
├── cleaning/ # Nettoyage, déduplication, validation
├── storage/ # Export JSON/CSV/SQLite
├── reports/ # Génération de rapport HTML/PDF
└── api/ # Interface web FastAPI
tests/ # Suite pytest (unitaires + intégration)
docs/ # Documentation technique
scripts/ # Scripts d'exécution en lot
data/ # Données (gitignoré — voir ci-dessous)
weights/ # Poids OmniParser (gitignoré — voir docs/guide_installation.md)


## Auteure

NDJOKA NGHOKO Jodelle Baruch — Stage M1 Data Science, ENSPM INFOTEL, Université de Maroua.