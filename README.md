# Agent RAG — Microfinance au Cameroun

Stage M1 Data Science — YB-TECHs
Agent d'Analyse et de Valorisation des Interactions d'un Système RAG

**Étudiant :** Janvion Hamayadji
**Encadrement :** Yris Brice Wandji Piugie, PhD — Fondateur & CEO, YB-TECHs
**Durée :** 2 mois (Juillet–Août 2026)

---

## Présentation du projet

Ce projet vise à concevoir une architecture unique et intégrée de collecte, d'évaluation et de valorisation des données d'interaction d'un système RAG (Retrieval-Augmented Generation), afin de transformer un système RAG « boîte noire » en un système pilotable, mesurable et interrogeable en langage naturel.

**Thème documentaire :** Microfinance au Cameroun (réglementation COBAC, établissements de microfinance agréés, institutions locales).

## Architecture du pipeline

```
Corpus documentaire → Agent RAG maison → Journal d'interactions
→ Nettoyage (Pandas) → Évaluation (RAGAS) → Modélisation (scikit-learn)
→ Indexation → Dashboard + Copilot conversationnel
```

## Structure du dépôt

```
.
├── data/
│   ├── raw/            # Corpus documentaire brut (non versionné, voir .gitignore)
│   └── processed/       # Jeu de données d'interactions nettoyé (non versionné)
├── docs/                # Documentation technique, note de cadrage
├── notebooks/           # Notebooks Jupyter (EDA, RAGAS, modélisation)
├── src/                 # Code source du projet
│   └── ragas_compat.py  # Correctif de compatibilité RAGAS (voir section dédiée)
├── tests/               # Tests unitaires et d'intégration (pytest)
├── requirements.txt     # Dépendances exactes de l'environnement Python
└── README.md
```

## Stack technique

| Outil | Rôle |
|---|---|
| Python 3.11 | Langage principal |
| Ollama + Llama 3.2 3B | LLM local (voir justification ci-dessous) |
| LangChain | Orchestration du pipeline RAG |
| FAISS / ChromaDB | Base vectorielle |
| sentence-transformers | Embeddings |
| Pandas | Nettoyage et structuration des données |
| RAGAS | Évaluation de la qualité RAG |
| scikit-learn | Modélisation légère (scoring / clustering) |
| Streamlit | Dashboard et interface Copilot |
| pytest | Tests unitaires et d'intégration |

### Note sur le choix du LLM local

Le cahier des charges recommande Mistral 7B-Instruct ou Llama 3.1 8B. Compte tenu d'une contrainte matérielle réelle (CPU sans GPU dédié, 8 Go de RAM), **Llama 3.2 3B** a été retenu comme alternative, validée avec le tuteur. Cette décision est documentée dans `docs/Note_de_cadrage_S1.md` et sera discutée dans le rapport final (section limites du système).

## Installation

### Prérequis
- Python 3.11 (via Conda recommandé)
- [Ollama](https://ollama.com) installé localement
- Git

### Mise en place de l'environnement

```bash
# Cloner le dépôt
git clone https://github.com/YB-TECHs/<nom-du-depot>.git
cd <nom-du-depot>

# Créer l'environnement Conda
conda create -n rag-stage python=3.11
conda activate rag-stage

# Installer les dépendances
pip install -r requirements.txt

# Télécharger le modèle LLM local
ollama pull llama3.2:3b
```

### Correctif de compatibilité RAGAS

`ragas` 0.3.9 contient un bug de compatibilité connu avec les versions récentes de `langchain-community` (import cassé vers `langchain_community.chat_models.vertexai`). Un correctif est appliqué automatiquement via `src/ragas_compat.py`, qui doit être importé **avant** tout import de `ragas` :

```python
import sys
sys.path.insert(0, "src")
import ragas_compat  # doit précéder l'import de ragas
import ragas
```

Aucune action manuelle supplémentaire n'est requise après `pip install -r requirements.txt`.

## Utilisation

*(Section à compléter au fur et à mesure de l'avancement du projet — semaines 2 à 8)*

## Documentation

- [Note de cadrage (Semaine 1)](docs/Note_de_cadrage_S1.md)

## Licence

*(À préciser selon les consignes de YB-TECHs)*
