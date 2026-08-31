# Guide d'installation

Ce guide permet de reproduire l'environnement complet du pipeline (Selenium / OCR /
OmniParser / orchestrateur LLM) en local, à partir d'un clone frais du dépôt Git.

> ⚠️ **Passages à confirmer avant de committer ce guide** : certains points (marqués ⚠️
> ci-dessous) reposent sur une hypothèse de structure de projet que je n'ai pas pu vérifier
> directement. Merci de les corriger si besoin avant de remplacer l'ancien guide — voir la
> liste récapitulative en fin de document.

## 0. Vue d'ensemble

L'installation comporte cinq briques à mettre en place, dans cet ordre :
1. Deux environnements virtuels Python (`agent_pipe`, `agent_pipe_rag`)
2. Ollama + le modèle LLM local (Llama 3.2)
3. Google Chrome (ChromeDriver est géré automatiquement par Selenium)
4. Le dépôt tiers **OmniParser** (code + poids), cloné séparément — il n'est pas dans ce dépôt Git
5. Un fichier `.env` local (jamais commité)

## 1. Prérequis

- **Windows** avec **Python 3.11.x** (⚠️ pas une version plus récente — voir Dépannage §10.1)
- **Git**
- **[Google Chrome](https://www.google.com/chrome/)** installé (mise à jour automatique activée — c'est normal et pris en charge par Selenium Manager)
- **[Ollama](https://ollama.com)** installé

## 2. Récupération du projet

```powershell
git clone <URL_DU_DEPOT> Projet1
cd Projet1
```

## 3. Environnements virtuels Python

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
python -m venv agent_pipe_rag
```

> 💡 **Recommandé** : une fois l'environnement `agent_pipe` stable, figez les versions
> exactes pour que tout le monde installe la même chose :
> ```powershell
> pip freeze > requirements.txt
> ```
> puis ajoutez `requirements.txt` au dépôt. Les prochaines installations se résument alors à
> `pip install -r requirements.txt`.

## 4. Fichier `.env`

Le module `security.py` (couche Selenium) lit des identifiants sensibles depuis un fichier
`.env` à la racine du projet — volontairement exclu du dépôt (`.gitignore`).

⚠️ **À confirmer** : quelles variables exactes `.env` doit-il contenir ? (identifiants de
connexion à un site cible ? clé d'API ? autre ?) En attendant, créez un fichier
`.env.example` à committer, qui documente les clés attendues sans leurs valeurs, par ex. :

```env
# .env.example — copier en .env et renseigner les valeurs réelles
# SITE_LOGIN=
# SITE_PASSWORD=
```

```powershell
copy .env.example .env
# puis éditer .env avec les vraies valeurs
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
Ollama doit rester lancé (`ollama serve`) pendant toute utilisation du pipeline — l'orchestrateur
l'appelle via son API REST locale (`http://localhost:11434`).

## 6. Selenium / ChromeDriver

Aucune installation manuelle de ChromeDriver n'est nécessaire : Selenium Manager (intégré
à Selenium 4.6+) résout automatiquement la version correspondant à votre Chrome installé, à
chaque lancement. Ne pas fixer de chemin `executable_path` en dur dans `navigator.py`.

> Si Selenium Manager échoue à résoudre le driver (message `NoSuchDriverException` ou
> erreur réseau vers `googlechromelabs.github.io`), voir Dépannage §10.3 — solution de
> repli avec téléchargement manuel du binaire.

## 7. OmniParser — code et poids (dépôt tiers, à cloner séparément)

Le `.gitignore` de ce projet exclut entièrement le dossier `OmniParser/` : ni son code, ni
ses poids ne sont sur ce dépôt Git (poids ≈ 4 Go). Il faut les récupérer indépendamment.

```powershell
cd E:\NIVEAU4\Stage\Projet1
git clone https://github.com/microsoft/OmniParser.git
```

⚠️ **À confirmer** : `omni_engine.py` attend-il ce dossier à la racine du projet
(`Projet1\OmniParser\`) comme ci-dessus, ou ailleurs (ex. `Projet1\src\OmniParser\`) ? Le
chemin exact conditionne l'import dans `omni_engine.py` — à corriger dans cette section une
fois confirmé.

Puis, téléchargez les poids YOLO + Florence-2 sous `weights/` :

```powershell
hf download microsoft/Florence-2-base --local-dir weights\icon_caption_florence --include "*.json" "*.txt"
hf download microsoft/Florence-2-base --local-dir weights\icon_caption_florence --include "*.py"
```

⚠️ **À confirmer** : ce chemin `weights\...` est-il relatif à la racine du projet
(`Projet1\weights\`) ou au sous-dossier `OmniParser\` cloné juste au-dessus
(`Projet1\OmniParser\weights\`) ? C'est important pour que le `.gitignore` protège
effectivement ces fichiers — voir la note en tête de ce guide sur l'incohérence détectée.

Structure attendue (à confirmer/corriger) :
```
OmniParser/
├── weights/
│   ├── icon_detect/              (poids YOLO)
│   └── icon_caption_florence/    (config.json, preprocessor_config.json,
│                                   tokenizer.json, processing_florence2.py, ...)
```

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

⚠️ **À confirmer** : les commandes ci-dessous supposent des noms de fichiers/points d'entrée
que je n'ai pas pu vérifier — merci de corriger avec les vrais noms.

**Traiter un cas d'usage ponctuel** (produit des fichiers JSON/CSV/SQLite + un rapport PDF) :
```powershell
python executer_cas_usage.py
```

**Lancer l'interface web** (FastAPI) :
```powershell
uvicorn <module_a_confirmer>:app --reload
```
puis ouvrir `http://127.0.0.1:8000` dans un navigateur.

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
  télécharger manuellement le binaire ChromeDriver correspondant à votre version de Chrome
  depuis `https://storage.googleapis.com/chrome-for-testing-public/` et le placer dans un
  dossier `drivers/` référencé explicitement dans `navigator.py`.

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
python executer_cas_usage.py

# Lancer l'interface web
uvicorn <module_a_confirmer>:app --reload
```

---

## Points à confirmer avant de committer ce guide

1. **Chemin du dossier OmniParser** : à la racine du projet, ou ailleurs ?
2. **Chemin des poids** (`weights/`) : sous `OmniParser/` ou à la racine du projet ? (conditionne aussi la correction du `.gitignore`)
3. **Contenu réel du `.env`** : quelles variables `security.py` lit-il effectivement ?
4. **Point d'entrée FastAPI** : nom du fichier/module et de la variable `app` (pour la commande `uvicorn`)
5. **Syntaxe exacte de `executer_cas_usage.py`** : arguments en ligne de commande, ou entièrement interactif ?