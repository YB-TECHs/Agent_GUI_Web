# Guide d'installation

Ce guide permet de reproduire l'environnement complet du pipeline (Selenium / OCR /
OmniParser / orchestrateur LLM) en local, à partir d'un clone frais du dépôt Git.

Structure du projet une fois l'installation terminée :
```
Projet1/
├── data/                  (raw/, processed/, tests/ — générés ou fournis)
├── docs/                  (guides, architecture, rapport de stage)
├── drivers/               (chromedriver.exe si résolution manuelle nécessaire)
├── OmniParser/            ⚠️ dépôt tiers cloné séparément — absent du dépôt Git
│   └── weights/
│       ├── icon_detect/
│       └── icon_caption_florence/
├── scripts/
│   ├── executer_cas_usage.py
│   └── benchmark_kpis.py
├── src/
│   ├── api/                (interface web FastAPI)
│   ├── cleaning/
│   ├── ocr_layer/
│   ├── omniparser_layer/
│   ├── orchestrator_layer/
│   ├── reports/
│   ├── selenium_layer/
│   └── storage/
├── tests/
├── agent_pipe/             (venv — jamais commité)
├── agent_pipe_rag/         (venv — jamais commité)
├── requirements.txt
└── README.md
```

## 0. Vue d'ensemble

Cinq briques à mettre en place, dans cet ordre :
1. Environnement virtuel Python `agent_pipe` (via `requirements.txt`)
2. Ollama + le modèle LLM local (Llama 3.2)
3. Google Chrome (ChromeDriver est géré automatiquement par Selenium Manager)
4. Le dépôt tiers **OmniParser** (code + poids), cloné séparément à la racine du projet
5. *(optionnel, voir §4)* un fichier `.env` local

## 1. Prérequis

- **Windows** avec **Python 3.11.x** (⚠️ pas une version plus récente — voir Dépannage §10.1)
- **Git**
- **[Google Chrome](https://www.google.com/chrome/)** installé (mise à jour automatique activée — normal et pris en charge par Selenium Manager)
- **[Ollama](https://ollama.com)** installé

## 2. Récupération du projet

```powershell
git clone <URL_DU_DEPOT> Projet1
cd Projet1
```

## 3. Environnement virtuel Python

Un seul environnement est nécessaire pour faire tourner le pipeline actuel (la branche RAG,
non utilisée, dispose de son propre venv réservé pour une reprise future) :

```powershell
cd E:\NIVEAU4\Stage\Projet1

# agent_pipe : Selenium, OCR (EasyOCR), OmniParser, orchestrateur LLM, API web
python -m venv agent_pipe
.\agent_pipe\Scripts\Activate.ps1
pip install -r requirements.txt

# agent_pipe_rag : réservé à une reprise future de la branche RAG (ChromaDB, LangChain)
# — non utilisé par le pipeline actuel
python -m venv agent_pipe_rag
```

## 4. Fichier `.env` (réservé à une évolution future)

Aucun fichier `.env` n'existe encore dans le projet à ce jour — l'interface web ne persiste
pas encore ses données au-delà de la mémoire vive (voir `memoire_conversation.py`). Ce
fichier est prévu pour une évolution à venir, lorsque cette persistance sera implémentée.
Créez dès maintenant un `.env.example` à committer, pour documenter la convention même s'il
reste vide pour l'instant :

```env
# .env.example — copier en .env quand la persistance sera implémentée
# (aucune variable requise pour l'instant)
```

```powershell
copy .env.example .env
```

## 5. Ollama et le modèle LLM

```powershell
ollama pull llama3.2
ollama serve
```
Vérifiez que ça répond :
```powershell
ollama run llama3.2 "dis juste bonjour"
```
Ollama doit rester lancé (`ollama serve`, dans un terminal séparé) pendant toute utilisation
du pipeline — l'orchestrateur l'appelle via son API REST locale (`http://localhost:11434`).

## 6. Selenium / ChromeDriver

Aucune installation manuelle de ChromeDriver n'est nécessaire dans le cas général : Selenium
Manager (intégré à Selenium 4.6+) résout automatiquement la version correspondant à votre
Chrome installé, à chaque lancement. Ne pas fixer de chemin `executable_path` en dur dans
`navigator.py`.

Le dossier `drivers/` à la racine du projet contient un `chromedriver.exe` de secours,
utilisé en repli si Selenium Manager ne parvient pas à résoudre le driver automatiquement
(réseau bloqué — voir Dépannage §10.3).

## 7. OmniParser — code et poids (dépôt tiers, à cloner séparément)

Le `.gitignore` de ce projet exclut entièrement le dossier `OmniParser/` : ni son code, ni
ses poids ne sont sur ce dépôt Git (poids ≈ 4 Go). Il faut les récupérer indépendamment, à la
racine du projet, en tant que dossier frère de `src/`, `data/`, etc. :

```powershell
cd E:\NIVEAU4\Stage\Projet1
git clone https://github.com/microsoft/OmniParser.git
```

Puis téléchargez les poids YOLO + Florence-2, depuis l'intérieur du dossier `OmniParser/` :

```powershell
cd OmniParser
hf download microsoft/Florence-2-base --local-dir weights\icon_caption_florence --include "*.json" "*.txt"
hf download microsoft/Florence-2-base --local-dir weights\icon_caption_florence --include "*.py"
cd ..
```

⚠️ Les poids YOLO (`weights\icon_detect`) doivent également être présents — complétez la
commande de téléchargement correspondante si elle diffère de celle de Florence-2 ci-dessus.

## 8. Vérification de l'installation

```powershell
cd E:\NIVEAU4\Stage\Projet1
.\agent_pipe\Scripts\Activate.ps1
python -c "from src.orchestrator_layer.pipeline_orchestre import pipeline_oriente; print('Import OK')"
python -m pytest tests/ -v --cov=src --cov-report=term-missing
```

Une installation correcte doit afficher `Import OK` puis faire passer l'essentiel de la
suite de tests. Certains tests nécessitent un vrai Chrome et/ou Ollama démarré (§5 et §6) —
ils sont marqués comme tels dans les fichiers `tests/test_*.py`.

## 9. Lancer le pipeline

**Traiter un cas d'usage ponctuel** (produit des fichiers JSON/CSV/SQLite dans
`data/processed/` + un rapport PDF) :
```powershell
python scripts\executer_cas_usage.py
```

**Mesurer les indicateurs de performance (KPI)** :
```powershell
python scripts\benchmark_kpis.py
```

**Lancer l'interface web** (FastAPI, avec rechargement automatique en développement) :
```powershell
uvicorn src.api.app:app --reload
```
puis ouvrir `http://127.0.0.1:8000` dans un navigateur. Trois routes principales sont
disponibles :
- `POST /analyser` — analyse une URL + question (ou bascule en mode discussion si l'URL est vide)
- `POST /api/traiter-chaine` — extraction en chaîne à partir d'un fichier `.xlsx`/`.json` uploadé, retourne un rapport PDF
- `GET /historique` — historique de conversation (100 derniers messages)

## 10. Dépannage

Difficultés réellement rencontrées lors du développement — utiles si elles se reproduisent
sur une autre machine.

### 10.1 Python trop récent (ex. 3.14) incompatible avec l'écosystème IA
`numpy`/`torch` peuvent ne pas avoir de wheel précompilé pour une version Python trop
récente, ce qui déclenche une tentative de compilation depuis les sources (échoue sans
compilateur C). **Solution** : recréer le venv sous Python 3.11.x.

### 10.2 `ImportError: flash_attn` au chargement de Florence-2
`transformers` détecte la mention de `flash_attn` dans le code de Florence-2 et exige le
paquet, même s'il n'est jamais réellement appelé sur CPU. `flash_attn` ne s'installe pas sur
Windows sans GPU CUDA. **Solution** : créer un module factice (stub) qui expose les mêmes
noms de fonctions que `flash_attn`, avec des implémentations vides, pour satisfaire le
contrôle d'import statique sans que le code ne soit réellement exécuté.

### 10.3 Erreurs réseau en cascade vers `googlechromelabs.github.io`
Si ce domaine est bloqué par le réseau local (pare-feu, proxy, restriction régionale), trois
symptômes distincts peuvent apparaître l'un après l'autre :
- `ConnectionError` au chargement de Florence-2 → définir les variables d'environnement
  `HF_HUB_OFFLINE=1` et `TRANSFORMERS_OFFLINE=1` une fois les poids déjà téléchargés localement.
- `ConnectionResetError` / `NoSuchDriverException` à la création du driver Chrome →
  utiliser le `chromedriver.exe` déjà fourni sous `drivers/`, référencé explicitement dans
  `navigator.py`, plutôt que de laisser Selenium Manager le résoudre automatiquement.

### 10.4 `TimeoutException` intermittente sur Selenium
Peut avoir des causes externes non reproductibles (site cible temporairement indisponible,
latence réseau). Un mécanisme de réessai automatique (deux tentatives sur une session Chrome
fraîche) est déjà intégré au pipeline. Si le problème persiste, vérifiez d'abord
l'accessibilité du site cible indépendamment de Selenium (simple requête HTTP).

## 11. Récapitulatif — commandes essentielles

```powershell
# Activer l'environnement
.\agent_pipe\Scripts\Activate.ps1

# Démarrer Ollama (dans un terminal séparé, à laisser ouvert)
ollama serve

# Vérifier l'installation
python -m pytest tests/ -v --cov=src

# Lancer un cas d'usage
python scripts\executer_cas_usage.py

# Mesurer les KPI
python scripts\benchmark_kpis.py

# Lancer l'interface web
uvicorn src.api.app:app --reload
```

---

## Dernier point à confirmer

**Poids YOLO** (`OmniParser\weights\icon_detect`) — la commande de téléchargement de
Florence-2 est confirmée (§7), mais celle des poids YOLO (`icon_detect`) reste à préciser :
dépôt HuggingFace dédié, ou fichier fourni directement dans le dépôt `microsoft/OmniParser`
cloné à l'étape 7 ? Complétez la commande correspondante dans cette section une fois
vérifié.