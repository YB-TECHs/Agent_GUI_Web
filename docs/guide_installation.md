# Guide d'installation

## Prérequis

- Windows avec Python 3.11+
- Google Chrome installé (mis à jour automatiquement — c'est normal et pris en charge)
- [Ollama](https://ollama.com) installé et démarré

## 1. Environnements virtuels

Deux venv distincts, pour isoler les dépendances lourdes :

```powershell
cd E:\NIVEAU4\Stage\Projet1

# agent_pipe : Selenium, OCR (EasyOCR), OmniParser, orchestrateur LLM, API web
python -m venv agent_pipe
.\agent_pipe\Scripts\Activate.ps1
pip install selenium beautifulsoup4 lxml easyocr opencv-python torch pandas
pip install fastapi uvicorn python-multipart openpyxl requests
pip install pytest pytest-cov httpx

# agent_pipe_rag : réservé à une reprise future de la branche RAG (ChromaDB, LangChain)
# — non utilisé par le pipeline actuel (trajectoire sans RAG)
```

## 2. Ollama et le modèle LLM

```powershell
ollama pull llama3.2
ollama serve
```
Vérifie que ça répond :
```powershell
ollama run llama3.2 "dis juste bonjour"
```

## 3. Selenium / ChromeDriver

Aucune installation manuelle de ChromeDriver n'est nécessaire : Selenium Manager (intégré
à Selenium 4.6+) résout automatiquement la version correspondant à ton Chrome installé, à
chaque lancement. Ne pas fixer de chemin `executable_path` en dur dans `navigator.py`.

## 4. OmniParser (YOLO + Florence-2)

Les poids doivent être présents en local sous `weights/icon_detect` et
`weights/icon_caption_florence`, avec les fichiers de processeur complets
(`config.json`, `preprocessor_config.json`, `tokenizer.json`, `processing_florence2.py`).
En cas de fichier manquant :
```powershell
hf download microsoft/Florence-2-base --local-dir weights\icon_caption_florence --include "*.json" "*.txt"
hf download microsoft/Florence-2-base --local-dir weights\icon_caption_florence --include "*.py"
```

## 5. Vérification de l'installation

```powershell
cd E:\NIVEAU4\Stage\Projet1
.\agent_pipe\Scripts\Activate.ps1
python -c "from src.orchestrator_layer.pipeline_orchestre import pipeline_oriente; print('Import OK')"
python -m pytest tests/ -v --cov=src --cov-report=term-missing
```
Une installation correcte doit afficher `Import OK` puis faire passer l'essentiel de la
suite de tests (voir section précédente pour les tests nécessitant un vrai Chrome/Ollama).